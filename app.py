import streamlit as st
from dotenv import load_dotenv

from core.graph import app_graph
from core.tools import export_report_to_notion
from auth import render_auth_sidebar, get_current_profile

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
      1: 지시 접수
      2: 팩트 수집/검증
      3: 목차 컨펌 (HITL)
      4: 보고서 완성
    """
    steps = [
        (1, "1. 지시 접수"),
        (2, "2. 팩트 수집/검증"),
        (3, "3. 목차 컨펌(HITL)"),
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
    st.info("👈 좌측 사이드바에서 **[브랜드명] + [공식 URL] + [당면 과제]**를 입력하고 **[세션 생성 및 전략 분석 시작]**을 진행해 주세요.")
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

    st.header("🧭 So-What Agent: 비즈니스 동향 보고서 생성")
    st.markdown("상사의 모호한 구두 지시나 실무 자연어 넋두리를 입력하면, 실질 팩트만 걸러내 **1장 SCQA 전략 보고서** 초안을 작성합니다.")

    # 🏢 자사 비즈니스 맥락 3대 요소 인지용 안내 배지
    st.markdown(f"""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-size: 13px; font-weight: 700; color: #1e293b;">
                🏢 현재 적용 중인 자사 맥락: <span style="color: #2563eb;">{company_name}</span> | <span style="color: #475569; font-weight: 500;">{domain_bm}</span>
            </span>
            <span style="font-size: 11px; background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 9999px; font-weight: 600;">
                SME 자동 주입 모드
            </span>
        </div>
        <div style="font-size: 12px; color: #64748b; display: flex; gap: 16px; flex-wrap: wrap;">
            <span>🔒 <b>인프라 제약:</b> {constraints_info}</span>
            <span>📈 <b>목표 KPI:</b> {kpi_info}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("input_form"):
        raw_query = st.text_area(
            "상사 지시문 또는 실무 넋두리 (1~2줄)",
            placeholder="예: 젝시믹스나 안다르 등 타사 요가 레깅스 상세페이지에서 구매 전환율(CVR)을 끌어올린 프로모션 및 후기 배치 전략 조사해봐.",
            height=120
        )
        submit_btn = st.form_submit_button("🚀 비즈니스 팩트 수집 및 목차 생성 시작", use_container_width=True, type="primary")

    if submit_btn and raw_query.strip():
        # [2. 수집 및 정제 단계] 상단 Stepper를 즉시 [✅ 1. 지시 접수] ──▶ [🔵 2. 팩트 수집/검증]으로 동적 전환!
        render_stepper(2, container=stepper_placeholder)

        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        enriched_query = f"""[소속 기업: {company_name} | 사업 영역: {domain_bm}]
[인프라/리소스 제약: {constraints_info}]
[집중 관리 KPI: {kpi_info}]
[실무자 지시문]: {raw_query.strip()}"""

        initial_input = {
            "user_id": st.session_state.user_id,
            "raw_query": enriched_query,
            "company_context": {
                "company": company_name,
                "domain_bm": domain_bm,
                "constraints": constraints_info,
                "kpi": kpi_info
            },
            "search_retry_count": 0,
            "human_choice": None
        }

        with st.status("🔍 외부 시장 데이터 수집 및 가설 도출 중...", expanded=True) as status:
            st.write("1. 넋두리 분석 및 4대 앵커(KPI, 자사 제약, 태도, 앵글) 추출 중...")

            # LangGraph 실행 (interrupt_before=["human_gate"] 지점까지 자동 진행)
            for event in app_graph.stream(initial_input, config=config):
                for node_name, state_update in event.items():
                    if node_name == "parse_and_anchor":
                        st.write("2. 핵심 앵커 고정 완료 -> Tavily 고속 검색 실행...")
                    elif node_name == "research_and_filter":
                        filtered = state_update.get("filtered_articles", [])
                        st.write(f"3. HF mDeBERTa 노이즈 필터링 완료 (유효 팩트 {len(filtered)}건 확보)")
                    elif node_name == "rewrite_query":
                        st.write("⚠️ 팩트 부족으로 검색 쿼리 확장 재시도 중...")
                    elif node_name == "generate_outline":
                        st.write("4. 가설 1줄 및 SCQA 3대 목차 설계 완료!")

            # 인터럽트 상태의 최신 State 확보
            snapshot = app_graph.get_state(config)
            st.session_state.graph_state = snapshot.values
            st.session_state.app_phase = "HITL"
            st.session_state.pivot_version = 0  # 신규 지시 시 피벗 버전 리셋
            status.update(label="✅ 목차 설계 완료! 승인 대기 중", state="complete", expanded=False)
            st.rerun()


# ==============================================================================
# [화면 2 & 3] HITL 목차 검토 및 3-Way 분기 화면 (Sprint 6-3 고도화)
# ==============================================================================
elif st.session_state.app_phase == "HITL":
    render_stepper(3)

    st.header("📋 [HITL 게이트] 핵심 가설 및 3대 목차 승인")
    st.info("💡 에이전트가 도출한 가설과 목차를 검토하세요. 목차는 직접 수정할 수 있으며, 앵글 피벗 시 기존 팩트를 보존한 채 목차만 신속하게 재도출합니다.")

    state = st.session_state.graph_state
    anchors = state.get("anchors", {})
    outline_list = state.get("outline", ["", "", ""])
    current_angle = anchors.get("angle", "비용 절감 및 효율화")
    pivot_ver = st.session_state.get("pivot_version", 0)

    # 4대 앵커 메트릭 카드 영역
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("🎯 부서 KPI", anchors.get("kpi", "N/A"))
    col_b.metric("👥 수신자 성향", anchors.get("stakeholder", "N/A"))
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
        "목차 1 (상황 및 당면 과제)",
        value=outline_list[0] if len(outline_list) > 0 else "",
        key=f"outline_input_0_{current_angle}_{pivot_ver}"
    )
    edited_o2 = st.text_input(
        "목차 2 (시장 동향 및 팩트 요약)",
        value=outline_list[1] if len(outline_list) > 1 else "",
        key=f"outline_input_1_{current_angle}_{pivot_ver}"
    )
    edited_o3 = st.text_input(
        "목차 3 (시사점 및 실행 방안)",
        value=outline_list[2] if len(outline_list) > 2 else "",
        key=f"outline_input_2_{current_angle}_{pivot_ver}"
    )

    st.markdown("---")

    # 3-Way 액션 버튼 시각적 계층화 (Sprint 6-3)
    st.markdown("##### 🚦 3-Way 의사결정")
    btn_col1, btn_col2, btn_col3 = st.columns([2.5, 2.5, 1.2])
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

    # [2] 피벗: 보조 탐색 행동 (Secondary 스타일)
    with btn_col2:
        pivot_angles = ["비용 절감 및 효율화", "리스크 선제 방어", "신규 사업 기회", "기술 역량 내재화", "경쟁사 벤치마킹"]
        curr_idx = pivot_angles.index(current_angle) if current_angle in pivot_angles else 0
        new_angle = st.selectbox(
            "피벗할 앵글 선택",
            options=pivot_angles,
            index=(curr_idx + 1) % len(pivot_angles),
            label_visibility="collapsed"
        )
        if st.button(f"🔄 '{new_angle}' 관점으로 피벗", type="secondary", use_container_width=True):
            updated_anchors = dict(anchors)
            updated_anchors["angle"] = new_angle

            app_graph.update_state(
                config,
                {"human_choice": "pivot_angle", "anchors": updated_anchors},
                as_node="human_gate"
            )

            with st.spinner("기존 팩트 풀 보존 상태에서 신규 앵글 목차 재도출 중..."):
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

    st.header("📄 1-Page SCQA 비즈니스 전략 브리프")
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
                title = f"[전략 브리프] {hypothesis[:40] if hypothesis else '비즈니스 동향 보고서'}"
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