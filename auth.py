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
# 하위 호환용 기본 프리셋 딕셔너리 (테스트 및 레거시 호환성 보존)
# ==============================================================================
PRESET_PROFILES: Dict[str, dict] = {
    "SHOPPING": {
        "key": "SHOPPING",
        "label": "🛍️ D2C 패션 쇼핑몰 (SHOP-101)",
        "user_id": "SHOP-101",
        "name": "이대표",
        "title": "대표 / 총괄 디렉터",
        "company": "아틀리에 패션 D2C",
        "domain_bm": "자체 제작 패션 브랜드 및 자사몰 D2C 커머스",
        "challenge": "여성용 요가 레깅스 자사몰 상세페이지 구매 전환율(CVR) 개선 및 프로모션 전략",
        "constraints": "단기 1~2주 내 실행 가능한 상세페이지 최적화 및 프로모션 중심",
        "kpi": "광고 ROAS 350% 달성 및 상세페이지 구매 전환율(CVR) 극대화",
        "badge_color": "#EC4899",
        "icon": "🛍️",
    },
    "SAAS": {
        "key": "SAAS",
        "label": "⚡ 초기 B2B SaaS (SAAS-202)",
        "user_id": "SAAS-202",
        "name": "박파운더",
        "title": "공동창업자 / CPO",
        "company": "플로우링크(주)",
        "domain_bm": "클라우드 기반 중소기업용 업무 협업 및 워크플로우 자동화 SaaS",
        "challenge": "무료 체험 유저 온보딩 최적화 및 유료 구독 전환율 개선",
        "constraints": "개발 리소스 투입 최소화 및 즉시 적용 가능한 온보딩 플로우 개선",
        "kpi": "무료 체험 유저의 유료 전환율(CVR) 15% 달성",
        "badge_color": "#3B82F6",
        "icon": "⚡",
    },
    "LOGISTICS": {
        "key": "LOGISTICS",
        "label": "🚚 스마트 풀필먼트 물류 (LOGI-303)",
        "user_id": "LOGI-303",
        "name": "최팀장",
        "title": "물류운영 총괄",
        "company": "스피드 풀필먼트 솔루션",
        "domain_bm": "이커머스 셀러 대상 소규모 3PL 당일 출고 대행",
        "challenge": "스마트 배차 프로세스 개선 및 출고 당일 원가 절감 방안",
        "constraints": "즉시 현장 적용 가능한 피킹/패킹 동선 및 배차 스케줄 최적화",
        "kpi": "건당 물류 처리비용 12% 절감 및 오배송률 0.1% 이하",
        "badge_color": "#10B981",
        "icon": "🚚",
    },
}

DEFAULT_CUSTOM_PROFILE = {
    "key": "CUSTOM",
    "user_id": "BRAND-001",
    "name": "실무 리드",
    "title": "전략 담당자",
    "company": "자사 브랜드",
    "domain_bm": "D2C 이커머스 비즈니스",
    "challenge": "상세페이지 전환율 극대화 및 프로모션 전략 수립",
    "constraints": "1~2주 내 즉시 실행 가능한 전환율 최적화 중심",
    "kpi": "상세페이지 구매 전환율(CVR) 개선 및 ROAS 극대화",
    "badge_color": "#2563EB",
    "icon": "🏢",
}

DEFAULT_SME_FALLBACK = {
    "domain_bm": "자사몰 및 오픈마켓 기반 이커머스 유통/판매",
    "constraints": "단기 1~2주 내 실행 가능한 마케팅/전환율 개선 중심",
    "kpi": "광고비 대비 매출액(ROAS) 극대화 및 구매 전환율 개선",
}


# ==============================================================================
# 핵심 인증 및 세션 격리 함수 (Zero-Regression 보장)
# ==============================================================================
def validate_employee_id(user_id: str) -> Tuple[bool, str]:
    """
    사내 사번 규격 검증 함수 (실무형 유효성 체크)
    - 형식: 영문 대문자 및 숫자, 하이픈 조합 3~15자리
    """
    clean_id = user_id.strip().upper()
    if not clean_id:
        return False, "식별 ID를 입력해주세요."

    pattern = r"^[A-Z0-9\-]{3,15}$"
    if not re.match(pattern, clean_id):
        return False, "올바른 ID 형식이 아닙니다 (영문 대문자, 숫자, 하이픈 3~15자)."

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


def analyze_company_profile(brand_name: str, url: str) -> dict:
    """하위 호환용 프로파일 분석 인터페이스"""
    return {
        "domain_bm": DEFAULT_SME_FALLBACK["domain_bm"],
        "constraints": DEFAULT_SME_FALLBACK["constraints"],
        "kpi": DEFAULT_SME_FALLBACK["kpi"],
        "is_fallback": True,
        "message": "간편 브랜드 입력 모드 적용됨"
    }


def render_company_id_card(profile: dict, thread_id: str) -> None:
    """
    브랜드 / 기업 프로필 카드 컴포넌트 렌더링
    """
    badge_color = profile.get("badge_color", "#2563EB")
    company = profile.get("company", "자사 브랜드")
    user_id = profile.get("user_id", "BRAND-001")
    icon = profile.get("icon", "🏢")
    challenge = profile.get("challenge", profile.get("domain_bm", "비즈니스 과제"))

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
                {icon} BRAND SESSION
            </span>
            <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); border-radius: 9999px; font-size: 10px; padding: 2px 8px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                <span style="width: 6px; height: 6px; border-radius: 50%; background: #22c55e; display: inline-block;"></span>
                ACTIVE
            </span>
        </div>
        <div style="margin-bottom: 10px;">
            <div style="font-size: 16px; font-weight: 700; color: #f8fafc; line-height: 1.2;">
                {company}
            </div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 3px;">
                세션 ID: <span style="color: #38bdf8; font-family: monospace;">{user_id}</span>
            </div>
        </div>
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 6px; padding: 8px 10px; font-size: 11px; color: #cbd5e1; line-height: 1.4;">
            <span style="color: #60a5fa; font-weight: 600;">🎯 당면 과제:</span><br>
            {challenge[:45]}...
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


# ==============================================================================
# UI 단순화: [브랜드명] + [공식 URL] + [당면 과제] 직접 입력 사이드바
# ==============================================================================
def render_auth_sidebar() -> Tuple[str, str, bool]:
    """
    사이드바: 불필요한 프리셋을 제거하고 [브랜드명] + [공식 URL] + [당면 과제]를 직접 입력받아 세션을 시작
    """
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = ""
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "current_profile" not in st.session_state:
        st.session_state.current_profile = DEFAULT_CUSTOM_PROFILE.copy()

    with st.sidebar:
        st.title("🛡️ 브랜드 컨텍스트")
        st.caption("So-What Agent 전략 부사수")

        if st.session_state.is_authenticated:
            # 인증 완료 상태: 프로필 카드 및 로그아웃 버튼
            profile = get_current_profile()
            render_company_id_card(profile, st.session_state.thread_id)

            if st.button("🚪 세션 종료 및 브랜드 변경", use_container_width=True, type="secondary"):
                st.session_state.user_id = ""
                st.session_state.thread_id = ""
                st.session_state.is_authenticated = False
                st.session_state.app_phase = "INPUT"
                st.session_state.graph_state = {}
                st.session_state.notion_url = None
                st.session_state.current_profile = DEFAULT_CUSTOM_PROFILE.copy()
                st.info("세션이 초기화되었습니다.")
                st.rerun()

        else:
            # 미인증 상태: [브랜드명] + [공식 URL] + [당면 과제] 직접 입력
            st.markdown("##### 🏢 분석 대상 브랜드 등록")
            st.caption("분석할 브랜드와 주력 과제를 입력해 세션을 시작하세요.")

            brand_name = st.text_input(
                "① 브랜드 / 회사명",
                placeholder="예: 젝시믹스, 안다르, 아틀리에 패션",
                help="자사 브랜드 또는 분석하고 싶은 기업명을 입력하세요."
            )

            brand_url = st.text_input(
                "② 공식 홈페이지 URL (선택)",
                placeholder="예: https://www.brand.co.kr",
                help="공식 자사몰 또는 브랜드 링크입니다."
            )

            brand_challenge = st.text_area(
                "③ 당면 과제 / 주력 제품",
                placeholder="예: 여성 요가 레깅스 자사몰 상세페이지 구매 전환율(CVR) 극대화 및 프로모션 전략",
                height=90,
                help="현재 풀고 싶은 핵심 실무 문제나 제품군을 구체적으로 적어주세요."
            )

            if st.button("🚀 세션 생성 및 전략 분석 시작", use_container_width=True, type="primary"):
                name_clean = brand_name.strip()
                if not name_clean:
                    st.warning("브랜드명을 입력해주세요.")
                else:
                    # 브랜드명 기반 사번 생성 (규격: 3~15자 영숫자+하이픈)
                    slug = re.sub(r"[^A-Z0-9]", "", name_clean.upper())[:6] or "BRD"
                    if len(slug) < 3:
                        slug = f"BRD{slug}"[:6]
                    auto_id = f"{slug}-{uuid.uuid4().hex[:4].upper()}"

                    is_valid, clean_id = validate_employee_id(auto_id)
                    if not is_valid:
                        clean_id = f"BRAND-{uuid.uuid4().hex[:4].upper()}"

                    thread_id = generate_session_thread_id(clean_id)

                    challenge_text = brand_challenge.strip() or f"{name_clean} D2C 상세페이지 전환율 개선"

                    # 세션 프로필 바인딩
                    st.session_state.user_id = clean_id
                    st.session_state.thread_id = thread_id
                    st.session_state.is_authenticated = True
                    st.session_state.app_phase = "INPUT"
                    st.session_state.graph_state = {}
                    st.session_state.notion_url = None

                    st.session_state.current_profile = {
                        "key": "CUSTOM",
                        "user_id": clean_id,
                        "name": f"{name_clean} 실무 리드",
                        "title": "전략 담당",
                        "company": name_clean,
                        "url": brand_url.strip(),
                        "challenge": challenge_text,
                        "domain_bm": challenge_text,
                        "constraints": "단기 1~2주 내 즉각 실행 가능한 전환율 최적화 및 프로모션 중심",
                        "kpi": "상세페이지 구매 전환율(CVR) 극대화 및 광고 ROAS 개선",
                        "badge_color": "#2563EB",
                        "icon": "🏢"
                    }
                    st.success(f"'{name_clean}' 분석 세션이 생성되었습니다!")
                    st.rerun()

            st.markdown("---")
            st.markdown("""
            <div style="font-size: 11px; color: #64748b; line-height: 1.5;">
                🔒 <b>개별 세션 격리</b>: 입력하신 브랜드 정보는 독립된 체크포인터 세션(<code>thread_id</code>)으로 보호됩니다.
            </div>
            """, unsafe_allow_html=True)

    return st.session_state.user_id, st.session_state.thread_id, st.session_state.is_authenticated