"""
Phase 3.1 - Video2DocWorkflow 클래스 분리를 위한 TDD 테스트

Red 단계: core.workflow.Video2DocWorkflow 가져오기 실패 테스트
"""

import sys
from pathlib import Path
import pytest

# 상위 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_video2doc_workflow_can_be_initialized():
    """Video2DocWorkflow가 core.workflow 모듈에서 초기화 가능한지 테스트
    
    Red 단계: 아직 core.workflow 모듈이 없으므로 ModuleNotFoundError 발생 예상
    """
    from core.workflow import Video2DocWorkflow
    
    # 단순히 인스턴스 생성만 확인
    workflow = Video2DocWorkflow()
    assert workflow is not None
