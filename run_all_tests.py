#!/usr/bin/env python3
"""
Video2Doc 프로젝트 전체 테스트 실행 스크립트

test/ 디렉토리에 있는 모든 테스트 파일을 순차적으로 실행하고
결과를 취합하여 보고서를 생성합니다.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Dict

def get_test_files() -> List[Path]:
    """test 디렉토리에서 모든 테스트 파일 찾기"""
    test_dir = Path("test")
    if not test_dir.exists():
        print("❌ test 디렉토리가 존재하지 않습니다.")
        return []
    
    test_files = list(test_dir.glob("test_*.py"))
    test_files.sort()  # 파일명 순으로 정렬
    return test_files

def run_single_test(test_file: Path) -> Tuple[bool, str, float]:
    """단일 테스트 파일 실행"""
    print(f"🧪 {test_file.name} 실행 중...", end=" ")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=120  # 2분 타임아웃
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ ({duration:.2f}s)")
            return True, result.stdout, duration
        else:
            print(f"❌ ({duration:.2f}s)")
            return False, result.stderr or result.stdout, duration
            
    except subprocess.TimeoutExpired:
        print("⏰ (타임아웃)")
        return False, "테스트 실행 시간 초과 (2분)", 120.0
    except Exception as e:
        print(f"🔥 (에러)")
        return False, f"실행 중 예외 발생: {e}", 0.0

def print_summary(results: Dict[str, Tuple[bool, str, float]]):
    """테스트 결과 요약 출력"""
    total_tests = len(results)
    passed_tests = sum(1 for success, _, _ in results.values() if success)
    failed_tests = total_tests - passed_tests
    total_time = sum(duration for _, _, duration in results.values())
    
    print("\n" + "="*80)
    print(f"📊 테스트 결과 요약")
    print("="*80)
    print(f"총 테스트 파일: {total_tests}개")
    print(f"성공: {passed_tests}개 ✅")
    print(f"실패: {failed_tests}개 ❌")
    print(f"총 실행 시간: {total_time:.2f}초")
    print(f"성공률: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print(f"\n❌ 실패한 테스트들:")
        for test_name, (success, output, duration) in results.items():
            if not success:
                print(f"  • {test_name} ({duration:.2f}s)")
                # 에러 메시지의 첫 줄만 표시
                first_line = output.split('\n')[0] if output else "알 수 없는 오류"
                print(f"    └─ {first_line[:80]}...")
    
    print("\n" + "="*80)

def print_detailed_failures(results: Dict[str, Tuple[bool, str, float]]):
    """실패한 테스트들의 상세 정보 출력"""
    failed_tests = {name: (success, output, duration) 
                   for name, (success, output, duration) in results.items() 
                   if not success}
    
    if not failed_tests:
        return
    
    print("\n🔍 실패 상세 정보:")
    print("="*80)
    
    for test_name, (_, output, duration) in failed_tests.items():
        print(f"\n❌ {test_name} ({duration:.2f}s)")
        print("-" * 60)
        # 출력을 적절히 잘라서 표시
        lines = output.split('\n')
        for i, line in enumerate(lines[:20]):  # 최대 20줄만 표시
            print(f"   {line}")
        if len(lines) > 20:
            print(f"   ... ({len(lines) - 20}줄 더 있음)")
        print()

def main():
    """메인 실행 함수"""
    print("🚀 Video2Doc 전체 테스트 실행 시작")
    print("="*80)
    
    # 테스트 파일 목록 가져오기
    test_files = get_test_files()
    
    if not test_files:
        print("❌ 실행할 테스트 파일이 없습니다.")
        return 1
    
    print(f"📁 {len(test_files)}개의 테스트 파일 발견")
    print()
    
    # 각 테스트 파일 실행
    results = {}
    for test_file in test_files:
        success, output, duration = run_single_test(test_file)
        results[test_file.name] = (success, output, duration)
    
    # 결과 요약 출력
    print_summary(results)
    
    # 상세 실패 정보 출력 (선택적)
    failed_count = sum(1 for success, _, _ in results.values() if not success)
    if failed_count > 0:
        response = input(f"\n실패한 {failed_count}개 테스트의 상세 정보를 보시겠습니까? (y/N): ")
        if response.lower() in ['y', 'yes']:
            print_detailed_failures(results)
    
    # 종료 코드 반환
    all_passed = all(success for success, _, _ in results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  사용자에 의해 테스트 실행이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n🔥 예상치 못한 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
