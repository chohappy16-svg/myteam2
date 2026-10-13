"""4대 핵심 노드 로직 함수 모듈
- Node 1: Parse & Anchor (넋두리 파싱 및 검색 키워드 추출)
- Node 2: Web Research & HF Filter (Tavily 수집 + HF PR 필터링)
- Node 2-R: Query Regeneration (검색 쿼리 재시도)
- Node 3: Outline Generator (가설 및 SCQA 목차 생성)
- Node 4: Draft Final Report (최종 1장 SCQA 보고서 작성)
"""

import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from core.state import AgentState, ParsedAnchorOutput, OutlineOutput
from core.tools import search_web_articles, filter_pr_articles

# ------------------------------------------------------------------------------
# LLM 클라이언트 인스턴스 초기화
# 속도와 비용을 고려하여 파싱/목차에는 mini, 최종 보고서에도 고속 모델을 매핑합니다.
# ------------------------------------------------------------------------------
FAST_MODEL = "gpt-4o-mini"

def get_llm(temperature: float = 0.2):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ .env에 OPENAI_API_KEY가 설정되어 있지 않습니다.")
    return ChatOpenAI(model=FAST_MODEL, temperature=temperature)


# ==============================================================================
# Node 1: 지시문 파싱 및 4대 앵커 고정 (Parse & Anchor)
# ==============================================================================
def parse_and_anchor_node(state: AgentState) -> Dict[str, Any]:
    """
    사용자의 모호한 넋두리/지시에서 4대 앵커(KPI, 제약, 태도, 앵글)를 확정하고,
    Tavily 검색용 최적 키워드 1개를 생성합니다.
    """
    raw_query = state.get("raw_query", "")
    llm = get_llm(temperature=0.1)
    structured_llm = llm.with_structured_output(ParsedAnchorOutput)

    system_prompt = """당신은 실무 중심의 이커머스 & 비즈니스 전략 컨설턴트입니다.
사용자의 지시문에서 핵심 대상 제품/서비스와 실무 과제를 정확히 파악하여 4대 핵심 앵커를 구조화하고, 
실제 매출 증대 및 실행에 직결되는 고정밀 비즈니스 팩트 검색 쿼리 1개를 생성하세요.

[검색 쿼리(search_query) 생성 필수 규칙 - 절대 준수]
1. 타깃 직격 검색: 사용자가 언급한 구체적 제품/아이템(예: 레깅스, 이너웨어, 뷰티, 영양제 등)을 반드시 검색어의 최우선 핵심 키워드로 포함하십시오.
2. 거대 산업 리포트 검색 절대 금지: "글로벌 시장 전망", "고령화 통계", "산업 생태계", "거대 물류 인프라" 같은 엉뚱하고 추상적인 거시 통계 쿼리를 절대 생성하지 마십시오. (예: 레깅스 질문에 유모차/보행기 시장 등을 검색하는 행위 엄격 금지)
3. 실무 전환 지표 타겟팅: "상세페이지 구매 전환율(CVR) 개선 사례", "D2C 마케팅 프로모션 전략", "고객 후기 리뷰 최적화", "객단가 상승 벤치마크", "인기 브랜드 마케팅 성공 사례" 등 실제 실무 전략과 성과 지표가 나오는 구체적 키워드 조합으로 작성하십시오.
4. 예시:
   - 나쁜 쿼리: 글로벌 패션 의류 산업 시장 동향 및 전망 리포트
   - 좋은 쿼리: 여성 요가 레깅스 자사몰 상세페이지 구매 전환율 프로모션 마케팅 성공 사례
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "지시 및 상황: {raw_query}")
    ])

    chain = prompt | structured_llm
    parsed: ParsedAnchorOutput = chain.invoke({"raw_query": raw_query})

    anchors = {
        "kpi": parsed.department_kpi,
        "stakeholder": parsed.stakeholder_mood,
        "constraints": parsed.system_constraints,
        "angle": parsed.reporting_angle
    }

    return {
        "anchors": anchors,
        "search_queries": [parsed.search_query],
        "search_retry_count": 0
    }


# ==============================================================================
# Node 2: 웹 리서치 및 HF Zero-Shot PR 필터링 (Research & Filter)
# ==============================================================================
def research_and_filter_node(state: AgentState) -> Dict[str, Any]:
    """
    Tavily로 기사 5건을 수집하고, HF mDeBERTa를 통해 PR/광고성 기사를 배제합니다.
    """
    search_queries = state.get("search_queries", [])
    query = search_queries[-1] if search_queries else state.get("raw_query", "")

    # 1. Tavily 검색 실행 (최대 5건)
    raw_articles = search_web_articles(query=query, max_results=5)

    # 2. HF mDeBERTa PR 노이즈 필터링 (임계값 0.5)
    filtered_articles, dropped_articles = filter_pr_articles(raw_articles, threshold=0.5)

    # 3. 안전장치: 필터링 통과 팩트가 전무한 경우 원본 기사 중 상위 2건을 긴급 fallback
    if len(filtered_articles) < 2 and raw_articles:
        filtered_articles = raw_articles[:2]

    return {
        "raw_articles": raw_articles,
        "filtered_articles": filtered_articles
    }


# ==============================================================================
# Node 2-R: 검색 쿼리 재생성 (Query Rewrite - 루프백 노드)
# ==============================================================================
def rewrite_query_node(state: AgentState) -> Dict[str, Any]:
    """
    유효 팩트가 부족할 때, 검색 범위를 확장하거나 산업 표준 용어로 키워드를 재작성합니다.
    """
    raw_query = state.get("raw_query", "")
    anchors = state.get("anchors", {})
    retry_count = state.get("search_retry_count", 0)

    llm = get_llm(temperature=0.3)

    system_prompt = """당신은 테크 리서치 전문가입니다.
기존 검색어로는 충분한 비즈니스 팩트를 확보하지 못했습니다. 
보도자료나 광고를 피하고 실제 산업 현장의 적용 사례, 도입 비용, ROI 지표가 검색되도록 
더 넓고 객관적인 비즈니스 동향 검색 쿼리 1개를 한 줄로 작성하세요."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "기존 의도: {raw_query}\n보고 앵글: {angle}\n기존 쿼리: {prev_queries}")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "raw_query": raw_query,
        "angle": anchors.get("angle", "비용 절감 및 효율화"),
        "prev_queries": ", ".join(state.get("search_queries", []))
    })

    new_query = response.content.strip().replace('"', '')
    queries = state.get("search_queries", []) + [new_query]

    return {
        "search_queries": queries,
        "search_retry_count": retry_count + 1
    }


# ==============================================================================
# Node 3: 가설 도출 및 SCQA 목차 생성 (Outline Generator)
# ==============================================================================
def generate_outline_node(state: AgentState) -> Dict[str, Any]:
    """
    정제된 팩트와 4대 앵커를 결합하여 '가설 1줄'과 SCQA 3대 목차를 생성합니다.
    (HITL 진입 전 검토 대상 데이터)
    """
    anchors = state.get("anchors", {})
    filtered_articles = state.get("filtered_articles", [])

    facts_summary = "\n".join([
        f"- {art.get('title')}: {art.get('content')[:150]}"
        for art in filtered_articles[:3]
    ])

    llm = get_llm(temperature=0.3)
    structured_llm = llm.with_structured_output(OutlineOutput)

    system_prompt = """당신은 맥킨지 출신 전략 컨설턴트입니다.
수집된 외부 시장 팩트와 사내 앵커(KPI, 제약조건, 보고 앵글)를 결합하여,
우리 조직 관점의 '가설 1줄'과 3단 논리 목차(상황/문제, 팩트 분석, 시사점 및 제언)를 작성하세요.

[규칙]
1. 가설: "타사의 ~ 도입 사례를 볼 때, 우리 조직은 ~ 제약 속에서 ~ 방식으로 접근해야 KPI를 달성할 수 있다"는 식의 구체적 명제
2. 목차(outline): 반드시 정확히 3개의 소제목 리스트로 작성할 것
   - [1] 상황 및 당면 과제 (SCQA 중 Situation & Complication)
   - [2] 시장 동향 및 경쟁사 팩트 분석 (Question & 팩트 요약)
   - [3] 우리 조직 관점의 시사점 및 실행 방안 (Answer & So-What 제언)
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "4대 앵커: {anchors}\n수집된 핵심 팩트:\n{facts}")
    ])

    chain = prompt | structured_llm
    result: OutlineOutput = chain.invoke({
        "anchors": str(anchors),
        "facts": facts_summary
    })

    return {
        "hypothesis": result.hypothesis,
        "outline": result.outline
    }


# ==============================================================================
# Node 4: 1장 분량 최종 마크다운 보고서 생성 (Draft Final Report)
# ==============================================================================
def draft_report_node(state: AgentState) -> Dict[str, Any]:
    """
    확정된 목차와 팩트를 기반으로 사내 보고용 1장 SCQA 마크다운 보고서를 작성합니다.
    """
    anchors = state.get("anchors", {})
    hypothesis = state.get("hypothesis", "")
    outline = state.get("outline", [])
    filtered_articles = state.get("filtered_articles", [])

    articles_context = "\n\n".join([
        f"출처: {art.get('title')} ({art.get('url')})\n내용: {art.get('content')}"
        for art in filtered_articles
    ])

    llm = get_llm(temperature=0.2)

    system_prompt = """당신은 냉철하고 날카로운 C-Level 직속 전략 컨설턴트입니다.
상사/대표가 3초 만에 핵심 수치와 실행 방안을 파악할 수 있도록, A4 1장 규격의 고밀도 개조식 비즈니스 전략 브리프를 작성하세요.

[절대 금지 사항 - 위반 시 감점]
1. 변명성 문장 출력 엄격 금지: "사내 개발 인력 부족", "외부 솔루션 의존", "인프라 한계로 인해" 같은 회사 핑계나 패배주의적 넋두리 문장을 단 한 단어도 적지 마십시오.
2. 설명조 줄글 작성 금지: 긴 줄글이나 모호한 원론 나열을 일체 배제하고, 수치와 액션 중심의 날카로운 개조식(불릿 포인트, 볼드 하이라이트)으로만 작성하십시오.

[반드시 준수해야 할 고밀도 개조식 4대 출력 규격]
반드시 다음 목차 구조를 정확한 마크다운 문법으로 출력하십시오:

# 💡 핵심 결론 (Hypothesis)
(2~3줄로 무엇을 어떻게 바꾸어 구매 전환율(CVR)이나 매출/지표를 올릴지 단도직입적으로 제시)

## [1] 현 상황 및 핵심 병목
- 고객 이탈 구간, 후기/상세페이지 미흡, 소구점 불명확 등 실무 관점의 핵심 병목 요인을 불릿 포인트 2~3개로 날카롭게 요약하십시오.

## [2] 타사 벤치마크 및 전환 최적화 팩트
- 수집된 팩트 데이터를 바탕으로 경쟁사/타사 성공 사례 및 핵심 지표(CVR, ROAS, 객단가 등)를 반드시 [마크다운 비교 표] 형태로 깔끔하게 정리하십시오.
| 구분 / 브랜드 | 적용 전략 및 핵심 소구점 | 달성 성과 및 전환율(CVR) 지표 | 출처 |
| :--- | :--- | :--- | :--- |
(위 형태의 표를 작성하고, 각 팩트마다 [출처](URL) 링크 각주를 포함하십시오)

## [3] 즉시 실행 권고안 (Action Plan)
- 거창한 장기 과제가 아니라, 당장 1~2주 내 현업 실무진이 즉시 실행 가능한 구체적 액션 3가지와 소요 기간을 명시하십시오:
  1. **[액션 1]** 세부 실행 내용 (소요 기간: X일)
  2. **[액션 2]** 세부 실행 내용 (소요 기간: X일)
  3. **[액션 3]** 세부 실행 내용 (소요 기간: X일)
"""

    user_content = f"""[분석 및 보고서 작성 컨텍스트]
- 핵심 앵커: {anchors}
- 분석 가설: {hypothesis}
- 검토된 목차 방향: {outline}

[수집된 외부 시장 팩트 데이터]
{articles_context}

위 지침에 따라 변명성 문장을 일체 배제하고, 반드시 마크다운 비교 표를 포함하여 [핵심 결론] -> [현 상황 및 핵심 병목] -> [타사 벤치마크 및 전환 최적화 팩트(표)] -> [즉시 실행 권고안]의 4단 고밀도 개조식 브리프로 작성해 주세요.
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ])

    return {
        "final_report": response.content.strip()
    }