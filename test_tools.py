#!/usr/bin/env python3
"""
Phase 3.2 TDD Red: smolagents Tools 분리 테스트
core.tools 모듈로 @tool 데코레이터 함수들 분리를 위한 TDD 테스트
"""

import pytest


def test_youtube_download_tool_exists():
    """
    TDD Red: youtube_download_tool 함수가 core.tools 모듈에 존재하는지 테스트
    
    예상 실패: ModuleNotFoundError (아직 core.tools 모듈이 존재하지 않음)
    """
    # 이 import는 실패해야 함 (아직 core/tools.py가 없음)
    from core.tools import youtube_download_tool
    
    # 함수 존재 확인
    assert callable(youtube_download_tool)
