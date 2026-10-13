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

    system_prompt = """당신은 비즈니스 전략 기획 전문가입니다.
사용자의 거친 넋두리나 상사의 모호한 구두 지시를 분석하여 보고서의 4대 핵심 앵커를 구조화하고, 
외부 비즈니스 팩트를 수집할 Tavily 검색 쿼리를 생성하세요.

[규칙]
1. KPI: 구체적인 정량/정성 목표 (예: 물류비 15% 절감, 배차 지연율 개선 등)
2. 태도(stakeholder_mood): 성과 갈증(공격형) / 리스크 우려(방어형) / 원인 규명(분석형) 중 선택
3. 제약(system_constraints): 레거시 시스템, 3개월 내 납기, 인력 부족 등 현실적 한계 반영
4. 앵글(reporting_angle): 비용 절감 및 효율화 / 리스크 선제 방어 / 신규 사업 기회 / 기술 역량 내재화 / 경쟁사 벤치마킹 중 선택
5. 검색 쿼리: 보도자료나 광고를 피하고 실질적인 산업 동향/지표가 나올 수 있는 명확한 키워드 문장
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

    llm = get_llm(temperature=0.3)

    system_prompt = """당신은 대기업 비즈니스 전략실 수석 부사수입니다.
상사의 성향과 사내 제약 조건을 철저히 반영하여 1장(A4 1페이지 분량, 약 800~1,200자)의 
고밀도 마크다운 비즈니스 동향 보고서를 작성하세요.

[작성 원칙]
1. 단순 팩트 나열 금지: 모든 문단은 "그래서 우리 조직은 무엇을 해야 하는가?(So What)"로 귀결되어야 함.
2. 상사 성향 반영: 
   - 공격형: 기대 ROI 및 신속 실행 전략 강조
   - 방어형: 실패 리스크 예방 및 단계적 검증 강조
   - 분석형: 구체적 근거 데이터와 인과관계 위주 서술
3. 지정된 3대 목차를 `## 소제목` 형식으로 온전히 반영할 것.
4. 출처 링크 표기: 각 팩트 뒤에 [출처](URL) 형태로 각주를 달 것.

Fallback 안전장치 내장 (research_and_filter_node):
HF mDeBERTa 모델이 과도하게 엄격하여 기사 5건이 모두 배제되더라도, 
파이프라인이 즉시 크래시되지 않도록 원본 기사 상위 2건을 긴급 공급하여 다음 노드로 전달합니다.

단일 책임 준수 (Partial Update):
각 노드는 자신이 수정한 데이터(anchors, filtered_articles, hypothesis, final_report 등)만 
딕셔너리로 반환하므로 상태 덮어쓰기 버그가 원천 차단됩니다.

Pydantic Structured Output 결합:
Node 1과 Node 3은 LLM의 자유 줄글 대신 정확한 키값을 가진 데이터 객체로 결과물을 산출하므로, 
이후 노드와 프론트엔드가 안정적으로 읽어들일 수 있습니다.
"""

    user_content = f"""[보고서 작성 메타데이터]
- 4대 앵커: {anchors}
- 핵심 가설: {hypothesis}
- 확정된 3대 목차:
  1. {outline[0] if len(outline) > 0 else '상황 및 당면 과제'}
  2. {outline[1] if len(outline) > 1 else '시장 동향 및 팩트 분석'}
  3. {outline[2] if len(outline) > 2 else '시사점 및 실행 방안'}

[참고할 검증 팩트 데이터]
{articles_context}
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ])

    return {
        "final_report": response.content.strip()
    }