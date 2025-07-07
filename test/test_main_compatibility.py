"""main.py import 호환성 테스트"""

import sys
import ast
from pathlib import Path


# 상위 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))




def test_main_py_imports_from_new_structure():
    """
    Red 단계: main.py가 새로운 모듈 구조에서 정상 import하는지 테스트
    
    이 테스트는 의도적으로 실패해야 합니다 (아직 기존 구조 import 사용 중)
    
    새로운 모듈 구조에서는 다음과 같이 import해야 합니다:
    - Video2DocAgent: from core.agent import Video2DocAgent
    - is_youtube_url: from utils.youtube import is_youtube_url  
    - Exceptions: from utils.exceptions import Video2DocError, InvalidInputError
    """
    main_py_path = Path("main.py")
    
    # 파일 존재 확인
    assert main_py_path.exists(), "main.py 파일이 존재하지 않습니다"
    
    # 파일 내용 읽기
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # AST 파싱하여 import 구문 분석
    tree = ast.parse(content)
    
    # 현재 import 구문들 수집
    current_imports = []
    expected_new_imports = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "video2doc_agent":
                # 기존 구조 import 발견 - 새로운 구조로 변경 필요
                names = [alias.name for alias in node.names]
                current_imports.append(f"from {node.module} import {', '.join(names)}")
                
                # 새로운 구조 제안
                if "Video2DocAgent" in names:
                    expected_new_imports.append("from core.agent import Video2DocAgent")
                if "is_youtube_url" in names:
                    expected_new_imports.append("from utils.youtube import is_youtube_url")
                if any(exc in names for exc in ["Video2DocError", "InvalidInputError"]):
                    exc_names = [name for name in names if name in ["Video2DocError", "InvalidInputError"]]
                    expected_new_imports.append(f"from utils.exceptions import {', '.join(exc_names)}")
    
    # 기존 구조 import가 발견되면 테스트 실패 (의도적 실패)
    if current_imports:
        assert False, f"기존 구조 import 발견: {current_imports}. 새로운 구조: {expected_new_imports}"
    
    print(f"✅ main.py는 새로운 모듈 구조를 사용합니다")


if __name__ == "__main__":
    try:
        test_main_py_imports_from_new_structure()
        print("✅ test_main_py_imports_from_new_structure PASSED")
    except AssertionError as e:
        print(f"❌ test_main_py_imports_from_new_structure FAILED: {e}")
    except Exception as e:
        print(f"🔥 test_main_py_imports_from_new_structure ERROR: {e}")
