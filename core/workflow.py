"""
Video2DocWorkflow 클래스 모듈

비디오/오디오 파일과 참조 문서를 처리하는 워크플로우 관리
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import torch
from transformers import pipeline
from markitdown import MarkItDown
import yt_dlp

from utils.exceptions import (
    Video2DocError, YoutubeDownloadError, AudioProcessingError,
    DocumentConversionError, NetworkError, InvalidInputError
)
from utils.error_handlers import (
    get_youtube_error_suggestions, get_audio_error_suggestions,
    get_document_error_suggestions, handle_error_with_suggestions
)
from utils.youtube import (
    is_youtube_url, extract_video_id_from_url, sanitize_filename
)
from processors.audio import AudioProcessor
from processors.document import DocumentProcessor
from processors.report import ReportProcessor


# 로깅 설정
logger = logging.getLogger(__name__)


class Video2DocWorkflow:
    """Video2Doc 워크플로우 관리 클래스"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # markitdown 초기화 (통합 문서 변환)
        try:
            self.markitdown = MarkItDown()
            logger.info("markitdown 통합 문서 변환기 초기화 완료")
        except Exception as e:
            logger.warning(f"markitdown 초기화 실패: {e}")
            self.markitdown = None
        
        # Whisper 모델 초기화 (Hugging Face transformers)
        try:
            # GPU 사용 가능 여부 확인
            device = "cuda" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            
            # Hugging Face Whisper pipeline 초기화
            self.whisper_model = pipeline(
                "automatic-speech-recognition",
                model="openai/whisper-large-v3-turbo",
                torch_dtype=torch_dtype,
                device=device,
                return_timestamps=True,
                generate_kwargs={
                    "language": None,  # 자동 언어 감지
                    "task": "transcribe"  # 번역 대신 전사 명시
                }
            )
            logger.info(f"Hugging Face Whisper large-v3-turbo 모델 로드 완료 (device: {device})")
        except Exception as e:
            logger.warning(f"Hugging Face Whisper 모델 로드 실패: {e}")
            self.whisper_model = None
        
        # AudioProcessor 초기화
        self.audio_processor = AudioProcessor(str(self.output_dir), self.whisper_model)
        
        # DocumentProcessor 초기화
        self.document_processor = DocumentProcessor(str(self.output_dir), self.markitdown)
        
        # ReportProcessor 초기화
        self.report_processor = ReportProcessor(str(self.output_dir))
    
    def extract_mp3_from_mp4(self, mp4_path: str) -> str:
        """MP4에서 MP3 추출"""
        return self.audio_processor.extract_mp3_from_mp4(mp4_path)
    
    def extract_script_from_mp3(self, mp3_path: str) -> str:
        """MP3에서 스크립트 추출 (Hugging Face Whisper 사용)"""
        return self.audio_processor.extract_script_from_mp3(mp3_path)
    
    def convert_pptx_to_md(self, pptx_path: str) -> str:
        """PPTX를 마크다운으로 변환 (레거시 방식 - markitdown 실패 시 사용)"""
        return self.document_processor.convert_pptx_to_md(pptx_path)
    
    def convert_image_to_md(self, image_path: str) -> str:
        """이미지를 마크다운으로 변환 (markitdown 실패 시 기본 정보만 제공)"""
        return self.document_processor.convert_image_to_md(image_path)

    def convert_reference_file_to_md(self, file_path: str) -> str:
        """
        참조 파일을 마크다운으로 변환 (markitdown 통합 방식)
        
        Args:
            file_path: 변환할 파일 경로
            
        Returns:
            변환된 마크다운 파일 경로
        """
        return self.document_processor.convert_reference_file_to_md(file_path)
    
    def download_youtube_video(self, youtube_url: str) -> str:
        """
        유튜브 비디오를 다운로드하여 로컬 MP4 파일로 저장합니다.
        
        Args:
            youtube_url: 유튜브 비디오 URL
            
        Returns:
            다운로드된 MP4 파일 경로
        """
        if not is_youtube_url(youtube_url):
            raise InvalidInputError(
                message=f"올바르지 않은 유튜브 URL 형식입니다: {youtube_url}",
                error_code="INVALID_YOUTUBE_URL",
                suggestions=[
                    "올바른 유튜브 URL 형식을 사용해주세요 (예: https://www.youtube.com/watch?v=VIDEO_ID)",
                    "유튜브 동영상이 공개되어 있는지 확인해주세요",
                    "로컬 MP4/MP3 파일 사용을 고려해보세요"
                ]
            )
        
        try:
            # 비디오 정보 먼저 추출
            video_info = self._get_youtube_video_info(youtube_url)
            video_id = extract_video_id_from_url(youtube_url)
            
            # 다운로드 디렉토리 생성
            download_dir = self.output_dir / "downloads"
            download_dir.mkdir(exist_ok=True)
            
            # 안전한 파일명 생성
            safe_title = sanitize_filename(video_info.get('title', f'video_{video_id}'))
            output_filename = f"01_youtube_{video_id}_{safe_title}.%(ext)s"
            output_path = download_dir / output_filename
            
            # yt-dlp 설정
            ydl_opts = {
                'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',  # 720p 이하 MP4 우선
                'outtmpl': str(output_path),
                'max_filesize': 500 * 1024 * 1024,  # 500MB 제한
                'no_warnings': False,
                'quiet': False,
                'extract_flat': False,
                'writeinfojson': False,  # JSON 메타데이터는 별도로 저장하지 않음
            }
            
            logger.info(f"유튜브 비디오 다운로드 시작: {video_info.get('title', 'Unknown')}")
            logger.info(f"비디오 ID: {video_id}")
            logger.info(f"다운로드 경로: {download_dir}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            
            # 다운로드된 파일 찾기 (확장자가 실제로 결정된 후)
            downloaded_files = list(download_dir.glob(f"01_youtube_{video_id}_{safe_title}.*"))
            
            if not downloaded_files:
                raise YoutubeDownloadError(
                    message="유튜브 비디오 다운로드가 완료되었지만 파일을 찾을 수 없습니다",
                    error_code="DOWNLOAD_FILE_NOT_FOUND", 
                    suggestions=[
                        "다시 시도해주세요",
                        "디스크 용량을 확인해주세요",
                        "다른 유튜브 URL로 시도해보세요",
                        "로컬 파일 사용을 고려해보세요"
                    ]
                )
            
            # MP4 파일 우선 선택
            mp4_files = [f for f in downloaded_files if f.suffix.lower() == '.mp4']
            final_file = mp4_files[0] if mp4_files else downloaded_files[0]
            
            logger.info(f"유튜브 비디오 다운로드 완료: {final_file}")
            logger.info(f"파일 크기: {final_file.stat().st_size / 1024 / 1024:.2f} MB")
            
            return str(final_file)
            
        except Exception as e:
            logger.error(f"유튜브 비디오 다운로드 실패: {e}")
            raise handle_error_with_suggestions(e, "youtube")

    def _get_youtube_video_info(self, youtube_url: str) -> dict:
        """
        유튜브 비디오의 메타데이터 정보를 추출합니다.
        
        Args:
            youtube_url: 유튜브 비디오 URL
            
        Returns:
            비디오 정보 딕셔너리 (title, duration, description 등)
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                # 필요한 정보만 추출
                video_info = {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'description': info.get('description', ''),
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date', ''),
                    'view_count': info.get('view_count', 0),
                    'webpage_url': info.get('webpage_url', youtube_url),
                }
                
                logger.info(f"비디오 정보 추출 완료: {video_info['title']}")
                return video_info
                
        except Exception as e:
            logger.warning(f"비디오 정보 추출 실패: {e}")
            # 실패 시 기본 정보 반환
            video_id = extract_video_id_from_url(youtube_url)
            return {
                'title': f'video_{video_id}',
                'duration': 0,
                'description': '',
                'uploader': 'Unknown',
                'upload_date': '',
                'view_count': 0,
                'webpage_url': youtube_url,
            }
