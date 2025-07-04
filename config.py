"""
Video2Doc Agent 설정 파일

이 파일은 Video2Doc 에이전트의 기본 설정을 정의합니다.
"""

import os
from pathlib import Path

class Config:
    """Video2Doc 에이전트 설정 클래스"""
    
    # 기본 디렉토리 설정
    BASE_DIR = Path(__file__).parent
    INPUT_DIR = BASE_DIR / "input"
    OUTPUT_DIR = BASE_DIR / "output"
    TEMP_DIR = BASE_DIR / "temp"
    
    # 출력 디렉토리 생성
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    
    # 지원 파일 형식
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv']
    SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a']
    SUPPORTED_DOC_FORMATS = ['.pdf', '.pptx', '.docx']
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp']
    
    # Whisper 설정
    WHISPER_MODEL = "large-v3"  # 또는 "medium", "small", "base", "tiny"
    WHISPER_LANGUAGE = None  # None이면 자동 감지, "ko", "en" 등 지정 가능
    
    # FFmpeg 설정
    FFMPEG_AUDIO_QUALITY = "0"  # 0이 최고 품질
    FFMPEG_AUDIO_CODEC = "mp3"
    
    # LLM 모델 설정
    DEFAULT_MODEL_CONFIG = {
        "model_id": "ollama_chat/qwen3:custom",
        "api_base": "http://localhost:11434",
        "num_ctx": 16384,
        "temperature": 0.7,
    }
    
    # 대안 모델 설정들
    ALTERNATIVE_MODELS = {
        "local_qwen": {
            "model_id": "ollama_chat/qwen3:custom",
            "api_base": "http://localhost:11434",
            "num_ctx": 16384,
        },
        "local_deepseek": {
            "model_id": "ollama_chat/deepseek-r1:14b",
            "api_base": "http://localhost:11434", 
            "num_ctx": 32768,
        },
        "openai_gpt4": {
            "model_id": "gpt-4-turbo-preview",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "num_ctx": 32768,
        }
    }
    
    # 보고서 템플릿 설정
    REPORT_TEMPLATES = {
        "summary": {
            "short": ["요약", "주요 포인트"],
            "mid": ["요약", "주요 내용", "결론"],
            "long": ["요약", "상세 분석", "주요 내용", "결론 및 시사점"]
        },
        "detailed": {
            "short": ["개요", "핵심 내용"],
            "mid": ["개요", "상세 분석", "핵심 내용", "결론"],
            "long": ["개요", "상세 분석", "심층 분석", "핵심 내용", "결론 및 제언"]
        },
        "presentation": {
            "short": ["슬라이드 1: 개요", "슬라이드 2: 핵심 내용", "슬라이드 3: 결론"],
            "mid": ["개요", "주요 내용", "세부 분석", "결론", "질의응답"],
            "long": ["개요", "배경", "주요 내용", "세부 분석", "사례 연구", "결론", "향후 과제"]
        }
    }
    
    # 파일 크기 제한 (바이트)
    MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
    MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # OCR 설정
    TESSERACT_CONFIG = {
        "lang": "kor+eng",  # 한국어 + 영어
        "config": "--oem 3 --psm 6"  # OCR Engine Mode, Page Segmentation Mode
    }
    
    # 로깅 설정
    LOGGING_CONFIG = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": OUTPUT_DIR / "video2doc.log"
    }
    
    # 에이전트 설정
    AGENT_CONFIG = {
        "verbosity_level": 1,
        "max_steps": 20,
        "planning_interval": 5,
        "add_base_tools": True,
        "additional_authorized_imports": [
            "whisper", "markdownify", "PIL", 
            "pandas", "pptx", "docx", "fitz", "pathlib", 
            "subprocess", "json", "os", "requests"
        ]
    }
    
    @classmethod
    def get_model_config(cls, model_name: str = "default"):
        """지정된 모델 설정을 반환합니다."""
        if model_name == "default":
            return cls.DEFAULT_MODEL_CONFIG.copy()
        elif model_name in cls.ALTERNATIVE_MODELS:
            return cls.ALTERNATIVE_MODELS[model_name].copy()
        else:
            raise ValueError(f"알 수 없는 모델: {model_name}")
    
    @classmethod
    def get_report_structure(cls, report_type: str, length: str):
        """보고서 구조를 반환합니다."""
        if report_type in cls.REPORT_TEMPLATES:
            if length in cls.REPORT_TEMPLATES[report_type]:
                return cls.REPORT_TEMPLATES[report_type][length]
        
        # 기본 구조 반환
        return ["개요", "주요 내용", "결론"]
    
    @classmethod
    def is_supported_file(cls, file_path: str):
        """파일이 지원되는 형식인지 확인합니다."""
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        
        return (suffix in cls.SUPPORTED_VIDEO_FORMATS or
                suffix in cls.SUPPORTED_AUDIO_FORMATS or
                suffix in cls.SUPPORTED_DOC_FORMATS or
                suffix in cls.SUPPORTED_IMAGE_FORMATS)
    
    @classmethod
    def get_file_type(cls, file_path: str):
        """파일 유형을 반환합니다."""
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        
        if suffix in cls.SUPPORTED_VIDEO_FORMATS:
            return "video"
        elif suffix in cls.SUPPORTED_AUDIO_FORMATS:
            return "audio"
        elif suffix in cls.SUPPORTED_DOC_FORMATS:
            return "document"
        elif suffix in cls.SUPPORTED_IMAGE_FORMATS:
            return "image"
        else:
            return "unknown"


# 환경별 설정
class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    WHISPER_MODEL = "medium"  # 개발 시에는 더 빠른 모델 사용
    
    DEFAULT_MODEL_CONFIG = {
        "model_id": "ollama_chat/qwen3:custom",
        "api_base": "http://localhost:11434",
        "num_ctx": 8192,  # 개발 시에는 더 작은 컨텍스트
        "temperature": 0.7,
    }


class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False
    WHISPER_MODEL = "large-v3"  # 운영에서는 최고 품질 모델 사용
    
    DEFAULT_MODEL_CONFIG = {
        "model_id": "ollama_chat/qwen3:custom",
        "api_base": "http://localhost:11434",
        "num_ctx": 32768,  # 운영에서는 큰 컨텍스트 사용
        "temperature": 0.5,  # 더 일관된 출력
    }


# 환경에 따른 설정 선택
def get_config():
    """환경 변수에 따라 적절한 설정을 반환합니다."""
    env = os.getenv("VIDEO2DOC_ENV", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()


# 기본 설정 인스턴스
config = get_config()
