# ───────────────────────────────────────────────────────
# PVD Search App – full 30k rows, smart column width
# ───────────────────────────────────────────────────────
import streamlit as st
st.set_page_config(page_title="PVD Search", layout="wide",
                   initial_sidebar_state="collapsed")

import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# ── 0. 로그인 로직 ──────────────────────────────────────
VALID_USERS = {"Korloy": "19660611"}
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    if VALID_USERS.get(st.session_state["__uid"].strip()) == st.session_state["__pw"].strip():
        st.session_state.authenticated = True
        st.success("로그인 성공! 🎉")
        st.rerun()
    else:
        st.error("ID 또는 비밀번호가 틀렸습니다.")

def logout():
    st.session_state.authenticated = False
    st.rerun()

if not st.session_state.authenticated:
    st.title("🔐 PVD Search ‒ Login")
    st.text_input("ID", key="__uid")
    st.text_input("Password", type="password", key="__pw")
    st.button("로그인", on_click=login)
    st.stop()

st.sidebar.button("🔓 로그아웃", on_click=logout)

# ── 1. 데이터 로드 ──────────────────────────────────────
DATA_PATH = "data/___PVD 공정 데이터 APPS_1.xlsx"
@st.cache_data
def load_data():
    raw = pd.read_excel(DATA_PATH, sheet_name="raw", engine="openpyxl")
    ref = pd.read_excel(DATA_PATH, sheet_name="참조표2", engine="openpyxl")
    return raw.fillna(""), ref.fillna("")
raw_df, ref_df = load_data()

# ── 유틸 : 컬럼 폭 계산 ─────────────────────────────────
def calc_widths(df: pd.DataFrame, cols,
                px_per_char=8, max_px=300, min_px=80):
    out = {}
    for c in cols:
        max_len = max(df[c].astype(str).map(len).max(), len(c))
        out[c] = int(max(min_px, min(max_len * px_per_char, max_px)))
    return out

# ── 2. UI 탭 ───────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 자재번호 검색", "🔍 재종 검색"])

# ─ TAB 1 : 자재번호 검색 ──────────────────────────────
with tab1:
    st.subheader("자재번호·형번·재종 전역 검색")
    query = st.text_input("검색어 입력", placeholder="예: 1-02-, APKT1604, PC6510 ...")

    raw_sorted = raw_df.sort_values(["코팅그룹", "자재번호"])
    view = raw_sorted if not query else raw_sorted[
        raw_sorted.apply(lambda r: query.lower() in " ".join(r.astype(str)).lower(), axis=1)
    ]

    cols1 = ["자재번호", "형번", "CB", "재종", "전처리", "후처리",
             "핀", "스프링 종류", "스프링 개수", "간격", "줄", "IS 개수(개/줄)"]

    gb1 = GridOptionsBuilder.from_dataframe(view[cols1])
    for col, w in calc_widths(view, cols1).items():
        gb1.configure_column(col, width=w)

    # ❌ pagination 제거 → 모든 행 버추얼 스크롤
    grid_opt1 = gb1.build()
    AgGrid(
        view[cols1].astype(str),
        gridOptions=grid_opt1,
        height=600,                      # 그리드 높이 (조절 가능)
        fit_columns_on_grid_load=True
    )

# ─ TAB 2 : 재종 검색 ──────────────────────────────────
with tab2:
    st.subheader("재종·코팅그룹 상세 검색")
    c1, c2 = st.columns(2)
    with c1:
        alloy = st.selectbox("합금 선택", ["전체"] + sorted(ref_df["합금"].unique()))
    with c2:
        tmp = ref_df if alloy == "전체" else ref_df[ref_df["합금"] == alloy]
        grade = st.selectbox("재종 선택", ["전체"] + sorted(tmp["재종"].unique()))

    key2 = st.text_input("검색어 입력", placeholder="CX0824, TiAlN ...")

    filt = ref_df.copy()
    if alloy != "전체": filt = filt[filt["합금"] == alloy]
    if grade != "전체": filt = filt[filt["재종"] == grade]
    if key2: filt = filt[filt.apply(lambda r: key2.lower() in " ".join(r.astype(str)).lower(), axis=1)]

    filt = filt.sort_values(["박막명", "코팅그룹"])

    cols2 = ["재종", "코팅그룹", "재종내역", "코팅재종그룹 내역", "박막명",
             "색상", "관리규격", "가용설비", "작업시간", "합금",
             "공정특이사항", "인선처리"]

    gb2 = GridOptionsBuilder.from_dataframe(filt[cols2])
    for col, w in calc_widths(filt, cols2).items():
        gb2.configure_column(col, width=w)

    grid_opt2 = gb2.build()
    AgGrid(
        filt[cols2].astype(str),
        gridOptions=grid_opt2,
        height=600,
        fit_columns_on_grid_load=True
    )

# ─ 푸터 ────────────────────────────────────────────────
st.caption("ⓒ 2025 Korloy DX · 연삭코팅기술팀 홍재민 선임")
