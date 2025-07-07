"""
AudioProcessor 클래스 - 오디오 처리 관련 기능을 담당
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from utils.exceptions import AudioProcessingError
from utils.error_handlers import handle_error_with_suggestions

logger = logging.getLogger(__name__)


class AudioProcessor:
    """오디오 파일 처리를 담당하는 클래스"""
    
    def __init__(self, output_dir: str = "output", whisper_model=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.whisper_model = whisper_model
    
    def extract_mp3_from_mp4(self, mp4_path: str) -> str:
        """MP4에서 MP3 추출"""
        mp4_file = Path(mp4_path)
        mp3_file = self.output_dir / f"02_{mp4_file.stem}.mp3"
        
        try:
            cmd = [
                "ffmpeg", "-i", str(mp4_file), 
                "-q:a", "0", "-map", "a", 
                str(mp3_file), "-y"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"MP3 추출 완료: {mp3_file}")
            return str(mp3_file)
        except subprocess.CalledProcessError as e:
            logger.error(f"MP3 추출 실패: {e}")
            raise handle_error_with_suggestions(e, "audio")
    
    def extract_script_from_mp3(self, mp3_path: str) -> str:
        """MP3에서 스크립트 추출 (Hugging Face Whisper 사용)"""
        mp3_file = Path(mp3_path)
        text_only_file = self.output_dir / f"03_{mp3_file.stem}_script_text.md"
        timestamp_file = self.output_dir / f"03_{mp3_file.stem}_script_timestamp.md"
        
        try:
            if self.whisper_model is None:
                raise AudioProcessingError(
                    message="음성 인식 모델이 로드되지 않았습니다",
                    error_code="WHISPER_MODEL_NOT_LOADED",
                    suggestions=[
                        "시스템을 다시 시작해보세요",
                        "인터넷 연결을 확인해주세요 (모델 다운로드 필요)",
                        "디스크 용량을 확인해주세요",
                        "Hugging Face 토큰 설정을 확인해주세요"
                    ]
                )
            
            # Hugging Face pipeline을 사용한 음성 인식
            logger.info(f"음성 인식 시작: {mp3_path}")
            result = self.whisper_model(mp3_path)
            
            # 기본 정보 헤더 템플릿
            header_template = f"""# 동영상 스크립트

**파일명:** {mp3_file.name}
**모델:** openai/whisper-large-v3-turbo (Hugging Face)

"""
            
            # 1. 텍스트만 파일 생성 (항상 생성)
            text_content = header_template
            text_content += f"## 전체 텍스트\n\n{result['text']}\n\n"
            
            with open(text_only_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            logger.info(f"텍스트만 스크립트 파일 생성: {text_only_file}")
            
            # 2. 타임스탬프 정보가 있는지 확인하고 타임스탬프 파일 생성
            has_timestamps = 'chunks' in result and result['chunks'] and any(
                'timestamp' in chunk and chunk['timestamp'] for chunk in result['chunks']
            )
            
            if has_timestamps:
                # 타임스탬프 파일 생성
                timestamp_content = header_template
                timestamp_content += "## 시간별 세그먼트 (타임스탬프 포함)\n\n"
                
                for chunk in result['chunks']:
                    if 'timestamp' in chunk and chunk['timestamp']:
                        start_time = chunk['timestamp'][0] if chunk['timestamp'][0] is not None else 0
                        end_time = chunk['timestamp'][1] if chunk['timestamp'][1] is not None else start_time
                        text = chunk['text'].strip()
                        
                        start_min, start_sec = divmod(int(start_time), 60)
                        end_min, end_sec = divmod(int(end_time), 60)
                        timestamp_content += f"**[{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}]** {text}\n\n"
                    else:
                        # 타임스탬프가 없는 청크
                        text = chunk['text'].strip()
                        timestamp_content += f"**[시간 정보 없음]** {text}\n\n"
                
                with open(timestamp_file, 'w', encoding='utf-8') as f:
                    f.write(timestamp_content)
                logger.info(f"타임스탬프 스크립트 파일 생성: {timestamp_file}")
                
                # 타임스탬프가 있으면 타임스탬프 파일 경로 반환
                logger.info("타임스탬프가 있는 스크립트 - 타임스탬프 파일을 메인으로 사용")
                return str(timestamp_file)
            else:
                # 타임스탬프가 없으면 텍스트만 파일 경로 반환
                logger.info("타임스탬프 정보 없음 - 텍스트만 파일을 메인으로 사용")
                return str(text_only_file)
            
        except Exception as e:
            logger.error(f"스크립트 추출 실패: {e}")
            raise handle_error_with_suggestions(e, "audio")
