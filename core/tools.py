"""
Core Tools Module
smolagents @tool 데코레이터 함수들을 모아놓은 모듈
"""

import logging
from pathlib import Path
from typing import List

from smolagents import tool, LiteLLMModel, ChatMessage, MessageRole
from core.workflow import Video2DocWorkflow
from config import config

# 로깅 설정
logger = logging.getLogger(__name__)


@tool
def youtube_download_tool(youtube_url: str) -> str:
    """
    유튜브 비디오를 다운로드하고 MP4 파일 경로를 반환합니다.
    
    Args:
        youtube_url: 유튜브 비디오 URL
    
    Returns:
        다운로드된 MP4 파일 경로
    """
    workflow = Video2DocWorkflow()
    return workflow.download_youtube_video(youtube_url)


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

        
        # ReportProcessor를 통해 페르소나 프롬프트 생성
        workflow = Video2DocWorkflow()
        persona_prompt = workflow.report_processor.get_report_persona_prompt(report_type, length)
        system_prompt = f"""{persona_prompt}

당신은 제공된 동영상 스크립트를 분석하여, 전문적인 발표 요약 보고서를 작성하는 AI 전문가입니다.
주어진 스크립트에서 발표자, 발표의 핵심 주제, 그리고 가장 중요한 시사점을 추출하여 아래 형식에 맞춰 보고서를 작성해야 합니다.

**보고서 작성 형식:**

### [발표 제목]
스크립트의 핵심 주제를 나타내는 제목을 작성하세요.

**발표자:**
스크립트에서 언급된 발표자의 이름과 소속을 기입하세요.

**발표 소개:**
발표의 전체적인 내용을 요약하는 단락입니다. 다음 내용을 포함하여 구체적으로 서술하세요.
- 발표의 주요 목표 
- 다루는 핵심 개념 및 전략 (예: 정규화, 리플레이, 구조 확장 기반 접근법)
- 발표의 주요 대상 및 적용 분야 (예: 의료 AI)

**시사점:**
스크립트의 내용과 토론을 바탕으로, 청중이 얻을 수 있는 중요한 인사이트를 4가지 항목으로 정리하세요. 각 항목은 단순 요약이 아닌, 발표 내용이 가지는 의미와 중요성을 설명해야 합니다.
- **현실적인 AI 모델 배포의 과제:** 이론과 실제 적용의 차이, 현실 세계의 데이터 문제점 등을 중심으로 서술합니다.
- **다양한 해결 전략의 트레이드오프:** 제시된 해결책들의 장단점(메모리, 개인정보, 복잡도 등)을 비교 분석합니다.
- **특정 도메인(예: 의료)에서의 중요성:** 해당 기술이 특정 산업 분야에서 왜 중요하고 어떤 문제를 해결할 수 있는지 설명합니다.
- **미래 기술과의 연관성:** 파운데이션 모델 등 최신 기술 트렌드와 발표 내용이 어떻게 연결되는지 설명합니다.

**요구사항:**
- 모든 내용은 한글로 작성하고, 기술 용어(Keyword)는 영어를 병기할 수 있습니다.
- 마크다운 형식을 사용하되, 위에서 제시된 구조를 정확히 따라야 합니다.
- 스크립트에 없는 내용은 추측하여 작성하지 말고, 있는 사실에 기반하여 깊이 있게 분석하세요.

보고서 요구사항:
- 보고서 유형: {report_type}
- 보고서 길이: {length}
- 구조: {structure_text}
"""

        user_prompt = f"""다음 컨텍스트를 바탕으로 보고서를 작성해주세요:

{context_content}

요청사항:
- 보고서 유형: {report_type}
- 보고서 길이: {length}
- 마크다운 형식으로 작성
- 실제 내용을 바탕으로 구체적이고 실용적인 보고서를 작성
- 모든 내용은 한글로 작성하고 키워드는 영어 사용 허용"""


        # 모델에 메시지 전송
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=[{"type": "text", "text": system_prompt}]),
            ChatMessage(role=MessageRole.USER, content=[{"type": "text", "text": user_prompt}])
        ]
        
        response = model(messages)
        report_content = response.content if hasattr(response, 'content') else str(response)

        # 보고서 파일 저장
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"보고서 생성 완료: {report_file}")
        return str(report_file)
        
    except Exception as e:
        logger.error(f"보고서 생성 실패: {e}")
        # 오류 발생시 fallback 보고서 생성
        workflow = Video2DocWorkflow()
        fallback_report = workflow.report_processor.generate_fallback_report(
            context_file, report_type, length, str(report_file)
        )
        return fallback_report
