import streamlit as st
import awswrangler as wr
import pandas as pd
from recursion_helper import recursion_helper
from forward_render_tree import forward_render_tree
from recursion_flat import recursion_flatten
import pprint

st.set_page_config(page_title="SaaS Frontend", layout="wide")

# 탭 구성
tabs = st.tabs(["검사 및 척도 선택", "인적사항 입력","문항 응답", "결과 확인"])

# [1] 검사 및 척도 선택 화면
with tabs[0]:
    st.title("검사 및 척도 선택")
    # 검사 목록 (추후에 동적으로 불러올 수 있음)
    # Athena 쿼리 실행 → Pandas DataFrame
    # 초기 로딩 시 한번만 쿼리 실행되도록 캐싱
    @st.cache_data()
    def test_load_data():
        return wr.athena.read_sql_query(
            sql="""
                SELECT a.test_id, a.test_name, a.essential_info,
                    b.scale_code, b.scale_name, b.parent_scale_id, b.level, b.version
                FROM test_info a
                INNER JOIN scale_tree b
            ON a.test_id = b.test_id
            AND a.version = b.version
            WHERE a.version = 'V 1.0'
        """,
        database="saas_proto",
        ctas_approach=False,                           # 기본은 CTAS, False로 두면 그냥 SELECT 실행
        s3_output="s3://saas-inpsyt/athena-query-results/")    # 쿼리 결과 저장될 S3 경로
    df = test_load_data()

    # 재귀 데이터 전처리
    grouped_testid_df = df.groupby('test_id')
    tree_dict = {}
    for test_id, group in grouped_testid_df:
        print(f"Processing test_id: {test_id}")
        tree_dict[test_id] = {
            'test_name': group['test_name'].iloc[0],
            'essential_info': group['essential_info'].iloc[0],
            'version': group['version'].iloc[0],
            'scale_tree': {}
        }
        group = group.sort_values(by=['level', 'scale_code']) # level, scale_code 기준 정렬
        max_level = group['level'].max()
        min_level = group['level'].min()
        for idx, row in group.iterrows():
            node = {
                "scale_name": row['scale_name'],
                "children": {}
            }
            if pd.isna(row['parent_scale_id']):  # 최상위 척도
                tree_dict[test_id]['scale_tree'][row['scale_code']] = node
            else:
                parent_node = recursion_helper(tree_dict[test_id]['scale_tree'], row['parent_scale_id']) # parent 위치 찾아서 children에 추가
                if parent_node:
                    parent_node['children'][row['scale_code']] = node
    print(tree_dict)

    # 재귀 데이터 평탄화
    # (test_id, scale_code)로 인덱싱된 캐시 생성 -> 재귀형태의 raw 데이터를 쉽게 접근하기 위해
    # {'GOLDEN_CO_SG': {'a01': {'node': {...}, 'path': ['a01']}, ...}, ...}
    @st.cache_data()
    def flat_tree(tree_dict):
        flat_cache = {}
        for test_id, test_info in tree_dict.items():
            recursion_flatten(test_info['scale_tree'], test_id, flat_cache)
        return flat_cache
    flat_cache = flat_tree(tree_dict)
    print(flat_cache)

    # 검사 목록 및 구조 데이터(tree_dict) 트리 선택 전파 ui
    # 검사 선택 목록을 먼저 받고, 그에 따른 트리 딕셔너리 분리해서 구성
    selected_tests = st.multiselect("실시할 검사 선택", options=list(tree_dict.keys()), format_func=lambda x: f"{tree_dict[x]['test_name']}")
    if selected_tests:
        for test_id in selected_tests:
            tree_dict[test_id]['choice'] = True  # 선택 상태 표시
            st.write(f"검사: {tree_dict[test_id]['test_name']} (버전: {tree_dict[test_id]['version']})")
            selected_state = forward_render_tree(test_id, tree_dict[test_id]['scale_tree'])
            for code, checked in selected_state.items():
                target_tree_dict = tree_dict[test_id]['scale_tree']
                for key in flat_cache[(test_id, code)]['path']:
                    if key in target_tree_dict:
                        target_tree_dict = target_tree_dict[key]
                    elif 'children' in target_tree_dict:
                        target_tree_dict = target_tree_dict['children'][key]
                    else:
                        raise KeyError(f"Key {key} not found in the tree structure.")
                    target_tree_dict['choice'] = checked  # 선택 상태 표시
    else:
        pass
    pprint.pprint(tree_dict)
    st.session_state['selected_tests'] = selected_tests
    st.session_state['tree_dict'] = tree_dict  # 전체 트리 구조 세션 상태에 저장
    # 선택된 검사 및 척도 세션 상태에 저장
    # 선택된 검사 essential_info도 함께 저장

# [2] 인적사항 입력
with tabs[1]:
    st.title("인적사항 입력")
    if not st.session_state['selected_tests']:
        st.warning("먼저 '검사 및 척도 선택' 탭에서 검사를 선택하세요.")
        st.stop()
    else:
        # essential_info에 매칭되는 인적정보 이름
        info_map = {
            'age': '나이',
            'sex': '성별',
            'education': '학력',
            'occupation': '직업',
            'marital_status': '결혼 여부',
            'residence': '거주지',
            'contact': '연락처',
            'role': '역할',
            'position': '직책'
        }
        tree_dict = st.session_state['tree_dict']
        selected_tests = st.session_state['selected_tests']
        essential_info_set = set()
        for test_id in selected_tests:
            essential_info = tree_dict[test_id]['essential_info']
            essential_info = set(item.strip() for item in essential_info.strip("{}").split(","))
            essential_info_set = essential_info_set | essential_info  # 집합 합집합 연산
        essential_info_list = list(essential_info_set)
        user_info = {}
        for info in essential_info_list:
            label = info_map.get(info, info)  # 매핑된 라벨이 없으면 원래 키 사용
            if info == 'age':
                user_info[info] = st.number_input(f"{label} 입력", min_value=0, max_value=120, step=1)
            elif info == 'sex':
                user_info[info] = st.selectbox(f"{label} 선택", options=['남', '여'])
            elif info == 'education':
                user_info[info] = st.selectbox(f"{label} 선택", options=['고등학교', '대학', '대학원'])
            elif info == 'occupation':
                user_info[info] = st.text_input(f"{label} 입력")
            elif info == 'marital_status':
                user_info[info] = st.selectbox(f"{label} 선택", options=['미혼', '기혼', '이혼'])
            elif info == 'residence':
                user_info[info] = st.text_input(f"{label} 입력")
            elif info == 'contact':
                user_info[info] = st.text_input(f"{label} 입력")
            elif info == 'role':
                user_info[info] = st.text_input(f"{label} 입력")
            elif info == 'position':
                user_info[info] = st.text_input(f"{label} 입력")
            else:
                user_info[info] = st.text_input(f"{label} 입력")
        st.session_state['user_info'] = user_info
        st.write("입력된 인적사항:", user_info)

# [3] 문항 응답
with tabs[2]:
    st.title("문항 응답")
    if not st.session_state['selected_tests']:
        st.warning("먼저 '검사 및 척도 선택' 탭에서 검사를 선택하세요.")
        st.stop()
    elif not st.session_state.get('user_info'):
        st.warning("먼저 '인적사항 입력' 탭에서 인적사항을 입력하세요.")
        st.stop()
    else:
        st.write("문항 응답 화면 (구현 예정)")
        # 선택된 검사 및 척도에 따라 문항 로드 및 응답 처리 로직 구현 필요
        # 예: st.radio, st.selectbox, st.slider 등 다양한 입력 위젯 사용 가능

# mac : streamlit run front/streamlit/pipeline.py