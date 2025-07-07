"""
Utils Error Handlers 모듈
에러 핸들러 관련 유틸리티 함수들
"""

from pathlib import Path
from typing import List
from utils.exceptions import (
    Video2DocError, YoutubeDownloadError, AudioProcessingError, 
    DocumentConversionError, NetworkError
)


def get_youtube_error_suggestions(error_msg: str) -> List[str]:
    """유튜브 에러에 대한 해결방법 제안"""
    suggestions = []
    
    if "network" in error_msg.lower() or "connection" in error_msg.lower():
        suggestions.extend([
            "인터넷 연결을 확인해주세요",
            "방화벽 설정을 확인해주세요",
            "잠시 후 다시 시도해주세요"
        ])
    
    if "private" in error_msg.lower() or "unavailable" in error_msg.lower():
        suggestions.extend([
            "비디오가 비공개이거나 삭제되었을 수 있습니다",
            "다른 유튜브 URL을 시도해보세요",
            "비디오의 접근 권한을 확인해주세요"
        ])
    
    if "format" in error_msg.lower() or "quality" in error_msg.lower():
        suggestions.extend([
            "비디오 품질 설정을 낮춰보세요",
            "다른 형식의 비디오를 시도해보세요"
        ])
    
    if "size" in error_msg.lower() or "large" in error_msg.lower():
        suggestions.extend([
            "더 짧은 비디오를 선택해주세요 (현재 제한: 500MB)",
            "비디오 품질을 낮춰서 다시 시도해주세요"
        ])
    
    # 기본 제안사항
    if not suggestions:
        suggestions.extend([
            "유튜브 URL이 올바른지 확인해주세요",
            "yt-dlp 업데이트를 확인해주세요: pip install --upgrade yt-dlp",
            "로컬 MP4/MP3 파일 사용을 고려해보세요"
        ])
    
    return suggestions


def get_audio_error_suggestions(error_msg: str) -> List[str]:
    """오디오 처리 에러에 대한 해결방법 제안"""
    suggestions = []
    
    if "ffmpeg" in error_msg.lower():
        suggestions.extend([
            "FFmpeg가 설치되어 있는지 확인해주세요",
            "FFmpeg 경로가 시스템 PATH에 있는지 확인해주세요"
        ])
    
    if "whisper" in error_msg.lower() or "model" in error_msg.lower():
        suggestions.extend([
            "Whisper 모델 다운로드를 확인해주세요",
            "인터넷 연결 상태를 확인해주세요",
            "다시 시도하면 모델이 자동으로 다운로드됩니다"
        ])
    
    if "memory" in error_msg.lower() or "cuda" in error_msg.lower():
        suggestions.extend([
            "더 작은 오디오 파일로 시도해보세요",
            "GPU 메모리 부족 시 CPU 모드로 전환됩니다"
        ])
    
    if "format" in error_msg.lower() or "codec" in error_msg.lower():
        suggestions.extend([
            "지원되는 형식인지 확인해주세요 (MP4, MP3)",
            "다른 오디오 형식으로 변환해보세요"
        ])
    
    if not suggestions:
        suggestions.extend([
            "파일이 손상되지 않았는지 확인해주세요",
            "다른 오디오 파일로 시도해보세요",
            "파일 경로에 특수문자가 없는지 확인해주세요"
        ])
    
    return suggestions


def get_document_error_suggestions(error_msg: str, file_path: str = None) -> List[str]:
    """문서 변환 에러에 대한 해결방법 제안"""
    suggestions = []
    
    if "permission" in error_msg.lower():
        suggestions.extend([
            "파일이 다른 프로그램에서 사용 중이 아닌지 확인해주세요",
            "파일 읽기 권한을 확인해주세요"
        ])
    
    if "password" in error_msg.lower() or "encrypted" in error_msg.lower():
        suggestions.extend([
            "암호로 보호된 문서는 지원하지 않습니다",
            "암호를 제거한 후 다시 시도해주세요"
        ])
    
    if "corrupt" in error_msg.lower() or "damaged" in error_msg.lower():
        suggestions.extend([
            "파일이 손상되었을 수 있습니다",
            "원본 파일을 다시 확인해주세요",
            "다른 형식으로 저장한 후 시도해보세요"
        ])
    
    if file_path:
        file_ext = Path(file_path).suffix.lower()
        if file_ext in ['.pptx', '.ppt']:
            suggestions.append("PowerPoint 파일을 PDF로 변환한 후 시도해보세요")
        elif file_ext in ['.xlsx', '.xls']:
            suggestions.append("Excel 파일을 CSV로 변환한 후 시도해보세요")
        elif file_ext in ['.docx', '.doc']:
            suggestions.append("Word 파일을 PDF로 변환한 후 시도해보세요")
    
    if not suggestions:
        suggestions.extend([
            "지원되는 파일 형식인지 확인해주세요",
            "파일을 다시 저장한 후 시도해보세요",
            "다른 문서 파일로 시도해보세요"
        ])
    
    return suggestions


def handle_error_with_suggestions(error: Exception, error_type: str = "general", file_path: str = None) -> Video2DocError:
    """에러를 분석하고 적절한 제안사항과 함께 Video2DocError로 변환"""
    
    error_msg = str(error)
    
    if error_type == "youtube":
        suggestions = get_youtube_error_suggestions(error_msg)
        return YoutubeDownloadError(
            message=f"유튜브 다운로드 중 오류가 발생했습니다: {error_msg}",
            error_code="YOUTUBE_DOWNLOAD_FAILED",
            suggestions=suggestions
        )
    
    elif error_type == "audio":
        suggestions = get_audio_error_suggestions(error_msg)
        return AudioProcessingError(
            message=f"오디오 처리 중 오류가 발생했습니다: {error_msg}",
            error_code="AUDIO_PROCESSING_FAILED", 
            suggestions=suggestions
        )
    
    elif error_type == "document":
        suggestions = get_document_error_suggestions(error_msg, file_path)
        return DocumentConversionError(
            message=f"문서 변환 중 오류가 발생했습니다: {error_msg}",
            error_code="DOCUMENT_CONVERSION_FAILED",
            suggestions=suggestions
        )
    
    elif error_type == "network":
        suggestions = [
            "인터넷 연결을 확인해주세요",
            "잠시 후 다시 시도해주세요",
            "로컬 파일 사용을 고려해보세요"
        ]
        return NetworkError(
            message=f"네트워크 오류가 발생했습니다: {error_msg}",
            error_code="NETWORK_ERROR",
            suggestions=suggestions
        )
    
    else:
        suggestions = [
            "입력 파일들을 다시 확인해주세요",
            "시스템 로그를 확인해주세요",
            "다른 파일로 시도해보세요"
        ]
        return Video2DocError(
            message=f"예상치 못한 오류가 발생했습니다: {error_msg}",
            error_code="UNEXPECTED_ERROR",
            suggestions=suggestions
        )
