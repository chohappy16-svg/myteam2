"""AgentState 및 Pydantic 출력 스키마 정의 모듈
README.md 4.1 LangGraph State Schema 명세 준수

Pydantic의 Literal 활용: 
stakeholder_mood와 reporting_angle을 str 대신 Literal로 묶어두면, 
LLM이 엉뚱한 값을 생성하지 못하도록 문법 수준에서 엄격히 제한됩니다.

min_length=3, max_length=3 제약: 
목차 생성 시 LLM이 임의로 2개나 5개로 늘리지 못하도록 
SCQA 규격(상황/문제, 팩트 요약, 시사점 및 액션) 3개로 출력 개수를 고정했습니다.
"""

from typing import TypedDict, List, Dict, Optional, Literal
from pydantic import BaseModel, Field


# ==============================================================================
# 1. LangGraph 공통 State 스키마 (Graph Global State)
# ==============================================================================
class AgentState(TypedDict):
    user_id: str                  # 사내 사번 (세션 격리 키: thread_id)
    raw_query: str                # 사용자 넋두리 / 상사 원문 지시
    anchors: Dict[str, str]       # 4대 앵커 (kpi, constraints, stakeholder, angle)
    search_queries: List[str]     # 생성된 검색 쿼리 목록
    raw_articles: List[Dict]      # Tavily 수집 원본 기사
    filtered_articles: List[Dict] # HF 필터링 통과 팩트 풀 (최소 2건 확보)
    search_retry_count: int       # 검색 재시도 카운트 (최대 1회 제한)
    hypothesis: str               # 도출된 가설 1줄
    outline: List[str]            # SCQA 3대 목차 목록
    human_choice: Optional[str]   # HITL 선택 ("approve" | "pivot_angle" | "reset")
    final_report: str             # 1장 최종 마크다운 보고서 본문
    notion_url: Optional[str]     # 노션 발행 페이지 URL

# ==============================================================================
# 2. LLM Structured Output 강제용 Pydantic 스키마
# ==============================================================================
class ParsedAnchorOutput(BaseModel):
    """Node 1 (Parse & Anchor) 전용 Pydantic 모델 - 동적 미러링 및 2대 벤치마크 쿼리"""
    background: str = Field(
        description="사용자가 처한 상황을 품격 있는 비즈니스 문장으로 재정의 (내부 가짜 수치 날조 금지)"
    )
    core_challenge: str = Field(
        description="이번 건에서 해결해야 할 실무 병목 (CVR 저하, 객단가 정체, 시즌 기획 등)"
    )
    research_goal: str = Field(
        description="타사에서 무엇을 벤치마크해야 하는지 명확한 리서치 목적"
    )
    department_kpi: str = Field(
        description="사용자 입력에서 추출되거나 기본 보정된 부서 핵심 KPI"
    )
    stakeholder_mood: Literal["성과 갈증(공격형)", "리스크 우려(방어형)", "원인 규명(분석형)"] = Field(
        description="보고 수신자(상사)의 성향 및 감정 모드 3종 중 택 1"
    )
    system_constraints: str = Field(
        description="예산, 일정, 레거시 환경 등 기술적/조직적 제약 조건"
    )
    reporting_angle: Literal["비용 절감 및 효율화", "리스크 선제 방어", "신규 사업 기회", "기술 역량 내재화", "경쟁사 벤치마킹"] = Field(
        description="보고서의 BSC 기반 5대 핵심 앵글 중 택 1"
    )
    search_queries: List[str] = Field(
        description="조사 목표와 제품/카테고리를 결합한 실무 벤치마크 검색 쿼리 2개 리스트",
        min_length=2,
        max_length=2
    )
    search_query: str = Field(
        default="",
        description="하위 호환용 단일 검색 쿼리"
    )


class OutlineOutput(BaseModel):
    """Node 3 (Outline Generator) 전용 Pydantic 모델"""
    hypothesis: str = Field(
        description="수집된 팩트와 앵커를 결합해 도출한 '우리 조직 관점의 핵심 가설 1줄'"
    )
    outline: List[str] = Field(
        description="맥킨지 SCQA 구조를 반영한 3대 핵심 소제목 목차 리스트",
        min_length=3,
        max_length=3
    )