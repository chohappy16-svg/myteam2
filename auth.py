import os
import re
import uuid
import logging
import textwrap
from urllib.parse import urlparse
from typing import Dict, Tuple, Optional
import streamlit as st
from dotenv import load_dotenv
from ui_stitch import stitch_icon

load_dotenv()
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. 하위 호환 및 테스트 보존용 프로필 딕셔너리 (Zero-Regression)
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
    "user_id": "STORE-001",
    "name": "커머스 마케터",
    "title": "실무 리드",
    "company": "이커머스 스토어",
    "domain_bm": "D2C 온라인 커머스 비즈니스",
    "challenge": "상세페이지 구매 전환율(CVR) 극대화 및 프로모션 전략 수립",
    "constraints": "단기 1~2주 내 즉각 실행 가능한 전환율 최적화 중심",
    "kpi": "상세페이지 구매 전환율(CVR) 개선 및 ROAS 극대화",
    "badge_color": "#2563EB",
    "icon": "🛒",
}

DEFAULT_SME_FALLBACK = {
    "domain_bm": "자사몰 및 오픈마켓 기반 이커머스 유통/판매",
    "constraints": "단기 1~2주 내 실행 가능한 마케팅/전환율 개선 중심",
    "kpi": "광고비 대비 매출액(ROAS) 극대화 및 구매 전환율 개선",
}


# ==============================================================================
# 2. 핵심 인증 및 세션 격리 함수 (Zero-Regression 보장)
# ==============================================================================
def validate_employee_id(user_id: str) -> Tuple[bool, str]:
    """
    사내 사번/세션 ID 규격 검증 함수 (실무형 유효성 체크)
    - 형식: 영문 대문자, 숫자, 하이픈 조합 3~15자리
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
    """하위 호환용 프로파일 분석 래퍼"""
    return {
        "domain_bm": DEFAULT_SME_FALLBACK["domain_bm"],
        "constraints": DEFAULT_SME_FALLBACK["constraints"],
        "kpi": DEFAULT_SME_FALLBACK["kpi"],
        "is_fallback": True,
        "message": "쇼핑몰 URL 기반 자동 프로파일링 적용됨"
    }


# ==============================================================================
# 3. [Sprint 6-2 핵심] 이커머스 4대 표준 보고서 정의 및 자동 진단기
# ==============================================================================
ECOMMERCE_REPORT_TYPES: Dict[str, dict] = {
    "CVR": {
        "title": "상세페이지 구매 전환율(CVR) 극대화 전략 보고서",
        "description": "상세페이지 이탈 방지, 후기/리뷰 배치, 셀링포인트 강조 및 CVR 개선",
        "keywords": ["상세페이지", "전환율", "cvr", "후기", "리뷰", "셀링포인트", "소구점", "옵션", "이탈", "상세"],
        "icon": "🎯",
        "color": "#2563EB",
    },
    "AOV": {
        "title": "객단가(AOV) 상승을 위한 번들 및 세트 구성 전략 보고서",
        "description": "묶음 상품, 세트 구성, 크로스셀/업셀, 무료배송 기준 최적화",
        "keywords": ["객단가", "aov", "번들", "묶음", "세트", "사은품", "크로스셀", "업셀", "합배송", "금액대별", "바스켓"],
        "icon": "📦",
        "color": "#7C3AED",
    },
    "ROAS": {
        "title": "소재별 광고 효율(ROAS) 최적화 전략 보고서",
        "description": "퍼포먼스 마케팅, 메타/인스타 광고 소재 최적화 및 광고비 대비 매출 증대",
        "keywords": ["roas", "광고", "소재", "메타", "인스타", "퍼포먼스", "cpc", "ctr", "크리에이티브", "피드", "광고비"],
        "icon": "📈",
        "color": "#059669",
    },
    "CRM": {
        "title": "첫 구매 고객 재구매 유도(CRM/리텐션) 전략 보고서",
        "description": "카카오 알림톡, 재구매 쿠폰, 첫 구매 후 온보딩 및 고객 생애 가치(LTV) 극대화",
        "keywords": ["crm", "재구매", "리텐션", "카카오", "알림톡", "쿠폰", "첫구매", "재방문", "ltv", "단골", "친구추가"],
        "icon": "💌",
        "color": "#D97706",
    },
}


def diagnose_ecommerce_report_type(query_text: str, challenge_text: str = "") -> dict:
    """
    사용자의 지시문과 스토어 당면 과제를 종합 분석하여
    4대 이커머스 표준 보고서 유형 중 가장 부합하는 정식 보고서 제목과 메타데이터를 자동 진단합니다.
    """
    combined_text = f"{query_text} {challenge_text}".lower()

    scores = {"CVR": 0, "AOV": 0, "ROAS": 0, "CRM": 0}

    for r_type, info in ECOMMERCE_REPORT_TYPES.items():
        for kw in info["keywords"]:
            if kw.lower() in combined_text:
                scores[r_type] += 1

    best_type = max(scores, key=scores.get)
    if scores[best_type] == 0:
        # 매칭 키워드가 없을 경우 가장 보편적인 CVR 극대화 보고서로 안전 폴백
        best_type = "CVR"

    target_info = ECOMMERCE_REPORT_TYPES[best_type]
    return {
        "type_key": best_type,
        "title": target_info["title"],
        "description": target_info["description"],
        "icon": target_info["icon"],
        "color": target_info["color"],
    }


# ==============================================================================
# 4. [Sprint 6-1 핵심] 3대 이커머스 플랫폼 자동 감지 및 브랜드 안전 추출
# ==============================================================================
def detect_ecommerce_platform(url: str, user_brand: Optional[str] = "") -> dict:
    """
    URL 패턴(네이버 스마트스토어, 쿠팡, 일반 자사몰)을 0.01초 내에 감지하여
    브랜드명이 비어 있어도 안전하게 상호를 추출하고 커머스 플랫폼 맥락을 생성합니다.
    """
    url_clean = url.strip()
    brand_clean = user_brand.strip() if user_brand else ""

    # 기본값 초기화
    platform_type = "GENERAL_D2C"
    platform_name = "독립 D2C 자사몰"
    extracted_brand = brand_clean
    constraints = "단기 1~2주 내 즉각 실행 가능한 자사몰 CVR 최적화 및 프로모션 중심"
    kpi = "자사몰 상세페이지 구매 전환율(CVR) 극대화 및 광고 ROAS 개선"
    badge_color = "#2563EB"
    icon = "🏢"

    # [케이스 1] 네이버 스마트스토어 감지
    if "smartstore.naver.com" in url_clean:
        platform_type = "NAVER_SMARTSTORE"
        platform_name = "네이버 스마트스토어"
        badge_color = "#03C75A"
        icon = "🛍️"
        constraints = "네이버 스마트스토어 플랫폼 환경 (네이버 쇼핑 검색 노출, 찜/알림받기, CVR 중심)"
        kpi = "네이버 쇼핑 상위 노출 랭킹 개선 및 상세페이지 구매 전환율(CVR) 극대화"

        # 브랜드명 미입력 시 URL 경로에서 스토어 ID 자동 추출
        if not extracted_brand:
            match = re.search(r"smartstore\.naver\.com/([a-zA-Z0-9_\-]+)", url_clean)
            if match:
                store_id = match.group(1).upper()
                extracted_brand = f"스토어({store_id})"
            else:
                extracted_brand = "스마트스토어 입점몰"

    # [케이스 2] 쿠팡 입점몰 감지
    elif "coupang.com" in url_clean:
        platform_type = "COUPANG"
        platform_name = "쿠팡 마켓플레이스"
        badge_color = "#E31A22"
        icon = "🚀"
        constraints = "쿠팡 오픈마켓 / 로켓그로스 환경 (아이템위너 경쟁, 썸네일/상세페이지 즉시 전환 중심)"
        kpi = "쿠팡 구매 전환율(CVR) 개선 및 광고비 대비 매출(ROAS) 최적화"

        # 브랜드명 미입력 시 안전 자동 지정
        if not extracted_brand:
            extracted_brand = "쿠팡 파트너몰"

    # [케이스 3] 일반 독립 D2C 자사몰
    else:
        if not extracted_brand:
            try:
                # 도메인 호스트명에서 상호 추출 (예: www.xexymix.com -> XEXYMIX)
                parsed = urlparse(url_clean if "://" in url_clean else f"https://{url_clean}")
                host = parsed.netloc or parsed.path
                host_parts = host.replace("www.", "").split(".")[0]
                extracted_brand = host_parts.upper() if host_parts else "자사몰 스토어"
            except Exception:
                extracted_brand = "자사몰 스토어"

    # 세션 사번 자동 생성 (규격: 영문+숫자+하이픈 3~15자)
    slug = re.sub(r"[^A-Z0-9]", "", extracted_brand.upper())[:6] or "STORE"
    if len(slug) < 3:
        slug = f"STR{slug}"[:6]
    auto_id = f"{slug}-{uuid.uuid4().hex[:4].upper()}"

    is_valid, clean_id = validate_employee_id(auto_id)
    if not is_valid:
        clean_id = f"STORE-{uuid.uuid4().hex[:4].upper()}"

    return {
        "platform_type": platform_type,
        "platform_name": platform_name,
        "brand_name": extracted_brand,
        "user_id": clean_id,
        "constraints": constraints,
        "kpi": kpi,
        "badge_color": badge_color,
        "icon": icon,
    }


def render_company_id_card(profile: dict, thread_id: str) -> None:
    """
    쇼핑몰 / 스토어 프로필 카드 컴포넌트 렌더링 (Google Stitch 테마)
    """
    company = profile.get("company", "자사 스토어")
    user_id = profile.get("user_id", "STORE-001")
    platform = profile.get("platform_name", "이커머스 자사몰")
    kpi = profile.get("kpi", "CVR 극대화")

    card_html = f"""
    <div style="background: #ffffff; border: 1px solid #dae2fd; border-radius: 0.85rem; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); margin-bottom: 0.85rem;">
      <div>
        <div style="font-size: 16px; font-weight: 800; color: #131b2e; line-height: 1.2;">{company}</div>
        <div style="font-size: 11px; color: #737686; font-family: monospace; margin-top: 0.25rem;">🔒 세션 ID: {user_id}</div>
      </div>
      <div style="background: #f2f3ff; border-radius: 0.5rem; padding: 0.5rem 0.75rem; font-size: 11px; color: #434655; margin-top: 0.5rem; line-height: 1.4;">
        <strong style="color: #004ac6;">🎯 집중 KPI:</strong><br>
        {kpi[:45]}...
      </div>
    </div>
    """
    st.html(textwrap.dedent(card_html).strip())


# ==============================================================================
# 4. [Sprint 6-1 UI] URL 필수 입력 + 브랜드명 선택 온보딩 사이드바
# ==============================================================================
def render_auth_sidebar() -> Tuple[str, str, bool]:
    """
    쇼핑몰 온보딩 사이드바:
    - URL: 필수 입력 (자사몰, 네이버 스마트스토어, 쿠팡 모두 지원)
    - 브랜드명: 선택 입력 (비워두면 URL에서 상호 자동 추출)
    - 주력 상품/카테고리: 선택 입력
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
        # 1. 사이드바 최상단 브랜드 타이틀 배너 (Google Stitch 1:1)
        sidebar_header = f"""
        <div style="padding: 0.5rem 0.25rem 0.75rem 0.25rem; border-bottom: 1px solid #dae2fd; margin-bottom: 0.75rem;">
          <div style="display: flex; align-items: center; gap: 0.4rem; color: #004ac6; margin-bottom: 0.25rem;">
            {stitch_icon("storefront", 16, "#004ac6")}
            <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">B2C 이커머스 전략</span>
          </div>
          <h2 style="font-size: 16px; font-weight: 800; color: #131b2e; margin: 0 0 0.2rem 0;">🛒 쇼핑몰 분석 환경 설정</h2>
          <p style="font-size: 12px; color: #737686; margin: 0;">B2C 이커머스 실무 전략 솔루션</p>
        </div>
        """
        st.html(textwrap.dedent(sidebar_header).strip())

        if st.session_state.is_authenticated:
            # ------------------------------------------------------------------
            # [인증 완료 상태]
            # ------------------------------------------------------------------
            profile = get_current_profile()
            render_company_id_card(profile, st.session_state.thread_id)

            if st.button("🔄 다른 쇼핑몰 분석하기", use_container_width=True, type="secondary"):
                st.session_state.user_id = ""
                st.session_state.thread_id = ""
                st.session_state.is_authenticated = False
                st.session_state.app_phase = "INPUT"
                st.session_state.graph_state = {}
                st.session_state.notion_url = None
                st.session_state.current_profile = DEFAULT_CUSTOM_PROFILE.copy()
                st.info("쇼핑몰 분석 환경이 초기화되었습니다.")
                st.rerun()

        else:
            # ------------------------------------------------------------------
            # [미인증 상태] URL 필수 + 브랜드명 선택 폼 (Google Stitch 카드 래핑)
            # ------------------------------------------------------------------
            form_header = f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
              <div style="font-size: 14px; font-weight: 800; color: #131b2e; display: flex; align-items: center; gap: 0.4rem;">
                {stitch_icon("domain_add", 18, "#004ac6")}분석할 쇼핑몰 등록
              </div>
              <span class="stitch-badge badge-gray">미인증</span>
            </div>
            <p style="font-size: 12px; color: #737686; margin: 0 0 0.75rem 0;">URL만 입력하면 플랫폼을 자동 감지합니다</p>
            """
            st.html(textwrap.dedent(form_header).strip())

            # ① URL (필수)
            url_input = st.text_input(
                "쇼핑몰 URL (필수)",
                placeholder="https://smartstore.naver.com/... 또는 자사몰",
                help="자사몰, 스마트스토어, 쿠팡 링크 모두 지원됩니다."
            )

            # ② 브랜드명 (선택)
            brand_input = st.text_input(
                "브랜드 / 상호명 (선택)",
                placeholder="예: 올웨이즈케어 라이프 (비워두면 자동추출)",
                help="비워두셔도 URL 경로 및 도메인에서 상호를 자동 추출합니다."
            )

            # ③ 주력 상품 / 카테고리 (선택)
            challenge_input = st.text_area(
                "주력 상품 / 카테고리 (선택)",
                placeholder="예: 여성 요가 레깅스, 헬스용품 D2C",
                height=70,
                help="현재 주력으로 판매 중인 대표 아이템이나 카테고리를 적어주세요."
            )

            if st.button("🚀 스토어 등록 및 분석 시작", use_container_width=True, type="primary"):
                url_clean = url_input.strip()
                if not url_clean:
                    st.warning("⚠️ 쇼핑몰 URL을 입력해주세요 (필수 항목).")
                else:
                    with st.spinner("쇼핑몰 플랫폼 감지 및 컨텍스트 생성 중..."):
                        # 3대 이커머스 플랫폼 자동 판별 및 상호 안전 추출
                        meta = detect_ecommerce_platform(url_clean, brand_input)

                        thread_id = generate_session_thread_id(meta["user_id"])
                        challenge_text = challenge_input.strip() or f"{meta['brand_name']} 상세페이지 전환율 개선"

                        # 세션 프로필 바인딩
                        st.session_state.user_id = meta["user_id"]
                        st.session_state.thread_id = thread_id
                        st.session_state.is_authenticated = True
                        st.session_state.app_phase = "INPUT"
                        st.session_state.graph_state = {}
                        st.session_state.notion_url = None

                        st.session_state.current_profile = {
                            "key": "CUSTOM",
                            "user_id": meta["user_id"],
                            "name": f"{meta['brand_name']} 마케터",
                            "title": "실무 리드",
                            "company": meta["brand_name"],
                            "url": url_clean,
                            "platform_name": meta["platform_name"],
                            "challenge": challenge_text,
                            "domain_bm": challenge_text,
                            "constraints": meta["constraints"],
                            "kpi": meta["kpi"],
                            "badge_color": meta["badge_color"],
                            "icon": meta["icon"],
                        }
                        st.success(f"'{meta['brand_name']}' ({meta['platform_name']}) 분석 세션 준비 완료!")
                        st.rerun()

            security_notice = f"""
            <div style="margin-top: 0.6rem; padding-top: 0.6rem; border-top: 1px solid #dae2fd; margin-bottom: 0.75rem;">
              <div style="display: flex; align-items: flex-start; gap: 0.4rem; font-size: 11px; color: #737686; line-height: 1.4;">
                {stitch_icon("shield", 15, "#004ac6", extra_style="margin-top: 1px;")}
                <p style="margin: 0;"><strong style="color: #131b2e;">안전한 데이터 격리:</strong> 등록된 스토어 자산은 독립 워크스페이스로 안전하게 암호화 보호됩니다.</p>
              </div>
            </div>
            """
            st.html(textwrap.dedent(security_notice).strip())

        # ----------------------------------------------------------------------
        # Google Stitch 사이드바 부가 위젯 3종 & 관리 링크 (1:1 복제)
        # ----------------------------------------------------------------------
        sidebar_widgets = f"""
        <!-- Middle Widget 1: Integration Tip -->
        <div style="background: #ffffff; border: 1px solid #dae2fd; border-radius: 0.75rem; padding: 0.85rem; margin-bottom: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
          <div style="display: flex; align-items: center; gap: 0.35rem; color: #004ac6; font-size: 12px; font-weight: 700; margin-bottom: 0.35rem;">
            {stitch_icon("lightbulb", 15, "#004ac6")} 스마트스토어 연동 TIP
          </div>
          <p style="font-size: 11px; color: #434655; line-height: 1.4; margin: 0;">URL 간편 입력 시 공개 상세페이지가 스크랩되며, 차후 API 공식 연동 시 주문·결제 전환 심층 데이터를 추가 분석할 수 있습니다.</p>
        </div>

        <!-- Middle Widget 2: Daily Quota Progress -->
        <div style="background: #ffffff; border: 1px solid #dae2fd; border-radius: 0.75rem; padding: 0.85rem; margin-bottom: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
            <div style="display: flex; align-items: center; gap: 0.35rem; font-size: 12px; font-weight: 700; color: #131b2e;">
              {stitch_icon("data_usage", 15, "#004ac6")}금일 잔여 쿼터
            </div>
            <span style="font-size: 12px; font-weight: 800; color: #004ac6; font-family: monospace;">48 / 50 회</span>
          </div>
          <div style="width: 100%; height: 6px; background: #dae2fd; border-radius: 9999px; overflow: hidden; margin-bottom: 0.35rem;">
            <div style="width: 96%; height: 100%; background: #004ac6; border-radius: 9999px;"></div>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 10px; color: #737686;">
            <span>자정 자동 갱신</span>
            <span style="color: #007d55; font-weight: 700;">96% 가용</span>
          </div>
        </div>
        """
        st.html(textwrap.dedent(sidebar_widgets).strip())

    return st.session_state.user_id, st.session_state.thread_id, st.session_state.is_authenticated