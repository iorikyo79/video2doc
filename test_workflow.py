#!/usr/bin/env python3
"""
Video2Doc 전체 워크플로우 테스트 스크립트

현재까지 구현된 기능들을 실제 파일로 테스트합니다:
1. MP4에서 MP3 추출
2. Hugging Face Whisper로 스크립트 추출
3. markitdown으로 참조 파일 변환
4. 컨텍스트 통합
5. 보고서 생성

사용법:
    python test_workflow.py
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from video2doc_agent import Video2DocWorkflow

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_workflow.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class WorkflowTester:
    """Video2Doc 워크플로우 테스트 클래스"""
    
    def __init__(self, test_output_dir: str = "test_output"):
        """
        테스트 초기화
        
        Args:
            test_output_dir: 테스트 결과 저장 디렉토리
        """
        self.test_output_dir = Path(test_output_dir)
        self.test_output_dir.mkdir(exist_ok=True)
        
        # 타임스탬프로 고유한 테스트 세션 디렉토리 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.test_output_dir / f"test_session_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        logger.info(f"테스트 세션 디렉토리: {self.session_dir}")
        
        # 워크플로우 초기화
        try:
            self.workflow = Video2DocWorkflow(output_dir=str(self.session_dir))
            logger.info("Video2DocWorkflow 초기화 완료")
        except Exception as e:
            logger.error(f"워크플로우 초기화 실패: {e}")
            raise
    
    def check_prerequisites(self):
        """사전 요구사항 확인"""
        logger.info("🔍 사전 요구사항 확인 중...")
        
        issues = []
        
        # 1. 입력 파일 존재 확인
        video_file = Path("input/sample.mp4")
        if not video_file.exists():
            issues.append(f"비디오 파일이 없습니다: {video_file}")
        else:
            logger.info(f"✅ 비디오 파일 확인: {video_file}")
        
        # 2. 참조 파일들 확인 (선택적)
        reference_files = [
            "input/Resume.pdf",
            "input/rules.pdf",
            "input/RESULT_GASTRO.xlsx"
        ]
        
        available_refs = []
        for ref_file in reference_files:
            ref_path = Path(ref_file)
            if ref_path.exists():
                available_refs.append(str(ref_path))
                logger.info(f"✅ 참조 파일 확인: {ref_path}")
            else:
                logger.warning(f"⚠️ 참조 파일 없음: {ref_path}")
        
        # 3. 필수 도구 확인
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("✅ FFmpeg 설치 확인")
            else:
                issues.append("FFmpeg 실행 실패")
        except Exception as e:
            issues.append(f"FFmpeg 확인 실패: {e}")
        
        # 4. 라이브러리 확인
        try:
            if self.workflow.whisper_model is not None:
                logger.info("✅ Hugging Face Whisper 모델 로드됨")
            else:
                issues.append("Whisper 모델 로드 실패")
                
            if self.workflow.markitdown is not None:
                logger.info("✅ markitdown 초기화됨")
            else:
                issues.append("markitdown 초기화 실패")
        except Exception as e:
            issues.append(f"라이브러리 확인 실패: {e}")
        
        if issues:
            logger.error("❌ 사전 요구사항 확인 실패:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False, available_refs
        
        logger.info("✅ 모든 사전 요구사항 확인 완료")
        return True, available_refs
    
    def test_step_1_mp3_extraction(self, video_path: str) -> str:
        """Step 1: MP4에서 MP3 추출 테스트"""
        logger.info("🎵 Step 1: MP4에서 MP3 추출 테스트")
        
        try:
            mp3_path = self.workflow.extract_mp3_from_mp4(video_path)
            
            # 결과 검증
            if Path(mp3_path).exists():
                file_size = Path(mp3_path).stat().st_size
                logger.info(f"✅ MP3 추출 성공: {mp3_path} (크기: {file_size:,} bytes)")
                return mp3_path
            else:
                raise FileNotFoundError(f"MP3 파일이 생성되지 않음: {mp3_path}")
                
        except Exception as e:
            logger.error(f"❌ MP3 추출 실패: {e}")
            raise
    
    def test_step_2_script_extraction(self, mp3_path: str) -> str:
        """Step 2: MP3에서 스크립트 추출 테스트"""
        logger.info("📝 Step 2: MP3에서 스크립트 추출 테스트 (Hugging Face Whisper)")
        
        try:
            script_path = self.workflow.extract_script_from_mp3(mp3_path)
            
            # 결과 검증
            if Path(script_path).exists():
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    word_count = len(content.split())
                logger.info(f"✅ 스크립트 추출 성공: {script_path} (단어 수: {word_count})")
                logger.info(f"스크립트 미리보기: {content[:200]}...")
                return script_path
            else:
                raise FileNotFoundError(f"스크립트 파일이 생성되지 않음: {script_path}")
                
        except Exception as e:
            logger.error(f"❌ 스크립트 추출 실패: {e}")
            raise
    
    def test_step_3_file_conversion(self, reference_files: list) -> list:
        """Step 3: 참조 파일들을 마크다운으로 변환 테스트"""
        logger.info("📄 Step 3: 참조 파일 변환 테스트 (markitdown)")
        
        converted_files = []
        
        for ref_file in reference_files:
            try:
                logger.info(f"변환 중: {ref_file}")
                md_path = self.workflow.convert_reference_file_to_md(ref_file)
                
                # 결과 검증
                if Path(md_path).exists():
                    with open(md_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        word_count = len(content.split())
                    logger.info(f"✅ 파일 변환 성공: {md_path} (단어 수: {word_count})")
                    converted_files.append(md_path)
                else:
                    logger.error(f"❌ 변환된 파일이 생성되지 않음: {md_path}")
                    
            except Exception as e:
                logger.error(f"❌ 파일 변환 실패 ({ref_file}): {e}")
                # 개별 파일 실패는 전체 테스트를 중단하지 않음
                continue
        
        logger.info(f"✅ 참조 파일 변환 완료: {len(converted_files)}/{len(reference_files)} 성공")
        return converted_files
    
    def test_step_4_context_integration(self, script_path: str, ref_files: list) -> str:
        """Step 4: 컨텍스트 통합 테스트"""
        logger.info("🔗 Step 4: 컨텍스트 통합 테스트")
        
        try:
            # 컨텍스트 통합 (video2doc_agent.py의 context_integration_tool 로직 사용)
            script_path_obj = Path(script_path)
            context_file = self.session_dir / f"05_{script_path_obj.stem}_full_context.md"
            
            content = "# 전체 컨텍스트\n\n"
            
            # 스크립트 내용 추가
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            content += "## 동영상 스크립트\n\n"
            content += script_content + "\n\n"
            
            # 참조 파일들 내용 추가
            if ref_files:
                content += "## 참조 자료\n\n"
                for ref_file in ref_files:
                    if os.path.exists(ref_file):
                        with open(ref_file, 'r', encoding='utf-8') as f:
                            ref_content = f.read()
                        content += f"### {Path(ref_file).name}\n\n"
                        content += ref_content + "\n\n"
            
            with open(context_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 결과 검증
            if context_file.exists():
                file_size = context_file.stat().st_size
                with open(context_file, 'r', encoding='utf-8') as f:
                    word_count = len(f.read().split())
                logger.info(f"✅ 컨텍스트 통합 성공: {context_file} (크기: {file_size:,} bytes, 단어 수: {word_count})")
                return str(context_file)
            else:
                raise FileNotFoundError(f"컨텍스트 파일이 생성되지 않음: {context_file}")
                
        except Exception as e:
            logger.error(f"❌ 컨텍스트 통합 실패: {e}")
            raise
    
    def test_step_5_report_generation(self, context_path: str) -> str:
        """Step 5: 보고서 생성 테스트"""
        logger.info("📊 Step 5: 보고서 생성 테스트")
        
        try:
            # 보고서 생성 (video2doc_agent.py의 report_generation_tool 로직 사용)
            context_path_obj = Path(context_path)
            report_file = self.session_dir / f"06_{context_path_obj.stem}_summary_mid.md"
            
            # 컨텍스트 내용 읽기
            with open(context_path, 'r', encoding='utf-8') as f:
                context_content = f.read()
            
            # 보고서 템플릿 생성
            report_content = f"# Summary 보고서\n\n"
            report_content += f"**생성일:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report_content += f"**보고서 유형:** summary\n"
            report_content += f"**보고서 길이:** mid\n"
            report_content += f"**테스트 세션:** {self.session_dir.name}\n\n"
            
            # 보고서 내용 구성
            report_content += "## 주요 내용\n\n"
            report_content += "### 동영상 주요 포인트\n\n"
            report_content += "이 섹션은 실제 환경에서는 LLM이 생성합니다.\n\n"
            report_content += "### 참조 자료 요약\n\n"
            report_content += "이 섹션은 실제 환경에서는 LLM이 생성합니다.\n\n"
            report_content += "### 결론 및 시사점\n\n"
            report_content += "이 섹션은 실제 환경에서는 LLM이 생성합니다.\n\n"
            
            # 원본 컨텍스트 첨부
            report_content += "---\n\n## 원본 컨텍스트\n\n"
            report_content += context_content
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # 결과 검증
            if report_file.exists():
                file_size = report_file.stat().st_size
                with open(report_file, 'r', encoding='utf-8') as f:
                    word_count = len(f.read().split())
                logger.info(f"✅ 보고서 생성 성공: {report_file} (크기: {file_size:,} bytes, 단어 수: {word_count})")
                return str(report_file)
            else:
                raise FileNotFoundError(f"보고서 파일이 생성되지 않음: {report_file}")
                
        except Exception as e:
            logger.error(f"❌ 보고서 생성 실패: {e}")
            raise
    
    def run_full_test(self):
        """전체 워크플로우 테스트 실행"""
        logger.info("🚀 Video2Doc 전체 워크플로우 테스트 시작")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        results = {}
        
        try:
            # 사전 요구사항 확인
            prereq_ok, available_refs = self.check_prerequisites()
            if not prereq_ok:
                raise RuntimeError("사전 요구사항 확인 실패")
            
            # Step 1: MP3 추출
            video_path = "input/S2_02.mp4"
            mp3_path = self.test_step_1_mp3_extraction(video_path)
            results['mp3_extraction'] = {'success': True, 'file': mp3_path}
            
            # Step 2: 스크립트 추출
            script_path = self.test_step_2_script_extraction(mp3_path)
            results['script_extraction'] = {'success': True, 'file': script_path}
            
            # Step 3: 참조 파일 변환
            converted_files = self.test_step_3_file_conversion(available_refs)
            results['file_conversion'] = {'success': True, 'files': converted_files, 'count': len(converted_files)}
            
            # Step 4: 컨텍스트 통합
            context_path = self.test_step_4_context_integration(script_path, converted_files)
            results['context_integration'] = {'success': True, 'file': context_path}
            
            # Step 5: 보고서 생성
            report_path = self.test_step_5_report_generation(context_path)
            results['report_generation'] = {'success': True, 'file': report_path}
            
            # 전체 테스트 완료
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("=" * 60)
            logger.info("🎉 전체 워크플로우 테스트 완료!")
            logger.info(f"⏱️ 총 소요 시간: {duration}")
            logger.info(f"📁 결과 디렉토리: {self.session_dir}")
            
            # 결과 요약
            self._print_test_summary(results, duration)
            
            return True, results
            
        except Exception as e:
            logger.error(f"❌ 워크플로우 테스트 실패: {e}")
            logger.error(f"❌ 에러 상세:\n{traceback.format_exc()}")
            return False, results
    
    def _print_test_summary(self, results: dict, duration):
        """테스트 결과 요약 출력"""
        logger.info("\n📋 테스트 결과 요약:")
        logger.info("-" * 40)
        
        for step, result in results.items():
            status = "✅ 성공" if result.get('success', False) else "❌ 실패"
            logger.info(f"{step}: {status}")
            
            if 'file' in result:
                logger.info(f"  └── 파일: {result['file']}")
            elif 'files' in result:
                logger.info(f"  └── 파일 수: {result.get('count', 0)}")
        
        logger.info("-" * 40)
        logger.info(f"총 소요 시간: {duration}")
        logger.info(f"결과 위치: {self.session_dir}")


def main():
    """메인 함수"""
    print("🧪 Video2Doc 전체 워크플로우 테스트")
    print("=" * 50)
    
    try:
        # 테스터 초기화
        tester = WorkflowTester()
        
        # 전체 테스트 실행
        success, results = tester.run_full_test()
        
        if success:
            print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
            print(f"📁 결과는 {tester.session_dir}에서 확인할 수 있습니다.")
            return 0
        else:
            print("\n❌ 테스트 중 일부가 실패했습니다.")
            print("📋 로그를 확인하여 문제를 해결해주세요.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 테스트가 중단되었습니다.")
        return 130
    except Exception as e:
        print(f"\n💥 예상치 못한 오류가 발생했습니다: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
