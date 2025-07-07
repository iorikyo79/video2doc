#!/bin/bash
# Video2Doc 워크플로우 테스트 실행 스크립트

echo "🧪 Video2Doc 워크플로우 테스트 준비"
echo "================================="

# 1. 필요한 디렉토리 생성
echo "📁 디렉토리 구조 확인..."
mkdir -p input
mkdir -p test_output

# 2. Python 가상환경 활성화 (선택적)
if [ -d ".venv" ]; then
    echo "🐍 Python 가상환경 활성화..."
    source .venv/bin/activate
fi

# 3. 입력 파일 확인
echo "📋 입력 파일 확인..."
if [ ! -f "input/sample.mp4" ]; then
    echo "⚠️ 경고: input/sample.mp4 파일이 없습니다."
    echo "   테스트를 위해 이 위치에 MP4 파일을 배치해주세요."
fi

# 참조 파일 확인
if [ -f "input/Resume.pdf" ]; then
    echo "✅ 참조 파일 확인: input/Resume.pdf"
else
    echo "ℹ️ 선택적 참조 파일: input/Resume.pdf (없어도 테스트 가능)"
fi

if [ -f "input/rules.pdf" ]; then
    echo "✅ 참조 파일 확인: input/rules.pdf"
else
    echo "ℹ️ 선택적 참조 파일: input/rules.pdf (없어도 테스트 가능)"
fi

if [ -f "input/RESULT_GASTRO.xlsx" ]; then
    echo "✅ 참조 파일 확인: input/RESULT_GASTRO.xlsx"
else
    echo "ℹ️ 선택적 참조 파일: input/RESULT_GASTRO.xlsx (없어도 테스트 가능)"
fi

# 4. 의존성 확인
echo "🔍 의존성 확인..."

# Python 모듈 확인
python3 -c "import transformers; print('✅ transformers')" 2>/dev/null || echo "❌ transformers 설치 필요: pip install transformers"
python3 -c "import torch; print('✅ torch')" 2>/dev/null || echo "❌ torch 설치 필요: pip install torch"
python3 -c "import markitdown; print('✅ markitdown')" 2>/dev/null || echo "❌ markitdown 설치 필요: pip install 'markitdown[all]'"

# FFmpeg 확인
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg"
else
    echo "❌ ffmpeg 설치 필요"
fi

echo ""
echo "🚀 테스트 시작..."
echo "================================="

# 5. 테스트 실행
python3 test_workflow.py

# 테스트 결과 확인
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 테스트 완료!"
    echo "📁 결과 파일들을 test_output 디렉토리에서 확인할 수 있습니다."
    
    # 최신 테스트 결과 디렉토리 찾기
    latest_dir=$(find test_output -name "test_session_*" -type d | sort | tail -1)
    if [ -n "$latest_dir" ]; then
        echo "📂 최신 테스트 결과: $latest_dir"
        echo "📋 생성된 파일들:"
        ls -la "$latest_dir"
    fi
else
    echo ""
    echo "❌ 테스트 실패"
    echo "📋 test_workflow.log 파일을 확인하여 문제를 해결해주세요."
fi
