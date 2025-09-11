import streamlit as st

# --- 커스텀 스타일 적용 (버튼 간격 조절) ---
st.markdown(
    """
    <style>
    /* Streamlit secondary 버튼의 기본 간격을 조정 */
    button[kind="secondary"] {
        margin: 0 4px 4px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 앱 제목 ---
st.title("검사 선택 UI")

# --- 전체 검사 목록 ---
all_exams = ["golden", "adhd", "ohss", "iess", "bayley", "wmt", "tmt"]

# --- 세션 상태 초기화 ---
if "selected_exams" not in st.session_state:
    st.session_state.selected_exams = []

# --- 상단: 선택된 검사 표시 ---
st.markdown("### ✅ 선택된 검사")
if st.session_state.selected_exams:
    st.write(", ".join(f"`{x}`" for x in st.session_state.selected_exams))
else:
    st.info("아직 선택된 검사가 없습니다.")

st.divider()

# --- 버튼을 가로로 배치 ---
num_cols = 4
rows = [all_exams[i:i+num_cols] for i in range(0, len(all_exams), num_cols)]

for row in rows:
    cols = st.columns(num_cols)
    for col, exam in zip(cols, row):
        with col:
            if exam in st.session_state.selected_exams:
                st.button(f"✔️ {exam}", key=f"disabled_{exam}", disabled=True)
            else:
                if st.button(f"➕ {exam}", key=f"add_{exam}"):
                    st.session_state.selected_exams.append(exam)
                    st.rerun()

# --- 선택 초기화 버튼 ---
if st.button("선택 초기화"):
    st.session_state.selected_exams = []
    st.rerun()