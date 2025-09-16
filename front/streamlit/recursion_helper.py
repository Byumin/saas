# 재귀 헬퍼 함수
def recursion_helper(tree, parent_code):
    """트리(dict) 안에서 parent_code에 해당하는 노드를 찾아 반환"""
    if parent_code in tree:  # 현재 depth에서 찾은 경우
        return tree[parent_code]
    
    # children 재귀 탐색
    for node in tree.values():
        if "children" in node:
            found = recursion_helper(node["children"], parent_code)
            if found:
                return found
    return None