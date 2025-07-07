"""
Utils YouTube 모듈 테스트
TDD Red 단계: 유튜브 유틸리티 분리를 위한 실패 테스트 작성
"""

import pytest


def test_is_youtube_url_exists_in_module():
    """
    Red 테스트: is_youtube_url 함수가 utils.youtube 모듈에 존재하는지 확인
    예상 실패: ModuleNotFoundError (아직 분리되지 않음)
    """
    from utils.youtube import is_youtube_url
    
    # 단일 검증: 함수가 존재하는지만 확인 (기능은 이미 검증됨)
    assert callable(is_youtube_url)
