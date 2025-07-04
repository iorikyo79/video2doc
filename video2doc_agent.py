"""
Video2Doc Agent System using smolagents
오디오 파일(MP4/MP3)과 참조 파일을 입력받아 문서를 생성하는 에이전트 시스템

워크플로우:
1. [MP4인 경우] MP4에서 MP3 추출 (MP3인 경우 이 단계 건너뛰기)
2. MP3에서 스크립트 추출 (Hugging Face Whisper)
3. 참조 파일을 MD로 변환 (markitdown)
4. 컨텍스트 통합
5. 보고서 생성

지원 형식:
- 오디오: MP4, MP3
- 참조 문서: PPTX, PDF, DOCX, XLSX, 이미지 등
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import subprocess
import tempfile
import json

from smolagents import CodeAgent, LiteLLMModel, tool, ChatMessage, MessageRole
# import whisper  # Legacy - replaced by Hugging Face transformers
from transformers import pipeline
import torch
from markitdown import MarkItDown  # Microsoft's unified document converter
from markdownify import markdownify
import requests
from PIL import Image
import pandas as pd
# Legacy document processing imports (kept for fallback)
from pptx import Presentation  # Legacy - replaced by markitdown
from config import config


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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
            raise
    
    def extract_script_from_mp3(self, mp3_path: str) -> str:
        """MP3에서 스크립트 추출 (Hugging Face Whisper 사용)"""
        mp3_file = Path(mp3_path)
        text_only_file = self.output_dir / f"03_{mp3_file.stem}_script_text.md"
        timestamp_file = self.output_dir / f"03_{mp3_file.stem}_script_timestamp.md"
        
        try:
            if self.whisper_model is None:
                raise RuntimeError("Hugging Face Whisper 모델이 로드되지 않음")
            
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
            raise
    
    def convert_pptx_to_md(self, pptx_path: str) -> str:
        """PPTX를 마크다운으로 변환 (레거시 방식 - markitdown 실패 시 사용)"""
        pptx_file = Path(pptx_path)
        md_file = self.output_dir / f"04_{pptx_file.stem}_ref.md"
        
        try:
            prs = Presentation(pptx_path)
            content = f"# {pptx_file.name} 내용\n\n"
            
            for slide_num, slide in enumerate(prs.slides, 1):
                content += f"## 슬라이드 {slide_num}\n\n"
                
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        content += f"{shape.text}\n\n"
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"PPTX 변환 완료: {md_file}")
            return str(md_file)
            
        except Exception as e:
            logger.error(f"PPTX 변환 실패: {e}")
            raise
    
    def convert_image_to_md(self, image_path: str) -> str:
        """이미지를 마크다운으로 변환 (markitdown 실패 시 기본 정보만 제공)"""
        image_file = Path(image_path)
        md_file = self.output_dir / f"04_{image_file.stem}_ref.md"
        
        try:
            # 이미지 기본 정보 제공
            image = Image.open(image_path)
            width, height = image.size
            
            content = f"# {image_file.name} 이미지 정보\n\n"
            content += f"**이미지 파일:** {image_file.name}\n"
            content += f"**파일 형식:** {image_file.suffix.upper()}\n"
            content += f"**크기:** {width} x {height} pixels\n\n"
            content += f"## 참고\n\n"
            content += f"이미지 내용 분석을 위해서는 markitdown의 LLM 연동 기능을 사용하세요.\n\n"
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"이미지 정보 변환 완료: {md_file}")
            return str(md_file)
            
        except Exception as e:
            logger.error(f"이미지 정보 변환 실패: {e}")
            raise

    def convert_reference_file_to_md(self, file_path: str) -> str:
        """
        참조 파일을 마크다운으로 변환 (markitdown 통합 방식)
        
        Args:
            file_path: 변환할 파일 경로
            
        Returns:
            변환된 마크다운 파일 경로
        """
        input_file = Path(file_path)
        md_file = self.output_dir / f"04_{input_file.stem}_ref.md"
        
        try:
            if self.markitdown is None:
                logger.warning("markitdown이 초기화되지 않음, 레거시 방식으로 변환 시도")
                return self._convert_file_legacy(file_path)
            
            logger.info(f"markitdown으로 파일 변환 시작: {file_path}")
            
            # 이미지 파일인 경우 특별 처리 옵션 확인
            if input_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
                return self._convert_image_with_markitdown(file_path)
            
            # markitdown을 사용한 일반 문서 변환
            result = self.markitdown.convert(file_path)
            
            # 변환 결과를 마크다운 형식으로 저장
            content = f"# {input_file.name} 내용\n\n"
            content += f"**파일 형식:** {input_file.suffix.upper()}\n"
            content += f"**변환 도구:** markitdown (Microsoft)\n"
            content += f"**원본 파일:** {input_file.name}\n\n"
            content += "---\n\n"
            content += result.text_content
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"markitdown 변환 완료: {md_file}")
            return str(md_file)
            
        except Exception as e:
            logger.warning(f"markitdown 변환 실패: {e}, 레거시 방식으로 시도")
            try:
                return self._convert_file_legacy(file_path)
            except Exception as legacy_error:
                logger.error(f"레거시 변환도 실패: {legacy_error}")
                raise
    
    def _convert_image_with_markitdown(self, image_path: str) -> str:
        """
        이미지 파일을 markitdown을 사용하여 변환 (LLM 지원 고려)
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            변환된 마크다운 파일 경로
        """
        input_file = Path(image_path)
        md_file = self.output_dir / f"04_{input_file.stem}_ref.md"
        
        try:
            # markitdown으로 이미지 처리 시도 (LLM 연동 시 더 나은 결과)
            result = self.markitdown.convert(image_path)
            
            content = f"# {input_file.name} 이미지 분석\n\n"
            content += f"**파일 형식:** {input_file.suffix.upper()}\n"
            content += f"**변환 도구:** markitdown (Microsoft)\n"
            content += f"**원본 파일:** {input_file.name}\n\n"
            content += "## 이미지 내용 분석\n\n"
            content += result.text_content
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"markitdown 이미지 변환 완료: {md_file}")
            return str(md_file)
            
        except Exception as e:
            logger.warning(f"markitdown 이미지 변환 실패: {e}, 기본 이미지 정보로 대체")
            return self.convert_image_to_md(image_path)
    
    def _convert_file_legacy(self, file_path: str) -> str:
        """
        레거시 방식으로 파일 변환 (fallback)
        
        Args:
            file_path: 변환할 파일 경로
            
        Returns:
            변환된 마크다운 파일 경로
        """
        file_path_obj = Path(file_path)
        suffix = file_path_obj.suffix.lower()
        
        if suffix == '.pptx':
            return self.convert_pptx_to_md(file_path)
        elif suffix in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
            return self.convert_image_to_md(file_path)
        elif suffix in ['.txt', '.md']:
            # 텍스트 파일은 단순 복사
            return self._convert_text_file(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {suffix}")
    
    def _convert_text_file(self, text_path: str) -> str:
        """
        텍스트 파일을 마크다운으로 변환 (단순 복사)
        
        Args:
            text_path: 텍스트 파일 경로
            
        Returns:
            변환된 마크다운 파일 경로
        """
        text_file = Path(text_path)
        md_file = self.output_dir / f"04_{text_file.stem}_ref.md"
        
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 마크다운 헤더 추가
            md_content = f"# {text_file.name} 내용\n\n"
            md_content += f"**파일 형식:** {text_file.suffix.upper()}\n"
            md_content += f"**원본 파일:** {text_file.name}\n\n"
            md_content += "---\n\n"
            md_content += content
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.info(f"텍스트 파일 변환 완료: {md_file}")
            return str(md_file)
            
        except Exception as e:
            logger.error(f"텍스트 파일 변환 실패: {e}")
            raise


# smolagents 도구 정의
@tool
def mp3_extraction_tool(mp4_path: str) -> str:
    """
    MP4 파일에서 MP3 오디오를 추출합니다.
    
    Args:
        mp4_path: MP4 파일 경로
    
    Returns:
        추출된 MP3 파일 경로
    """
    workflow = Video2DocWorkflow()
    return workflow.extract_mp3_from_mp4(mp4_path)


@tool 
def script_extraction_tool(mp3_path: str) -> str:
    """
    MP3 파일에서 Hugging Face Whisper 모델을 사용하여 스크립트를 추출합니다.
    
    Args:
        mp3_path: MP3 파일 경로
    
    Returns:
        추출된 스크립트 마크다운 파일 경로
    """
    workflow = Video2DocWorkflow()
    return workflow.extract_script_from_mp3(mp3_path)


@tool
def file_conversion_tool(file_path: str) -> str:
    """
    참조 파일(PPTX, 이미지 등)을 markitdown을 사용하여 마크다운으로 변환합니다.
    
    Args:
        file_path: 변환할 파일 경로
    
    Returns:
        변환된 마크다운 파일 경로
    """
    workflow = Video2DocWorkflow()
    return workflow.convert_reference_file_to_md(file_path)


@tool
def context_integration_tool(script_file: str, ref_files: List[str]) -> str:
    """
    스크립트와 참조 파일들을 통합하여 전체 컨텍스트를 생성합니다.
    
    Args:
        script_file: 스크립트 마크다운 파일 경로 (타임스탬프 또는 텍스트만)
        ref_files: 참조 파일들의 마크다운 파일 경로 목록
    
    Returns:
        통합된 컨텍스트 마크다운 파일 경로
    """
    script_path = Path(script_file)
    output_dir = script_path.parent
    
    # 사용된 스크립트 파일 유형에 따라 컨텍스트 파일명 결정
    if "_timestamp" in script_path.name:
        context_file = output_dir / f"05_{script_path.stem}_full_context.md"
        script_type = "타임스탬프"
    else:
        context_file = output_dir / f"05_{script_path.stem}_full_context.md"
        script_type = "텍스트만"
    
    try:
        content = "# 전체 컨텍스트\n\n"
        content += f"**사용된 스크립트 유형:** {script_type}\n"
        content += f"**스크립트 파일:** {script_path.name}\n\n"
        
        # 스크립트 내용 추가
        with open(script_file, 'r', encoding='utf-8') as f:
            script_content = f.read()
        content += "## 동영상 스크립트\n\n"
        content += script_content + "\n\n"
        
        # 참조 파일들 내용 추가
        if ref_files:
            content += "## 참조 자료\n\n"
            for ref_file in ref_files:
                if Path(ref_file).exists():
                    with open(ref_file, 'r', encoding='utf-8') as f:
                        ref_content = f.read()
                    content += f"### {Path(ref_file).stem}\n\n"
                    content += ref_content + "\n\n"
        
        # 컨텍스트 파일 저장
        with open(context_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"컨텍스트 통합 완료: {context_file}")
        return str(context_file)
        
    except Exception as e:
        logger.error(f"컨텍스트 통합 실패: {e}")
        raise


@tool
def report_generation_tool(context_file: str, report_type: str = "summary", length: str = "mid") -> str:
    """
    통합된 컨텍스트를 바탕으로 LLM을 사용하여 보고서를 생성합니다.
    
    Args:
        context_file: 통합 컨텍스트 파일 경로
        report_type: 보고서 유형 ("summary", "detailed", "presentation")
        length: 보고서 길이 ("short", "mid", "long")
    
    Returns:
        생성된 보고서 마크다운 파일 경로
    """
    context_path = Path(context_file)
    output_dir = context_path.parent
    report_file = output_dir / f"06_{context_path.stem}_{report_type}_{length}.md"
    
    try:
        # 컨텍스트 내용 읽기
        with open(context_file, 'r', encoding='utf-8') as f:
            context_content = f.read()
        
        # config.py에서 보고서 구조 템플릿 가져오기
        report_structure = config.get_report_structure(report_type, length)
        structure_text = ", ".join(report_structure)
        
        # LLM 모델 초기화 (config.py 설정 사용)
        model_config = config.DEFAULT_MODEL_CONFIG.copy()
        model = LiteLLMModel(**model_config)

        
        # 페르소나와 보고서 생성 프롬프트 구성
        persona_prompt = _get_report_persona_prompt(report_type, length)
        system_prompt = f"""{persona_prompt}

당신의 임무는 제공된 동영상 스크립트와 참조 자료를 바탕으로 고품질의 {report_type} 보고서를 작성하는 것입니다.

보고서 요구사항:
- 보고서 유형: {report_type}
- 보고서 길이: {length}
- 구조: {structure_text}
- 형식: 마크다운 (.md)

보고서 작성 가이드라인:
1. 제공된 구조에 따라 섹션을 구성하세요
2. 동영상 스크립트의 핵심 내용을 정확히 파악하여 반영하세요
3. 참조 자료의 내용과 동영상 내용을 연결하여 분석하세요
4. 각 섹션은 논리적 흐름을 가져야 합니다
5. 마크다운 형식을 준수하여 가독성을 높이세요
6. 전문적이고 객관적인 어조를 유지하세요
7. 구체적인 예시와 데이터가 있다면 적극 활용하세요

응답은 완전한 마크다운 보고서 형태로 제공해주세요."""

        user_prompt = f"""다음 컨텍스트를 바탕으로 {report_type} 보고서({length} 길이)를 작성해주세요:

{context_content}

보고서 구조는 다음과 같이 구성해주세요:
{chr(10).join([f"## {section}" for section in report_structure])}

완전한 마크다운 형식의 보고서를 작성해주세요."""

        # LLM을 사용하여 보고서 생성
        logger.info(f"LLM을 사용하여 {report_type} 보고서 생성 중... (길이: {length})")
       
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=[{"type": "text", "text": system_prompt}]),
            ChatMessage(role=MessageRole.USER, content=[{"type": "text", "text": user_prompt}])
        ]
        # LLM 호출 (smolagents LiteLLMModel은 직접 호출 가능)
        response = model(messages)
        generated_report = response.content if hasattr(response, 'content') else str(response)
        
        # 보고서 메타데이터 헤더 추가
        final_report = f"""# {report_type.title()} 보고서

**생성일:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
**보고서 유형:** {report_type}
**보고서 길이:** {length}
**생성 모델:** {model_config['model_id']}

---

{generated_report}

---

## 메타데이터
- **사용된 템플릿 구조:** {structure_text}
- **원본 컨텍스트 파일:** {Path(context_file).name}
- **생성 시간:** {pd.Timestamp.now().isoformat()}
"""
        
        # 보고서 파일 저장
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(final_report)
        
        logger.info(f"LLM 기반 보고서 생성 완료: {report_file}")
        logger.info(f"사용된 모델: {model_config['model_id']}")
        logger.info(f"사용된 템플릿 구조: {report_structure}")
        return str(report_file)
        
    except Exception as e:
        logger.error(f"LLM 기반 보고서 생성 실패: {e}")
        # 실패 시 기본 템플릿 기반 보고서 생성 (fallback)
        logger.info("기본 템플릿 기반 보고서 생성으로 대체")
        return _generate_fallback_report(context_file, report_type, length, context_content)
        

def _get_report_persona_prompt(report_type: str, length: str) -> str:
    """
    보고서 유형과 길이에 따른 페르소나 프롬프트를 생성합니다.
    
    Args:
        report_type: 보고서 유형
        length: 보고서 길이
        
    Returns:
        페르소나 프롬프트 문자열
    """
    base_persona = """당신은 20년 경력의 전문 보고서 작성자이자 콘텐츠 분석 전문가입니다. 
다양한 분야의 동영상 콘텐츠와 문서를 분석하여 고품질의 보고서를 작성하는 것이 전문 분야입니다."""
    
    if report_type == "summary":
        persona = f"""{base_persona}
특히 복잡한 내용을 핵심만 추려서 명확하고 간결하게 요약하는 데 탁월한 능력을 가지고 있습니다.
주요 포인트를 놓치지 않으면서도 불필요한 세부사항은 제거하여 독자가 빠르게 핵심을 파악할 수 있도록 합니다."""
        
    elif report_type == "detailed":
        persona = f"""{base_persona}
심층적인 분석과 상세한 해석을 통해 포괄적인 보고서를 작성하는 것이 특기입니다.
복잡한 개념을 체계적으로 분해하고, 다각도에서 분석하여 독자에게 완전한 이해를 제공합니다."""
        
    elif report_type == "presentation":
        persona = f"""{base_persona}
프레젠테이션용 보고서 작성에 특화되어 있으며, 시각적 구성과 발표 흐름을 고려한 구조화된 내용을 만드는 데 전문성을 가지고 있습니다.
청중의 주의를 끌고 메시지를 효과적으로 전달할 수 있는 형태로 내용을 구성합니다."""
    
    # 길이별 추가 특성
    if length == "short":
        persona += "\n간결성과 효율성을 최우선으로 하여, 핵심 메시지만을 담은 압축적인 보고서를 작성합니다."
    elif length == "mid":
        persona += "\n적절한 상세도와 가독성의 균형을 맞춰, 실무진이 읽기에 최적화된 보고서를 작성합니다."
    elif length == "long":
        persona += "\n포괄적이고 깊이 있는 분석을 통해, 학술적이거나 전략적 의사결정에 활용할 수 있는 상세한 보고서를 작성합니다."
    
    return persona


def _generate_fallback_report(context_file: str, report_type: str, length: str, context_content: str) -> str:
    """
    LLM 실패 시 기본 템플릿 기반 보고서를 생성합니다 (fallback).
    
    Args:
        context_file: 컨텍스트 파일 경로
        report_type: 보고서 유형
        length: 보고서 길이
        context_content: 컨텍스트 내용
        
    Returns:
        생성된 보고서 파일 경로
    """
    try:
        context_path = Path(context_file)
        output_dir = context_path.parent
        report_file = output_dir / f"06_{context_path.stem}_{report_type}_{length}_fallback.md"
        
        # config.py에서 보고서 구조 템플릿 가져오기
        report_structure = config.get_report_structure(report_type, length)
        
        # 기본 템플릿 보고서 생성
        report_content = f"# {report_type.title()} 보고서 (기본 템플릿)\n\n"
        report_content += f"**생성일:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report_content += f"**보고서 유형:** {report_type}\n"
        report_content += f"**보고서 길이:** {length}\n"
        report_content += f"**생성 방식:** 기본 템플릿 (LLM 사용 실패로 인한 대체)\n\n"
        report_content += "---\n\n"
        
        # 기본 섹션 구조 생성
        for section in report_structure:
            report_content += f"## {section}\n\n"
            report_content += "<!-- 이 섹션은 LLM을 통해 자동 생성되어야 합니다. -->\n"
            report_content += "<!-- 원본 컨텍스트를 참고하여 수동으로 내용을 작성해주세요. -->\n\n"
        
        # 원본 컨텍스트 첨부
        report_content += "---\n\n"
        report_content += "## 원본 컨텍스트\n\n"
        report_content += "```\n"
        report_content += context_content
        report_content += "\n```\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"기본 템플릿 보고서 생성 완료: {report_file}")
        return str(report_file)
        
    except Exception as e:
        logger.error(f"기본 템플릿 보고서 생성도 실패: {e}")
        raise


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
    
    def _get_audio_file_type(self, audio_path: str) -> str:
        """
        오디오 파일의 타입을 확인합니다.
        
        Args:
            audio_path: 오디오 파일 경로
            
        Returns:
            파일 타입 ("mp4", "mp3", "unsupported")
        """
        audio_file = Path(audio_path)
        
        if not audio_file.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        
        suffix = audio_file.suffix.lower()
        
        if suffix == ".mp4":
            return "mp4"
        elif suffix == ".mp3":
            return "mp3"
        else:
            return "unsupported"
    
    def _is_supported_audio_format(self, audio_path: str) -> bool:
        """
        지원되는 오디오 형식인지 확인합니다.
        
        Args:
            audio_path: 오디오 파일 경로
            
        Returns:
            지원 여부
        """
        file_type = self._get_audio_file_type(audio_path)
        return file_type in ["mp4", "mp3"]
    
    def process_audio_and_references(self, 
                                   audio_path: str, 
                                   reference_files: Optional[List[str]] = None,
                                   report_type: str = "summary",
                                   length: str = "mid") -> Dict[str, str]:
        """
        오디오 파일(MP4/MP3)과 참조 파일들을 처리하여 보고서를 생성합니다.
        
        Args:
            audio_path: 오디오 파일 경로 (MP4 또는 MP3)
            reference_files: 참조 파일 목록 (PPTX, 이미지)
            report_type: 보고서 유형
            length: 보고서 길이
        
        Returns:
            처리 결과 딕셔너리 (각 단계별 파일 경로)
        """
        
        # 오디오 파일 타입 확인
        audio_file_type = self._get_audio_file_type(audio_path)
        
        if audio_file_type == "mp4":
            instruction = f"""
            다음 단계에 따라 Video2Doc 워크플로우를 실행하세요:
            
            1. MP4 파일에서 MP3 추출: {audio_path}
            2. MP3에서 스크립트 추출 (Whisper 사용)
            3. 참조 파일들을 마크다운으로 변환: {reference_files or []}
            4. 스크립트와 참조 파일들을 통합하여 통합 컨텍스트 생성
            5. 통합 컨텍스트 기반의 최종 보고서 생성 (유형: {report_type}, 길이: {length})
            
            각 단계가 완료되면 생성된 파일 경로를 반환하고 다음 단계로 진행하세요.
            """
        elif audio_file_type == "mp3":
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
            raise ValueError(f"지원하지 않는 오디오 파일 형식: {audio_file_type}. MP4 또는 MP3 파일만 지원됩니다.")
        
        try:
            result = self.agent.run(instruction)
            logger.info(f"Audio2Doc 워크플로우 완료 (입력: {audio_file_type.upper()})")
            return {"result": str(result), "input_type": audio_file_type}
            
        except Exception as e:
            logger.error(f"Audio2Doc 워크플로우 실행 실패: {e}")
            raise
    
    def process_video_and_references(self, 
                                   video_path: str, 
                                   reference_files: Optional[List[str]] = None,
                                   report_type: str = "summary",
                                   length: str = "mid") -> Dict[str, str]:
        """
        [DEPRECATED] 기존 메서드명 호환성을 위한 래퍼 메서드
        새 코드에서는 process_audio_and_references()를 사용하세요.
        
        Args:
            video_path: 비디오 파일 경로 (MP4)
            reference_files: 참조 파일 목록
            report_type: 보고서 유형
            length: 보고서 길이
        
        Returns:
            처리 결과 딕셔너리
        """
        logger.warning("process_video_and_references()는 deprecated입니다. process_audio_and_references()를 사용하세요.")
        return self.process_audio_and_references(
            audio_path=video_path,
            reference_files=reference_files,
            report_type=report_type,
            length=length
        )
    
    # ...existing code...


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
        # 오디오 파일 타입 확인
        audio_file_type = agent._get_audio_file_type(audio_path)
        print(f"\n� 오디오 파일 타입: {audio_file_type.upper()}")
        print(f"📁 오디오 파일: {Path(audio_path).name}")
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
