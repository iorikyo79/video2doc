"""
Utils Error Handlers 모듈 테스트
TDD Red 단계: 에러 핸들러 분리를 위한 실패 테스트 작성
"""

import pytest


def test_get_youtube_error_suggestions_returns_list():
    """
    Red 테스트: get_youtube_error_suggestions 함수가 list를 반환하는지 확인
    예상 실패: ModuleNotFoundError (아직 분리되지 않음)
    """
    from utils.error_handlers import get_youtube_error_suggestions
    
    # 단일 검증: 함수가 list를 반환하는지만 확인
    result = get_youtube_error_suggestions("test")
    assert isinstance(result, list)
