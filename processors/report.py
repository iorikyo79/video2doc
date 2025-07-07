"""
ReportProcessor 클래스 - 보고서 생성 관련 기능을 담당
"""

import logging
import pandas as pd
from pathlib import Path
from config import config

logger = logging.getLogger(__name__)


class ReportProcessor:
    """보고서 생성을 담당하는 클래스"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def get_report_persona_prompt(self, report_type: str, length: str) -> str:
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

    def generate_fallback_report(self, context_file: str, report_type: str, length: str, context_content: str) -> str:
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
