import streamlit as st

st.set_page_config(page_title="SaaS Frontend", layout="wide")

# 단계 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 0
else:
    pass
# 단계 이동 함수
def next_step():
    st.session_state.step += 1
    st.rerun()
def prev_step():
    st.session_state.step -= 1
    st.rerun()

# 인적사항 입력 화면
try:
    if st.session_state.step == 0:
        st.title("검사 및 척도 선택")
        # 검사 목록 (추후에 동적으로 불러올 수 있음)
        all_tests = ["Golden", "ADHD", "OHSS", "IESS"]
        # 검사 다중 선택
        selected_tests = st.multiselect("실시할 검사를 선택해주세요.", all_tests, key="selected_tests_widget")
        st.session_state['selected_tests'] = selected_tests

        # 검사 선택에 따라 척도 목록 (추후에 동적으로 불러올 수 있음)
        selected_scales_dict = {"Golden": ["외향성", "감정"],
                           "ADHD": ["주의력", "과잉행동"],
                           "OHSS": ["직무부하", "신체화"],
                           "IESS": ["직무만족", "불안"]}
        for test in selected_tests:
            a = st.multiselect(f"{test} 척도를 선택해주세요.", selected_scales_dict[test], key=test)
            st.session_state['selected_scales'] = a

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")

