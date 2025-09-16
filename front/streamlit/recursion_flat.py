def recursion_flatten(tree, test_id, cache, path=None):
    # 재귀적으로 트리를 순회하며 평탄화된 캐시 생성
    # 재귀 데이터 비용 처리를 줄이기 위해 path 인자로 인덱싱 쉽게 하기 위해서
    if path is None:
        path = []

    for code, node in tree.items():
        current_path = path + [code]   # 경로 누적
        cache[(test_id, code)] = {
            "node": node,              # 노드 참조 (scale_name, children 등)
            "path": current_path       # 루트부터 현재까지 경로
        }
        # 재귀적으로 children 탐색
        if node["children"]:
            recursion_flatten(node["children"], test_id, cache, current_path)
    return cache