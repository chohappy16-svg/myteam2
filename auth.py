import os
import re
import uuid
import logging
from typing import Dict, Tuple, Optional
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. SME / 스타트업 맞춤형 3대 검증 프리셋 (모드 A)
# ==============================================================================
PRESET_PROFILES: Dict[str, dict] = {
    "SHOPPING": {
        "key": "SHOPPING",
        "label": "🛍️ D2C 패션 쇼핑몰 (이대표 / SHOP-101)",
        "user_id": "SHOP-101",
        "name": "이대표",
        "title": "대표 / 총괄 디렉터",
        "company": "아틀리에 패션 D2C",
        "domain_bm": "자체 제작 패션 브랜드 및 자사몰 D2C 커머스",
        "constraints": "자체 개발 인력 부재, 카페24/스마트스토어 호스팅 의존, 외주 마케팅 대행사 의존",
        "kpi": "광고 ROAS 350% 달성 및 반품/교환율 10% 미만 억제",
        "badge_color": "#EC4899",
        "icon": "🛍️",
    },
    "SAAS": {
        "key": "SAAS",
        "label": "⚡ 초기 B2B SaaS (박파운더 / SAAS-202)",
        "user_id": "SAAS-202",
        "name": "박파운더",
        "title": "공동창업자 / CPO",
        "company": "플로우링크(주)",
        "domain_bm": "클라우드 기반 중소기업용 업무 협업 및 워크플로우 자동화 SaaS",
        "constraints": "개발자 2명(핵심 기능 개발 집중), 비즈니스/마케팅 전담 인력 부재, AWS 크레딧 소진 임박",
        "kpi": "무료 체험 유저의 유료 전환율(CVR) 15% 및 월간 이탈률(Churn) 3% 미만",
        "badge_color": "#3B82F6",
        "icon": "⚡",
    },
    "LOGISTICS": {
        "key": "LOGISTICS",
        "label": "🚚 스마트 풀필먼트 물류 (최팀장 / LOGI-303)",
        "user_id": "LOGI-303",
        "name": "최팀장",
        "title": "물류운영 총괄",
        "company": "스피드 풀필먼트 솔루션",
        "domain_bm": "이커머스 셀러 대상 소규모 3PL 당일 출고 대행",
        "constraints": "영세 상용 WMS 패키지 사용, 화주사 ERP 연동 API 부재, 수작업 배차 의존",
        "kpi": "건당 물류 처리비용 12% 절감 및 오배송률 0.1% 이하",
        "badge_color": "#10B981",
        "icon": "🚚",
    },
}

# API 장애 시 무중단 화면 복구를 위한 표준 SME 안전 폴백 기본값
DEFAULT_SME_FALLBACK = {
    "domain_bm": "자사몰 및 오픈마켓 기반 이커머스 유통/판매",
    "constraints": "자사몰 호스팅 기반, 사내 개발팀 부재(외주 의존), 제한된 마케팅 예산",
    "kpi": "광고비 대비 매출액(ROAS) 극대화 및 재고 회전율 개선",
}

DEFAULT_CUSTOM_PROFILE = {
    "key": "CUSTOM",
    "label": "✍️ 직접 수동 입력",
    "user_id": "",
    "name": "실무 담당자",
    "title": "전략 기획 담당",
    "company": "자사 비즈니스 조직",
    "domain_bm": "자사 핵심 비즈니스 도메인",
    "constraints": "사내 개발 인프라 및 예산 제약",
    "kpi": "핵심 성과 지표(KPI) 최적화",
    "badge_color": "#6B7280",
    "icon": "👤",
}


# ==============================================================================
# 2. 핵심 인증 및 세션 격리 함수 (Zero-Regression 보장)
# ==============================================================================
def validate_employee_id(user_id: str) -> Tuple[bool, str]:
    """
    사내 사번 규격 검증 함수 (실무형 유효성 체크)
    - 형식: 영문 대문자 2~4자리 + 하이픈(-) + 숫자 3~6자리 (예: EMP-84920, SHOP-101)
    - 단순 입력도 허용하되, 최소 3자 이상의 식별값 검증
    """
    clean_id = user_id.strip().upper()
    if not clean_id:
        return False, "사번을 입력해주세요."

    pattern = r"^[A-Z0-9\-]{3,15}$"
    if not re.match(pattern, clean_id):
        return False, "올바른 사번 형식이 아닙니다 (예: EMP-84920 또는 알파벳+숫자)."

    return True, clean_id


def generate_session_thread_id(user_id: str) -> str:
    """
    LangGraph Checkpointer(MemorySaver) 세션 격리용 thread_id 생성기
    - 공식: thread_{정제된사번}_{고유세션해시}
    """
    session_hash = uuid.uuid4().hex[:8]
    return f"thread_{user_id}_{session_hash}"


def get_current_profile() -> dict:
    """현재 세션에 바인딩된 자사 맥락 프로필 반환"""
    if "current_profile" not in st.session_state or not st.session_state.current_profile:
        return DEFAULT_CUSTOM_PROFILE.copy()
    return st.session_state.current_profile


# ==============================================================================
# 3. 경량 AI 기업 프로파일링 함수 (모드 B: Tavily + OpenAI 안전 폴백)
# ==============================================================================
def analyze_company_profile(brand_name: str, url: str) -> dict:
    """
    브랜드명과 공식 URL을 바탕으로 기존 Tavily/OpenAI 스택을 활용해
    자사 맥락 3대 요소(도메인/BM, 현실적 제약, 추천 KPI)를 경량 분석 추출합니다.
    
    [안전 폴백 가드레일]
    - API 키 부재, 네트워크 오류, LLM 타임아웃 등 어떤 예외가 발생해도 Exception을 던지지 않고
      표준 SME 기본값(DEFAULT_SME_FALLBACK)으로 안전 복구하여 Pre-fill을 제공합니다.
    """
    brand_clean = brand_name.strip()
    url_clean = url.strip()

    # 기본 안전 반환 템플릿
    result = {
        "domain_bm": DEFAULT_SME_FALLBACK["domain_bm"],
        "constraints": DEFAULT_SME_FALLBACK["constraints"],
        "kpi": DEFAULT_SME_FALLBACK["kpi"],
        "is_fallback": True,
        "message": "기본 SME 템플릿 적용됨"
    }

    if not brand_clean:
        return result

    try:
        tavily_key = os.getenv("TAVILY_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        # API 키 부재 시 즉시 안전 폴백 반환
        if not tavily_key or not openai_key:
            logger.warning("API 키 부재로 기본 SME 템플릿으로 안전 폴백합니다.")
            return result

        # 1. Tavily 경량 검색 (회사 소개 및 주요 서비스 스니펫 1~2건 수집)
        from tavily import TavilyClient
        tavily_client = TavilyClient(api_key=tavily_key)
        search_query = f"{brand_clean} {url_clean} 회사 소개 서비스 주요 제품"
        tavily_res = tavily_client.search(query=search_query, max_results=2, search_depth="basic")
        
        search_snippets = []
        for r in tavily_res.get("results", []):
            snippet = r.get("content", "")
            if snippet:
                search_snippets.append(snippet[:250])
        context_text = "\n".join(search_snippets) if search_snippets else f"{brand_clean} ({url_clean})"

        # 2. gpt-4o-mini 호출 (SME 실무 관점 3대 맥락 요약)
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from pydantic import BaseModel, Field

        class SMEProfileOutput(BaseModel):
            domain_bm: str = Field(description="무엇을 어떻게 파는 회사인지 핵심 비즈니스 모델 1줄")
            constraints: str = Field(description="사내 개발팀 부재, 외부 호스팅 의존 등 현실적인 인프라/리소스 제약 1줄")
            recommended_kpi: str = Field(description="SME 관점에서 가장 직결되는 핵심 목표 KPI 1줄")

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=openai_key)
        structured_llm = llm.with_structured_output(SMEProfileOutput)

        system_prompt = """당신은 중소기업/스타트업(SME) 전문 비즈니스 컨설턴트입니다.
제공된 회사 소개 정보를 바탕으로 실무 1장 보고서에 필요한 '자사 비즈니스 맥락 3대 요소'를 요약하세요.

[엄격한 가드레일 규칙]
1. 과대평가 금지: 사내에 거대 AI 인프라나 대규모 자체 개발팀이 있다고 상상하지 마십시오.
2. 현실적 제약 기본값: "사내 전담 개발 인력 부재, 외부 호스팅/SaaS 솔루션 의존, 단기 ROI 검증 필요" 등 보수적인 SME 제약을 전제하십시오.
3. 간결성: 각 항목은 반드시 명확하고 군더더기 없는 1줄(40자 내외)로 작성하십시오.
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "브랜드명: {brand}\n공식 URL: {url}\n웹 검색 정보:\n{context}")
        ])

        chain = prompt | structured_llm
        parsed: SMEProfileOutput = chain.invoke({
            "brand": brand_clean,
            "url": url_clean,
            "context": context_text
        })

        if parsed:
            result["domain_bm"] = parsed.domain_bm
            result["constraints"] = parsed.constraints
            result["kpi"] = parsed.recommended_kpi
            result["is_fallback"] = False
            result["message"] = "AI 자동 프로파일링 완료"

    except Exception as e:
        logger.error(f"AI 프로파일링 중 예외 발생 (안전 폴백 적용): {e}")
        # 예외 발생 시 에러를 띄우지 않고 폴백 기본값 유지
        result["is_fallback"] = True
        result["message"] = "연결 지연으로 표준 SME 템플릿이 안전하게 채워졌습니다."

    return result


# ==============================================================================
# 4. 사원증 / 기업 프로필 카드 UI 시각화 컴포넌트
# ==============================================================================
def render_company_id_card(profile: dict, thread_id: str) -> None:
    """
    SME 임직원 사원증 / 기업 프로필 카드 컴포넌트 렌더링
    엔터프라이즈 품격의 다크 ID Card UI 스타일 적용
    """
    badge_color = profile.get("badge_color", "#3B82F6")
    name = profile.get("name", "실무 담당자")
    title = profile.get("title", "총괄")
    company = profile.get("company", "자사 조직")
    user_id = profile.get("user_id", "EMP-UNKNOWN")
    icon = profile.get("icon", "🏢")
    domain_bm = profile.get("domain_bm", "-")
    constraints = profile.get("constraints", "-")
    kpi = profile.get("kpi", "-")

    card_html = f"""
    <div style="
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-top: 4px solid {badge_color};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        color: #f8fafc;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 8px;">
            <span style="font-size: 11px; font-weight: 700; letter-spacing: 1px; color: #94a3b8; text-transform: uppercase;">
                {icon} SME ENTERPRISE PASS
            </span>
            <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); border-radius: 9999px; font-size: 10px; padding: 2px 8px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                <span style="width: 6px; height: 6px; border-radius: 50%; background: #22c55e; display: inline-block;"></span>
                ONLINE
            </span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <div style="
                width: 44px; height: 44px; border-radius: 10px;
                background: {badge_color}22; border: 1.5px solid {badge_color};
                display: flex; align-items: center; justify-content: center;
                font-size: 20px;
            ">
                {icon}
            </div>
            <div>
                <div style="font-size: 15px; font-weight: 700; color: #f8fafc; line-height: 1.2;">
                    {name} <span style="font-size: 12px; font-weight: 400; color: #cbd5e1;">{title}</span>
                </div>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">
                    {company}
                </div>
            </div>
        </div>
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 6px; padding: 8px 10px; font-size: 11px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                <span style="color: #64748b;">사번 (ID)</span>
                <span style="color: #38bdf8; font-weight: 600; font-family: monospace;">{user_id}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #64748b;">세션 격리</span>
                <span style="color: #a78bfa; font-family: monospace; font-size: 10px;">{thread_id[:16]}...</span>
            </div>
        </div>
        <div style="font-size: 11px; color: #cbd5e1; line-height: 1.4; border-top: 1px dashed #334155; pt-2; padding-top: 8px;">
            <div style="margin-bottom: 2px;"><span style="color: #94a3b8;">🎯 BM:</span> {domain_bm[:30]}...</div>
            <div style="margin-bottom: 2px;"><span style="color: #ef4444;">🔒 제약:</span> {constraints[:30]}...</div>
            <div><span style="color: #10b981;">📈 KPI:</span> {kpi[:30]}...</div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


# ==============================================================================
# 5. 메인 사이드바 렌더링 함수 (Sprint 6-1 핵심)
# ==============================================================================
def render_auth_sidebar() -> Tuple[str, str, bool]:
    """
    Streamlit 좌측 사이드바에 사내 인증 폼 및 기업 프로필을 렌더링하는 함수
    
    - 모드 A: 3대 SME/스타트업 검증 프리셋 원클릭 로그인
    - 모드 B: 브랜드명 + URL 입력 기반 경량 AI 자동 프로파일링 (안전 폴백 포함)
    - 모드 C: 기존 수동 사번 입력 방식 (하위 호환 100% 보장)

    Returns:
        Tuple[user_id: str, thread_id: str, is_authenticated: bool]
    """
    # 세션 상태 안전 초기화
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = ""
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "current_profile" not in st.session_state:
        st.session_state.current_profile = DEFAULT_CUSTOM_PROFILE.copy()
    if "ai_draft_profile" not in st.session_state:
        st.session_state.ai_draft_profile = None

    with st.sidebar:
        st.title("🛡️ 사내 인증 & 프로필")
        st.caption("So-What Agent SME 세션 시스템")

        # ----------------------------------------------------------------------
        # [상태 1: 인증 완료] 사원증 / 기업 프로필 카드 렌더링
        # ----------------------------------------------------------------------
        if st.session_state.is_authenticated:
            profile = get_current_profile()
            render_company_id_card(profile, st.session_state.thread_id)

            with st.expander("🏢 자사 비즈니스 맥락 3대 요소", expanded=False):
                st.caption(f"**BM/도메인**: {profile.get('domain_bm', '-')}")
                st.caption(f"**인프라 제약**: {profile.get('constraints', '-')}")
                st.caption(f"**핵심 KPI**: {profile.get('kpi', '-')}")

            if st.button("🚪 세션 종료 및 로그아웃", use_container_width=True, type="secondary"):
                st.session_state.user_id = ""
                st.session_state.thread_id = ""
                st.session_state.is_authenticated = False
                st.session_state.app_phase = "INPUT"
                st.session_state.graph_state = {}
                st.session_state.notion_url = None
                st.session_state.current_profile = DEFAULT_CUSTOM_PROFILE.copy()
                st.session_state.ai_draft_profile = None
                st.info("세션이 초기화되었습니다.")
                st.rerun()

        # ----------------------------------------------------------------------
        # [상태 2: 미인증] 온보딩 이원화 인터페이스 (프리셋 vs AI 자동 프로파일링 vs 수동)
        # ----------------------------------------------------------------------
        else:
            mode = st.radio(
                "온보딩 방식 선택",
                ["⚡ 데모 프리셋", "🤖 AI 자동 프로파일링", "✍️ 직접 수동 입력"],
                index=0,
                label_visibility="collapsed"
            )

            # ------------------------------------------------------------------
            # [모드 A] 빠른 테스트/데모용 프리셋
            # ------------------------------------------------------------------
            if mode == "⚡ 데모 프리셋":
                st.markdown("###### ⚡ SME 검증 프리셋 선택")
                preset_keys = list(PRESET_PROFILES.keys())
                preset_labels = {k: PRESET_PROFILES[k]["label"] for k in preset_keys}

                selected_key = st.selectbox(
                    "직무 페르소나",
                    options=preset_keys,
                    format_func=lambda k: preset_labels[k]
                )
                chosen = PRESET_PROFILES[selected_key]

                st.caption(f"💡 **도메인**: {chosen['domain_bm'][:26]}...")
                st.caption(f"🔒 **제약**: {chosen['constraints'][:26]}...")

                if st.button("🚀 프리셋으로 원클릭 로그인", use_container_width=True, type="primary"):
                    clean_id = chosen["user_id"]
                    st.session_state.user_id = clean_id
                    st.session_state.thread_id = generate_session_thread_id(clean_id)
                    st.session_state.is_authenticated = True
                    st.session_state.app_phase = "INPUT"
                    st.session_state.graph_state = {}
                    st.session_state.notion_url = None
                    st.session_state.current_profile = chosen.copy()
                    st.success(f"{chosen['company']} ({clean_id}) 로그인 완료!")
                    st.rerun()

            # ------------------------------------------------------------------
            # [모드 B] 실제 사용자용 AI 자동 프로파일링
            # ------------------------------------------------------------------
            elif mode == "🤖 AI 자동 프로파일링":
                st.markdown("###### 🤖 브랜드/URL 기반 AI 프로파일링")
                st.caption("홈페이지 소개글을 바탕으로 자사 맥락 3요소를 3초 만에 추출합니다.")

                brand_input = st.text_input("브랜드 / 회사명", placeholder="예: 무신사, 토스, 오늘의집")
                url_input = st.text_input("공식 홈페이지 URL", placeholder="예: https://www.brand.co.kr")

                if st.button("🔍 AI 기업 맥락 자동 분석", use_container_width=True):
                    if not brand_input.strip():
                        st.warning("브랜드명을 입력해주세요.")
                    else:
                        with st.spinner("웹 사이트 소개 파싱 및 자사 맥락 추출 중..."):
                            analysis_result = analyze_company_profile(brand_input, url_input)
                            st.session_state.ai_draft_profile = {
                                "brand": brand_input.strip(),
                                "url": url_input.strip(),
                                **analysis_result
                            }
                            if analysis_result.get("is_fallback"):
                                st.info(analysis_result.get("message"))
                            else:
                                st.success(analysis_result.get("message"))

                # 분석 결과가 있거나 폴백 생성된 경우 확인/수정 인라인 폼 (HITL)
                draft = st.session_state.ai_draft_profile
                if draft:
                    st.markdown("---")
                    st.markdown("###### 📋 도출된 자사 맥락 (확인 후 수정 가능)")

                    edit_domain = st.text_input("① 비즈니스 모델(BM)", value=draft.get("domain_bm", ""))
                    edit_constraints = st.text_input("② 인프라/리소스 제약", value=draft.get("constraints", ""))
                    edit_kpi = st.text_input("③ 추천 목표 KPI", value=draft.get("kpi", ""))

                    if st.button("✅ 프로필 확정 및 세션 생성", use_container_width=True, type="primary"):
                        # 브랜드 영문 정제 기반 사번 생성
                        brand_slug = re.sub(r"[^A-Z0-9]", "", draft["brand"].upper())[:6] or "SME"
                        auto_id = f"AI-{brand_slug}-{uuid.uuid4().hex[:4].upper()}"

                        st.session_state.user_id = auto_id
                        st.session_state.thread_id = generate_session_thread_id(auto_id)
                        st.session_state.is_authenticated = True
                        st.session_state.app_phase = "INPUT"
                        st.session_state.graph_state = {}
                        st.session_state.notion_url = None

                        st.session_state.current_profile = {
                            "key": "AI_AUTO",
                            "user_id": auto_id,
                            "name": f"{draft['brand']} 실무자",
                            "title": "전략 담당자",
                            "company": draft["brand"],
                            "domain_bm": edit_domain.strip(),
                            "constraints": edit_constraints.strip(),
                            "kpi": edit_kpi.strip(),
                            "badge_color": "#8B5CF6",
                            "icon": "🤖"
                        }
                        st.success(f"'{draft['brand']}' 세션 생성 완료!")
                        st.rerun()

            # ------------------------------------------------------------------
            # [모드 C] 직접 수동 입력 (하위 호환 모드)
            # ------------------------------------------------------------------
            else:
                st.markdown("###### ✍️ 사번 직접 수동 입력")
                manual_id = st.text_input(
                    "사번 (User ID)",
                    value=st.session_state.user_id,
                    placeholder="예: EMP-84920"
                )

                if st.button("인증 및 세션 생성", use_container_width=True, type="primary"):
                    is_valid, result = validate_employee_id(manual_id)
                    if is_valid:
                        st.session_state.user_id = result
                        st.session_state.thread_id = generate_session_thread_id(result)
                        st.session_state.is_authenticated = True
                        st.session_state.app_phase = "INPUT"
                        st.session_state.graph_state = {}
                        st.session_state.notion_url = None

                        custom_p = DEFAULT_CUSTOM_PROFILE.copy()
                        custom_p["user_id"] = result
                        st.session_state.current_profile = custom_p

                        st.success("인증 완료")
                        st.rerun()
                    else:
                        st.error(result)

            st.markdown("---")
            st.markdown("""
            <div style="font-size: 11px; color: #64748b; line-height: 1.5;">
                🔒 <b>세션 격리 보장</b>: 모든 세션은 <code>thread_{USER_ID}_{HASH}</code> 단위로 엄격히 독립 분리됩니다.
            </div>
            """, unsafe_allow_html=True)

    return st.session_state.user_id, st.session_state.thread_id, st.session_state.is_authenticated