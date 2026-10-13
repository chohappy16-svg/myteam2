import streamlit as st
from dotenv import load_dotenv

from core.graph import app_graph
from core.tools import export_report_to_notion
from auth import render_auth_sidebar, get_current_profile

# ------------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 초기화
# ------------------------------------------------------------------------------
load_dotenv()
st.set_page_config(
    page_title="So-What Agent | 실무 전략 부사수",
    page_icon="🧭",
    layout="wide"
)

# 사이드바 인증 게이트 렌더링 (사번, thread_id, 인증여부 반환)
user_id, thread_id, is_authenticated = render_auth_sidebar()

# 인증 미완료 시 메인 화면 차단
if not is_authenticated:
    st.header("🧭 So-What Agent: 비즈니스 동향 보고서 생성")
    st.info("👈 좌측 사이드바에서 **[데모 프리셋]**을 선택하거나 **[AI 자동 프로파일링]**을 통해 로그인해 주세요.")
    st.stop()

# 세션 상태 기본값 초기화
if "app_phase" not in st.session_state:
    st.session_state.app_phase = "INPUT"
if "graph_state" not in st.session_state:
    st.session_state.graph_state = {}
if "notion_url" not in st.session_state:
    st.session_state.notion_url = None

# 현재 인증된 SME 프로필 조회 (Sprint 6-2)
current_profile = get_current_profile()
company_name = current_profile.get("company", "자사 조직")
domain_bm = current_profile.get("domain_bm", "비즈니스 도메인")
constraints_info = current_profile.get("constraints", "사내 인프라 및 예산 제약")
kpi_info = current_profile.get("kpi", "핵심 목표 KPI")


# ==============================================================================
# [화면 1] 지시 접수 및 자사 맥락 주입 화면 (Sprint 6-2)
# ==============================================================================
if st.session_state.app_phase == "INPUT":
    st.header("🧭 So-What Agent: 비즈니스 동향 보고서 생성")
    st.markdown("상사의 모호한 구두 지시나 실무 자연어 넋두리를 입력하면, 실질 팩트만 걸러내 **1장 SCQA 전략 보고서** 초안을 작성합니다.")

    # 🏢 [Sprint 6-2] 자사 비즈니스 맥락 3대 요소 인지용 안내 배지
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
            placeholder="예: 타사 AI 마케팅 개인화 솔루션 도입한다는데, 우리 쇼핑몰 호스팅 환경 연동 비용이랑 실제 ROAS 개선 지표 위주로 파악해봐.",
            height=120
        )
        submit_btn = st.form_submit_button("🚀 비즈니스 팩트 수집 및 목차 생성 시작", use_container_width=True, type="primary")

    if submit_btn and raw_query.strip():
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        # [Sprint 6-2] 자사 맥락 3요소를 지시문에 자연스럽게 합성하고 initial_state에 비파괴 주입
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
            status.update(label="✅ 목차 설계 완료! 승인 대기 중", state="complete", expanded=False)
            st.rerun()


# ==============================================================================
# [화면 2 & 3] HITL 목차 검토 및 3-Way 분기 화면
# ==============================================================================
elif st.session_state.app_phase == "HITL":
    st.header("📋 [HITL 게이트] 가설 및 3대 목차 승인")
    st.info("💡 에이전트가 도출한 가설과 목차를 검토하세요. 목차는 직접 수정할 수 있으며, 앵글 피벗 시 기존 팩트를 보존한 채 목차만 재도출합니다.")

    state = st.session_state.graph_state
    anchors = state.get("anchors", {})
    outline_list = state.get("outline", ["", "", ""])

    # 상단 메타데이터 요약 카드
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("부서 KPI", anchors.get("kpi", "N/A"))
    col_b.metric("수신자 성향", anchors.get("stakeholder", "N/A"))
    col_c.metric("보고 앵글", anchors.get("angle", "N/A"))
    col_d.metric("정제 팩트 풀", f"{len(state.get('filtered_articles', []))}건 확보")

    st.subheader("💡 도출된 핵심 가설 (1줄)")
    st.code(state.get("hypothesis", ""), language="text")

    st.subheader("📝 SCQA 3대 목차 (필요시 인라인 수정)")
    edited_o1 = st.text_input("목차 1 (상황 및 당면 과제)", value=outline_list[0] if len(outline_list) > 0 else "")
    edited_o2 = st.text_input("목차 2 (시장 동향 및 팩트 요약)", value=outline_list[1] if len(outline_list) > 1 else "")
    edited_o3 = st.text_input("목차 3 (시사점 및 실행 방안)", value=outline_list[2] if len(outline_list) > 2 else "")

    st.divider()

    # 3-Way 분기 버튼 영역
    btn_col1, btn_col2, btn_col3 = st.columns([2, 1.5, 1])
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    # [1] 승인 (Approve -> Node 4 직행)
    with btn_col1:
        if st.button("✅ 목차 승인 및 보고서 작성", type="primary", use_container_width=True):
            updated_outline = [edited_o1, edited_o2, edited_o3]

            # 사용자 수정 목차 및 승인 분기 State에 주입
            app_graph.update_state(
                config,
                {"human_choice": "approve", "outline": updated_outline},
                as_node="human_gate"
            )

            with st.spinner("✍️ 1장 분량 고밀도 SCQA 마크다운 보고서 작성 중..."):
                for _ in app_graph.stream(None, config=config):
                    pass
                final_snapshot = app_graph.get_state(config)
                st.session_state.graph_state = final_snapshot.values
                st.session_state.app_phase = "REPORT"
                st.rerun()

    # [2] 앵글 피벗 (Pivot Angle -> Node 3 롤백)
    with btn_col2:
        new_angle = st.selectbox(
            "피벗할 앵글 선택",
            ["비용 절감 및 효율화", "리스크 선제 방어", "신규 사업 기회", "기술 역량 내재화", "경쟁사 벤치마킹"],
            label_visibility="collapsed"
        )
        if st.button("🔄 앵글 피벗 (재검색 없이 롤백)", use_container_width=True):
            updated_anchors = dict(anchors)
            updated_anchors["angle"] = new_angle

            # 앵글 수정 주입 및 Time-Travel 롤백
            app_graph.update_state(
                config,
                {"human_choice": "pivot_angle", "anchors": updated_anchors},
                as_node="human_gate"
            )

            with st.spinner("기존 팩트 풀 기반으로 신규 앵글 목차 재도출 중..."):
                for _ in app_graph.stream(None, config=config):
                    pass
                pivot_snapshot = app_graph.get_state(config)
                st.session_state.graph_state = pivot_snapshot.values
                st.rerun()

    # [3] 전면 초기화 (Reset -> START)
    with btn_col3:
        if st.button("❌ 전면 취소", use_container_width=True):
            st.session_state.app_phase = "INPUT"
            st.session_state.graph_state = {}
            st.rerun()


# ==============================================================================
# [화면 4] 최종 1장 SCQA 보고서 열람 및 노션 전송 화면
# ==============================================================================
elif st.session_state.app_phase == "REPORT":
    st.header("📄 최종 비즈니스 동향 보고서 (1-Page Brief)")
    state = st.session_state.graph_state
    report_text = state.get("final_report", "생성된 보고서가 없습니다.")

    # 상단 메타 브리핑 배지
    st.caption(f"🏢 대상 기업: **{company_name}** | 🎯 적용 앵글: **{state.get('anchors', {}).get('angle', '-')}** | 📊 팩트: **{len(state.get('filtered_articles', []))}건**")

    # 마크다운 보고서 렌더링 카드
    st.markdown(report_text)

    st.divider()

    col_btn, col_link = st.columns([1, 2])
    with col_btn:
        if st.button("📤 사내 Notion 데이터베이스로 내보내기", type="primary", use_container_width=True):
            with st.spinner("Notion API 전송 중..."):
                title = f"[전략 브리프] {state.get('hypothesis', '비즈니스 동향 보고서')[:40]}"
                urls = [art.get("url") for art in state.get("filtered_articles", []) if art.get("url")]
                notion_link = export_report_to_notion(
                    title=title,
                    report_markdown=report_text,
                    source_urls=urls
                )
                if notion_link:
                    st.session_state.notion_url = notion_link
                    st.success("✅ 노션 페이지 생성 완료!")
                else:
                    st.error("노션 전송에 실패했습니다. .env의 토큰 및 DB 설정을 확인하세요.")

    with col_link:
        if st.session_state.notion_url:
            st.link_button("🔗 생성된 노션 페이지 열람하기", st.session_state.notion_url, use_container_width=True)

    if st.button("새로운 지시 분석 시작하기"):
        st.session_state.app_phase = "INPUT"
        st.session_state.graph_state = {}
        st.session_state.notion_url = None
        st.rerun()