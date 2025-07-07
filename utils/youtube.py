"""
Utils YouTube 모듈
유튜브 관련 유틸리티 함수들
"""

import re


def is_youtube_url(url: str) -> bool:
    """
    URL이 유튜브 링크인지 확인합니다.
    
    Args:
        url: 확인할 URL 문자열
        
    Returns:
        유튜브 URL 여부
    """
    if not isinstance(url, str):
        return False
    
    # 유튜브 URL 패턴 매칭
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
        r'(?:https?://)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+',
        r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=[\w-]+',
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url.strip()):
            return True
    
    return False


def extract_video_id_from_url(url: str) -> str:
    """
    유튜브 URL에서 비디오 ID를 추출합니다.
    
    Args:
        url: 유튜브 URL
        
    Returns:
        비디오 ID (11자리 문자열)
        
    Raises:
        ValueError: 유효하지 않은 유튜브 URL인 경우
    """
    if not is_youtube_url(url):
        raise ValueError(f"유효하지 않은 유튜브 URL: {url}")
    
    # 다양한 유튜브 URL 형식에서 비디오 ID 추출
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            # 유튜브 비디오 ID는 정확히 11자리여야 함
            if len(video_id) == 11:
                return video_id
    
    raise ValueError(f"유튜브 URL에서 비디오 ID를 추출할 수 없습니다: {url}")


def sanitize_filename(filename: str) -> str:
    """
    파일명에서 특수문자를 제거하여 파일시스템에서 안전하게 사용할 수 있도록 합니다.
    
    Args:
        filename: 원본 파일명
        
    Returns:
        정리된 파일명
    """
    if not filename:
        return "untitled"
    
    # 위험한 문자들을 안전한 문자로 교체
    dangerous_chars = r'[<>:"/\\|?*]'
    filename = re.sub(dangerous_chars, '_', filename)
    
    # 연속된 공백을 하나로 교체
    filename = re.sub(r'\s+', ' ', filename)
    
    # 앞뒤 공백 및 점 제거
    filename = filename.strip(' .')
    
    # 너무 긴 파일명 자르기 (Windows 파일명 제한 고려)
    max_length = 200
    if len(filename) > max_length:
        filename = filename[:max_length].rsplit(' ', 1)[0]  # 단어 단위로 자르기
    
    # 빈 문자열인 경우 기본값 사용
    if not filename:
        return "untitled"
    
    return filename
