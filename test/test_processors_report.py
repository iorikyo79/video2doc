"""
ReportProcessor 클래스 분리 테스트
TDD Red → Green → Refactor 사이클 적용
"""

import sys
from pathlib import Path

# 상위 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from processors.report import ReportProcessor

def test_report_processor_can_be_initialized():
    """ReportProcessor 클래스가 초기화 가능한지 테스트"""
    processor = ReportProcessor()
    assert processor is not None
