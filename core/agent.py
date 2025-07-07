"""Video2DocAgent 클래스 모듈"""

import os
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from smolagents import CodeAgent, LiteLLMModel
from config import config
from utils.exceptions import (
    Video2DocError, YoutubeDownloadError, AudioProcessingError,
    DocumentConversionError, NetworkError, InvalidInputError
)
from utils.youtube import is_youtube_url
from core.workflow import Video2DocWorkflow
from core.tools import (
    youtube_download_tool, mp3_extraction_tool, script_extraction_tool,
    file_conversion_tool, context_integration_tool, report_generation_tool
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Video2DocAgent:
    """Audio2Doc 메인 에이전트 클래스 - MP4/MP3 오디오 파일과 참조 문서 처리"""
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """
        Video2Doc 에이전트 초기화
        
        Args:
            model_config: LLM 모델 설정
        """
        self.workflow = Video2DocWorkflow()
        
        # config.py에서 기본 모델 설정 가져오기
        if model_config:
            # 사용자 설정이 있으면 기본 설정과 병합
            default_config = config.DEFAULT_MODEL_CONFIG.copy()
            default_config.update(model_config)
        else:
            # 사용자 설정이 없으면 config.py의 기본 설정 사용
            default_config = config.DEFAULT_MODEL_CONFIG.copy()
        
        # LLM 모델 초기화
        try:
            self.model = LiteLLMModel(**default_config)
            logger.info("LLM 모델 초기화 완료")
        except Exception as e:
            logger.error(f"LLM 모델 초기화 실패: {e}")
            raise
        
        # 에이전트 초기화 (config.py 설정 활용)
        agent_config = config.AGENT_CONFIG.copy()
        self.agent = CodeAgent(
            tools=[
                youtube_download_tool,
                mp3_extraction_tool,
                script_extraction_tool, 
                file_conversion_tool,
                context_integration_tool,
                report_generation_tool
            ],
            model=self.model,
            add_base_tools=agent_config["add_base_tools"],
            verbosity_level=agent_config["verbosity_level"],
            additional_authorized_imports=agent_config["additional_authorized_imports"]
        )
        
        logger.info("Video2Doc 에이전트 초기화 완료")
    
    def _get_input_type(self, input_path: str) -> str:
        """
        입력이 로컬 파일인지 유튜브 URL인지 확인합니다.
        
        Args:
            input_path: 입력 경로 또는 URL
            
        Returns:
            입력 타입 ("mp4", "mp3", "youtube", "unsupported")
        """
        # 유튜브 URL인지 먼저 확인
        if is_youtube_url(input_path):
            return "youtube"
        
        # 로컬 파일인지 확인
        input_file = Path(input_path)
        
        if not input_file.exists():
            # 파일이 존재하지 않고 URL도 아닌 경우
            return "unsupported"
        
        suffix = input_file.suffix.lower()
        
        if suffix == ".mp4":
            return "mp4"
        elif suffix == ".mp3":
            return "mp3"
        else:
            return "unsupported"
    
    def _is_supported_input(self, input_path: str) -> bool:
        """
        지원되는 입력 형식인지 확인합니다 (로컬 파일 + 유튜브 URL).
        
        Args:
            input_path: 입력 경로 또는 URL
            
        Returns:
            지원 여부
        """
        input_type = self._get_input_type(input_path)
        return input_type in ["mp4", "mp3", "youtube"]
    
    def process_audio_and_references(self, 
                                   audio_path: str, 
                                   reference_files: Optional[List[str]] = None,
                                   report_type: str = "summary",
                                   length: str = "mid") -> Dict[str, str]:
        """
        오디오 파일(MP4/MP3)이나 유튜브 URL과 참조 파일들을 처리하여 보고서를 생성합니다.
        
        Args:
            audio_path: 오디오 파일 경로 (MP4, MP3) 또는 유튜브 URL
            reference_files: 참조 파일 목록 (PPTX, 이미지)
            report_type: 보고서 유형
            length: 보고서 길이
        
        Returns:
            처리 결과 딕셔너리 (각 단계별 파일 경로)
        """
        
        # 입력 타입 확인 (로컬 파일 또는 유튜브 URL)
        input_type = self._get_input_type(audio_path)
        
        if input_type == "youtube":
            instruction = f"""
            다음 단계에 따라 YouTube2Doc 워크플로우를 실행하세요:
            
            1. 유튜브 비디오 다운로드: {audio_path}
            2. 다운로드된 MP4 파일에서 MP3 추출
            3. MP3에서 스크립트 추출 (Whisper 사용)
            4. 참조 파일들을 마크다운으로 변환: {reference_files or []}
            5. 스크립트와 참조 파일들을 통합하여 통합 컨텍스트 생성
            6. 통합 컨텍스트 기반의 최종 보고서 생성 (유형: {report_type}, 길이: {length})
            
            각 단계가 완료되면 생성된 파일 경로를 반환하고 다음 단계로 진행하세요.
            """
        elif input_type == "mp4":
            instruction = f"""
            다음 단계에 따라 Video2Doc 워크플로우를 실행하세요:
            
            1. MP4 파일에서 MP3 추출: {audio_path}
            2. MP3에서 스크립트 추출 (Whisper 사용)
            3. 참조 파일들을 마크다운으로 변환: {reference_files or []}
            4. 스크립트와 참조 파일들을 통합하여 통합 컨텍스트 생성
            5. 통합 컨텍스트 기반의 최종 보고서 생성 (유형: {report_type}, 길이: {length})
            
            각 단계가 완료되면 생성된 파일 경로를 반환하고 다음 단계로 진행하세요.
            """
        elif input_type == "mp3":
            instruction = f"""
            다음 단계에 따라 Audio2Doc 워크플로우를 실행하세요:
            
            MP3 파일이 이미 제공되었으므로 MP3 추출 단계를 건너뛰고 다음 단계들을 수행하세요:
            
            1. MP3에서 스크립트 추출 (Whisper 사용): {audio_path}
            2. 참조 파일들을 마크다운으로 변환: {reference_files or []}
            3. 스크립트와 참조 파일들을 통합하여 통합 컨텍스트 생성
            4. 통합 컨텍스트 기반의 최종 보고서 생성 (유형: {report_type}, 길이: {length})
            
            각 단계가 완료되면 생성된 파일 경로를 반환하고 다음 단계로 진행하세요.
            """
        else:
            raise ValueError(f"지원하지 않는 입력 형식: {input_type}. MP4/MP3 파일 또는 유튜브 URL만 지원됩니다.")
        
        try:
            result = self.agent.run(instruction)
            logger.info(f"워크플로우 완료 (입력 타입: {input_type.upper()})")
            return {"result": str(result), "input_type": input_type}
            
        except Exception as e:
            logger.error(f"워크플로우 처리 실패: {e}")
            raise


def main():
    """메인 함수 - 사용 예시"""
    
    # config.py 기본 설정으로 에이전트 초기화
    print(f"Video2Doc Agent 시작 - 모델: {config.DEFAULT_MODEL_CONFIG['model_id']}")
    agent = Video2DocAgent()
    
    # config.py INPUT_DIR 기반 샘플 파일 경로
    # MP4 또는 MP3 파일을 지원
    audio_path = str(config.INPUT_DIR / "S2_03.mp4")  # MP4 예시
    # audio_path = str(config.INPUT_DIR / "meeting_recording.mp3")  # MP3 예시
    
    reference_files = [
        str(config.INPUT_DIR / "Resume.pdf"),
        str(config.INPUT_DIR / "rules.pdf"), 
        str(config.INPUT_DIR / "RESULT_GASTRO.xlsx")
    ]
    
    # 존재하는 파일만 필터링
    existing_files = []
    for ref_file in reference_files:
        if Path(ref_file).exists():
            existing_files.append(ref_file)
            print(f"✅ 참조 파일 발견: {Path(ref_file).name}")
        else:
            print(f"⚠️ 참조 파일 없음: {Path(ref_file).name}")
    
    try:
        # 입력 타입 확인 (로컬 파일 또는 유튜브 URL)
        input_type = agent._get_input_type(audio_path)
        print(f"\n🎯 입력 타입: {input_type.upper()}")
        if input_type == "youtube":
            print(f"🔗 유튜브 URL: {audio_path}")
        else:
            print(f"📁 파일: {Path(audio_path).name}")
        print(f"📄 참조 파일 수: {len(existing_files)}")
        print(f"📊 보고서 유형: summary (mid)")
        
        result = agent.process_audio_and_references(
            audio_path=audio_path,
            reference_files=existing_files if existing_files else None,
            report_type="summary",
            length="mid"
        )
        
        print("\n✅ Audio2Doc 처리 완료:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\n📂 출력 디렉토리: {config.OUTPUT_DIR}")
        
    except Exception as e:
        print(f"\n❌ 처리 중 오류 발생: {e}")
        logger.exception("상세 오류 정보:")


if __name__ == "__main__":
    main()
