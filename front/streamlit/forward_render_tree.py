def forward_render_tree(test_id, scale_tree, parent_checked=False, depth=0):
    import streamlit as st
    state = {}
    indent = "  " * depth  # 보기 좋게 들여쓰기
    for code, node in scale_tree.items():
        widget_key = f"{test_id}_{depth}_{code}"  # 위젯 고유 키 -> st.session_state에서 해당 키값으로 value(체크상태) 저장
        checked = st.checkbox(
            f"{indent}{code} : {node['scale_name']}",
            value=parent_checked,
            key=widget_key
        )
        children_state = {}
        if node["children"]:
            children_state = forward_render_tree(test_id, node["children"], parent_checked=checked, depth=depth+1) # parent_checked=checked 인자의 이유, 부모 체크박스 상태에 따라 자식 체크박스 상태 결정
            #print(f"Children state for {code}: {children_state}")
            if any(val is False for val in children_state.values()):
                checked = False
            elif all(val is True for val in children_state.values()):
                checked = True
        state[code] = checked
        state.update(children_state) # 딕셔너리 내장 메서드 (다른 딕셔너리의 키-값 쌍을 현재 딕셔너리에 추가/갱신)
        print(state)
    return state