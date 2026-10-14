import streamlit as st
from dotenv import load_dotenv

from core.graph import app_graph
from core.tools import export_report_to_notion
from auth import (
    render_auth_sidebar,
    get_current_profile,
    diagnose_ecommerce_report_type,
    ECOMMERCE_REPORT_TYPES,
)

# ------------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인 테마 CSS 주입
# ------------------------------------------------------------------------------
load_dotenv()
st.set_page_config(
    page_title="So-What Agent | 실무 전략 부사수",
    page_icon="🧭",
    layout="wide"
)

# B2B 엔터프라이즈 UX 스타일링 (4단계 Stepper, 카드 레이아웃, 액션 버튼 분리)
STEPPER_CSS = """
<style>
/* 4단계 진행 Stepper 컴포넌트 */
.stepper-wrapper {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px 24px;
    margin-bottom: 24px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.step-node {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 500;
    color: #94a3b8;
}
.step-node.completed {
    color: #059669;
    font-weight: 600;
}
.step-node.active {
    color: #2563eb;
    font-weight: 700;
}
.step-circle {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    background: #e2e8f0;
    color: #64748b;
}
.step-node.completed .step-circle {
    background: #10b981;
    color: #ffffff;
}
.step-node.active .step-circle {
    background: #2563eb;
    color: #ffffff;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
}
.step-divider {
    flex: 1;
    height: 2px;
    background: #e2e8f0;
    margin: 0 12px;
}
.step-divider.filled {
    background: #10b981;
}

/* 핵심 가설 및 하이라이트 박스 */
.hypothesis-callout {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 12px 0 20px 0;
    font-size: 14px;
    color: #1e3a8a;
}
</style>
"""
st.markdown(STEPPER_CSS, unsafe_allow_html=True)


def render_stepper(active_step_idx: int, container=None):
    """
    상단 4단계 Stepper UI 컴포넌트 렌더링 (Sprint 6-3)
    active_step_idx:
      1: 고민 접수
      2: 커머스 팩트 수집
      3: 목차 컨펌
      4: 보고서 완성
    """
    steps = [
        (1, "1. 고민 접수"),
        (2, "2. 커머스 팩트 수집"),
        (3, "3. 목차 컨펌"),
        (4, "4. 보고서 완성"),
    ]

    html_parts = ['<div class="stepper-wrapper">']
    for idx, (num, name) in enumerate(steps):
        if num < active_step_idx:
            status_cls = "completed"
            badge = "✓"
        elif num == active_step_idx:
            status_cls = "active"
            badge = str(num)
        else:
            status_cls = "pending"
            badge = str(num)

        html_parts.append(f"""
        <div class="step-node {status_cls}">
            <div class="step-circle">{badge}</div>
            <span>{name}</span>
        </div>
        """)

        if idx < len(steps) - 1:
            divider_cls = "filled" if num < active_step_idx else ""
            html_parts.append(f'<div class="step-divider {divider_cls}"></div>')

    html_parts.append('</div>')
    target = container if container is not None else st
    target.markdown("".join(html_parts), unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 2. 사이드바 인증 게이트 및 전역 SME 컨텍스트 바인딩
# ------------------------------------------------------------------------------
user_id, thread_id, is_authenticated = render_auth_sidebar()

# 인증 미완료 시 메인 화면 차단
if not is_authenticated:
    st.header("🧭 So-What Agent: 비즈니스 동향 보고서 생성")
    st.info("👈 좌측 사이드바에서 **쇼핑몰 URL (필수)**을 입력하고 **[세션 생성 및 전략 분석 시작]**을 진행해 주세요. (브랜드명은 비워두셔도 자동 추출됩니다)")
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
    stepper_placeholder = st.empty()
    render_stepper(1, container=stepper_placeholder)

    st.header("🧭 So-What Agent: 이커머스 전략 보고서 생성")
    st.markdown("상사의 모호한 구두 지시나 실무 자연어 넋두리를 입력하면, 실질 팩트만 걸러내 **1장 SCQA 전략 보고서** 초안을 작성합니다.")

    # 🏢 자사 비즈니스 맥락 3대 요소 인지용 안내 배지
    st.markdown(f"""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-size: 13px; font-weight: 700; color: #1e293b;">
                🏢 현재 적용 중인 자사 맥락: <span style="color: #2563eb;">{company_name}</span> | <span style="color: #475569; font-weight: 500;">{domain_bm}</span>
            </span>
            <span style="font-size: 11px; background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 9999px; font-weight: 600;">
                이커머스 SME 자동 주입
            </span>
        </div>
        <div style="font-size: 12px; color: #64748b; display: flex; gap: 16px; flex-wrap: wrap;">
            <span>🔒 <b>인프라 제약:</b> {constraints_info}</span>
            <span>📈 <b>목표 KPI:</b> {kpi_info}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # [B2C 쇼핑몰 마케터 5대 핵심 보고서 목적 정의]
    MARKETER_OBJECTIVES = [
        {
            "key": "CVR",
            "title": "상세페이지 구매 전환율(CVR) 극대화 전략 보고서",
            "label": "🎯 상세페이지 리뉴얼 & CVR 개선안 (후기 상단 배치, 소구점 최적화)",
            "icon": "🎯",
            "color": "#2563EB",
            "description": "상세페이지 이탈 방지, 후기/리뷰 최상단 배치, 셀링포인트 강조 및 CVR 개선",
            "placeholder": "예: 디다 린넨 원피스 상세페이지인데, 유입은 많은데 장바구니 전환이 낮아. 타사처럼 첫 화면에 실착 포토리뷰를 어떻게 배치해야 CVR이 오를지 벤치마크 조사해줘."
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

    objective_labels = [obj["label"] for obj in MARKETER_OBJECTIVES]

    st.markdown("##### 1️⃣ 보고서 작성 목적 선택 (필수)")
    selected_label = st.selectbox(
        "어떤 의사결정을 위한 보고서인가요?",
        options=objective_labels,
        index=0,
        help="작성하고자 하는 비즈니스 보고서의 목적을 선택하면 타깃 벤치마크 팩트만 정밀 검색합니다.",
        key="selected_objective_label"
    )

    selected_obj = next(obj for obj in MARKETER_OBJECTIVES if obj["label"] == selected_label)

    st.markdown("##### 2️⃣ 자사 쇼핑몰 상황 및 구체적 고민 (넋두리 1~2줄)")
    raw_query = st.text_area(
        "주력 제품 및 현재 겪고 있는 실무 병목을 편하게 적어주세요",
        placeholder=selected_obj["placeholder"],
        height=110,
        help="제품명, 카테고리, 당면 고민을 적어주시면 AI가 가짜 숫자 없이 사실 그대로 앵커링합니다.",
        key="user_raw_query"
    )

    submit_btn = st.button("🚀 1장 실무 전략 보고서 생성 시작", use_container_width=True, type="primary")

    if submit_btn:
        if not raw_query or not raw_query.strip():
            st.warning("⚠️ 주력 제품이나 당면 고민(넋두리)을 1줄 이상 입력해 주세요.")
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

        enriched_query = f"""[소속 기업: {company_name} | 사업 영역: {domain_bm}]
[선택된 보고서 목적]: {selected_obj['label']}
[정식 보고서 명칭]: {selected_obj['title']}
[인프라/리소스 제약: {constraints_info}]
[집중 관리 KPI: {kpi_info}]
[실무자 고민/넋두리]: {raw_query.strip()}"""

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

        with st.status("🔍 외부 시장 데이터 수집 및 가설 도출 중...", expanded=True) as status:
            st.write(f"1. 넋두리 분석 -> 🏷️ **[{diagnosed['title']}]** 진단 완료")
            st.write("2. 4대 앵커(KPI, 자사 제약, 태도, 앵글) 추출 및 타깃 검색 쿼리 구성 중...")

            # LangGraph 실행 (interrupt_before=["human_gate"] 지점까지 자동 진행)
            for event in app_graph.stream(initial_input, config=config):
                for node_name, state_update in event.items():
                    if node_name == "parse_and_anchor":
                        st.write("3. 핵심 앵커 고정 완료 -> Tavily 고속 검색 실행...")
                    elif node_name == "research_and_filter":
                        filtered = state_update.get("filtered_articles", [])
                        st.write(f"4. HF mDeBERTa 노이즈 필터링 완료 (유효 팩트 {len(filtered)}건 확보)")
                    elif node_name == "rewrite_query":
                        st.write("⚠️ 팩트 부족으로 검색 쿼리 확장 재시도 중...")
                    elif node_name == "generate_outline":
                        st.write("5. 가설 1줄 및 SCQA 3대 목차 설계 완료!")

            # 인터럽트 상태의 최신 State 확보
            snapshot = app_graph.get_state(config)
            st.session_state.graph_state = snapshot.values
            st.session_state.app_phase = "HITL"
            st.session_state.pivot_version = 0  # 신규 지시 시 피벗 버전 리셋
            status.update(label="✅ 목차 설계 완료! 승인 대기 중", state="complete", expanded=False)
            st.rerun()


# ==============================================================================
# [화면 2 & 3] HITL 목차 검토 및 3-Way 분기 화면 (Sprint 6-2 & 6-3 고도화)
# ==============================================================================
elif st.session_state.app_phase == "HITL":
    render_stepper(3)

    st.header("📋 [HITL 게이트] 핵심 가설 및 3대 목차 승인")
    st.info("💡 에이전트가 도출한 가설과 목차를 검토하세요. 목차는 직접 수정할 수 있으며, 앵글 피벗 시 기존 팩트를 보존한 채 목차만 신속하게 재도출합니다.")

    # [Sprint 6-2] 진단된 정식 보고서 유형 배지 렌더링
    diagnosed = st.session_state.get("diagnosed_report")
    if diagnosed:
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #1e293b, #0f172a);
            border: 1px solid #334155;
            border-left: 5px solid {diagnosed['color']};
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px;">
                    🏷️ 자동 진단된 정식 보고서 유형
                </span>
                <span style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 9999px; font-size: 11px; padding: 2px 10px; font-weight: 600;">
                    B2C 커머스 표준 진단
                </span>
            </div>
            <div style="font-size: 16px; font-weight: 700; color: #f8fafc;">
                {diagnosed['icon']} {diagnosed['title']}
            </div>
            <div style="font-size: 12px; color: #cbd5e1; margin-top: 3px;">
                {diagnosed['description']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    state = st.session_state.graph_state
    anchors = state.get("anchors", {})
    outline_list = state.get("outline", ["", "", ""])
    current_target = anchors.get("stakeholder", "👑 C-Level/대표 (재무 성과 & ROI 중심)")
    current_angle = anchors.get("angle", "비용 절감 및 효율화")
    pivot_ver = st.session_state.get("pivot_version", 0)

    # 4대 앵커 메트릭 카드 영역
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("🎯 부서 KPI", anchors.get("kpi", "N/A"))
    col_b.metric("👥 보고 대상(수신자)", current_target.split(" ")[1] if " " in current_target else current_target)
    col_c.metric("📐 보고 앵글", current_angle)
    col_d.metric("📊 정제 팩트 풀", f"{len(state.get('filtered_articles', []))}건 확보")

    if anchors.get("constraints"):
        st.caption(f"🔒 **반영된 자사 제약**: {anchors.get('constraints')}")

    # 핵심 가설 1줄 표시
    st.markdown("##### 💡 도출된 핵심 가설 (1줄)")
    st.markdown(f"""
    <div class="hypothesis-callout">
        <b>가설:</b> {state.get('hypothesis', '가설이 도출되지 않았습니다.')}
    </div>
    """, unsafe_allow_html=True)

    # SCQA 3대 목차 인라인 수정창 (Sprint 6-3: Dynamic Key 바인딩으로 위젯 캐싱 트랩 100% 제거!)
    st.markdown("##### 📝 SCQA 3대 목차 (필요 시 인라인 수정)")

    edited_o1 = st.text_input(
        "목차 1 (당면 과제 및 기획 배경)",
        value=outline_list[0] if len(outline_list) > 0 else "",
        key=f"outline_input_0_{current_target}_{pivot_ver}"
    )
    edited_o2 = st.text_input(
        "목차 2 (타사 벤치마크 및 시장 팩트)",
        value=outline_list[1] if len(outline_list) > 1 else "",
        key=f"outline_input_1_{current_target}_{pivot_ver}"
    )
    edited_o3 = st.text_input(
        "목차 3 (즉시 실행 권고안)",
        value=outline_list[2] if len(outline_list) > 2 else "",
        key=f"outline_input_2_{current_target}_{pivot_ver}"
    )

    st.markdown("---")

    # 3-Way 액션 버튼 시각적 계층화 (Sprint 6-3 고도화: 드롭다운 선택 시 원클릭 자동 피벗)
    st.markdown("##### 🚦 3-Way 의사결정")
    st.caption("💡 보고 대상(가운데 드롭다운)을 변경하면 별도 버튼 클릭 없이 기존 팩트를 보존한 채 맞춤 목차가 즉시 자동 재도출됩니다.")
    btn_col1, btn_col2, btn_col3 = st.columns([2.5, 2.8, 1.2])
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    # [1] 승인: 메인 성공 경로 (type="primary" 강조색)
    with btn_col1:
        if st.button("✅ 목차 승인 및 1장 보고서 작성", type="primary", use_container_width=True):
            updated_outline = [edited_o1, edited_o2, edited_o3]

            app_graph.update_state(
                config,
                {"human_choice": "approve", "outline": updated_outline},
                as_node="human_gate"
            )

            with st.spinner("✍️ 1장 분량 고밀도 SCQA 전략 보고서 작성 중..."):
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
            "피벗할 보고 대상(수신자) 선택",
            options=pivot_targets,
            index=curr_idx,
            label_visibility="collapsed",
            key=f"pivot_target_select_{pivot_ver}",
            help="보고 대상을 선택하면 기존 팩트를 보존한 채, 해당 대상자의 눈높이에 맞춘 가설과 목차가 즉시 자동 재도출됩니다."
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

            with st.spinner(f"기존 팩트 풀 보존 상태에서 [{target_name}] 맞춤 목차 자동 재도출 중..."):
                for _ in app_graph.stream(None, config=config):
                    pass
                pivot_snapshot = app_graph.get_state(config)
                st.session_state.graph_state = pivot_snapshot.values
                st.session_state.pivot_version += 1  # Dynamic Key 갱신 트리거!
                st.rerun()

    # [3] 전면 초기화: 상태 파괴적 행동 (분리 배치 및 주의 라벨링)
    with btn_col3:
        if st.button("⚠️ 전면 취소 (초기화)", use_container_width=True, help="현재 수집된 팩트와 목차를 폐기하고 첫 화면으로 돌아갑니다."):
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
    render_stepper(4)

    state = st.session_state.graph_state
    # Dual-Rendering 원칙: Notion API 전송용 순수 마크다운 원형 보존
    report_text = state.get("final_report", "생성된 보고서가 없습니다.")
    anchors = state.get("anchors", {})
    filtered_articles = state.get("filtered_articles", [])
    hypothesis = state.get("hypothesis", "")

    diagnosed = st.session_state.get("diagnosed_report")
    report_title = diagnosed["title"] if diagnosed else "1-Page SCQA 비즈니스 전략 브리프"

    st.header(f"📄 {report_title}")
    st.markdown("사내 보고용 고밀도 1장 전략 보고서입니다. 상사용 핵심 지표와 권고 실행안이 요약되어 있습니다.")

    # 1. 상단 브리프 핵심 메트릭 카드 (Sprint 6-4)
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("🏢 대상 기업", company_name)
    with m_col2:
        st.metric("📐 적용 앵글", anchors.get("angle", "비용 절감 및 효율화"))
    with m_col3:
        st.metric("🎯 목표 KPI", kpi_info[:16] + "..." if len(kpi_info) > 16 else kpi_info)
    with m_col4:
        st.metric("📊 검증 팩트", f"{len(filtered_articles)}건 기반")

    # 2. 도출된 핵심 가설 (3초 인지용 콜아웃)
    if hypothesis:
        st.markdown(f"""
        <div class="hypothesis-callout">
            <b>💡 핵심 결론 (Hypothesis):</b> {hypothesis}
        </div>
        """, unsafe_allow_html=True)

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
        if st.button("🚀 Notion 전략 DB에 1-Click 내보내기", type="primary", use_container_width=True):
            with st.spinner("Notion API 연동 중 (블록 파싱 및 데이터베이스 적재)..."):
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
        if st.button("🔄 새 지시 분석", use_container_width=True):
            st.session_state.app_phase = "INPUT"
            st.session_state.graph_state = {}
            st.session_state.notion_url = None
            st.session_state.pivot_version = 0
            st.rerun()