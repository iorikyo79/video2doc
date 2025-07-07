"""
DocumentProcessor 클래스 분리 테스트
TDD Red → Green → Refactor 사이클 적용
"""

import pytest
from processors.document import DocumentProcessor


def test_document_processor_can_be_initialized():
    """DocumentProcessor 클래스가 초기화 가능한지 테스트"""
    processor = DocumentProcessor()
    assert processor is not None
