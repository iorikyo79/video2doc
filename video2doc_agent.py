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

# Video2DocAgent 클래스는 core.agent 모듈로 이동됨
from core.agent import Video2DocAgent, main

# 하위 호환성을 위해 main 함수를 여기서도 실행 가능하도록 함
if __name__ == "__main__":
    main()
