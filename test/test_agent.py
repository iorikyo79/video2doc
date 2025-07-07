"""Video2DocAgent 클래스 분리를 위한 TDD 테스트"""

import sys
from pathlib import Path
import pytest

# 상위 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_video2doc_agent_from_core_module():
    """
    Red 단계: Video2DocAgent가 core.agent 모듈에서 import 가능한지 테스트
    
    이 테스트는 의도적으로 실패해야 합니다 (아직 core.agent 모듈이 존재하지 않음)
    """
    # 이 import는 ModuleNotFoundError를 발생시켜야 함
    from core.agent import Video2DocAgent
    
    # 최소한의 기능 검증: 클래스 인스턴스 생성 가능
    agent = Video2DocAgent()
    assert agent is not None


if __name__ == "__main__":
    test_video2doc_agent_from_core_module()
    print("✅ test_video2doc_agent_from_core_module PASSED")
