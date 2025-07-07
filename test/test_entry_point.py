"""video2doc_agent.py Entry Point 리팩토링을 위한 TDD 테스트"""

import sys
from pathlib import Path
import ast
import inspect

# 상위 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_video2doc_agent_py_is_entry_point_only():
    """
    Red 단계: video2doc_agent.py가 단순한 entry point만 포함하는지 테스트
    
    이 테스트는 의도적으로 실패해야 합니다 (아직 완전한 entry point가 아님)
    Entry point 파일은 다음 조건을 만족해야 합니다:
    1. import 구문과 docstring만 포함
    2. 클래스나 함수 정의가 없음
    3. if __name__ == "__main__" 블록만 허용
    """
    video2doc_agent_path = Path("video2doc_agent.py")
    
    # 파일 존재 확인
    assert video2doc_agent_path.exists(), "video2doc_agent.py 파일이 존재하지 않습니다"
    
    # 파일 내용 읽기
    with open(video2doc_agent_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # AST 파싱하여 코드 구조 분석
    tree = ast.parse(content)
    
    # 허용되지 않는 노드 타입들 검사
    forbidden_nodes = []
    for node in ast.walk(tree):
        # 클래스 정의 금지
        if isinstance(node, ast.ClassDef):
            forbidden_nodes.append(f"클래스 정의 발견: {node.name}")
        
        # 함수 정의 금지 (단, if __name__ == "__main__" 내부 제외)
        elif isinstance(node, ast.FunctionDef):
            forbidden_nodes.append(f"함수 정의 발견: {node.name}")
    
    # 실패해야 하는 조건: 금지된 노드들이 발견되면 테스트 실패
    assert len(forbidden_nodes) == 0, f"Entry point가 아님: {', '.join(forbidden_nodes)}"
    
    # 추가 검증: import와 docstring, if __name__ 블록만 있는지 확인
    allowed_statements = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            allowed_statements.append("import")
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            allowed_statements.append("docstring")
        elif isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            # if __name__ == "__main__" 패턴 확인
            if (isinstance(node.test.left, ast.Name) and 
                node.test.left.id == "__name__" and
                len(node.test.comparators) == 1 and
                isinstance(node.test.comparators[0], ast.Constant) and
                node.test.comparators[0].value == "__main__"):
                allowed_statements.append("main_block")
            else:
                forbidden_nodes.append("허용되지 않는 if 블록")
        else:
            forbidden_nodes.append(f"허용되지 않는 구문: {type(node).__name__}")
    
    # 최종 검증
    assert len(forbidden_nodes) == 0, f"Entry point 위반사항: {', '.join(forbidden_nodes)}"
    print(f"✅ video2doc_agent.py는 순수한 entry point입니다: {allowed_statements}")


if __name__ == "__main__":
    try:
        test_video2doc_agent_py_is_entry_point_only()
        print("✅ test_video2doc_agent_py_is_entry_point_only PASSED")
    except AssertionError as e:
        print(f"❌ test_video2doc_agent_py_is_entry_point_only FAILED: {e}")
    except Exception as e:
        print(f"🔥 test_video2doc_agent_py_is_entry_point_only ERROR: {e}")
