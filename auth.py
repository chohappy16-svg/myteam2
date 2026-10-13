import re
import uuid
import streamlit as st
from typing import Tuple, Optional


def validate_employee_id(user_id: str) -> Tuple[bool, str]:
    """
    사내 사번 규격 검증 함수 (실무형 유효성 체크)
    - 형식: 영문 대문자 2~4자리 + 하이픈(-) + 숫자 4~6자리 (예: EMP-84920, AI-1029)
    - 단순 입력도 허용하되, 최소 3자 이상의 식별값 검증
    """
    clean_id = user_id.strip().upper()
    if not clean_id:
        return False, "사번을 입력해주세요."

    # 사내 사번 패턴 검증 (느슨한 정규식: 영숫자 및 하이픈 조합 3~15자)
    pattern = r"^[A-Z0-9\-]{3,15}\$"
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


def render_auth_sidebar() -> Tuple[str, str, bool]:
    """
    Streamlit 좌측 사이드바에 사내 인증 폼 및 인프라 상태를 렌더링하는 함수
    
    Returns:
        Tuple[user_id: str, thread_id: str, is_authenticated: bool]
    """
    # 세션 키 안전 초기화
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = ""
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False

    with st.sidebar:
        st.title("🛡️ 사내 인증 게이트")
        st.caption("So-What Agent 세션 격리 시스템")

        user_input = st.text_input(
            "사번 (User ID)",
            value=st.session_state.user_id,
            placeholder="예: EMP-84920",
            disabled=st.session_state.is_authenticated
        )

        col_login, col_logout = st.columns(2)

        with col_login:
            login_clicked = st.button("인증 및 세션 생성", use_container_width=True, disabled=st.session_state.is_authenticated)

        with col_logout:
            logout_clicked = st.button("세션 초기화", use_container_width=True, disabled=not st.session_state.is_authenticated)

        # 로그인 이벤트 처리
        if login_clicked:
            is_valid, result = validate_employee_id(user_input)
            if is_valid:
                st.session_state.user_id = result
                st.session_state.thread_id = generate_session_thread_id(result)
                st.session_state.is_authenticated = True
                st.session_state.app_phase = "INPUT"
                st.session_state.graph_state = {}
                st.session_state.notion_url = None
                st.success("인증 완료")
                st.rerun()
            else:
                st.error(result)

        # 로그아웃/초기화 이벤트 처리
        if logout_clicked:
            st.session_state.user_id = ""
            st.session_state.thread_id = ""
            st.session_state.is_authenticated = False
            st.session_state.app_phase = "INPUT"
            st.session_state.graph_state = {}
            st.session_state.notion_url = None
            st.info("세션이 초기화되었습니다.")
            st.rerun()

        st.divider()

        # 세션 정보 출력
        if st.session_state.is_authenticated:
            st.markdown(f"**활성 계정**: `{st.session_state.user_id}`")
            st.caption(f"**Thread ID**: `{st.session_state.thread_id}`")
        else:
            st.warning("로그인이 필요합니다.")

    return st.session_state.user_id, st.session_state.thread_id, st.session_state.is_authenticated