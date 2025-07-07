"""
TDD 기반 Utils 패키지 분리 테스트
예외 클래스들을 utils.exceptions 모듈로 분리하기 위한 테스트
"""

import pytest
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_video2doc_error_has_message_attribute():
    """
    Red Phase: Video2DocError가 utils.exceptions에서 import 가능하고 message 속성을 가지는지 테스트
    현재는 의도적으로 실패할 것입니다 (utils.exceptions 모듈이 존재하지 않음)
    """
    # 이 import는 현재 실패할 것입니다 (Red 단계)
    from utils.exceptions import Video2DocError
    
    # 기본 기능 테스트
    error = Video2DocError("test message")
    assert error.message == "test message"
    assert hasattr(error, 'error_code')
    assert hasattr(error, 'suggestions')
    assert isinstance(error.suggestions, list)
