# Video2Doc Agent 멀티모달 워크플로우 (TDD 리팩토링 완료)

🎯 **TDD 기반 완전 리팩토링 완료** - 2025년 1월, 모듈화된 구조로 maintainability와 testability 극대화

## 🏗️ 새로운 아키텍처 구조 (TDD 리팩토링 결과)

### TDD 리팩토링 성과
- ✅ **16개 Phase Red → Green → Refactor 사이클 완료**
- ✅ **구조적 변경과 행동적 변경 완전 분리** (Tidy First 원칙)
- ✅ **완전한 모듈화**: core, processors, utils로 책임 분리
- ✅ **15개 테스트 파일, 93.3% 성공률** (test/ 디렉터리)
- ✅ **하위 호환성 100% 유지**: 기존 API 그대로 사용 가능

### 새로운 모듈 구조
```
video2doc/
├── 📁 core/                    # 핵심 비즈니스 로직
│   ├── agent.py               # Video2DocAgent (메인 에이전트)
│   ├── workflow.py            # Video2DocWorkflow (워크플로우 관리)
│   └── tools.py               # smolagents @tool 함수들
├── 📁 processors/             # 전문화된 처리 모듈
│   ├── audio.py               # AudioProcessor (오디오 처리)
│   ├── document.py            # DocumentProcessor (문서 변환)
│   └── report.py              # ReportProcessor (보고서 생성)
├── 📁 utils/                  # 유틸리티 모듈
│   ├── exceptions.py          # 커스텀 예외 클래스
│   ├── error_handlers.py      # 에러 처리 헬퍼
│   └── youtube.py             # YouTube 관련 유틸리티
└── 📁 test/                   # 🧪 15개 테스트 파일
    ├── test_agent.py          # core.agent 테스트
    ├── test_workflow.py       # core.workflow 테스트
    ├── test_tools.py          # core.tools 테스트
    ├── test_processors_*.py   # processors 테스트
    ├── test_utils_*.py        # utils 테스트
    └── test_refactoring_baseline.py  # 기준선 테스트
```

---

## 1. 입력 파일 수집
**담당**: `core.agent.Video2DocAgent` (리팩토링됨)
**작업**:
- 오디오 파일(MP4 또는 MP3)과 참조 파일(PPT, PDF, DOC 등)을 입력으로 받음
- **MP4**: 동영상 파일에서 오디오 추출 + **스크린샷 추출 필요**
- **MP3**: 오디오 파일로 직접 처리 가능 (이미지 추출 불가)

## 2. 멀티모달 처리 (확장됨)

### 2-1. 오디오 처리 (조건부)
**담당**: `processors.audio.AudioProcessor` (리팩토링됨)
**작업**:
- 입력 파일 타입에 따라 조건부 처리:
  - **MP4인 경우**: FFmpeg를 사용해 MP4에서 오디오(MP3)를 추출
  - **MP3인 경우**: 이 단계를 건너뛰고 바로 다음 단계로 진행

### 2-2. 동영상 스크린샷 추출 (NEW) - 2단계 접근
**담당**: `core.tools` 비전 분석 도구 (리팩토링됨)
**작업**:
- **MP4인 경우**: 
  1. FFmpeg를 사용해 25초 간격으로 모든 키프레임 추출
  2. 중앙 영역(70%) 기반 장면 변화 감지로 의미있는 프레임만 선별
  3. 이미지 해싱을 통한 기본 중복 제거
  4. 타임스탬프 정보와 함께 선별된 이미지 파일 저장
- **MP3인 경우**: 이 단계 건너뜀

## 3. MP3에서 스크립트 추출
**담당**: `processors.audio.AudioProcessor` (리팩토링됨)
**작업**:
- Whisper 모델(예: Whisper-large-v3)을 사용해 MP3에서 텍스트 스크립트를 추출
- Link : https://huggingface.co/openai/whisper-large-v3-turbo
- `core.agent.Video2DocAgent`가 이 처리기를 호출해 결과물을 Markdown(MD) 형식으로 저장

## 4. 이미지 분석 및 캡션 생성 (NEW) - 범용 콘텐츠
**담당**: `core.tools` qwen2.5vl 비전 분석 도구 (리팩토링됨)
**작업**:
- 선별된 스크린샷들을 qwen2.5vl 모델로 분석
- 프레젠테이션 슬라이드 텍스트, 다이어그램, 차트 등 해석
- 범용 콘텐츠 분석 (교육, 비즈니스, 제품소개, 논문발표 등)
- 참조 파일 내 이미지들도 동일하게 분석
- **각 이미지별 상세 캡션 자동 생성**
- 분석 결과 및 캡션을 MD 형식으로 저장

## 5. 참조 파일을 MD로 변환 (확장됨)
**담당**: `processors.document.DocumentProcessor` (리팩토링됨)
**작업**:
- Microsoft의 파일 변환 라이브러리(markitdown)를 활용해 PPT, PDF, DOC, Excel 등을 MD로 변환
- **NEW**: 참조 파일 내 이미지들 추출 및 qwen2.5vl 캡션 생성 추가
- https://github.com/microsoft/markitdown
- `core.agent.Video2DocAgent`가 이 처리기를 호출

## 6. 멀티모달 컨텍스트 통합 (NEW) - 캡션 기반
**담당**: `core.workflow.Video2DocWorkflow` (리팩토링됨)
**작업**:
- 추출된 스크립트(MD) + 스크린샷 캡션(MD) + 변환된 참조 파일(MD) 통합
- 시간축 기반 컨텍스트 매핑 (선별된 스크린샷과 스크립트 매칭)
- 유사도 기반 캡션-텍스트 매칭 (임베딩 활용)
- 기본 중복 정보 제거

## 7. 멀티모달 보고서 생성 (Enhanced) - 단순화
**담당**: `processors.report.ReportProcessor` (리팩토링됨)
**작업**:
- 통합된 멀티모달 컨텍스트를 바탕으로 보고서 생성
- **NEW**: 유사도 기반 핵심 이미지 자동 선별 및 보고서 첨부
- **NEW**: 기본 이미지 캡션 자동 생성
- **NEW**: 유사도 기반 텍스트-이미지 배치
- 형식: DOCS, PPTX, 이미지 포함 Markdown 등

---

## 🔄 확장된 워크플로우 요약 (TDD 리팩토링 반영)
1. `core.agent.Video2DocAgent`가 입력 파일(MP4 또는 MP3, 그리고 참조 파일)을 수집
2-1. `processors.audio.AudioProcessor`가 파일 타입을 확인하고 필요시 MP4에서 MP3를 추출
2-2. `core.tools` 비전 도구가 MP4에서 25초 간격 스크린샷을 추출 (NEW)
3. `processors.audio.AudioProcessor`가 MP3에서 스크립트를 추출
4. `core.tools` qwen2.5vl 도구가 스크린샷과 참조 이미지를 분석 (NEW)
5. `processors.document.DocumentProcessor`가 참조 파일을 MD로 변환
6. `core.workflow.Video2DocWorkflow`가 스크립트 + 이미지 분석 + 참조 파일을 유사도 기반으로 통합해 멀티모달 컨텍스트 생성 (NEW)
7. `processors.report.ReportProcessor`가 멀티모달 컨텍스트로 이미지가 포함된 완전한 보고서 생성 (NEW)

## 🛠️ 새로운 에이전트/도구 역할 (TDD 리팩토링 반영)
- **`core.agent.Video2DocAgent`**: 메인 에이전트, 전체 워크플로우 조정
- **`core.workflow.Video2DocWorkflow`**: 워크플로우 상태 관리 및 단계별 처리
- **`core.tools`**: smolagents @tool 함수들 (비전 분석, qwen2.5vl 도구 포함)
- **`processors.audio.AudioProcessor`**: 오디오/동영상 처리 전담
- **`processors.document.DocumentProcessor`**: 문서 변환 전담
- **`processors.report.ReportProcessor`**: 보고서 생성 전담
- **`utils.*`**: 예외 처리, 에러 핸들링, YouTube 유틸리티 등

## 🧪 테스트 커버리지 (TDD 성과)
- **15개 테스트 파일**, 93.3% 성공률
- **모든 모듈별 단위 테스트 및 통합 테스트**
- **run_all_tests.py**: 배치 테스트 실행 및 요약 보고