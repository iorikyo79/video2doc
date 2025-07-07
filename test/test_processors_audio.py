"""
AudioProcessor 모듈 분리를 위한 TDD 테스트
"""

import sys
from pathlib import Path
from pathlib import Path
import pytest

# 상위 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_audio_processor_can_be_initialized():
    """AudioProcessor 클래스가 초기화될 수 있는지 테스트 (실패하도록)"""
    # 아직 processors.audio 모듈이 없으므로 이 테스트는 실패해야 함
    from processors.audio import AudioProcessor
    
    processor = AudioProcessor()
    assert processor is not None


def test_audio_processor_has_extract_mp3_method():
    """AudioProcessor가 extract_mp3_from_mp4 메서드를 가지고 있는지 테스트 (실패하도록)"""
    from processors.audio import AudioProcessor
    
    processor = AudioProcessor()
    assert hasattr(processor, 'extract_mp3_from_mp4')


def test_audio_processor_has_extract_script_method():
    """AudioProcessor가 extract_script_from_mp3 메서드를 가지고 있는지 테스트 (실패하도록)"""
    from processors.audio import AudioProcessor
    
    processor = AudioProcessor()
    assert hasattr(processor, 'extract_script_from_mp3')
