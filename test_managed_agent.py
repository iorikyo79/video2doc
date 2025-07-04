#!/usr/bin/env python3
"""
Video2Doc Managed Agent 테스트 스크립트
보고서 생성 에이전트가 별도 클래스로 분리되고 managed agent로 활용되는지 테스트
"""

import sys
import logging
from pathlib import Path

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from video2doc_agent import Video2DocAgent, ReportGenerationAgent
from config import config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_report_generation_agent():
    """ReportGenerationAgent 단독 테스트"""
    print("=" * 60)
    print("📝 ReportGenerationAgent 단독 테스트")
    print("=" * 60)
    
    try:
        # 보고서 생성 에이전트 초기화
        report_agent = ReportGenerationAgent()
        print("✅ ReportGenerationAgent 초기화 완료")
        
        # 테스트용 더미 컨텍스트 파일 생성
        test_context_file = config.OUTPUT_DIR / "test_context.md"
        test_context_content = """# 테스트 컨텍스트

## 동영상 스크립트
안녕하세요. 이것은 테스트용 스크립트입니다.
오늘은 AI와 머신러닝에 대해 이야기하겠습니다.

## 참조 자료
- AI 기술 동향
- 머신러닝 활용 사례
- 딥러닝 알고리즘 개요
"""
        
        with open(test_context_file, 'w', encoding='utf-8') as f:
            f.write(test_context_content)
        
        # 보고서 생성 테스트
        report_file = report_agent.generate_report(
            str(test_context_file),
            report_type="summary",
            length="short"
        )
        
        print(f"✅ 보고서 생성 완료: {report_file}")
        
        # 생성된 보고서 확인
        if Path(report_file).exists():
            print(f"✅ 보고서 파일 존재 확인: {Path(report_file).name}")
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📄 보고서 길이: {len(content)} 문자")
                print(f"📄 보고서 첫 100자: {content[:100]}...")
        else:
            print("❌ 보고서 파일이 생성되지 않음")
            
    except Exception as e:
        print(f"❌ ReportGenerationAgent 테스트 실패: {e}")
        logger.exception("상세 오류:")


def test_video2doc_agent_initialization():
    """Video2DocAgent 초기화 및 managed agent 등록 테스트"""
    print("\n" + "=" * 60)
    print("🤖 Video2DocAgent Managed Agent 등록 테스트")
    print("=" * 60)
    
    try:
        # Video2DocAgent 초기화
        agent = Video2DocAgent()
        print("✅ Video2DocAgent 초기화 완료")
        
        # managed agent 확인
        if hasattr(agent, 'report_agent'):
            print("✅ ReportGenerationAgent 인스턴스 확인")
            print(f"   - 타입: {type(agent.report_agent)}")
        else:
            print("❌ ReportGenerationAgent 인스턴스 없음")
        
        # CodeAgent의 managed_agents 확인
        if hasattr(agent.agent, 'managed_agents') and agent.agent.managed_agents:
            print(f"✅ Managed agents 등록 확인: {len(agent.agent.managed_agents)}개")
            for i, managed_agent in enumerate(agent.agent.managed_agents):
                print(f"   - Agent {i+1}: {managed_agent.name} - {managed_agent.description[:50]}...")
        else:
            print("❌ Managed agents 등록되지 않음")
        
        # 직접 managed agent 사용 테스트 (더미 컨텍스트 사용)
        test_context_file = config.OUTPUT_DIR / "test_context.md"
        if test_context_file.exists():
            direct_result = agent.generate_report_with_managed_agent(
                str(test_context_file),
                report_type="detailed",
                length="mid"
            )
            print(f"✅ Managed agent 직접 사용 성공: {Path(direct_result).name}")
        else:
            print("⚠️ 테스트 컨텍스트 파일 없음, 직접 사용 테스트 건너뜀")
            
    except Exception as e:
        print(f"❌ Video2DocAgent 테스트 실패: {e}")
        logger.exception("상세 오류:")


def test_architecture_summary():
    """아키텍처 요약 및 비교"""
    print("\n" + "=" * 60)
    print("🏗️ 아키텍처 요약")
    print("=" * 60)
    
    print("📊 리팩토링 결과:")
    print("1. ReportGenerationAgent:")
    print("   - 별도 클래스로 분리")
    print("   - 전문적인 보고서 생성 기능")
    print("   - 독립적으로 사용 가능")
    
    print("\n2. Video2DocAgent:")
    print("   - ReportGenerationAgent를 managed agent로 등록")
    print("   - 기존 tool 방식과 managed agent 방식 모두 지원")
    print("   - 더 유연하고 확장 가능한 구조")
    
    print("\n3. 장점:")
    print("   - 모듈화: 보고서 생성 로직 분리")
    print("   - 재사용성: ReportGenerationAgent 독립 사용")
    print("   - 확장성: 추가 전문 에이전트 쉽게 추가")
    print("   - 호환성: 기존 tool 방식도 유지")


def main():
    """메인 테스트 함수"""
    print("🚀 Video2Doc Managed Agent 리팩토링 테스트 시작")
    
    # 출력 디렉토리 확인
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 각 테스트 실행
    test_report_generation_agent()
    test_video2doc_agent_initialization()
    test_architecture_summary()
    
    print(f"\n📂 모든 출력은 다음 디렉토리에 저장됩니다: {config.OUTPUT_DIR}")
    print("🎉 테스트 완료!")


if __name__ == "__main__":
    main()
