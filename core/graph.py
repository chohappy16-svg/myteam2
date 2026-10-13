"""LangGraph 워크플로우 조립 및 컴파일 모듈
StateGraph 구성, 조건부 분기(HITL 3-Way 등), Checkpointer 세션 격리 적용

human_gate 패스스루 노드 도입 이유:
임의의 노드 중간에 복잡한 조건 분기와 인터럽트를 섞으면 디버깅 추적이 어려워집니다. 
human_gate라는 명시적인 대기 노드를 두면, "그래프가 정확히 어디서 멈췄고 사용자가 무엇을 결정해야 하는지" 명확하게 분리됩니다.

MemorySaver 기반 세션 격리 (thread_id):
컴파일 시 checkpointer를 바인딩해 두었기 때문에, 
실행 시 {"configurable": {"thread_id": "사번-세션ID"}}만 넘겨주면 사용자별로 상태가 격리 보존됩니다.

Time-Travel (앵글 피벗) 지원:
사용자가 pivot_angle을 선택하면 이미 수집·필터링된 filtered_articles 팩트 풀은 그대로 유지된 채 
generate_outline으로 롤백되어, Tavily 검색 비용과 대기 시간을 낭비하지 않고 목차만 즉각 다시 만듭니다.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import AgentState
from core.nodes import (
    parse_and_anchor_node,
    research_and_filter_node,
    rewrite_query_node,
    generate_outline_node,
    draft_report_node,
)


# ==============================================================================
# 1. 조건부 분기 라우팅 함수 (Conditional Edge Routers)
# ==============================================================================
def route_after_research(state: AgentState) -> Literal["rewrite_query", "generate_outline"]:
    """
    [TC-2 / Loopback 검증]
    유효 팩트가 2건 미만이고 재시도 횟수가 1회 미만인 경우 Node 2-R(쿼리 재생성)로 루프백,
    충분한 팩트를 확보했거나 이미 재시도한 경우 Node 3(목차 생성)으로 진행합니다.
    """
    filtered_articles = state.get("filtered_articles", [])
    retry_count = state.get("search_retry_count", 0)

    if len(filtered_articles) < 2 and retry_count < 1:
        return "rewrite_query"
    return "generate_outline"


def human_gate_node(state: AgentState) -> Dict[str, Any]:
    """
    HITL 일시 정지를 위한 명시적 인터럽트 게이트 노드.
    그래프 상태를 그대로 보존하며 사용자의 승인/피벗 입력을 대기합니다.
    """
    return {}


def route_after_human_gate(
    state: AgentState
) -> Literal["draft_report", "generate_outline", "parse_and_anchor"]:
    """
    [TC-4 HITL 3-Way 라우팅 검증]
    사용자의 선택에 따라 다음 실행 경로를 결정합니다.
    - 'approve': 목차 승인 -> 최종 보고서 작성(Node 4) 직행
    - 'pivot_angle': 앵글 수정 -> 팩트는 보존한 채 목차 재생성(Node 3) 롤백
    - 'reset': 전면 취소 -> 지시 파싱 단계(Node 1)로 리셋
    """
    choice = state.get("human_choice", "approve")

    if choice == "pivot_angle":
        return "generate_outline"
    elif choice == "reset":
        return "parse_and_anchor"
    return "draft_report"


# ==============================================================================
# 2. StateGraph 빌드 및 컴파일 팩토리 함수
# ==============================================================================
def create_agent_graph(checkpointer: MemorySaver = None):
    """
    So-What Agent의 전체 워크플로우를 조립하고 컴파일합니다.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    # 1. 그래프 빌더 초기화
    builder = StateGraph(AgentState)

    # 2. 노드 등록
    builder.add_node("parse_and_anchor", parse_and_anchor_node)
    builder.add_node("research_and_filter", research_and_filter_node)
    builder.add_node("rewrite_query", rewrite_query_node)
    builder.add_node("generate_outline", generate_outline_node)
    builder.add_node("human_gate", human_gate_node)
    builder.add_node("draft_report", draft_report_node)

    # 3. 엣지 연결 (Workflow Wiring)
    # START -> Node 1 (Parse & Anchor)
    builder.add_edge(START, "parse_and_anchor")

    # Node 1 -> Node 2 (Research & Filter)
    builder.add_edge("parse_and_anchor", "research_and_filter")

    # Node 2 -> 조건부 분기 (재검색 루프백 vs 목차 생성)
    builder.add_conditional_edges(
        "research_and_filter",
        route_after_research,
        {
            "rewrite_query": "rewrite_query",
            "generate_outline": "generate_outline",
        }
    )

    # Node 2-R -> Node 2 (루프백 연결)
    builder.add_edge("rewrite_query", "research_and_filter")

    # Node 3 -> HITL 인터럽트 게이트
    builder.add_edge("generate_outline", "human_gate")

    # HITL 게이트 -> 3-Way 조건부 분기
    builder.add_conditional_edges(
        "human_gate",
        route_after_human_gate,
        {
            "draft_report": "draft_report",
            "generate_outline": "generate_outline",
            "parse_and_anchor": "parse_and_anchor",
        }
    )

    # Node 4 -> END
    builder.add_edge("draft_report", END)

    # 4. 컴파일: human_gate 진입 전 인터럽트를 걸어 사용자 HITL 입력을 대기
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_gate"],
    )


# 전역 기본 컴파일 인스턴스 (MemorySaver 기본 세션 격리 적용)
app_graph = create_agent_graph()