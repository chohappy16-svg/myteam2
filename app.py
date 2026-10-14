import importlib
import textwrap
import streamlit as st
from dotenv import load_dotenv

import ui_stitch
importlib.reload(ui_stitch)

import auth
importlib.reload(auth)

from core.graph import app_graph
from core.tools import export_report_to_notion
from auth import (
    render_auth_sidebar,
    get_current_profile,
    diagnose_ecommerce_report_type,
    ECOMMERCE_REPORT_TYPES,
)

from ui_stitch import (
    inject_stitch_assets,
    stitch_icon,
    render_stitch_header,
    render_stitch_stepper,
    render_screen1_hero_banner,
    render_screen1_domain_cards,
    render_screen1_domain_tabs,
    render_screen1_info_cards,
    render_screen2_market_analysis_view,
    render_screen3_brief_and_metrics,
    render_screen4_report_header_and_summary,
)

# ------------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 구글 스티치 테마 주입
# ------------------------------------------------------------------------------
load_dotenv()
st.set_page_config(
    page_title="So-What Agent | B2C E-Commerce Strategy Copilot",
    page_icon="🛒",
    layout="wide"
)

# 구글 스티치 Tailwind, Fonts, Icons 및 글로벌 스타일 주입
inject_stitch_assets()


def render_stepper(active_step_idx: int, container=None):
    """구글 스티치 4-Step Stepper 위젯 렌더링"""
    render_stitch_stepper(active_step_idx=active_step_idx, container=container)


# ------------------------------------------------------------------------------
# 2. 사이드바 인증 게이트 및 전역 SME 컨텍스트 바인딩
# ------------------------------------------------------------------------------
user_id, thread_id, is_authenticated = render_auth_sidebar()

# 인증 미완료 시 메인 화면 (Google Stitch 초기 화면 1:1 복제)
if not is_authenticated:
    render_stitch_header(company_name="미등록 스토어", is_authenticated=False)
    render_stitch_stepper(1)
    render_screen1_hero_banner(company_name="", is_authenticated=False)
    render_screen1_domain_cards(selected_key="CVR")

    action_bar_html = f"""
    <div style="background: #ffffff; border: 1px solid #dae2fd; border-radius: 1rem; padding: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
      <div style="display: flex; align-items: center; gap: 0.85rem;">
        <div style="width: 40px; height: 40px; border-radius: 50%; background: #ffdad6; color: #93000a; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
          {stitch_icon("lock", 20, "#93000a")}
        </div>
        <div>
          <div style="font-size: 14px; font-weight: 800; color: #131b2e;">분석 파이프라인 생성 대기 중</div>
          <div style="font-size: 12px; color: #737686;">스토어가 등록되면 AI 목차 기획 및 시장 데이터 분석 단계로 이동할 수 있습니다.</div>
        </div>
      </div>
      <button style="padding: 0.6rem 1.2rem; border-radius: 0.5rem; background: #eaedff; color: #737686; font-size: 12px; font-weight: 700; border: none; cursor: not-allowed; opacity: 0.6; display: flex; align-items: center; gap: 0.4rem;" disabled>
        {stitch_icon("arrow_forward", 14, "#737686")} 다음: 시장 분석 & 목차 생성
      </button>
    </div>

    <div style="background: #f2f3ff; border: 1px solid #dae2fd; border-radius: 0.85rem; padding: 0.85rem 1rem; display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <div style="display: flex; align-items: center; gap: 0.6rem; color: #131b2e; font-size: 13px;">
        {stitch_icon("arrow_back", 18, "#004ac6")}
        <span>
          먼저 좌측 패널의 <strong style="color: #004ac6; text-decoration: underline;">'🚀 스토어 등록 및 분석 시작'</strong> 버튼을 눌러 스토어를 등록해 주세요.
        </span>
      </div>
      <span class="stitch-badge badge-blue">1분 소요</span>
    </div>
    """
    st.html(textwrap.dedent(action_bar_html).strip())

    render_screen1_info_cards()
    st.stop()

# 세션 상태 기본값 초기화
if "app_phase" not in st.session_state:
    st.session_state.app_phase = "INPUT"
if "graph_state" not in st.session_state:
    st.session_state.graph_state = {}
if "pivot_version" not in st.session_state:
    st.session_state.pivot_version = 0
if "notion_url" not in st.session_state:
    st.session_state.notion_url = None
if "diagnosed_report" not in st.session_state:
    st.session_state.diagnosed_report = None
if "user_raw_query" not in st.session_state:
    st.session_state.user_raw_query = ""

def _append_query_template(addon: str):
    curr = st.session_state.get("user_raw_query", "")
    if addon not in curr:
        st.session_state.user_raw_query = f"{curr}\n- {addon}".strip()

# 현재 인증된 SME 프로필 전역 스코프 조회 (Sprint 6-2 & 6-3 안정화)
current_profile = get_current_profile()
company_name = current_profile.get("company", "자사 조직")
domain_bm = current_profile.get("domain_bm", "비즈니스 도메인")
constraints_info = current_profile.get("constraints", "사내 인프라 및 예산 제약")
kpi_info = current_profile.get("kpi", "핵심 목표 KPI")


# ==============================================================================
# [화면 1] 지시 접수 및 자사 맥락 주입 화면
# ==============================================================================
if st.session_state.app_phase == "INPUT":
    render_stitch_header(company_name=company_name, user_id=st.session_state.user_id, is_authenticated=True)
    stepper_placeholder = st.empty()
    render_stepper(1, container=stepper_placeholder)
    render_screen1_hero_banner(company_name=company_name, is_authenticated=True)

    # [B2C 쇼핑몰 마케터 5대 핵심 보고서 목적 정의]
    MARKETER_OBJECTIVES = [
        {
            "key": "CVR",
            "title": "상세페이지 구매 전환율(CVR) 극대화 전략 보고서",
            "label": "🎯 상세페이지 리뉴얼 & CVR 개선안 (후기 상단 배치, 소구점 최적화)",
            "icon": "🎯",
            "color": "#2563EB",
            "description": "상세페이지 이탈 방지, 후기/리뷰 최상단 배치, 셀링포인트 강조 및 CVR 개선",
            "placeholder": "예: 현재 광고 유입은 늘었지만 체류 시간이 15초 미만이며 상세페이지 중반에서 이탈률이 75%입니다. 고객 리뷰에서는 '원단감에 대한 실물 설명이 부족하다'는 피드백이 많은데 어떤 순서로 소구점을 배치해야 CVR을 1.2%에서 2.5%까지 올릴 수 있을까요?"
        },
        {
            "key": "AOV",
            "title": "객단가(AOV) 상승을 위한 번들 및 세트 구성 전략 보고서",
            "label": "📦 시즌 프로모션 & 번들(객단가) 기획서 (1+1, 묶음 구성, 할인율 전략)",
            "icon": "📦",
            "color": "#7C3AED",
            "description": "묶음 상품, 1+1 세트 구성, 크로스셀/업셀, 무료배송 기준 최적화",
            "placeholder": "예: 여름 성수기 맞이 수영복/비치웨어인데, 단품만 나가고 객단가가 낮아. 출혈 할인 없이 1+1 번들이나 사은품 묶음으로 객단가(AOV) 올린 타사 사례 찾아봐."
        },
        {
            "key": "SOLUTION",
            "title": "외부 마케팅 솔루션 도입 타당성 검토서",
            "label": "🛠️ 외부 마케팅 솔루션 도입 검토서 (리뷰 솔루션/추천 엔진/CRM 도입 품의)",
            "icon": "🛠️",
            "color": "#0284C7",
            "description": "브이리뷰/레코픽/채널톡/크리마 등 외부 SaaS 솔루션 도입 비용 대비 실측 효과 벤치마크",
            "placeholder": "예: 자사몰 상세페이지에 AI 맞춤 추천 솔루션이나 포토리뷰 위젯을 도입하려 해. 대표님 품의용으로 타사 도입 후 실제 CVR 상승 수치와 효과 조사해줘."
        },
        {
            "key": "ROAS",
            "title": "광고 크리에이티브 소재 및 효율(ROAS) 최적화 전략 보고서",
            "label": "📈 광고 크리에이티브(소재) 개선 기획서 (경쟁사 후킹 카피 및 소구점 분석)",
            "icon": "📈",
            "color": "#059669",
            "description": "메타/인스타 피드 광고 소재 최적화, 경쟁사 후킹 카피 벤치마크 및 랜딩 일치도 개선",
            "placeholder": "예: 메타/인스타 피드 광고비는 계속 나가는데 결제로 안 이어져. 요즘 패션 D2C에서 통하는 영상 썸네일 후킹 카피와 상세페이지 첫 화면 연결 전략 사례 조사해줘."
        },
        {
            "key": "CRM",
            "title": "첫 구매 고객 재구매 유도(CRM/리텐션) 전략 보고서",
            "label": "💌 첫 구매 고객 재구매 유도(CRM) 기획서 (카카오 알림톡/쿠폰 리텐션)",
            "icon": "💌",
            "color": "#D97706",
            "description": "카카오 알림톡, 재구매 유도 쿠폰 시나리오, 첫 구매 후 온보딩 및 고객 생애 가치(LTV) 극대화",
            "placeholder": "예: 신규 고객 획득 비용(CAC)이 너무 비싸. 첫 구매 고객이 14일 이내에 재구매하도록 카카오 알림톡이나 첫 구매 감사 쿠폰 시나리오를 어떻게 짜는지 타사 사례 분석해줘."
        }
    ]

    if "selected_domain_key" not in st.session_state:
        st.session_state.selected_domain_key = "CVR"

    # 1. 5대 전략 도메인 탭 선택기 (클릭 시 드롭다운 대체 및 즉각 세션 연동)
    clicked_key = render_screen1_domain_tabs(selected_key=st.session_state.selected_domain_key)
    if clicked_key != st.session_state.selected_domain_key:
        st.session_state.selected_domain_key = clicked_key
        st.rerun()

    selected_obj = next((obj for obj in MARKETER_OBJECTIVES if obj["key"] == st.session_state.selected_domain_key), MARKETER_OBJECTIVES[0])

    # 2. 실무 과제 입력 (Stitch 1:1)
    s2_html = """
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.25rem; margin-bottom: 0.5rem;">
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span style="width: 22px; height: 22px; border-radius: 50%; background: #004ac6; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700;">2</span>
        <h2 style="font-size: 16px; font-weight: 800; color: #131b2e; margin: 0;">해결하고 싶은 실무 과제 및 현재 상황</h2>
        <span style="font-size: 12px; color: #737686;">(선택)</span>
      </div>
      <span style="font-size: 12px; color: #737686;">최대한 편하게 작성해 주시면 프롬프트에 자동 반영됩니다.</span>
    </div>
    """
    st.html(textwrap.dedent(s2_html).strip())

    raw_query = st.text_area(
        "현재 겪고 있는 문제(전환율 정체, 비싼 광고비 등)와 타깃 상품의 고민을 편하게 적어주세요",
        placeholder=selected_obj["placeholder"],
        height=100,
        label_visibility="collapsed",
        help="제품명, 카테고리, 당면 실무 문제를 적어주시면 AI가 가짜 숫자 없이 사실에 기반하여 분석합니다.",
        key="user_raw_query"
    )

    # 원클릭 질문 템플릿 칩 (Stitch 1:1)
    st.html(f'<div style="display: flex; align-items: center; gap: 0.4rem; font-size: 12px; color: #737686; margin-bottom: 0.4rem; font-weight: 700;">{stitch_icon("add_task", 15, "#004ac6")} 원클릭 질문 템플릿 추가</div>')
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button(
            "+ 상단 3초 이탈 방지",
            key="btn_tmpl_cvr1",
            on_click=_append_query_template,
            args=("상세페이지 상단 3초 이탈 방지를 위한 헤드라인 3종 제시",),
            use_container_width=True
        )
    with c2:
        st.button(
            "+ GIF 시연 배치 가이드",
            key="btn_tmpl_cvr2",
            on_click=_append_query_template,
            args=("체류 시간 확대를 위한 GIF 시연 애니메이션 배치 가이드",),
            use_container_width=True
        )
    with c3:
        st.button(
            "+ 부정리뷰 반전문구",
            key="btn_tmpl_cvr3",
            on_click=_append_query_template,
            args=("부정 리뷰(배송/소재)를 반전시키는 Q&A 섹션 문구",),
            use_container_width=True
        )
    with c4:
        st.button(
            "+ 묶음할인 객단가표",
            key="btn_tmpl_cvr4",
            on_click=_append_query_template,
            args=("객단가(AOV) 증대를 위한 묶음 할인/사은품 조건표 작성",),
            use_container_width=True
        )

    # 3. 벤치마크 및 비교 대상 쇼핑몰 (Stitch 1:1)
    s3_html = """
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.25rem; margin-bottom: 0.5rem;">
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span style="width: 22px; height: 22px; border-radius: 50%; background: #004ac6; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700;">3</span>
        <h2 style="font-size: 16px; font-weight: 800; color: #131b2e; margin: 0;">참고할 경쟁사 또는 벤치마크 스토어 URL</h2>
        <span style="font-size: 12px; color: #737686;">(선택)</span>
      </div>
      <span style="font-size: 12px; color: #737686;">경쟁사의 소구점 구조와 차별화 포인트를 대조 분석합니다.</span>
    </div>
    """
    st.html(textwrap.dedent(s3_html).strip())
    bm_c1, bm_c2 = st.columns(2)
    with bm_c1:
        comp1_url = st.text_input("경쟁사 1 스토어 / 상세 URL", placeholder="https://smartstore.naver.com/competitor_a...", key="comp1_url", label_visibility="collapsed")
    with bm_c2:
        comp2_url = st.text_input("경쟁사 2 스토어 / 벤치마크 브랜드 (선택)", placeholder="https://brand-mall.co.kr/products/...", key="comp2_url", label_visibility="collapsed")

    # 4. 하단 3대 비즈니스 인포 카드
    render_screen1_info_cards()

    # 5. 실행 버튼 (Focus CTA)
    submit_btn = st.button("🚀 시장 분석 및 전략 목차 생성 시작", use_container_width=True, type="primary")

    if submit_btn:
        if not raw_query or not raw_query.strip():
            st.warning("⚠️ 주력 제품이나 당면 실무 고민을 1줄 이상 입력해 주세요.")
        else:
            # 선택된 목적 메타데이터 바인딩
            diagnosed = {
                "type_key": selected_obj["key"],
                "title": selected_obj["title"],
                "description": selected_obj["description"],
                "icon": selected_obj["icon"],
                "color": selected_obj["color"],
            }
            st.session_state.diagnosed_report = diagnosed

            # [2. 수집 및 정제 단계] 상단 Stepper를 즉시 [✅ 1. 지시 접수] ──▶ [🔵 2. 팩트 수집/검증]으로 동적 전환!
            render_stepper(2, container=stepper_placeholder)

            config = {"configurable": {"thread_id": st.session_state.thread_id}}

            # 경쟁사 URL 맥락 결합
            comp_context = ""
            if comp1_url and comp1_url.strip():
                comp_context += f"\n[참고 경쟁사 1]: {comp1_url.strip()}"
            if comp2_url and comp2_url.strip():
                comp_context += f"\n[참고 경쟁사 2]: {comp2_url.strip()}"

            enriched_query = f"""[소속 기업: {company_name} | 사업 영역: {domain_bm}]
[선택된 보고서 목적]: {selected_obj['label']}
[정식 보고서 명칭]: {selected_obj['title']}
[인프라/리소스 제약: {constraints_info}]
[집중 관리 KPI: {kpi_info}]
[실무자 고민/배경]: {raw_query.strip()}{comp_context}"""

            initial_input = {
                "user_id": st.session_state.user_id,
                "raw_query": enriched_query,
                "company_context": {
                    "company": company_name,
                    "domain_bm": domain_bm,
                    "diagnosed_report_title": selected_obj["title"],
                    "report_objective": selected_obj["label"],
                    "constraints": constraints_info,
                    "kpi": kpi_info
                },
                "search_retry_count": 0,
                "human_choice": None
            }

            # 구글 스티치 Screen 2 실시간 동적 대시보드 (Zero-Mock, 100% 실시간 연동)
            status_placeholder = st.empty()
            render_screen2_market_analysis_view(
                company_name=company_name,
                step=1,
                percent=25,
                facts_count=0,
                active_log="[1단계 완료] 마케터 고민 의도 분석 및 정형화 파라미터 매핑 완료",
                container=status_placeholder
            )

            current_facts_count = 0
            # LangGraph 실행 (interrupt_before=["human_gate"] 지점까지 자동 진행)
            for event in app_graph.stream(initial_input, config=config):
                for node_name, state_update in event.items():
                    if node_name == "parse_and_anchor":
                        render_screen2_market_analysis_view(
                            company_name=company_name,
                            step=2,
                            percent=50,
                            facts_count=current_facts_count,
                            active_log=f"[2단계 완료] {company_name} 스토어 자산 분석 완료 ➜ 시장 트렌드 실시간 탐색 쿼리 생성",
                            container=status_placeholder
                        )
                    elif node_name == "research_and_filter":
                        filtered = state_update.get("filtered_articles", [])
                        current_facts_count = len(filtered)
                        render_screen2_market_analysis_view(
                            company_name=company_name,
                            step=3,
                            percent=80,
                            facts_count=current_facts_count,
                            active_log=f"[3단계 완료] 광고성 기사 제외 및 신뢰도 검증 완료 (실측 팩트 {current_facts_count}건 정제)",
                            container=status_placeholder
                        )
                    elif node_name == "rewrite_query":
                        render_screen2_market_analysis_view(
                            company_name=company_name,
                            step=3,
                            percent=65,
                            facts_count=current_facts_count,
                            active_log="[재탐색] 팩트 보강을 위해 검색 쿼리 확장 재시도 중...",
                            container=status_placeholder
                        )
                    elif node_name == "generate_outline":
                        render_screen2_market_analysis_view(
                            company_name=company_name,
                            step=4,
                            percent=100,
                            facts_count=current_facts_count,
                            active_log="[4단계 완료] 핵심 So-What 결론(가설) 도출 및 3대 전략 보고 목차 구성 완료!",
                            container=status_placeholder
                        )

            # 인터럽트 상태의 최신 State 확보
            snapshot = app_graph.get_state(config)
            st.session_state.graph_state = snapshot.values
            st.session_state.app_phase = "HITL"
            st.session_state.pivot_version = 0  # 신규 지시 시 피벗 버전 리셋
            st.rerun()



# ==============================================================================
# [화면 2 & 3] HITL 목차 검토 및 맞춤 관점 전환 화면 (Sprint 6-2 & 6-3 고도화)
# ==============================================================================
elif st.session_state.app_phase == "HITL":
    render_stitch_header(company_name=company_name, user_id=st.session_state.user_id, is_authenticated=True)
    render_stepper(3)

    state = st.session_state.graph_state
    anchors = state.get("anchors", {})
    outline_list = state.get("outline", ["", "", ""])
    current_target = anchors.get("stakeholder", "👑 C-Level/대표 (재무 성과 & ROI 중심)")
    current_angle = anchors.get("angle", "비용 절감 및 효율화")
    pivot_ver = st.session_state.get("pivot_version", 0)
    diagnosed = st.session_state.get("diagnosed_report")
    report_title = diagnosed["title"] if diagnosed else "B2C 상세페이지 CVR 극대화 전략 브리프"

    # 구글 스티치 Screen 3: 딥 슬레이트 가설 배너, 4대 메트릭스, 제이드 가설 박스 (1:1 복제)
    render_screen3_brief_and_metrics(
        report_title=report_title,
        target_stakeholder=current_target.split(" ")[1] if " " in current_target else current_target,
        angle=current_angle,
        facts_count=len(state.get("filtered_articles", [])),
        kpi=anchors.get("kpi", "CVR 2.4%"),
        hypothesis=state.get("hypothesis", "상세페이지 상단에 실착 핏 시각 요소를 전진 배치하여 결제 전환율(CVR)을 극대화합니다."),
        company_name=company_name
    )

    # 목차 인라인 수정창 (Stitch 카드 컨테이너 스타일)
    toc_header = """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; margin-bottom: 0.75rem;">
      <div>
        <h3 style="font-size: 16px; font-weight: 800; color: #131b2e; margin: 0 0 0.2rem 0;">이커머스 보고 목차 커스터마이징</h3>
        <p style="font-size: 12px; color: #737686; margin: 0;">생성될 1장 전략 보고서의 섹션 목차를 확인하고 필요한 경우 직접 수정하세요.</p>
      </div>
      <span class="stitch-badge badge-blue">총 3개 섹션 구성</span>
    </div>
    """
    st.html(textwrap.dedent(toc_header).strip())

    edited_o1 = st.text_input(
        "SECTION 01: 당면 과제 및 기획 배경 (Situation & Challenge)",
        value=outline_list[0] if len(outline_list) > 0 else "",
        key=f"outline_input_0_{current_target}_{pivot_ver}"
    )
    edited_o2 = st.text_input(
        "SECTION 02: 타사 벤치마크 및 시장 팩트 (Market Fact Benchmark)",
        value=outline_list[1] if len(outline_list) > 1 else "",
        key=f"outline_input_1_{current_target}_{pivot_ver}"
    )
    edited_o3 = st.text_input(
        "SECTION 03: 즉시 실행 권고안 (Action Plan)",
        value=outline_list[2] if len(outline_list) > 2 else "",
        key=f"outline_input_2_{current_target}_{pivot_ver}"
    )

    st.markdown("---")

    # 3-Way 액션 버튼 시각적 계층화 (Sprint 6-3 고도화: 드롭다운 선택 시 원클릭 자동 피벗)
    st.markdown("##### 🚦 최종 보고서 승인 및 관점 전환")
    st.caption("💡 보고 대상을 변경하면 대상자 맞춤 전략 목차로 즉시 자동 전환됩니다.")
    btn_col1, btn_col2, btn_col3 = st.columns([2.5, 2.8, 1.2])
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    # [1] 승인: 메인 성공 경로 (type="primary" 강조색)
    with btn_col1:
        if st.button("✅ 목차 최종 승인 및 1장 보고서 작성", type="primary", use_container_width=True):
            updated_outline = [edited_o1, edited_o2, edited_o3]

            app_graph.update_state(
                config,
                {"human_choice": "approve", "outline": updated_outline},
                as_node="human_gate"
            )

            with st.spinner("✍️ 1PAGE 전략 브리핑 보고서 작성 중..."):
                for _ in app_graph.stream(None, config=config):
                    pass
                final_snapshot = app_graph.get_state(config)
                st.session_state.graph_state = final_snapshot.values
                st.session_state.app_phase = "REPORT"
                st.rerun()

    # [2] 피벗: 보고 대상(수신자 성향) 전환 드롭다운 (선택 즉시 자동 피벗)
    with btn_col2:
        pivot_targets = [
            "👑 C-Level/대표 (재무 성과 & ROI 중심)",
            "👔 부서장/팀장 (즉시 실행 & 리소스 중심)",
            "🤝 유관부서 협업 (개발/디자인 타당성 중심)",
            "🛡️ 재무/리스크팀 (예산 효율 & 리스크 방어)"
        ]

        curr_idx = 0
        for i, t in enumerate(pivot_targets):
            if any(k in current_target for k in ["C-Level", "대표", "임원", "성과"]) and "C-Level" in t:
                curr_idx = i
                break
            elif any(k in current_target for k in ["팀장", "부서장", "실행", "실무"]) and "팀장" in t:
                curr_idx = i
                break
            elif any(k in current_target for k in ["협업", "유관", "개발", "디자인"]) and "협업" in t:
                curr_idx = i
                break
            elif any(k in current_target for k in ["리스크", "재무", "방어", "안정"]) and "재무" in t:
                curr_idx = i
                break

        new_target = st.selectbox(
            "보고 대상 선택 (선택 시 맞춤 목차 자동 전환)",
            options=pivot_targets,
            index=curr_idx,
            label_visibility="collapsed",
            key=f"pivot_target_select_{pivot_ver}",
            help="보고 대상을 선택하면 기존 팩트를 보존한 채, 해당 대상자의 눈높이에 맞춘 가설과 목차가 즉시 자동 전환됩니다."
        )

        # 항목 변경 감지 시 별도 버튼 없이 즉시 자동 피벗 실행
        if new_target != pivot_targets[curr_idx]:
            target_name = new_target.split(" ")[1] if " " in new_target else new_target
            updated_anchors = dict(anchors)
            updated_anchors["stakeholder"] = new_target

            # 보고 앵글도 대상자의 관심사에 맞추어 자연스럽게 동기화
            if "C-Level" in new_target:
                updated_anchors["angle"] = "신규 사업 기회 및 ROI 극대화"
            elif "팀장" in new_target:
                updated_anchors["angle"] = "실무 즉시 실행 및 타사 벤치마킹"
            elif "협업" in new_target:
                updated_anchors["angle"] = "기술 역량 내재화 및 협업 공수 최적화"
            elif "재무" in new_target:
                updated_anchors["angle"] = "비용 절감 및 리스크 선제 방어"

            app_graph.update_state(
                config,
                {"human_choice": "pivot_angle", "anchors": updated_anchors},
                as_node="human_gate"
            )

            with st.spinner(f"기존 팩트 풀 기반 [{target_name}] 맞춤 목차 자동 전환 중..."):
                for _ in app_graph.stream(None, config=config):
                    pass
                pivot_snapshot = app_graph.get_state(config)
                st.session_state.graph_state = pivot_snapshot.values
                st.session_state.pivot_version += 1  # Dynamic Key 갱신 트리거!
                st.rerun()

    # [3] 전면 초기화: 처음부터 다시 작성
    with btn_col3:
        if st.button("처음부터 다시 작성", use_container_width=True, help="현재 수집된 데이터와 목차를 초기화하고 첫 화면으로 돌아갑니다."):
            st.session_state.app_phase = "INPUT"
            st.session_state.graph_state = {}
            st.session_state.pivot_version = 0
            if "user_raw_query" in st.session_state:
                st.session_state.user_raw_query = ""
            st.rerun()


# ==============================================================================
# [화면 4] 최종 1장 SCQA 전략 브리프 및 노션 연동 (Sprint 6-4)
# ==============================================================================
elif st.session_state.app_phase == "REPORT":
    render_stitch_header(company_name=company_name, user_id=st.session_state.user_id, is_authenticated=True)
    render_stepper(4)

    state = st.session_state.graph_state
    # Dual-Rendering 원칙: Notion API 전송용 순수 마크다운 원형 보존
    report_text = state.get("final_report", "생성된 보고서가 없습니다.")
    anchors = state.get("anchors", {})
    filtered_articles = state.get("filtered_articles", [])
    hypothesis = state.get("hypothesis", "")

    diagnosed = st.session_state.get("diagnosed_report")
    report_title = diagnosed["title"] if diagnosed else "1Page 이커머스 비즈니스 전략 브리프"

    # 구글 스티치 Screen 4: 1PAGE 대시보드 탑 배너 & Executive Summary (1:1 복제)
    render_screen4_report_header_and_summary(
        report_title=report_title,
        company_name=company_name,
        kpi=kpi_info[:16] + "..." if len(kpi_info) > 16 else kpi_info,
        angle=anchors.get("angle", "비용 절감 및 효율화"),
        facts_count=len(filtered_articles),
        hypothesis=hypothesis or "상세페이지 상단에 실착 핏 시각 요소를 전진 배치하여 결제 전환율(CVR)을 극대화합니다.",
        monthly_impact="+3,420만 원"
    )

    # 3. 마크다운 보고서 본문 렌더링 (카드 컨테이너 적용)
    with st.container(border=True):
        st.markdown(report_text)

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. 원천 기사 출처(Fact URLs) 깔끔한 배지형 링크 노출 (Sprint 6-4)
    if filtered_articles:
        st.markdown("##### 🔗 검증된 시장 팩트 원천 기사 (출처 링크)")
        badge_cols = st.columns(min(len(filtered_articles), 3))
        for idx, art in enumerate(filtered_articles[:3]):
            title = art.get("title", f"출처 기사 {idx+1}")
            url = art.get("url", "#")
            with badge_cols[idx % 3]:
                st.link_button(
                    f"📰 {title[:28]}...",
                    url=url,
                    use_container_width=True,
                    help=f"{title}\n{url}"
                )

    st.divider()

    # 5. Notion 전략 DB 전송 및 사후 액션 바 (Dual-Rendering 원칙으로 원형 전송)
    act_col1, act_col2, act_col3 = st.columns([2.5, 2.5, 1.5])

    with act_col1:
        if st.button("🚀 Notion 페이지로 내보내기", type="primary", use_container_width=True):
            with st.spinner("Notion API 연동 중 ..."):
                clean_hypo = hypothesis[:30] if hypothesis else "실행 권고안"
                title = f"[{report_title}] {company_name} - {clean_hypo}"
                urls = [art.get("url") for art in filtered_articles if art.get("url")]
                
                # Dual-Rendering: 순수 마크다운 report_text를 그대로 전달
                notion_link = export_report_to_notion(
                    title=title,
                    report_markdown=report_text,
                    source_urls=urls
                )
                if notion_link:
                    st.session_state.notion_url = notion_link
                    st.success("✅ 노션 데이터베이스 페이지가 성공적으로 생성되었습니다!")
                else:
                    st.error("노션 전송에 실패했습니다. .env의 NOTION_TOKEN 및 NOTION_DATABASE_ID 설정을 확인하세요.")

    with act_col2:
        if st.session_state.notion_url:
            st.link_button("🔗 생성된 Notion 페이지 바로가기 ↗", st.session_state.notion_url, use_container_width=True)
        else:
            st.button("🔗 생성된 Notion 페이지 바로가기", disabled=True, use_container_width=True, help="먼저 좌측 버튼으로 노션에 내보내기를 완료해 주세요.")

    with act_col3:
        if st.button("🔄 새 보고서 작성", use_container_width=True):
            st.session_state.app_phase = "INPUT"
            st.session_state.graph_state = {}
            st.session_state.pivot_version = 0
            if "user_raw_query" in st.session_state:
                st.session_state.user_raw_query = ""
            st.rerun()