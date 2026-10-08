# 🧭 So-What Agent (소왓 에이전트)
> 단순 팩트 나열을 넘어 **"그래서 우리 회사는 뭘 해야 하는가?"**를 즉각 도출하는 실무형 비즈니스 부사수 AI

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange)
![Hugging Face](https://img.shields.io/badge/Model-mDeBERTa--v3-yellow)
![Tavily](https://img.shields.io/badge/Search-Tavily%20API-teal)
![Notion](https://img.shields.io/badge/Export-Notion%20API-lightgrey)

---

## 📌 1. 프로젝트 개요 (Overview)
* **목적**: 상사의 모호한 구두 지시나 실무자의 자연어 넋두리를 입력받아, 홍보성 PR 노이즈를 자동 배제하고 조직 KPI에 맞춘 **1장 분량의 맥킨지 SCQA 비즈니스 동향 보고서 초안**을 2분 이내에 자동 생성합니다.
* **주요 해결 과제 (Pain Points)**:
  1. 기사 수십 건에서 보도자료·마케팅성 노이즈를 선별하는 리서치 병목 해소
  2. 단순 사실 나열을 탈피하여 "우리 조직 관점의 시사점(So What)" 도출
  3. 상사의 앵글 변경 시 데이터 재검색 없이 30초 내 관점 재작성(Time-Travel)
  4. 단 1회의 결정적 목차 승인(HITL)으로 할루시네이션 및 전면 재작업 방지

---

## 🏗️ 2. 시스템 아키텍처 & 워크플로우

```text
[Login Auth Gate: 사내 간이 인증 및 thread_id = f(user_id) 세션 격리]
       │
       ▼
 [START: 지시 접수 & 4대 앵커 고정]
       │
       ▼
 [Node 1: Parse & Anchor] ─────────── 넋두리 파싱 및 검색 키워드 추출
       │
       ▼
 [Node 2: Web Research & HF Filter] ── Tavily 5건 수집 + HF Zero-Shot PR 필터링
       │
       ├─────────────────────────────────────────┐
       ▼ [유효 팩트 < 2건 & 재시도 < 1]          ▼ [유효 팩트 >= 2건 또는 Fallback]
 [Node 2-R: 쿼리 재생성 (루프백 1회)]      [Node 3: Outline Generator]
       │                                         │
       └─────────────────────────────────────────┤
                                                 ▼
                                     [★ HITL Gate: 목차 승인]
                                                 │
          ┌──────────────────────────────────────┼──────────────────────────────────────┐
          ▼ [approve: 승인/수정]                  ▼ [pivot_angle: 앵글 변경]             ▼ [reset: 전면 리셋]
 [Node 4: Draft Final Report]           [Node 3으로 롤백 (Time-Travel)]           [START로 리셋]
          │
          ▼
        (END)
          │
          ▼ [Post-Action: 원클릭 전송]
 [Notion 동향 DB 내보내기 & URL 발급]
```

---

## 🛠️ 3. 기술 스택 (Tech Stack)

| 구분 | 도입 기술 | 적용 목적 및 실무 규격 |
| :--- | :--- | :--- |
| **Orchestration** | LangGraph, langchain-core | 노드 간 상태 전이 제어, 3-Way 조건부 분기, HITL 인터럽트 |
| **Checkpointer** | MemorySaver / SqliteSaver | 세션 격리(thread_id), 기사 풀 보존 기반 Time-Travel 재렌더링 |
| **Search Engine** | Tavily Search API | 월 1,000건 무료 플랜, 광고/스크립트 제거 순수 텍스트 5건 수집 (<= 15s) |
| **PR Noise Filter** | Hugging Face mDeBERTa-v3 | 로컬 Zero-Shot 분류, 본문 앞 100자 슬라이싱, PR 점수 >= 0.5 배제 |
| **LLM Engine** | OpenAI API (gpt-4o-mini / gpt-4o) | Pydantic 구조화 출력(Node 1, 3) 및 SCQA 마크다운 작성(Node 4) |
| **Collab Export** | Notion REST API (notion-client) | 사내 노션 DB에 보고서 블록 자동 생성 및 열람 URL 발급 (Post-Action) |
| **Frontend** | Streamlit (Phase 6 연동 예정) | 직관적인 4개 화면 UI 및 인터랙션 구현 |

---

## 📐 4. 핵심 엔지니어링 규약 (Engineering Contracts)

### 4.1. LangGraph State Schema (AgentState)

```python
from typing import TypedDict, List, Dict, Optional

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
```

### 4.2. HITL 3-Way 라우팅 리터럴

* `approve`: 승인된 목차로 Node 4 직행
* `pivot_angle`: 팩트는 보존한 채 앵글만 변경하여 Node 3 롤백
* `reset`: 지시문 입력 단계로 복귀하여 전체 파이프라인 초기화

---

## 📂 5. 프로젝트 디렉토리 구조 (Directory Structure)

```plaintext
├── .gitignore            # [필수 추가] API 키, 캐시, 로컬 DB 커밋 차단
├── .env.example          # [필수 추가] 팀원용 환경변수 템플릿 (키값 제외)
├── requirements.txt      # 프로젝트 의존성 라이브러리 목록
├── README.md             # 프로젝트 기술 명세 및 실행 가이드
│
├── core/                 # [Phase 4] LangGraph 파이프라인 모듈 (비즈니스 로직)
│   ├── __init__.py
│   ├── state.py          # AgentState 및 Pydantic 스키마
│   ├── tools.py          # Tavily 검색 / HF 필터링 래퍼 함수
│   ├── nodes.py          # 4대 핵심 노드 로직
│   └── graph.py          # StateGraph 조립 및 컴파일
│
├── tests/                # [Phase 3 & 5] 모든 테스트 스크립트 단일화
│   ├── test_tavily.py    # Tavily 단위 테스트 (TC-1)
│   ├── test_hf_filter.py # HF 노이즈 필터링 단위 테스트 (TC-2)
│   ├── test_notion.py    # Notion 연동 단위 테스트 (TC-5.4)
│   └── test_pipeline_cli.py # [이동] LangGraph E2E 통합 테스트 (TC-3, TC-4)
│
├── app.py                # [Phase 6] Streamlit 웹 UI 메인 엔트리포인트
└── auth.py               # [Phase 6] 사내 간이 로그인 및 thread_id 바인딩
```

---

## 🌳 6. Git 브랜치 전략 & 로드맵 (Branch Strategy & Roadmap)

본 프로젝트는 Git-Flow 기반의 피처 브랜치 전략을 따르며, `develop` 브랜치를 기준으로 각 Phase별 기능을 개발·검증한 후 통합합니다.

| 브랜치명 | 상태 | 브랜치 역할 | 주요 대상 파일 |
| :--- | :---: | :--- | :--- |
| `main` | 🏁 배포 | 최종 릴리즈 브랜치 (시연 가능한 완성본만 보관) | 전체 머지된 최종 완성본 |
| `develop` | 🌳 기준 | 통합 개발 기준 브랜치 (feature 브랜치들의 모임 장소) | 루트 설정 파일 및 머지된 누적 파일 |
| `feature/phase3-unit-tests` | ✅ 완료 | 부품 단위 테스트 브랜치 (Tavily, HF, Notion 단독 검증) | `tests/test_tavily.py`<br>`tests/test_hf_filter.py`<br>`tests/test_notion.py` |
| `feature/phase4-langgraph-core` | 🚀 **진행 중** | LangGraph 파이프라인 조립 (노드, State, 루프백, Checkpointer) | `core/__init__.py`<br>`core/state.py`<br>`core/tools.py`<br>`core/nodes.py`<br>`core/graph.py` |
| `feature/phase5-e2e-tests` | ⏳ 예정 | E2E 통합 테스트 브랜치 (TC-1~TC-5 14개 체크포인트 자동 검증) | `tests/test_pipeline_cli.py` |
| `feature/phase6-streamlit-ui` | ⏳ 예정 | 웹 UI 및 인증 연동 브랜치 (화면 1~4 UI 구현, 세션 격리) | `app.py`<br>`auth.py` |

### 📌 표준 Git 작업 워크플로우

```bash
# 1. develop 최신 소스 동기화
git checkout develop
git pull origin develop

# 2. 작업할 feature 브랜치 생성 및 이동 (예: Phase 4 착수 시)
git checkout -b feature/phase4-langgraph-core

# 3. 작업 완료 후 커밋 & 푸시
git add .
git commit -m "feat(core): LangGraph 파이프라인 조립 및 상태 스키마 정의"
git push origin feature/phase4-langgraph-core
```

---

## 🚀 7. 빠른 시작 (Quick Start)

### 1) 환경 세팅 및 패키지 설치

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2) 환경변수 설정 (.env)

```ini
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_TOKEN=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3) 단위 및 E2E 테스트 검증

```bash
# 부품 단위 테스트 (Phase 3)
python tests/test_tavily.py
python tests/test_hf_filter.py
python tests/test_notion.py

# E2E 파이프라인 통합 테스트 (Phase 5)
python tests/test_pipeline_cli.py
```
#   m y t e a m 2  
 