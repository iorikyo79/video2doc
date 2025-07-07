"""
Custom exception classes for Video2Doc system
"""

from typing import List


class Video2DocError(Exception):
    """Video2Doc 시스템의 기본 예외 클래스"""
    def __init__(self, message: str, error_code: str = None, suggestions: List[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.suggestions = suggestions or []
    
    def get_user_friendly_message(self) -> str:
        """사용자 친화적 에러 메시지 반환"""
        msg = f"❌ 오류: {self.message}"
        if self.suggestions:
            msg += "\n\n💡 해결 방법:"
            for i, suggestion in enumerate(self.suggestions, 1):
                msg += f"\n  {i}. {suggestion}"
        return msg

    def __str__(self):
        return self.message


class YoutubeDownloadError(Video2DocError):
    """유튜브 다운로드 관련 에러"""
    pass


class AudioProcessingError(Video2DocError):
    """오디오 처리 관련 에러"""
    pass


class DocumentConversionError(Video2DocError):
    """문서 변환 관련 에러"""
    pass


class NetworkError(Video2DocError):
    """네트워크 관련 에러"""
    pass


class InvalidInputError(Video2DocError):
    """잘못된 입력 관련 에러"""
    pass
