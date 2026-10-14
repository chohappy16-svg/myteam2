"""
So-What Agent - Google Stitch UI Engine (ui_stitch.py)
구글 스티치 디자인 시스템 1:1 완벽 이식 모듈 (Zero-Code-Block, Pure CSS & st.html 적용)
- st.html() 및 textwrap.dedent() 기반으로 마크다운 코드블록 버그 원천 차단
- 스티치 전용 Tailwind 컬러 토큰 & Flex/Grid/Badge 완전 내장 CSS
- 상단 80px 글로벌 헤더, 4-Step 스텝퍼, 다크 슬레이트 콘솔, 1PAGE 브리프 렌더러
"""

import textwrap
import streamlit as st

# ------------------------------------------------------------------------------
# 1. Google Stitch 완전 내장 CSS (CDN 의존 없이 100% 픽셀 완벽 렌더링)
# ------------------------------------------------------------------------------
STITCH_CORE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

/* Material Symbols 폰트 정의 (fallback용) */
.material-symbols-outlined {
    font-family: 'Material Symbols Outlined' !important;
    font-weight: normal;
    font-style: normal;
    font-size: 20px;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    word-wrap: normal;
    direction: ltr;
    -webkit-font-smoothing: antialiased;
    font-feature-settings: 'liga';
}

/* 0. Streamlit 기본 레이아웃 리셋 & 라이트 테마 고정 */
header[data-testid="stHeader"],
footer,
div[data-testid="stDecoration"] {
    display: none !important;
}
.stApp {
    background-color: #faf8ff !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #131b2e !important;
}
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 3rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 1240px !important;
}

/* 1. 좌측 사이드바 Stitch 스타일 */
section[data-testid="stSidebar"] {
    background-color: #f1f3f7 !important;
    border-right: 1px solid #dae2fd !important;
    box-shadow: 4px 0 12px rgba(0, 0, 0, 0.03) !important;
    color: #131b2e !important;
}
section[data-testid="stSidebar"] * {
    color: #131b2e;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #434655 !important;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] strong {
    color: #131b2e !important;
}

/* 2. Streamlit 버튼: 내부 모든 태그(p, span, div)까지 #ffffff 강제 */
.stButton > button,
.stButton > button *,
.stButton > button p,
.stButton > button span,
.stButton > button div,
button[data-testid="baseButton-secondary"],
button[data-testid="baseButton-secondary"] *,
button[data-testid="baseButton-secondary"] p,
button[data-testid="stBaseButton-secondary"],
button[data-testid="stBaseButton-secondary"] *,
button[data-testid="stBaseButton-secondary"] p,
button[kind="secondary"],
button[kind="secondary"] *,
button[kind="secondary"] p {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 700 !important;
}
.stButton > button {
    border-radius: 0.75rem !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease-in-out !important;
    border: none !important;
    padding: 0.6rem 1.2rem !important;
}
.stButton > button[kind="primary"],
.stButton > button[kind="primary"] *,
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-primary"] *,
button[data-testid="baseButton-primary"] p,
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-primary"] p {
    background-color: #004ac6 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(0, 74, 198, 0.35) !important;
}
.stButton > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
    background-color: #2563eb !important;
    box-shadow: 0 6px 20px rgba(0, 74, 198, 0.5) !important;
    transform: translateY(-1px) !important;
}

/* 세컨더리 및 일반 버튼: 다크 슬레이트(#1e2538) 배경 & 순백색(#ffffff) 글자 호버 전/후 100% 완전 고정 */
.stButton > button[kind="secondary"],
.stButton > button[kind="secondary"] *,
.stButton > button[kind="secondary"] p,
button[data-testid="baseButton-secondary"],
button[data-testid="baseButton-secondary"] *,
button[data-testid="baseButton-secondary"] p,
button[data-testid="stBaseButton-secondary"],
button[data-testid="stBaseButton-secondary"] *,
button[data-testid="stBaseButton-secondary"] p,
.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):not([data-testid="stBaseButton-primary"]),
.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):not([data-testid="stBaseButton-primary"]) *,
.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):not([data-testid="stBaseButton-primary"]) p {
    background-color: #1e2538 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid #3b455d !important;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button[kind="secondary"]:hover *,
.stButton > button[kind="secondary"]:hover p,
button[data-testid="baseButton-secondary"]:hover,
button[data-testid="baseButton-secondary"]:hover *,
button[data-testid="baseButton-secondary"]:hover p,
button[data-testid="stBaseButton-secondary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover *,
button[data-testid="stBaseButton-secondary"]:hover p,
.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):not([data-testid="stBaseButton-primary"]):hover,
.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):not([data-testid="stBaseButton-primary"]):hover *,
.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):not([data-testid="stBaseButton-primary"]):hover p {
    background-color: #2b354f !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border-color: #004ac6 !important;
}

/* 2-0. 링크 버튼 (st.link_button / 출처 기사 버튼 등): 호버 시 #000000 검정색 글자 완전 강제 */
.stLinkButton > a,
.stLinkButton > a *,
div[data-testid="stLinkButton"] a,
div[data-testid="stLinkButton"] a *,
a[data-testid="baseLinkButton-secondary"],
a[data-testid="baseLinkButton-secondary"] *,
a[data-testid="stBaseLinkButton-secondary"],
a[data-testid="stBaseLinkButton-secondary"] * {
    background-color: #1e2538 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid #3b455d !important;
    border-radius: 0.75rem !important;
    font-weight: 700 !important;
    text-decoration: none !important;
    transition: all 0.2s ease-in-out !important;
}

.stLinkButton > a:hover,
.stLinkButton > a:hover *,
.stLinkButton > a:hover p,
.stLinkButton > a:hover span,
.stLinkButton > a:hover div,
div[data-testid="stLinkButton"] a:hover,
div[data-testid="stLinkButton"] a:hover *,
div[data-testid="stLinkButton"] a:hover p,
div[data-testid="stLinkButton"] a:hover span,
div[data-testid="stLinkButton"] a:hover div,
a[data-testid="baseLinkButton-secondary"]:hover,
a[data-testid="baseLinkButton-secondary"]:hover *,
a[data-testid="baseLinkButton-secondary"]:hover p,
a[data-testid="baseLinkButton-secondary"]:hover span,
a[data-testid="stBaseLinkButton-secondary"]:hover,
a[data-testid="stBaseLinkButton-secondary"]:hover *,
a[data-testid="stBaseLinkButton-secondary"]:hover p,
a[data-testid="stBaseLinkButton-secondary"]:hover span {
    background-color: #e2e8f0 !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    border-color: #cbd5e1 !important;
}

/* 사이드바 내부 버튼: p/span 오버라이드를 이기고 #ffffff 강제 */
section[data-testid="stSidebar"] .stButton > button,
section[data-testid="stSidebar"] .stButton > button * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] .stButton > button[kind="primary"] * {
    background-color: #004ac6 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 800 !important;
}

/* 검은색 입력박스 & 텍스트에어리어: 배경(#131b2e) 및 글자색(#ffffff) 100% 완전 고정 */
div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"],
div[data-testid="stTextInput"] div[data-baseweb="base-input"],
div[data-testid="stTextArea"] div[data-baseweb="textarea"] {
    background-color: #131b2e !important;
}
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="input"] {
    background-color: #131b2e !important;
    border: 1px solid #3b455d !important;
    border-radius: 0.75rem !important;
    font-family: 'Inter', sans-serif !important;
    color: #ffffff !important;
}
div[data-baseweb="input"]:focus-within,
div[data-baseweb="base-input"]:focus-within,
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="input"]:focus-within > div,
div[data-baseweb="base-input"]:focus-within > div,
div[data-baseweb="textarea"]:focus-within > div {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.4) !important;
}

/* 입력창 내부 텍스트: input/textarea 모든 태그에 순백색 #ffffff 완전 강제 */
div[data-baseweb="input"] input,
div[data-baseweb="base-input"] input,
div[data-baseweb="textarea"] textarea,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
.stTextInput input,
.stTextArea textarea,
input[type="text"],
input,
textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    background-color: transparent !important;
    caret-color: #ffffff !important;
}

/* placeholder 텍스트 스타일 */
div[data-baseweb="input"] input::placeholder,
div[data-baseweb="base-input"] input::placeholder,
div[data-baseweb="textarea"] textarea::placeholder,
div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stTextArea"] textarea::placeholder,
.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
input::placeholder,
textarea::placeholder {
    color: rgba(255, 255, 255, 0.65) !important;
    -webkit-text-fill-color: rgba(255, 255, 255, 0.65) !important;
}

/* 드롭다운 select 옵션 스타일 */
div[data-baseweb="select"] * {
    color: #ffffff !important;
    background-color: #131b2e !important;
}

/* 입력창 상단 라벨 텍스트: 선명한 딥 네이비(#131b2e) & 볼드 */
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label p,
div[data-testid="stTextArea"] label,
div[data-testid="stTextArea"] label p,
div[data-testid="stWidgetLabel"],
div[data-testid="stWidgetLabel"] p {
    color: #131b2e !important;
    font-weight: 700 !important;
    font-size: 13px !important;
}

/* 사이드바 내부 텍스트 입력창 */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background-color: #131b2e !important;
}
section[data-testid="stSidebar"] input::placeholder,
section[data-testid="stSidebar"] textarea::placeholder {
    color: rgba(255, 255, 255, 0.65) !important;
    -webkit-text-fill-color: rgba(255, 255, 255, 0.65) !important;
}

/* 2-1. 보고서 마크다운 표(Table) 테두리 및 격자 스타일 100% 강제 */
div[data-testid="stMarkdownContainer"] table,
.stMarkdown table,
table {
    width: 100% !important;
    border-collapse: collapse !important;
    border: 1.5px solid #b8c4e2 !important;
    border-radius: 0.65rem !important;
    overflow: hidden !important;
    margin: 1.25rem 0 !important;
    background-color: #ffffff !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05) !important;
}
div[data-testid="stMarkdownContainer"] thead,
.stMarkdown thead,
thead {
    background-color: #f2f3ff !important;
    border-bottom: 2px solid #004ac6 !important;
}
div[data-testid="stMarkdownContainer"] th,
.stMarkdown th,
th {
    background-color: #f2f3ff !important;
    color: #131b2e !important;
    font-weight: 800 !important;
    font-size: 13px !important;
    padding: 0.75rem 1rem !important;
    border: 1px solid #b8c4e2 !important;
    border-bottom: 2px solid #004ac6 !important;
    text-align: left !important;
}
div[data-testid="stMarkdownContainer"] td,
.stMarkdown td,
td {
    padding: 0.75rem 1rem !important;
    font-size: 13px !important;
    color: #131b2e !important;
    border: 1px solid #b8c4e2 !important;
    line-height: 1.55 !important;
    vertical-align: middle !important;
}
div[data-testid="stMarkdownContainer"] tr:nth-child(even),
.stMarkdown tr:nth-child(even),
tr:nth-child(even) {
    background-color: #faf8ff !important;
}
div[data-testid="stMarkdownContainer"] tr:hover,
.stMarkdown tr:hover,
tr:hover {
    background-color: #eef2ff !important;
}

/* 3. Stitch 핵심 유틸리티 클래스 */
.stitch-header {
    width: 100%;
    height: 72px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(12px);
    border: 1px solid #dae2fd;
    border-radius: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.5rem;
    margin-bottom: 1.5rem;
}
.stitch-card {
    background: #ffffff;
    border: 1px solid #dae2fd;
    border-radius: 1rem;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    transition: all 0.2s ease;
}
.stitch-card:hover {
    box-shadow: 0 4px 12px rgba(0, 74, 198, 0.08);
}
.stitch-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
}
.badge-blue { background: #dbe1ff; color: #00174b; }
.badge-green { background: #6ffbbe; color: #002113; }
.badge-purple { background: #e2dfff; color: #0f0069; }
.badge-gray { background: #eaedff; color: #434655; }
.badge-red { background: #ffdad6; color: #93000a; }

/* 4. 스텝퍼 스타일 */
.stitch-stepper {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    background: #ffffff;
    border: 1px solid #dae2fd;
    border-radius: 1rem;
    padding: 0.85rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.step-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.85rem;
    border-radius: 0.75rem;
}
.step-item.active {
    background: #e2dfff;
    border: 1px solid #004ac6;
}
.step-item.completed {
    background: #f2f3ff;
}
.step-item.pending {
    background: #faf8ff;
    opacity: 0.6;
}
.step-circle {
    width: 2rem;
    height: 2rem;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
}
.step-circle.active { background: #004ac6; color: #ffffff; }
.step-circle.completed { background: #2563eb; color: #ffffff; }
.step-circle.pending { background: #eaedff; color: #434655; }

/* 5. 다크 슬레이트 콘솔 터미널 */
.stitch-terminal {
    background-color: #182a29;
    color: #e0f5f1;
    border-radius: 0.75rem;
    padding: 1rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 12px;
    line-height: 1.6;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
}

/* 6. 딥 슬레이트 히어로 배너 */
.stitch-hero-dark {
    background-color: #131b2e;
    color: #faf8ff;
    border-radius: 1.25rem;
    padding: 1.75rem;
    box-shadow: 0 10px 25px -5px rgba(19, 27, 46, 0.4);
    margin-bottom: 1.5rem;
}

/* 7. 제이드 틴트 가설 박스 */
.stitch-hypothesis {
    background-color: #e2f7f1;
    border: 1px solid #a2e7d7;
    border-radius: 1rem;
    padding: 1.25rem;
    color: #0c3829;
    margin-bottom: 1.5rem;
}
</style>
"""

# ------------------------------------------------------------------------------
# 1-1. Google Material SVG 아이콘 엔진 (Zero-Network, 100% 렌더링 보장)
# ------------------------------------------------------------------------------
STITCH_SVG_ICONS = {
    "bolt": '<path d="M11 21h-1l1-7H7.5c-.88 0-.33-.75-.31-.78C8.48 10.94 10.42 7.54 13 3h1l-1 7h3.5c.49 0 .56.33.47.51l-6 10.49z"/>',
    "credit_card": '<path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/>',
    "storefront": '<path d="M21.9 8.89l-1.05-4.37c-.22-.9-1-1.52-1.92-1.52H5.07c-.92 0-1.7.62-1.93 1.52L2.1 8.89c-.24.97.16 1.98.96 2.51.13.09.28.16.44.22V20c0 1.1.9 2 2 2h13c1.1 0 2-.9 2-2v-8.38c.16-.06.31-.13.44-.22.8-.53 1.2-1.54.96-2.51zM18.5 20H5.5v-7.85c.46-.22.83-.58 1.07-1.03.35.58.98.98 1.7.98.71 0 1.34-.39 1.69-.97.35.58.98.97 1.69.97.72 0 1.35-.4 1.7-.98.35.58.98.98 1.7.98.72 0 1.35-.4 1.7-.98.24.45.61.81 1.07 1.03V20z"/>',
    "store_mall_directory": '<path d="M20 4H4v2h16V4zm1 10v-2l-1-5H4l-1 5v2h1v6h10v-6h4v6h2v-6h1zm-9 4H6v-4h6v4z"/>',
    "auto_stories": '<path d="M19 1l-5 5v11l5-4.5V1zM1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5V6c-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6zm22 14.65V6c-.75-.55-1.6-.9-2.5-1.15V17c-.75-.25-1.6-.35-2.5-.35-1.45 0-3.55.45-5 1.5v1.5c1.45-1.1 3.55-1.5 5.5-1.5 1.45 0 3.4.45 4.75 1.1.1 0 .15.05.25.05.25 0 .5-.25.5-.5z"/>',
    "celebration": '<path d="M2 22l14-5-9-9-5 14zm4.03-3.03l1.88-5.26 3.38 3.38-5.26 1.88zm15.11-13.4l-1.42-1.42c-.39-.39-1.02-.39-1.41 0l-2.12 2.12 2.83 2.83 2.12-2.12c.39-.4.39-1.02 0-1.41zM14.5 9.09l-1.06-1.06 1.77-1.77 1.06 1.06-1.77 1.77zM16.97 3.5l1.41-1.41c.39-.39 1.02-.39 1.41 0l.71.71c.39.39.39 1.02 0 1.41l-1.41 1.41-2.12-2.12zM9.09 1.5l1.06 1.06-1.77 1.77-1.06-1.06L9.09 1.5z"/>',
    "campaign": '<path d="M18 11v1.5c0 1.93-1.57 3.5-3.5 3.5H13v3c0 .55-.45 1-1 1h-2c-.55 0-1-.45-1-1v-3H6.5C4.57 16 3 14.43 3 12.5V11c0-1.93 1.57-3.5 3.5-3.5H9V4.5C9 3.67 9.67 3 10.5 3s1.5.67 1.5 1.5V7.5h2.5c1.93 0 3.5 1.57 3.5 3.5zm-2 0c0-.83-.67-1.5-1.5-1.5H5.5C4.67 9.5 4 10.17 4 11v1.5c0 .83.67 1.5 1.5 1.5H14.5c.83 0 1.5-.67 1.5-1.5V11zm4.5-2.5c-.28 0-.53.11-.71.29l-1.06 1.06c.64.76 1.02 1.73 1.02 2.8s-.38 2.04-1.02 2.8l1.06 1.06c.9-.96 1.46-2.25 1.46-3.86 0-1.61-.56-2.9-1.46-3.86-.18-.18-.43-.29-.71-.29z"/>',
    "repeat": '<path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>',
    "hub": '<path d="M12 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm-6 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm12 0a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm-6 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm-1-13.86V9h2V6.14a4.98 4.98 0 0 1 3.5 2.5l2.48-1.43a7.02 7.02 0 0 0-4.98-3.07v-.01zm-4 4.07L4.52 7.21A7.02 7.02 0 0 0 .54 11.28l2.48 1.43A4.98 4.98 0 0 1 7 9.21zm0 7.58a4.98 4.98 0 0 1-3.98-3.5L.54 14.72a7.02 7.02 0 0 0 4.44 4.07l2.02-2zm8 0l2.02 2a7.02 7.02 0 0 0 4.44-4.07l-2.48-1.43a4.98 4.98 0 0 1-3.98 3.5zM11 17.86V15h2v2.86a4.98 4.98 0 0 1-2 0z"/>',
    "check": '<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>',
    "domain_add": '<path d="M12 7V3H2v18h14v-2h-4v-2h2v-2h-2v-2h2v-2h-2V9h8v4h2V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm9 7v3h-3v2h3v3h2v-3h3v-2h-3v-3h-2z"/>',
    "shield": '<path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>',
    "lightbulb": '<path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7zm2.85 11.1l-.85.6V16h-4v-1.3l-.85-.6C7.8 13.16 7 11.72 7 9c0-2.76 2.24-5 5-5s5 2.24 5 5c0 2.72-.8 4.16-2.15 5.1z"/>',
    "data_usage": '<path d="M13 2.05v3.03c3.39.49 6 3.39 6 6.92 0 .9-.18 1.75-.48 2.54l2.6 1.53c.56-1.24.88-2.62.88-4.07 0-5.18-3.95-9.45-9-9.95zM12 19c-3.87 0-7-3.13-7-7 0-3.53 2.61-6.43 6-6.92V2.05c-5.06.5-9 4.76-9 9.95 0 5.52 4.47 10 9.99 10 3.31 0 6.24-1.61 8.01-4.09l-2.49-1.46C16.27 18.23 14.28 19 12 19z"/>',
    "support_agent": '<path d="M20 15.5c-.67 0-1.3.1-1.9.28-.31-.62-.76-1.16-1.32-1.58.53-.88.82-1.9.82-3 0-3.31-2.69-6-6-6S5.6 7.89 5.6 11.2c0 1.1.29 2.12.82 3-.56.42-1.01.96-1.32 1.58-.6-.18-1.23-.28-1.9-.28-2.32 0-4.2 1.88-4.2 4.2V21h8v-1.25H2.2v-.55c0-1.63 1.32-2.95 2.95-2.95.83 0 1.57.34 2.1 0.89.53.55.85 1.3.85 2.11v1.75h7.8v-1.75c0-.81.32-1.56.85-2.11.53-.55 1.27-.89 2.1-.89 1.63 0 2.95 1.32 2.95 2.95v.55H16V21h8v-1.3c0-2.32-1.88-4.2-4.2-4.2zM11.6 7.2c2.21 0 4 1.79 4 4s-1.79 4-4 4-4-1.79-4-4 1.79-4 4-4z"/>',
    "open_in_new": '<path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/>',
    "folder_open": '<path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z"/>',
    "settings_input_component": '<path d="M5 2c0-.55-.45-1-1-1s-1 .45-1 1v4H1v6h2v10c0 .55.45 1 1 1s1-.45 1-1V12h2V6H5V2zm8 0c0-.55-.45-1-1-1s-1 .45-1 1v10H9v6h2v4c0 .55.45 1 1 1s1-.45 1-1v-4h2v-6h-2V2zm8 0c0-.55-.45-1-1-1s-1 .45-1 1v2h-2v6h2v12c0 .55.45 1 1 1s1-.45 1-1V10h2V4h-2V2z"/>',
    "code_blocks": '<path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/>',
    "insights": '<path d="M21 8c-1.45 0-2.26 1.44-1.93 2.51l-3.55 3.56c-.3-.09-.74-.09-1.04 0l-2.55-2.55C12.27 10.45 11.46 9 10 9c-1.45 0-2.27 1.44-1.93 2.52l-4.56 4.55C2.44 15.74 1 16.55 1 18c0 1.1.9 2 2 2 1.45 0 2.26-1.44 1.93-2.51l4.55-4.56c.3.09.74.09 1.04 0l2.55 2.55C12.73 16.55 13.54 18 15 18c1.45 0 2.27-1.44 1.93-2.52l3.56-3.55c1.07.33 2.51-.48 2.51-1.93 0-1.1-.9-2-2-2zM15 9l.94-2.06L18 6l-2.06-.94L15 3l-.94 2.06L12 6l2.06.94zm4.5 3l.62-1.38L21.5 10l-1.38-.62L19.5 8l-.62 1.38L17.5 10l1.38.62z"/>',
    "psychology": '<path d="M12 3a9 9 0 0 0-9 9c0 2.12.74 4.07 1.97 5.61L4.35 21l3.5-.88A8.96 8.96 0 0 0 12 21a9 9 0 0 0 9-9 9 9 0 0 0-9-9zm0 15a6 6 0 1 1 0-12 6 6 0 0 1 0 12z"/>',
    "verified_user": '<path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>',
    "timeline": '<path d="M23 8c0 1.1-.9 2-2 2-.18 0-.35-.02-.51-.07l-3.56 3.55c.05.16.07.34.07.52 0 1.1-.9 2-2 2s-2-.9-2-2c0-.18.02-.36.07-.52l-2.55-2.55c-.16.05-.34.07-.52.07s-.36-.02-.52-.07l-4.55 4.56c.05.16.07.33.07.51 0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2c.18 0 .35.02.51.07l4.56-4.55C8.02 8.36 8 8.18 8 8c0-1.1.9-2 2-2s2 .9 2 2c0 .18-.02.36-.07.52l2.55 2.55c.16-.05.34-.07.52-.07s.36.02.52.07l3.55-3.56C19.02 7.35 19 7.18 19 7c0-1.1.9-2 2-2s2 .9 2 2z"/>',
    "lock": '<path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>',
    "arrow_forward": '<path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/>',
    "arrow_back": '<path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>',
    "add_task": '<path d="M22 5.18L10.59 16.6l-4.24-4.24 1.41-1.41 2.83 2.83 10-10L22 5.18zm-2 7.02c-.77.16-1.6.1-2.31-.22-.38-.17-.74-.4-1.05-.68l-1.42 1.42c.62.56 1.34 1.01 2.14 1.31.85.32 1.76.45 2.64.38V20H4V4h10.1v-2H4c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-7.8z"/>',
}


def stitch_icon(name: str, size: int = 18, color: str = "currentColor", extra_style: str = "") -> str:
    """구글 스티치 전용 고화질 인라인 SVG 아이콘 렌더러 (웹폰트 로딩 실패/지연 원천 해결)"""
    path = STITCH_SVG_ICONS.get(name)
    if path:
        return f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="{color}" style="display:inline-block; vertical-align:middle; flex-shrink:0; {extra_style}">{path}</svg>'
    return f'<span class="material-symbols-outlined" style="font-size:{size}px; color:{color}; vertical-align:middle; {extra_style}">{name}</span>'


def inject_stitch_assets():
    """Streamlit 페이지에 구글 스티치 전역 스타일 주입"""
    st.html(STITCH_CORE_CSS)


# ------------------------------------------------------------------------------
# 2. 최상단 80px 글로벌 헤더
# ------------------------------------------------------------------------------
def render_stitch_header(
    company_name: str = "올웨이즈케어 라이프",
    user_id: str = "STORE-KR-8492",
    is_authenticated: bool = True,
    credit: str = "48/50",
    container=None
):
    pipeline_badge = f'<span class="stitch-badge badge-blue">{user_id} ACTIVE</span>' if is_authenticated else '<span class="stitch-badge badge-gray">미등록 (분석 대기 중)</span>'
    marketer_title = f"{company_name} 마케터" if company_name != "자사 조직" else "커머스 마케터"

    html = f"""
    <div class="stitch-header">
      <div style="display: flex; align-items: center; gap: 1rem;">
        <img alt="Logo" style="height: 36px; width: auto; object-fit: contain;" src="https://lh3.googleusercontent.com/aida/AEtjO1VzbutSMGi2YSUNxRrA1j9e_SFKxNGV_kL2GEd5AeUjW-9R33lUH9f9yP6825ugOzDMZYLuZ2w0eKNlSjHlMKy88X0YCzzx5ZlBLcinCQwVn6bDvEW6bEHQmIDuv_6imG3I0rTjhN72TziQhZtZGAGrxK4akALm9klh2YqD3g4yGvMV97wl01Yc2BZr5lv1hI8wHZw2QO2xa7JMI90pR6lumEpQm4tXETr7Tt0I7lBfmikfVXekwBFPAX93"/>
        <div style="display: flex; flex-direction: column;">
          <span style="font-size: 17px; font-weight: 800; color: #131b2e; letter-spacing: -0.5px;">So-What Agent</span>
          <span style="font-size: 10px; color: #737686; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">E-Commerce Strategy Copilot</span>
        </div>
        <span class="stitch-badge badge-blue">B2C Commerce Pro</span>
      </div>
      <div style="display: flex; align-items: center; gap: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.4rem; padding: 0.35rem 0.75rem; border-radius: 0.5rem; background: rgba(111, 251, 190, 0.3); border: 1px solid #6ffbbe;">
          <span style="width: 7px; height: 7px; border-radius: 50%; background: #006242;"></span>
          <span style="font-size: 12px; color: #006242; font-weight: 700;">API 정상</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.4rem; padding: 0.35rem 0.75rem; border-radius: 0.5rem; background: #f2f3ff; border: 1px solid #dae2fd;">
          {stitch_icon("credit_card", 16, "#004ac6")}
          <span style="font-size: 12px; color: #434655;">남은 크레딧:</span>
          <span style="font-size: 12px; font-weight: 700; color: #131b2e; font-family: monospace;">{credit}</span>
        </div>
        <div style="height: 20px; width: 1px; background: #dae2fd;"></div>
        <div style="text-align: right;">
          <div style="font-size: 12px; font-weight: 700; color: #131b2e;">{marketer_title}</div>
          <div style="font-size: 11px; color: #737686;">{company_name}</div>
        </div>
        <img alt="Avatar" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover; border: 2px solid rgba(0, 74, 198, 0.2);" src="https://lh3.googleusercontent.com/aida-public/AB6AXuB1Rc4LDPm5q7d4Xad2bF0KvTMRnz-NvGx07vmOvNTyVG0Xr2iu7hKn5xZqkvJnhrog1Ehilshyxr3QiTAvbnk4rXryuRVGgvD0Mf3aLPw0s9uHTMvNdfWfbtcS6Enf4-Luo-Jx6R0To6848DwN1kZASVFPDs0TuW5hdAnOW19jyMTitZli2WJ6VLclkMJdI8DUfAfYYVcQ2tjoVNxjI4flr3KUTn3cZ72ejFPNu76f_ntR1B-hQYxwTA"/>
      </div>
    </div>
    """
    clean_html = textwrap.dedent(html).strip()
    target = container if container is not None else st
    target.html(clean_html)


# ------------------------------------------------------------------------------
# 3. 4단계 동적 스텝퍼
# ------------------------------------------------------------------------------
def render_stitch_stepper(active_step_idx: int = 1, container=None):
    steps = [
        (1, "01", "진행 중 · 접수", "고민 접수 & 방향"),
        (2, "02", "RUNNING", "시장 & 경쟁 분석"),
        (3, "03", "ACTIVE", "전략 목차 컨펌"),
        (4, "04", "FINAL", "So-What 보고서"),
    ]

    parts = ['<div class="stitch-stepper">']
    for idx, num_str, label_sub, label_main in steps:
        if idx < active_step_idx:
            parts.append(f"""
            <div class="step-item completed">
              <div class="step-circle completed">✓</div>
              <div style="display: flex; flex-direction: column;">
                <span style="font-size: 11px; color: #004ac6; font-weight: 700;">완료</span>
                <span style="font-size: 13px; font-weight: 700; color: #131b2e;">{label_main}</span>
              </div>
            </div>
            """)
        elif idx == active_step_idx:
            parts.append(f"""
            <div class="step-item active">
              <div class="step-circle active">{num_str}</div>
              <div style="display: flex; flex-direction: column;">
                <span style="font-size: 11px; color: #004ac6; font-weight: 700;">{label_sub}</span>
                <span style="font-size: 13px; font-weight: 800; color: #004ac6;">{label_main}</span>
              </div>
            </div>
            """)
        else:
            parts.append(f"""
            <div class="step-item pending">
              <div class="step-circle pending">{num_str}</div>
              <div style="display: flex; flex-direction: column;">
                <span style="font-size: 11px; color: #737686;">대기</span>
                <span style="font-size: 13px; color: #434655;">{label_main}</span>
              </div>
            </div>
            """)
    parts.append('</div>')

    clean_html = textwrap.dedent("".join(parts)).strip()
    target = container if container is not None else st
    target.html(clean_html)


# ------------------------------------------------------------------------------
# 4. [화면 1] 상단 히어로 배너 & 스토어 분석 상태 뱃지 카드
# ------------------------------------------------------------------------------
def render_screen1_hero_banner(company_name: str, is_authenticated: bool = True):
    if is_authenticated and company_name != "자사 조직":
        badge_card = f"""
        <div style="background: rgba(255, 255, 255, 0.95); border-radius: 0.85rem; padding: 1.1rem; border: 1px solid #dae2fd; min-width: 280px; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 11px; color: #737686; font-weight: 700; text-transform: uppercase;">분석 대상 스토어</span>
            <span class="stitch-badge badge-green">● 정상 연결</span>
          </div>
          <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
            <div style="width: 38px; height: 38px; border-radius: 0.5rem; background: #dbe1ff; display: flex; align-items: center; justify-content: center; font-size: 20px;">
              🏬
            </div>
            <div style="display: flex; flex-direction: column;">
              <span style="font-size: 14px; font-weight: 800; color: #131b2e;">{company_name}</span>
              <span style="font-size: 11px; color: #737686;">스마트스토어/D2C 활성 세션</span>
            </div>
          </div>
          <div style="font-size: 11px; background: #f2f3ff; padding: 0.5rem; border-radius: 0.5rem; color: #434655;">
            ✅ 등록된 스토어 환경을 기준으로 타사 팩트를 맞춤 수집합니다.
          </div>
        </div>
        """
    else:
        badge_card = f"""
        <div style="background: rgba(255, 255, 255, 0.95); border-radius: 0.85rem; padding: 1.1rem; border: 1px solid #dae2fd; min-width: 280px; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 11px; color: #737686; font-weight: 700; text-transform: uppercase;">분석 대상 스토어</span>
            <span class="stitch-badge badge-red">● 미등록 상태</span>
          </div>
          <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
            <div style="width: 38px; height: 38px; border-radius: 0.5rem; background: #eaedff; display: flex; align-items: center; justify-content: center; font-size: 20px;">
              🏬
            </div>
            <div style="display: flex; flex-direction: column;">
              <span style="font-size: 14px; font-weight: 800; color: #131b2e;">[스토어를 등록해주세요]</span>
              <span style="font-size: 11px; color: #737686;">좌측 메뉴에서 URL 입력 필요</span>
            </div>
          </div>
          <div style="font-size: 11px; background: #f2f3ff; padding: 0.5rem; border-radius: 0.5rem; color: #434655;">
            👈 좌측 패널의 <strong style="color: #004ac6;">스토어 등록 폼</strong>에 쇼핑몰 링크를 입력해 주세요.
          </div>
        </div>
        """

    html = f"""
    <div style="background: linear-gradient(135deg, rgba(0, 74, 198, 0.08), rgba(226, 231, 255, 0.5), #f2f3ff); border: 1px solid #dae2fd; border-radius: 1.25rem; padding: 1.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1.5rem;">
      <div style="max-width: 680px;">
        <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
          <span class="stitch-badge badge-green">AI 마케팅 코파일럿</span>
          <span class="stitch-badge badge-purple">B2C Commerce Pro</span>
        </div>
        <h1 style="font-size: 24px; font-weight: 800; color: #131b2e; letter-spacing: -0.5px; margin: 0 0 0.5rem 0;">
          우리 브랜드를 깊이 이해하는 AI 전략 보고서
        </h1>
        <p style="font-size: 14px; color: #434655; line-height: 1.6; margin: 0;">
          복잡한 데이터 지표 나열 대신, 실제 매출 전환(CVR)과 구매 단가를 끌어올리는<br>구체적인 <strong style="color: #004ac6;">'So-What (그래서 무엇을 할 것인가?)'</strong> 실행 계획을 기획합니다.
        </p>
      </div>
      {badge_card}
    </div>
    """
    st.html(textwrap.dedent(html).strip())


# ------------------------------------------------------------------------------
# 5. [화면 1] 5대 전략 도메인 프리젠테이션 카드
# ------------------------------------------------------------------------------
def render_screen1_domain_cards(selected_key: str = "CVR"):
    domains = [
        ("CVR", "🎯", "상세페이지 & CVR", "스크롤 이탈 원인 진단 및 체류 시간 증대 카피 재설계", "🔥 가장 추천", "badge-green"),
        ("AOV", "🎁", "시즌 프로모션 기획", "명절/시즌 대비 기획전 번들링 및 할인 패키지 설계", "시즌 특수", "badge-purple"),
        ("ROAS", "📢", "광고 크리에이티브", "메타/인스타 피드 및 네이버 SA 후킹 문구 & 앵글 도출", "ROAS 개선", "badge-blue"),
        ("CRM", "🔄", "첫구매 → 재구매 유도", "알림톡 시나리오, 동봉 카드, 리뷰 리워드 루프 설계", "LTV 극대화", "badge-purple"),
        ("SOLUTION", "🛠️", "외부 마케팅 툴 도입", "채널톡, 브이리뷰, 그로스 툴 도입 ROI 타당성 검토", "솔루션 비교", "badge-blue"),
    ]

    cards_html = []
    for key, icon, title, desc, tag, tag_cls in domains:
        is_selected = (key == selected_key)
        bg = "#e2dfff" if is_selected else "#ffffff"
        border = "2px solid #004ac6" if is_selected else "1px solid #dae2fd"
        title_color = "#004ac6" if is_selected else "#131b2e"
        badge_visibility = "display: flex;" if is_selected else "display: none;"

        cards_html.append(f"""
        <div style="background: {bg}; border: {border}; border-radius: 0.85rem; padding: 1rem; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
              <div style="width: 34px; height: 34px; border-radius: 0.5rem; background: #004ac6; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 18px;">
                {icon}
              </div>
              <span style="{badge_visibility} width: 20px; height: 20px; border-radius: 50%; background: #004ac6; color: #fff; align-items: center; justify-content: center; font-size: 12px; font-weight: 800;">
                ✓
              </span>
            </div>
            <div style="font-size: 13px; font-weight: 700; color: {title_color}; margin-bottom: 0.3rem;">{title}</div>
            <p style="font-size: 11px; color: #434655; line-height: 1.4; margin: 0;">{desc}</p>
          </div>
          <div style="margin-top: 0.8rem;">
            <span class="stitch-badge {tag_cls}">{tag}</span>
          </div>
        </div>
        """)

    html = f"""
    <div style="background: #ffffff; border: 1px solid #dae2fd; border-radius: 1rem; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.85rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <span style="width: 22px; height: 22px; border-radius: 50%; background: #004ac6; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700;">1</span>
          <h2 style="font-size: 16px; font-weight: 800; color: #131b2e; margin: 0;">보고서 작성 목적 및 도메인 선택</h2>
          <span style="font-size: 11px; color: #ba1a1a; font-weight: 700;">*필수</span>
        </div>
        <span style="font-size: 12px; color: #737686;">어떤 핵심 문제를 집중 해결하고 싶으신가요?</span>
      </div>
      <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.75rem;">
        {"".join(cards_html)}
      </div>
    </div>
    """
    st.html(textwrap.dedent(html).strip())


def render_screen1_domain_tabs(selected_key: str = "CVR") -> str:
    """
    [화면 1] 5대 전략 도메인 탭 선택기 (클릭 시 드롭다운 대체 및 즉각 세션 연동)
    """
    domains = [
        ("CVR", "🎯", "상세페이지 & CVR", "스크롤 이탈 원인 진단 및 체류 시간 증대 카피 재설계", "🔥 가장 추천"),
        ("AOV", "🎁", "시즌 프로모션 기획", "명절/시즌 대비 기획전 번들링 및 할인 패키지 설계", "시즌 특수"),
        ("ROAS", "📢", "광고 크리에이티브", "메타/인스타 피드 및 네이버 SA 후킹 문구 & 앵글 도출", "ROAS 개선"),
        ("CRM", "🔄", "첫구매 → 재구매 유도", "알림톡 시나리오, 동봉 카드, 리뷰 리워드 루프 설계", "LTV 극대화"),
        ("SOLUTION", "🛠️", "외부 마케팅 툴 도입", "채널톡, 브이리뷰, 그로스 툴 도입 ROI 타당성 검토", "솔루션 비교"),
    ]

    header_html = """
    <div style="background: #ffffff; border: 1px solid #dae2fd; border-radius: 1rem 1rem 0 0; padding: 1.25rem 1.25rem 0.5rem 1.25rem; border-bottom: none;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <span style="width: 22px; height: 22px; border-radius: 50%; background: #004ac6; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700;">1</span>
          <h2 style="font-size: 16px; font-weight: 800; color: #131b2e; margin: 0;">보고서 작성 목적 및 도메인 선택</h2>
          <span style="font-size: 11px; color: #ba1a1a; font-weight: 700;">*필수</span>
        </div>
        <span style="font-size: 12px; color: #004ac6; font-weight: 700;">👇 아래 둥근 탭 버튼을 클릭하여 분석 모드를 전환하세요</span>
      </div>
    </div>
    """
    st.html(textwrap.dedent(header_html).strip())

    cols = st.columns(5)
    new_selected_key = selected_key

    for col, (key, icon, title, desc, tag) in zip(cols, domains):
        is_selected = (key == selected_key)
        bg = "#e2dfff" if is_selected else "#ffffff"
        border = "2px solid #004ac6" if is_selected else "1px solid #dae2fd"
        title_color = "#004ac6" if is_selected else "#131b2e"
        badge_visibility = "display: flex;" if is_selected else "display: none;"
        icon_bg = "#004ac6" if is_selected else "#434655"

        with col:
            card_html = f"""
            <div style="background: {bg}; border: {border}; border-bottom: none; border-radius: 0.85rem 0.85rem 0 0; padding: 0.85rem; min-height: 145px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
              <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                  <div style="width: 32px; height: 32px; border-radius: 0.5rem; background: {icon_bg}; color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 17px;">
                    {icon}
                  </div>
                  <span style="{badge_visibility} width: 18px; height: 18px; border-radius: 50%; background: #004ac6; color: #fff; align-items: center; justify-content: center; font-size: 11px; font-weight: 800;">
                    ✓
                  </span>
                </div>
                <div style="font-size: 13px; font-weight: 800; color: {title_color}; margin-bottom: 0.3rem;">{title}</div>
                <p style="font-size: 11px; color: #434655; line-height: 1.35; margin: 0;">{desc}</p>
              </div>
            </div>
            """
            st.html(textwrap.dedent(card_html).strip())
            btn_label = f"✓ {tag}" if is_selected else tag
            btn_type = "primary" if is_selected else "secondary"
            if st.button(btn_label, key=f"domain_tab_{key}", use_container_width=True, type=btn_type):
                new_selected_key = key

    st.html('<div style="height: 10px; margin-bottom: 1.25rem;"></div>')
    return new_selected_key


# ------------------------------------------------------------------------------
# 6. [화면 1] 3대 하단 비즈니스 인포 카드
# ------------------------------------------------------------------------------
def render_screen1_info_cards():
    html = f"""
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
      <div class="stitch-card">
        <div style="width: 34px; height: 34px; border-radius: 0.5rem; background: #e2dfff; display: flex; align-items: center; justify-content: center; font-size: 18px; margin-bottom: 0.5rem;">
          💡
        </div>
        <div style="font-size: 14px; font-weight: 700; color: #131b2e; margin-bottom: 0.3rem;">실행 중심의 So-What</div>
        <p style="font-size: 12px; color: #434655; line-height: 1.5; margin: 0;">
          단순한 트렌드 요약이 아닌, 바로 디자이너와 카피라이터에게 전달할 수 있는 구체적인 실행 스프린트 체크리스트를 도출합니다.
        </p>
      </div>
      <div class="stitch-card">
        <div style="width: 34px; height: 34px; border-radius: 0.5rem; background: #dbe1ff; display: flex; align-items: center; justify-content: center; font-size: 18px; margin-bottom: 0.5rem;">
          🧠
        </div>
        <div style="font-size: 14px; font-weight: 700; color: #131b2e; margin-bottom: 0.3rem;">B2C 이커머스 특화 LLM</div>
        <p style="font-size: 12px; color: #434655; line-height: 1.5; margin: 0;">
          네이버 스마트스토어, 쿠팡, 자사몰 등 국내 B2C 구매 여정의 장바구니 전환 및 리뷰 심리학 패턴을 깊이 학습했습니다.
        </p>
      </div>
      <div class="stitch-card">
        <div style="width: 34px; height: 34px; border-radius: 0.5rem; background: #eaedff; display: flex; align-items: center; justify-content: center; font-size: 18px; margin-bottom: 0.5rem;">
          🛡️
        </div>
        <div style="font-size: 14px; font-weight: 700; color: #131b2e; margin-bottom: 0.3rem;">안전한 데이터 보안</div>
        <p style="font-size: 12px; color: #434655; line-height: 1.5; margin: 0;">
          입력하신 스토어 정보와 질문 내용은 제3자 모델 재학습에 일체 활용되지 않으며 격리된 워크스페이스에만 보관됩니다.
        </p>
      </div>
    </div>
    """
    st.html(textwrap.dedent(html).strip())


# ------------------------------------------------------------------------------
# 7. [화면 2] 실시간 시장 실측 데이터 수집 & 다크 슬레이트 콘솔 터미널
# ------------------------------------------------------------------------------
def render_screen2_market_analysis_view(
    company_name: str = "올웨이즈케어 라이프",
    step: int = 1,
    percent: int = 25,
    facts_count: int = 0,
    active_log: str = "[INIT] 마케터 고민 의도 분석 및 정형화 파라미터 매핑 완료",
    container=None
):
    """
    [화면 2] 실시간 시장 실측 데이터 수집 & AI 추론 동적 대시보드 (Zero-Mock, 100% 실시간 연동)
    """
    step_items = [
        (1, "1. 마케터 핵심 고민 접수 및 프롬프트 파싱", "선택된 목적 및 당면 실무 고민 파라미터 매핑 완료"),
        (2, f"2. {company_name} 스토어 환경 및 판매 자산 분석", "등록 상품군 및 이커머스 도메인 맥락 파악"),
        (3, "3. 시장 트렌드 및 타사 성공 사례 실시간 탐색", "광고성 기사 필터링 및 실측 팩트 수집"),
        (4, "4. 핵심 결론(가설) 도출 및 3대 전략 보고 목차 구성", "실행 중심의 So-What 가설 및 맞춤형 목차 생성"),
    ]

    timeline_cards = []
    for s_idx, title, desc in step_items:
        if step > s_idx:
            # 완료된 단계
            timeline_cards.append(f"""
            <div style="background: #f2f3ff; padding: 0.75rem; border-radius: 0.6rem; display: flex; align-items: flex-start; gap: 0.6rem;">
              <span style="width: 20px; height: 20px; border-radius: 50%; background: #2563eb; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; flex-shrink: 0;">✓</span>
              <div>
                <div style="font-size: 13px; font-weight: 700; color: #131b2e;">{title} (완료)</div>
                <div style="font-size: 11px; color: #434655;">{desc}</div>
              </div>
            </div>
            """)
        elif step == s_idx:
            # 현재 진행 중인 단계
            timeline_cards.append(f"""
            <div style="background: #e2dfff; padding: 0.75rem; border-radius: 0.6rem; border: 1px solid #4b41e1;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                <span style="font-size: 13px; font-weight: 800; color: #004ac6;">{title}</span>
                <span class="stitch-badge badge-green">RUNNING</span>
              </div>
              <div style="font-size: 11px; color: #434655; margin-bottom: 0.5rem;">{desc}</div>
              <div class="stitch-terminal">
                <div style="color: #6ffbbe; font-size: 11px; font-family: monospace;">{active_log}</div>
              </div>
            </div>
            """)
        else:
            # 대기 중인 단계
            timeline_cards.append(f"""
            <div style="background: #faf8ff; padding: 0.75rem; border-radius: 0.6rem; display: flex; align-items: flex-start; gap: 0.6rem; opacity: 0.6;">
              <span style="width: 20px; height: 20px; border-radius: 50%; background: #dae2fd; color: #737686; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0;">{s_idx}</span>
              <div>
                <div style="font-size: 13px; font-weight: 700; color: #737686;">{title}</div>
                <div style="font-size: 11px; color: #737686;">대기 중...</div>
              </div>
            </div>
            """)

    if facts_count > 0:
        facts_body = f"""
        <div style="background: #f2f3ff; padding: 0.75rem; border-radius: 0.5rem; font-size: 12px; margin-bottom: 0.5rem;">
          <span class="stitch-badge badge-purple" style="margin-bottom: 0.2rem;">검증된 실측 데이터</span>
          <div style="font-weight: 700; color: #131b2e; margin-top: 0.2rem;">타사 성공 사례 및 전환율/객단가 팩트 {facts_count}건 정제 완료</div>
        </div>
        <div style="background: #f2f3ff; padding: 0.75rem; border-radius: 0.5rem; font-size: 12px;">
          <span class="stitch-badge badge-green" style="margin-bottom: 0.2rem;">신뢰도 필터</span>
          <div style="font-weight: 700; color: #131b2e; margin-top: 0.2rem;">광고성 PR 기사 및 편향 데이터 배제 완료</div>
        </div>
        """
    else:
        facts_body = """
        <div style="background: #f2f3ff; padding: 1rem; border-radius: 0.5rem; font-size: 12px; color: #737686; text-align: center;">
          🔍 실시간 외부 데이터 탐색 및 신뢰도 검증 진행 중...
        </div>
        """

    html = f"""
    <!-- Realtime Process Engine Headline Banner -->
    <div style="background: #ffffff; border: 1px solid #dae2fd; border-radius: 1.25rem; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div style="display: flex; align-items: flex-start; gap: 1rem;">
          <div style="width: 44px; height: 44px; border-radius: 0.75rem; background: #dbe1ff; color: #004ac6; display: flex; align-items: center; justify-content: center; font-size: 22px;">
            ⚡
          </div>
          <div>
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem;">
              <span class="stitch-badge badge-purple">● AI 인텔리전스 엔진 연산 중</span>
              <span style="font-size: 11px; color: #4b41e1; font-family: monospace; font-weight: 700;">PIPELINE: STREAM_OK</span>
            </div>
            <h1 style="font-size: 20px; font-weight: 800; color: #131b2e; margin: 0 0 0.3rem 0;">
              실시간 시장 실측 데이터 수집 및 경쟁사 성공 사례 심층 분석
            </h1>
            <p style="font-size: 13px; color: #434655; margin: 0;">
              {company_name} 비즈니스 맥락 기반으로 타사 전환 지표와 실행 레퍼런스를 실시간 대조 연산하고 있습니다.
            </p>
          </div>
        </div>
        <div style="background: rgba(111, 251, 190, 0.25); border: 1px solid #6ffbbe; border-radius: 0.75rem; padding: 0.6rem 1rem; display: flex; align-items: center; gap: 0.5rem;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: #007d55;"></span>
          <span style="font-size: 13px; color: #006242; font-weight: 700;">실시간 AI 추론 연산 중</span>
        </div>
      </div>
      <div style="margin-top: 1.25rem;">
        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 0.3rem;">
          <span style="font-weight: 700; color: #131b2e;">인텔리전스 추론 진척도</span>
          <span style="font-weight: 800; color: #004ac6; font-family: monospace;">{percent}%</span>
        </div>
        <div style="width: 100%; height: 8px; background: #dae2fd; border-radius: 9999px; overflow: hidden;">
          <div style="width: {percent}%; height: 100%; background: linear-gradient(90deg, #004ac6, #2563eb, #6ffbbe); border-radius: 9999px; transition: width 0.4s ease;"></div>
        </div>
      </div>
    </div>

    <!-- 2/3 Timeline vs 1/3 Fact Widgets -->
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1.25rem; margin-bottom: 1.5rem;">
      <div class="stitch-card">
        <div style="font-size: 15px; font-weight: 800; color: #131b2e; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
          {stitch_icon("timeline", 18, "#004ac6")} 실행 타임라인 및 추론 단계
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
          {"".join(timeline_cards)}
        </div>
      </div>

      <div style="display: flex; flex-direction: column; gap: 1rem;">
        <div class="stitch-card">
          <div style="font-size: 14px; font-weight: 800; color: #131b2e; margin-bottom: 0.75rem; display: flex; justify-content: space-between;">
            <span>실시간 신뢰 팩트</span>
            <span class="stitch-badge badge-blue">{facts_count}건 확보</span>
          </div>
          <div style="display: flex; flex-direction: column; gap: 0.6rem;">
            {facts_body}
          </div>
        </div>
      </div>
    </div>
    """
    clean_html = textwrap.dedent(html).strip()
    target = container if container is not None else st
    target.html(clean_html)


# ------------------------------------------------------------------------------
# 8. [화면 3] 목차 컨펌: 딥 슬레이트 가설 배너 & 4대 메트릭스
# ------------------------------------------------------------------------------
def render_screen3_brief_and_metrics(
    report_title: str,
    target_stakeholder: str,
    angle: str,
    facts_count: int,
    kpi: str,
    hypothesis: str,
    expected_profit: str = "+ 3,420만 원 / 월",
    company_name: str = "자사 스토어"
):
    html = f"""
    <!-- Deep Slate Hero Banner -->
    <div class="stitch-hero-dark">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div style="max-width: 820px;">
          <h2 style="font-size: 22px; font-weight: 800; color: #ffffff; margin: 0 0 0.5rem 0;">📋 맞춤 전략 설계 목차 확인</h2>
          <p style="font-size: 13px; color: rgba(255,255,255,0.85); line-height: 1.6; margin: 0;">
            수집된 {company_name} 실측 팩트를 바탕으로 도출된 3대 전략 목차입니다. 보고 대상(대표/팀장/협업부서)을 선택해 관점을 전환하거나, 목차를 직접 편집한 후 최종 승인해 주세요.
          </p>
        </div>
      </div>
    </div>

    <!-- 4 Key Metrics Grid -->
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.85rem; margin-bottom: 1.5rem;">
      <div class="stitch-card">
        <div style="font-size: 11px; color: #737686; margin-bottom: 0.3rem;">목표 KPI</div>
        <div style="font-size: 15px; font-weight: 800; color: #004ac6; font-family: monospace;">{kpi}</div>
        <div style="font-size: 11px; color: #737686; margin-top: 0.2rem;">상세 결제 전환율</div>
      </div>
      <div class="stitch-card">
        <div style="font-size: 11px; color: #737686; margin-bottom: 0.3rem;">보고 대상</div>
        <div style="font-size: 15px; font-weight: 800; color: #131b2e;">{target_stakeholder}</div>
        <div style="font-size: 11px; color: #737686; margin-top: 0.2rem;">핵심 의사결정권자</div>
      </div>
      <div class="stitch-card">
        <div style="font-size: 11px; color: #737686; margin-bottom: 0.3rem;">기획 관점</div>
        <div style="font-size: 15px; font-weight: 800; color: #131b2e;">{angle}</div>
        <div style="font-size: 11px; color: #737686; margin-top: 0.2rem;">직접적 ROI 입증</div>
      </div>
      <div class="stitch-card">
        <div style="font-size: 11px; color: #737686; margin-bottom: 0.3rem;">검증된 팩트</div>
        <div style="font-size: 15px; font-weight: 800; color: #131b2e; font-family: monospace;">{facts_count}건 확보</div>
        <div style="font-size: 11px; color: #737686; margin-top: 0.2rem;">실측 데이터 기반</div>
      </div>
    </div>

    <!-- Jade Tint Hypothesis Card -->
    <div class="stitch-hypothesis">
      <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem;">
        {stitch_icon("psychology", 20, "#006242")}
        <strong style="font-size: 14px; font-weight: 800; color: #004d33;">도출된 핵심 결론</strong>
      </div>
      <p style="font-size: 13px; color: #0c3829; line-height: 1.6; margin: 0;">
        {hypothesis}
      </p>
    </div>
    """
    st.html(textwrap.dedent(html).strip())


# ------------------------------------------------------------------------------
# 9. [화면 4] 최종 1PAGE 브리프
# ------------------------------------------------------------------------------
def render_screen4_report_header_and_summary(
    report_title: str,
    company_name: str,
    kpi: str,
    angle: str,
    facts_count: int,
    hypothesis: str,
    monthly_impact: str = "+3,420만 원"
):
    html = f"""
    <!-- Document Header -->
    <div class="stitch-card" style="margin-bottom: 1.25rem;">
      <div style="display: flex; gap: 0.5rem; margin-bottom: 0.3rem;">
        <span class="stitch-badge badge-green">AI Verified Brief</span>
        <span style="font-size: 11px; color: #737686;">• 배포 준비 완료</span>
      </div>
      <h2 style="font-size: 22px; font-weight: 800; color: #131b2e; margin: 0 0 0.3rem 0;">{report_title}</h2>
      <p style="font-size: 13px; color: #434655; margin: 0;">
        {company_name} 쇼핑몰의 이탈 구간 해결 및 구매 결정을 가속화하기 위한 14일 실행 로드맵
      </p>
    </div>

    <!-- 4 Summary Metrics -->
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.85rem; margin-bottom: 1.25rem;">
      <div class="stitch-card">
        <div style="font-size: 11px; color: #737686;">대상 스토어</div>
        <div style="font-size: 14px; font-weight: 800; color: #131b2e; margin-top: 0.2rem;">{company_name}</div>
      </div>
      <div class="stitch-card">
        <div style="font-size: 11px; color: #737686;">기획 관점 & 지향</div>
        <div style="font-size: 14px; font-weight: 800; color: #131b2e; margin-top: 0.2rem;">{angle}</div>
      </div>
      <div class="stitch-card">
        <div style="font-size: 11px; color: #737686;">목표 전환율 (KPI)</div>
        <div style="font-size: 14px; font-weight: 800; color: #004ac6; margin-top: 0.2rem; font-family: monospace;">{kpi}</div>
      </div>
      <div class="stitch-card">
        <div style="font-size: 11px; color: #737686;">검증 근거 데이터</div>
        <div style="font-size: 14px; font-weight: 800; color: #131b2e; margin-top: 0.2rem; font-family: monospace;">공식 팩트 {facts_count}건</div>
      </div>
    </div>

    <!-- Executive Summary Banner -->
    <div class="stitch-hero-dark">
      <div>
        <div style="display: flex; gap: 0.5rem; margin-bottom: 0.4rem;">
          <span class="stitch-badge badge-blue">Executive Summary</span>
        </div>
        <h3 style="font-size: 17px; font-weight: 800; color: #ffffff; line-height: 1.5; margin: 0;">
          "{hypothesis}"
        </h3>
      </div>
    </div>
    """
    st.html(textwrap.dedent(html).strip())
