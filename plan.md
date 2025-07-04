Agent 워크플로우
1. 입력 파일 수집
담당: manager-agent (코드 에이전트)
작업:
오디오 파일(MP4 또는 MP3)과 참조 파일(PPT, PDF, DOC 등)을 입력으로 받음.
- MP4: 동영상 파일에서 오디오 추출 필요
- MP3: 오디오 파일로 직접 처리 가능
2. 오디오 처리 (조건부)
담당: 도구 (tool)
작업:
입력 파일 타입에 따라 조건부 처리:
- MP4인 경우: FFmpeg를 사용해 MP4에서 오디오(MP3)를 추출
- MP3인 경우: 이 단계를 건너뛰고 바로 다음 단계로 진행
manager-agent가 파일 타입을 확인하고 필요시 이 도구를 호출.
3. MP3에서 스크립트 추출
담당: 도구 (tool)
작업:
Whisper 모델(예: Whisper-large-v3)을 사용해 MP3에서 텍스트 스크립트를 추출.
Link : https://huggingface.co/openai/whisper-large-v3-turbo
manager-agent가 이 도구를 호출해 결과물을 Markdown(MD) 형식으로 저장.
4. 참조 파일을 MD로 변환
담당: 도구 (tool)
작업:
Microsoft의 파일 변환 라이브러리(markitdown)를 활용해 PPT, PDF, DOC, Excel 등을 MD로 변환.
https://github.com/microsoft/markitdown
manager-agent가 이 도구를 호출.
5. 컨텍스트 통합
담당: manager-agent
작업:
추출된 스크립트(MD)와 변환된 참조 파일(MD)들을 하나의 컨텍스트로 통합.
6. 보고서 생성
담당: manager-agent
작업:
통합된 컨텍스트를 바탕으로 보고서를 생성(형식은 DOCS 또는 PPTX 등으로 사용자 지정 가능).
워크플로우 요약
manager-agent가 입력 파일(MP4 또는 MP3, 그리고 참조 파일)을 수집.
manager-agent가 파일 타입을 확인하고 필요시 MP4에서 MP3를 추출하는 도구 호출.
manager-agent가 MP3에서 스크립트를 추출하는 도구 호출.
manager-agent가 참조 파일을 MD로 변환하는 도구 호출.
manager-agent가 스크립트와 참조 파일을 통합해 컨텍스트 생성.
manager-agent가 컨텍스트로 보고서 생성.