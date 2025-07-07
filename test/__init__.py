"""Video2Doc 테스트 모듈

이 디렉토리는 Video2Doc 프로젝트의 모든 단위 테스트와 통합 테스트를 포함합니다.

테스트 구조:
- test_refactoring_baseline.py: 기준선 테스트
- test_*_*.py: 모듈별 단위 테스트
- test_agent.py: 에이전트 통합 테스트
- test_main_compatibility.py: 호환성 테스트
- test_entry_point.py: Entry point 테스트

실행 방법:
    # 모든 테스트 실행
    python -m pytest test/
    
    # 특정 테스트 파일 실행
    python -m pytest test/test_agent.py
    
    # 개별 테스트 실행
    python test/test_agent.py
"""
