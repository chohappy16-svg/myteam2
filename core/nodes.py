"""4대 핵심 노드 로직 함수 모듈
- Node 1: Parse & Anchor (B2C 목적 기반 동적 프레이밍 및 실측 쿼리 2개 생성)
- Node 2: Web Research & HF Filter (Tavily 복수 쿼리 수집 + HF PR 필터링)
- Node 2-R: Query Regeneration (검색 쿼리 재시도)
- Node 3: Outline Generator (가설 및 SCQA 목차 생성)
- Node 4: Draft Final Report (환각 0% B2C 고밀도 실무 1장 보고서 렌더링)
"""

import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from core.state import AgentState, ParsedAnchorOutput, OutlineOutput
from core.tools import search_web_articles, filter_pr_articles

# ------------------------------------------------------------------------------
# LLM 클라이언트 인스턴스 초기화
# ------------------------------------------------------------------------------
FAST_MODEL = "gpt-4o-mini"

def get_llm(temperature: float = 0.2):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ .env에 OPENAI_API_KEY가 설정되어 있지 않습니다.")
    return ChatOpenAI(model=FAST_MODEL, temperature=temperature)


# ==============================================================================
# Node 1: 지시 분석 및 동적 프레이밍 (Parse & Anchor with Dynamic Mirroring)
# ==============================================================================
def parse_and_anchor_node(state: AgentState) -> Dict[str, Any]:
    """
    사용자가 선택한 [보고서 목적]과 [자사 고민/넋두리]를 결합하여
    3대 동적 미러링 요소(배경, 핵심 과제, 조사 목표)를 도출하고,
    실제 정량 팩트를 찾기 위한 실무 벤치마크 검색 쿼리 2개를 생성합니다.
    (내부 수치 날조 엄격 금지)
    """
    raw_query = state.get("raw_query", "")
    llm = get_llm(temperature=0.1)
    structured_llm = llm.with_structured_output(ParsedAnchorOutput)

    system_prompt = """당신은 냉철하고 날카로운 B2C 이커머스 전문 전략 컨설턴트입니다.
사용자가 선택한 [보고서 목적]과 [자사 고민/넋두리]를 분석하여 다음 [3대 동적 미러링 요소]와 [실측 벤치마크 쿼리 2개]를 도출하세요.

[1. 3대 동적 미러링 필수 정의 (Dynamic Mirroring)]
1. 배경 (Background): 선택된 보고서 목적과 사용자의 고민 상황을 품격 있는 비즈니스 문장으로 재정의하십시오.
2. 핵심 과제 (Core Challenge): 이번 건에서 해결해야 할 실무 병목 (CVR 저하, 객단가 정체, 솔루션 검토, 소재 개선, 재구매 리텐션 등)을 명확히 규정하십시오.
3. 조사 목표 (Research Goal): 타사에서 무엇을 벤치마크하여 실질적 성과를 입증할지 명확한 리서치 목적을 도출하십시오.

[2. 내부 사정 수치 날조 절대 금지 규칙 - 위반 시 감점]
- 사용자가 지시문에 직접 명시하지 않은 사내 내부 수치(예: "고객 이탈률 40%", "현재 전환율 1.2%", "월 매출 몇 억")를 절대로 임의로 지어내지 마십시오.
- 사용자가 언급한 고민과 상황의 맥락 자체에만 집중하여 비즈니스 언어로 구조화하십시오.

[3. 실무 벤치마크 검색 쿼리 2개(search_queries) 생성 필수 규칙]
- 실제 정량 데이터와 사례가 포함된 양질의 기사를 찾기 위해, 쿼리에 "리포트", "백서", "전환율", "증가", "도입 성과", "성공 사례" 같은 실측 키워드를 반드시 결합한 벤치마크 쿼리 2개를 생성하십시오.
  - 쿼리 예시 1: "[제품/카테고리] [조사 목표 키워드] 도입 성과 리포트"
  - 쿼리 예시 2: "[제품/카테고리] CVR 프로모션 백서 성공 사례"
- 거대 산업 리포트, 글로벌 시장 통계 등 추상적인 거시 통계 쿼리는 엄격히 금지합니다.
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
        "angle": parsed.reporting_angle,
        "background": parsed.background,
        "core_challenge": parsed.core_challenge,
        "research_goal": parsed.research_goal
    }

    queries: List[str] = parsed.search_queries if parsed.search_queries else []
    if not queries and parsed.search_query:
        queries = [parsed.search_query]
    if not queries:
        queries = [f"{raw_query} 벤치마크 사례 리포트", f"{raw_query} CVR 개선 성과 백서"]

    return {
        "anchors": anchors,
        "search_queries": queries,
        "search_retry_count": 0
    }


# ==============================================================================
# Node 2: 웹 리서치 및 HF Zero-Shot PR 필터링 (Research & Filter)
# ==============================================================================
def research_and_filter_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 1에서 생성된 2개 쿼리를 활용하여 Tavily로 실무 팩트를 수집하고, 
    HF mDeBERTa를 통해 PR/광고성 기사를 배제합니다.
    """
    search_queries = state.get("search_queries", [])
    queries_to_run = search_queries[:2] if search_queries else [state.get("raw_query", "")]

    # 1. Tavily 복수 쿼리 검색 실행 및 URL 중복 제거
    all_raw = []
    seen_urls = set()

    for query in queries_to_run:
        if not query.strip():
            continue
        articles = search_web_articles(query=query, max_results=3)
        for art in articles:
            url = art.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_raw.append(art)

    if not all_raw and search_queries:
        all_raw = search_web_articles(query=search_queries[-1], max_results=5)

    # 2. HF mDeBERTa PR 노이즈 필터링 (임계값 0.5)
    filtered_articles, dropped_articles = filter_pr_articles(all_raw, threshold=0.5)

    # 3. 안전장치: 필터링 통과 팩트가 전무한 경우 원본 기사 중 상위 2건을 긴급 fallback
    if len(filtered_articles) < 2 and all_raw:
        filtered_articles = all_raw[:2]

    return {
        "raw_articles": all_raw,
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
보도자료나 광고를 피하고 실제 산업 현장의 적용 사례, 도입 성과, CVR/ROAS 지표가 검색되도록 
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
    정제된 팩트와 동적 미러링 앵커를 결합하여 '가설 1줄'과 SCQA 3대 목차를 생성합니다.
    """
    anchors = state.get("anchors", {})
    filtered_articles = state.get("filtered_articles", [])
    stakeholder = anchors.get("stakeholder", "사내 경영진 및 실무진")

    facts_summary = "\n".join([
        f"- {art.get('title')}: {art.get('content')[:150]}"
        for art in filtered_articles[:3]
    ])

    llm = get_llm(temperature=0.3)
    structured_llm = llm.with_structured_output(OutlineOutput)

    system_prompt = """당신은 맥킨지 출신 전략 컨설턴트입니다.
수집된 외부 시장 팩트와 사내 앵커(배경, 핵심 과제, 조사 목표, KPI, 보고 대상자 관점)를 결합하여,
특히 [보고 대상자(수신자 관점)]의 눈높이와 의사결정 기준에 최적화된 '가설 1줄'과 3단 논리 목차를 작성하세요.

[규칙]
1. 가설: "타사의 ~ 도입/운영 성공 사례를 볼 때, 우리 조직은 ~ 방식으로 접근해야 KPI를 달성할 수 있다"는 식의 구체적 1줄 명제 (보고 대상자의 관심 지표를 직접적으로 관통할 것)
2. 목차(outline): 반드시 정확히 다음 구조를 반영하되, 보고 대상자가 즉시 납득할 수 있는 명확한 소제목 리스트 3개로 작성할 것
   - [1] 당면 과제 및 기획 배경 (Situation & Challenge)
   - [2] 타사 벤치마크 및 시장 팩트 (Market Fact Benchmark)
   - [3] 즉시 실행 권고안 (Action Plan)
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "동적 미러링 앵커: {anchors}\n보고 대상자(수신자 관점): {stakeholder}\n수집된 핵심 팩트:\n{facts}")
    ])

    chain = prompt | structured_llm
    result: OutlineOutput = chain.invoke({
        "anchors": str(anchors),
        "stakeholder": stakeholder,
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
    확정된 목차와 팩트를 기반으로 사내 보고용 고신뢰도 1장 SCQA 마크다운 보고서를 작성합니다.
    (수치 환각 0% 헌법 준수, 가짜 브랜드 금지, 변명성 문장 100% 금지, 비교 표 강제)
    """
    anchors = state.get("anchors", {})
    hypothesis = state.get("hypothesis", "")
    outline = state.get("outline", [])
    filtered_articles = state.get("filtered_articles", [])

    background = anchors.get("background", "자사몰 및 상품 페이지의 경쟁력 강화 및 비즈니스 전환율 제고")
    core_challenge = anchors.get("core_challenge", "구매 전환율(CVR) 극대화 및 고객 이탈 방지")
    research_goal = anchors.get("research_goal", "동종 업계 성공 사례 벤치마킹을 통한 실무 액션 도출")
    stakeholder = anchors.get("stakeholder", "사내 경영진 및 실무진")

    articles_context = "\n\n".join([
        f"출처: {art.get('title')} ({art.get('url')})\n내용: {art.get('content')}"
        for art in filtered_articles
    ])

    llm = get_llm(temperature=0.2)

    system_prompt = """당신은 냉철하고 날카로운 C-Level 직속 B2C 이커머스 전략 컨설턴트입니다.
상사/대표/협업팀 등 지정된 보고 수신자가 3초 만에 핵심 수치와 실행 방안을 파악할 수 있도록, A4 1장 규격의 고밀도 개조식 비즈니스 전략 브리프를 작성하세요.

[수치 환각 원천 차단 헌법 (Negative Constraints) - 절대 준수]
1. No Metric, No Table (수치 날조 절대 금지):
   - 제공된 기사 원문에 %, 배수, 금액, 건수 등 구체적 정량 수치가 명시되어 있지 않은 내용은 절대로 임의의 숫자를 지어내지 마십시오.
   - 만약 기사에 정량 수치가 없다면 숫자를 소설 쓰듯 창작하지 말고, '정성적 개선 사례 (수치 미공개)'로 솔직하게 기재하십시오.
2. 가짜 브랜드 창작 영구 금지:
   - 기사 원문에 구체적 브랜드명이 없다면, 'Brand A', 'B사' 같은 가상 명칭을 절대 쓰지 마십시오.
   - 대신 '크리마 이커머스 백서', '아이보스 리포트', '브이리뷰 분석' 등 실제 발행처나 솔루션 명칭을 정직하게 기재하십시오.
3. 기준 시점(발행 연월) 명시:
   - 표의 마지막 열에 출처와 함께 언제적 데이터인지 [기준 시점(발행 연월)]을 반드시 표기하십시오 (예: `2024.03 [출처](URL)` 또는 `발행 시점 미표기 [출처](URL)`).
4. 변명성/자원 핑계 문장 100% 배제:
   - "사내 개발 인력 부족", "개발 인력", "외부 솔루션 의존", "인프라 한계로 인해", "어쩔 수 없" 같은 사내 자원 핑계나 패배주의적 넋두리 문장을 단 한 단어도 적지 마십시오.
5. 순수 마크다운 준수: HTML 태그(<div>, <style> 등)를 일체 사용하지 마십시오.

[반드시 준수해야 할 고밀도 개조식 4대 출력 규격]
반드시 다음 목차 구조를 정확한 마크다운 문법으로 출력하십시오:

# 💡 핵심 결론 (Hypothesis)
(선택한 목적을 달성하기 위해 어떤 핵심 레버를 건드릴지 2~3줄로 단도직입적으로 제시)

## [1] 당면 과제 및 기획 배경
- **배경 (Background)**: (제공된 배경 내용을 바탕으로 품격 있는 비즈니스 문장으로 요약)
- **핵심 과제 (Core Challenge)**: (해결해야 할 실무 병목 요인을 요약)
- **조사 목표 (Research Goal)**: (타사 벤치마크를 통해 얻고자 하는 목적 명시)

## [2] 타사 벤치마크 및 시장 팩트
- 수집된 팩트 데이터를 바탕으로 실제 확인된 성공 사례 및 지표를 반드시 [마크다운 비교 표] 형태로 깔끔하게 정리하십시오.
| 구분 / 브랜드 | 타사 벤치마크 팩트 및 달성 성과 | 자사 적용점 (Key Takeaway) | 기준 시점 & 출처 |
| :--- | :--- | :--- | :--- |
| (위 형태의 표를 작성하고, 각 행마다 실측 수치와 기준 시점 & [출처](URL) 링크 각주를 반드시 포함하십시오)

## [3] 즉시 실행 권고안 (Action Plan)
- 내일 당장 실행 가능한 실무 액션 3가지와 소요 기간을 명시하십시오:
  1. **[액션 1]** 세부 실행 내용 (소요 기간: X일)
  2. **[액션 2]** 세부 실행 내용 (소요 기간: X일)
  3. **[액션 3]** 세부 실행 내용 (소요 기간: X일)
"""

    user_content = f"""[분석 및 보고서 작성 컨텍스트]
- 핵심 앵커 및 동적 미러링 정보:
  * 배경: {background}
  * 핵심 과제: {core_challenge}
  * 조사 목표: {research_goal}
  * 부서 KPI: {anchors.get('kpi', '')}
  * 보고 대상자(수신자 성향): {stakeholder}
  * 보고 앵글: {anchors.get('angle', '')}
- 분석 가설: {hypothesis}
- 검토된 목차 방향: {outline}

[수집된 외부 시장 팩트 데이터]
{articles_context}

위 지침에 따라 가짜 브랜드/수치 날조와 변명성 문장을 일체 배제하고, 반드시 마크다운 비교 표를 포함하여 [핵심 결론] -> [당면 과제 및 기획 배경] -> [타사 벤치마크 및 시장 팩트] -> [즉시 실행 권고안]의 4단 고밀도 개조식 브리프로 작성해 주세요.
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ])

    return {
        "final_report": response.content.strip()
    }