"""
Video2Doc Frontend MVP - Streamlit Web Interface with Mock Data Support

간단하고 직관적인 웹 인터페이스로 Video2Doc 백엔드를 사용할 수 있습니다.
개발 단계에서는 Mock 데이터로 프론트엔드를 테스트할 수 있습니다.
"""

import streamlit as st
import os
import sys
import tempfile
import shutil
import threading
import time
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, Future
import requests
from urllib.parse import urlparse, parse_qs
import re
import random

# Mock 모드 설정 (개발용)
MOCK_MODE = st.sidebar.checkbox("🧪 Mock 모드 (개발용)", value=False, help="백엔드 없이 가짜 데이터로 테스트")

# 백엔드 모듈 import (Mock 모드가 아닐 때만)
if not MOCK_MODE:
    backend_path = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_path))

    try:
        from core.agent import Video2DocAgent
        from utils.youtube import is_youtube_url, extract_video_id_from_url
        from utils.exceptions import Video2DocError
        from config import config
    except ImportError as e:
        st.error(f"백엔드 모듈을 찾을 수 없습니다: {e}")
        st.error("Mock 모드를 사용하거나 backend 모듈을 설치해주세요.")
        st.stop()

# Mock 함수들
def mock_is_youtube_url(url: str) -> bool:
    """Mock YouTube URL 검증"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?youtu\.be/[\w-]+',
    ]
    for pattern in youtube_patterns:
        if re.match(pattern, url.strip()):
            return True
    return False

def mock_extract_video_id_from_url(url: str) -> str:
    """Mock YouTube 비디오 ID 추출"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return "dQw4w9WgXcQ"  # 기본 비디오 ID

class MockVideo2DocAgent:
    """Mock Video2Doc Agent for development"""
    
    def __init__(self, model_config=None):
        self.model_config = model_config or {"model_id": "mock_model"}
    
    def process_audio_and_references(self, audio_path: str, reference_files: List[str] = None,
                                   report_type: str = "summary", length: str = "mid") -> Dict[str, str]:
        """Mock 처리 함수"""
        # 가짜 처리 시간 시뮬레이션
        time.sleep(0.5)
        
        # Mock 결과 파일 생성
        output_dir = Path("mock_output")
        output_dir.mkdir(exist_ok=True)
        
        # 가짜 보고서 내용 생성
        mock_content = self._generate_mock_report(audio_path, reference_files, report_type, length)
        
        # 파일명 생성
        if mock_is_youtube_url(audio_path):
            video_id = mock_extract_video_id_from_url(audio_path)
            filename = f"06_youtube_{video_id}_{report_type}_{length}.md"
        else:
            base_name = Path(audio_path).stem if isinstance(audio_path, str) else "uploaded_file"
            filename = f"06_{base_name}_{report_type}_{length}.md"
        
        result_file = output_dir / filename
        
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(mock_content)
        
        return {"result": str(result_file), "input_type": "mock"}
    
    def _generate_mock_report(self, audio_path: str, reference_files: List[str], 
                            report_type: str, length: str) -> str:
        """Mock 보고서 내용 생성"""
        
        # 입력 타입 확인
        if mock_is_youtube_url(audio_path):
            video_id = mock_extract_video_id_from_url(audio_path)
            source_info = f"YouTube 비디오 (ID: {video_id})"
        else:
            source_info = f"업로드된 파일: {Path(audio_path).name if isinstance(audio_path, str) else '파일'}"
        
        # 보고서 길이에 따른 섹션 수
        section_counts = {"short": 2, "mid": 4, "long": 6}
        num_sections = section_counts.get(length, 4)
        
        # 보고서 유형별 제목
        type_titles = {
            "summary": "요약 보고서",
            "detailed": "상세 분석 보고서", 
            "presentation": "프레젠테이션 보고서"
        }
        
        content = f"""# {type_titles.get(report_type, "보고서")}

**생성일:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**소스:** {source_info}
**참조 파일 수:** {len(reference_files) if reference_files else 0}개
**보고서 유형:** {report_type}
**보고서 길이:** {length}
**생성 모드:** Mock 데이터 (개발용)

---

## 📋 개요

이것은 Mock 데이터로 생성된 샘플 보고서입니다. 실제 환경에서는 AI가 오디오 내용을 분석하여 구조화된 문서를 생성합니다.

"""

        # 동적 섹션 생성
        sample_sections = [
            ("🎯 핵심 내용", "주요 포인트들이 여기에 표시됩니다."),
            ("📊 상세 분석", "깊이 있는 분석 내용이 포함됩니다."),
            ("💡 주요 인사이트", "중요한 통찰과 발견사항들입니다."),
            ("🔍 기술적 세부사항", "기술적인 내용과 구현 방법들입니다."),
            ("📈 결과 및 성과", "달성된 결과와 성과 지표들입니다."),
            ("🚀 향후 계획", "앞으로의 방향성과 계획들입니다.")
        ]
        
        for i in range(min(num_sections, len(sample_sections))):
            title, desc = sample_sections[i]
            content += f"""
## {title}

{desc}

### 세부 내용
- 첫 번째 주요 포인트
- 두 번째 중요한 내용  
- 세 번째 핵심 사항

"""

        # 참조 파일 정보 추가
        if reference_files:
            content += """
## 📄 참조 자료 분석

다음 참조 자료들이 분석에 포함되었습니다:

"""
            for i, ref_file in enumerate(reference_files, 1):
                filename = Path(ref_file).name if isinstance(ref_file, str) else f"참조파일_{i}"
                content += f"- **{filename}**: 관련 내용이 보고서에 통합되었습니다.\n"

        content += """

---

## 🎉 결론

이 Mock 보고서는 Video2Doc의 출력 형식을 보여주는 샘플입니다. 
실제 사용 시에는 업로드된 오디오/비디오 내용을 기반으로 한 정확한 분석 결과가 제공됩니다.

**Mock 모드 특징:**
- ✅ 실제 UI/UX 플로우 테스트 가능
- ✅ 백엔드 의존성 없이 개발 가능
- ✅ 다양한 옵션 조합 테스트 가능
- ⚠️ 실제 콘텐츠 분석은 수행되지 않음

실제 기능을 사용하려면 Mock 모드를 비활성화하고 백엔드를 설정해주세요.
"""
        
        return content

# Mock 설정에 따른 함수 선택
if MOCK_MODE:
    Video2DocAgent = MockVideo2DocAgent
    is_youtube_url = mock_is_youtube_url
    extract_video_id_from_url = mock_extract_video_id_from_url
    Video2DocError = Exception
    
    # Mock config
    class MockConfig:
        def get_model_config(self, model_name):
            return {"model_id": f"mock_{model_name}"}
    
    config = MockConfig()

# Streamlit 페이지 설정
st.set_page_config(
    page_title="Video2Doc - 동영상/오디오 문서화 도구",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .mock-banner {
        background: linear-gradient(90deg, #ff9a56 0%, #ff6b6b 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: bold;
    }
    
    .step-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .info-box {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
def init_session_state():
    """세션 상태 변수들을 초기화합니다."""
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'progress' not in st.session_state:
        st.session_state.progress = 0
    if 'progress_text' not in st.session_state:
        st.session_state.progress_text = ""
    if 'result_file' not in st.session_state:
        st.session_state.result_file = None
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'youtube_info' not in st.session_state:
        st.session_state.youtube_info = None

def get_youtube_video_info(url: str) -> Optional[Dict[str, Any]]:
    """YouTube URL에서 비디오 정보를 가져옵니다."""
    try:
        if not is_youtube_url(url):
            return None
        
        video_id = extract_video_id_from_url(url)
        
        if MOCK_MODE:
            # Mock 데이터
            mock_titles = [
                "AI와 머신러닝의 미래",
                "Python 프로그래밍 마스터클래스",
                "데이터 사이언스 입문",
                "웹 개발 완전 정복",
                "클라우드 컴퓨팅 기초"
            ]
            return {
                'title': random.choice(mock_titles),
                'video_id': video_id,
                'url': url,
                'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
            }
        else:
            # 실제 구현에서는 yt-dlp 사용
            return {
                'title': f'YouTube Video ({video_id})',
                'video_id': video_id,
                'url': url,
                'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
            }
    except Exception as e:
        st.error(f"YouTube 정보 가져오기 실패: {e}")
        return None

def save_uploaded_file(uploaded_file, temp_dir: Path) -> str:
    """업로드된 파일을 임시 디렉토리에 저장합니다."""
    file_path = temp_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(file_path)

def mock_process_video2doc(audio_path: str, reference_files: List[str], 
                          report_type: str, length: str, model: str) -> str:
    """Mock 처리 함수 - 실제 백엔드 호출 시뮬레이션"""
    
    # 진행률 업데이트 함수
    def update_progress(progress: int, text: str):
        st.session_state.progress = progress
        st.session_state.progress_text = text
    
    try:
        update_progress(10, "🧪 Mock 에이전트 초기화 중...")
        time.sleep(0.5)
        
        update_progress(20, "📋 Mock 입력 파일 검증 중...")
        time.sleep(0.3)
        
        if is_youtube_url(audio_path):
            update_progress(30, "🔗 Mock YouTube 다운로드 시뮬레이션...")
            time.sleep(1.0)
            update_progress(50, "🎵 Mock 오디오 추출 중...")
        else:
            update_progress(40, "🎵 Mock 오디오 파일 처리 중...")
        
        time.sleep(0.8)
        update_progress(60, "🗣️ Mock 음성 인식 중...")
        time.sleep(1.2)
        
        update_progress(75, "📄 Mock 참조 문서 처리 중...")
        time.sleep(0.6)
        
        update_progress(85, "🤖 Mock AI 보고서 생성 중...")
        time.sleep(1.0)
        
        # Mock 에이전트로 처리
        agent = Video2DocAgent()
        result = agent.process_audio_and_references(
            audio_path=audio_path,
            reference_files=reference_files,
            report_type=report_type,
            length=length
        )
        
        update_progress(100, "✅ Mock 처리 완료!")
        return result["result"]
        
    except Exception as e:
        raise Exception(f"Mock 처리 중 오류 발생: {str(e)}")

def real_process_video2doc(audio_path: str, reference_files: List[str], 
                          report_type: str, length: str, model: str) -> str:
    """실제 백엔드 처리 함수"""
    
    # 진행률 업데이트 함수
    def update_progress(progress: int, text: str):
        st.session_state.progress = progress
        st.session_state.progress_text = text
    
    try:
        update_progress(10, "Video2Doc 에이전트 초기화 중...")
        
        # 모델 설정
        model_config = config.get_model_config(model)
        agent = Video2DocAgent(model_config=model_config)
        
        update_progress(20, "입력 파일 검증 중...")
        
        # YouTube URL인지 확인
        if is_youtube_url(audio_path):
            update_progress(30, "YouTube 비디오 다운로드 중...")
        else:
            update_progress(30, "오디오 파일 처리 중...")
        
        update_progress(50, "음성 인식 및 스크립트 추출 중...")
        
        # 백엔드 호출
        result = agent.process_audio_and_references(
            audio_path=audio_path,
            reference_files=reference_files,
            report_type=report_type,
            length=length
        )
        
        update_progress(90, "보고서 생성 완료, 파일 준비 중...")
        
        # 결과 파일 찾기 (output 디렉토리에서 최신 파일)
        output_dir = Path("output")
        if output_dir.exists():
            md_files = list(output_dir.glob("06_*_*.md"))
            if md_files:
                # 가장 최근 파일 선택
                latest_file = max(md_files, key=lambda x: x.stat().st_mtime)
                update_progress(100, "처리 완료!")
                return str(latest_file)
        
        raise FileNotFoundError("생성된 보고서 파일을 찾을 수 없습니다.")
        
    except Exception as e:
        raise Video2DocError(f"처리 중 오류 발생: {str(e)}")

def main():
    """메인 애플리케이션 함수"""
    
    init_session_state()
    
    # Mock 모드 배너
    if MOCK_MODE:
        st.markdown("""
        <div class="mock-banner">
            🧪 Mock 모드 활성화 - 개발용 가짜 데이터로 동작합니다
        </div>
        """, unsafe_allow_html=True)
    
    # 헤더
    st.markdown(f"""
    <div class="main-header">
        <h1>🎬 Video2Doc {' (Mock Mode)' if MOCK_MODE else ''}</h1>
        <p>동영상, 오디오, YouTube를 구조화된 문서로 변환</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 처리 중이 아닐 때만 입력 UI 표시
    if not st.session_state.processing:
        
        # Step 1: 소스 선택
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        st.subheader("📁 Step 1: 소스 선택")
        
        source_tab1, source_tab2 = st.tabs(["📁 파일 업로드", "🔗 YouTube URL"])
        
        audio_source = None
        
        with source_tab1:
            st.markdown("**MP4 또는 MP3 파일을 업로드하세요**")
            audio_file = st.file_uploader(
                "오디오/비디오 파일",
                type=['mp4', 'mp3', 'avi', 'mov', 'mkv', 'wav', 'm4a'],
                help="지원 형식: MP4, MP3, AVI, MOV, MKV, WAV, M4A"
            )
            
            if audio_file:
                st.success(f"✅ 파일 선택됨: {audio_file.name} ({audio_file.size:,} bytes)")
                audio_source = audio_file
        
        with source_tab2:
            st.markdown("**YouTube URL을 입력하세요**")
            youtube_url = st.text_input(
                "YouTube URL",
                placeholder="https://www.youtube.com/watch?v=...",
                help="YouTube 비디오 URL을 붙여넣으세요"
            )
            
            if youtube_url and is_youtube_url(youtube_url):
                if st.button("🔍 비디오 정보 확인"):
                    with st.spinner("YouTube 정보 가져오는 중..."):
                        video_info = get_youtube_video_info(youtube_url)
                        if video_info:
                            st.session_state.youtube_info = video_info
                
                if st.session_state.youtube_info:
                    info = st.session_state.youtube_info
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        try:
                            st.image(info['thumbnail'], width=200)
                        except:
                            st.info("썸네일을 불러올 수 없습니다")
                    
                    with col2:
                        st.success(f"✅ **{info['title']}**")
                        st.info(f"비디오 ID: {info['video_id']}")
                        if MOCK_MODE:
                            st.warning("🧪 Mock 모드: 실제 다운로드는 수행되지 않습니다")
                        audio_source = youtube_url
            
            elif youtube_url:
                st.error("올바른 YouTube URL을 입력해주세요")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Step 2: 참조 파일 (선택사항)
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        st.subheader("📄 Step 2: 참조 파일 (선택사항)")
        
        reference_files = st.file_uploader(
            "참조 문서들",
            type=['pdf', 'pptx', 'docx', 'xlsx', 'txt', 'md', 'jpg', 'jpeg', 'png', 'bmp', 'gif'],
            accept_multiple_files=True,
            help="PDF, PowerPoint, Word, Excel, 이미지 등을 추가할 수 있습니다"
        )
        
        if reference_files:
            st.success(f"✅ {len(reference_files)}개 참조 파일 선택됨:")
            for ref_file in reference_files:
                st.write(f"  • {ref_file.name} ({ref_file.size:,} bytes)")
            
            if MOCK_MODE:
                st.info("🧪 Mock 모드: 파일 내용은 실제로 분석되지 않습니다")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Step 3: 옵션 설정
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        st.subheader("⚙️ Step 3: 보고서 옵션")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**보고서 유형**")
            report_type = st.radio(
                "보고서 유형",
                ["summary", "detailed", "presentation"],
                format_func=lambda x: {
                    "summary": "📋 요약",
                    "detailed": "📊 상세 분석", 
                    "presentation": "🎯 프레젠테이션"
                }[x],
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("**보고서 길이**")
            length = st.radio(
                "보고서 길이",
                ["short", "mid", "long"],
                index=1,  # 기본값: mid
                format_func=lambda x: {
                    "short": "📄 짧게 (1페이지)",
                    "mid": "📑 중간 (소주제별 1페이지)",
                    "long": "📚 길게 (소주제별 2페이지+)"
                }[x],
                label_visibility="collapsed"
            )
        
        with col3:
            st.markdown("**AI 모델**")
            model_options = ["default", "local_qwen", "local_deepseek"]
            if not MOCK_MODE:
                model_options.append("openai_gpt4")
            
            model = st.selectbox(
                "AI 모델",
                model_options,
                format_func=lambda x: {
                    "default": f"🤖 기본 {'(Mock)' if MOCK_MODE else '(qwen3:custom)'}",
                    "local_qwen": f"🧠 Qwen {'(Mock)' if MOCK_MODE else '(로컬)'}",
                    "local_deepseek": f"🔬 DeepSeek {'(Mock)' if MOCK_MODE else '(로컬)'}",
                    "openai_gpt4": "🚀 GPT-4 (OpenAI)"
                }[x],
                label_visibility="collapsed"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Step 4: 실행
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        st.subheader("🚀 Step 4: 문서 생성")
        
        # 실행 조건 확인
        can_run = audio_source is not None
        
        if not can_run:
            st.warning("⚠️ 오디오/비디오 파일 또는 YouTube URL을 먼저 선택해주세요.")
        
        button_text = "🧪 Mock 문서 생성" if MOCK_MODE else "🎬 문서 생성 시작"
        
        if st.button(button_text, disabled=not can_run, type="primary"):
            st.session_state.processing = True
            st.session_state.progress = 0
            st.session_state.progress_text = "처리 시작..."
            st.session_state.result_file = None
            st.session_state.error_message = None
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 처리 중일 때 진행률 표시
    if st.session_state.processing:
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        st.subheader(f"⏳ {'Mock ' if MOCK_MODE else ''}처리 중...")
        
        # 진행률 바
        progress_bar = st.progress(st.session_state.progress / 100)
        status_text = st.empty()
        status_text.text(st.session_state.progress_text)
        
        # 백그라운드에서 처리 실행
        if 'future' not in st.session_state:
            # 임시 디렉토리 생성
            temp_dir = Path(tempfile.mkdtemp())
            
            # 파일 저장
            if isinstance(audio_source, str):  # YouTube URL
                audio_path = audio_source
            else:  # 업로드된 파일
                audio_path = save_uploaded_file(audio_source, temp_dir)
            
            # 참조 파일들 저장
            ref_file_paths = []
            if reference_files:
                for ref_file in reference_files:
                    ref_path = save_uploaded_file(ref_file, temp_dir)
                    ref_file_paths.append(ref_path)
            
            # 처리 함수 선택
            process_func = mock_process_video2doc if MOCK_MODE else real_process_video2doc
            
            # 백그라운드 처리 시작
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(
                process_func,
                audio_path,
                ref_file_paths,
                report_type,
                length,
                model
            )
            st.session_state.future = future
            st.session_state.temp_dir = temp_dir
        
        # 처리 완료 확인
        future = st.session_state.future
        if future.done():
            try:
                result_file = future.result()
                st.session_state.result_file = result_file
                st.session_state.processing = False
                
                # 임시 디렉토리 정리
                if 'temp_dir' in st.session_state:
                    shutil.rmtree(st.session_state.temp_dir, ignore_errors=True)
                    del st.session_state.temp_dir
                
                del st.session_state.future
                st.rerun()
                
            except Exception as e:
                st.session_state.error_message = str(e)
                st.session_state.processing = False
                
                # 임시 디렉토리 정리
                if 'temp_dir' in st.session_state:
                    shutil.rmtree(st.session_state.temp_dir, ignore_errors=True)
                    del st.session_state.temp_dir
                
                del st.session_state.future
                st.rerun()
        else:
            # 진행률 업데이트
            progress_bar.progress(st.session_state.progress / 100)
            status_text.text(st.session_state.progress_text)
            time.sleep(1)
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 결과 표시
    if st.session_state.result_file:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.subheader(f"🎉 {'Mock ' if MOCK_MODE else ''}문서 생성 완료!")
        
        result_path = Path(st.session_state.result_file)
        
        # 파일 정보
        file_size = result_path.stat().st_size
        st.success(f"✅ **{result_path.name}** 생성 완료 ({file_size:,} bytes)")
        
        if MOCK_MODE:
            st.info("🧪 이것은 Mock 데이터로 생성된 샘플 보고서입니다")
        
        # 다운로드 버튼
        with open(result_path, 'rb') as f:
            st.download_button(
                label="📥 보고서 다운로드",
                data=f.read(),
                file_name=result_path.name,
                mime="text/markdown",
                type="primary"
            )
        
        # 파일 내용 미리보기
        if st.checkbox("📖 내용 미리보기"):
            try:
                with open(result_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 처음 1000자만 표시
                    preview_content = content[:1000]
                    if len(content) > 1000:
                        preview_content += "\n\n... (더 많은 내용이 있습니다)"
                    
                    st.markdown("**보고서 내용 미리보기:**")
                    st.markdown(preview_content)
            except Exception as e:
                st.error(f"미리보기 로드 실패: {e}")
        
        # 출력 폴더 정보
        output_dir = result_path.parent
        st.info(f"📂 모든 생성 파일은 다음 위치에 있습니다: `{output_dir}`")
        
        # 새 작업 시작 버튼
        if st.button("🔄 새 문서 생성"):
            # 세션 상태 초기화
            for key in ['result_file', 'error_message', 'youtube_info', 'uploaded_files']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 에러 표시
    if st.session_state.error_message:
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.subheader(f"❌ {'Mock ' if MOCK_MODE else ''}처리 중 오류 발생")
        st.error(st.session_state.error_message)
        
        if not MOCK_MODE:
            # 로그 파일 링크
            log_file = Path("output/video2doc.log")
            if log_file.exists():
                st.info("📋 자세한 오류 정보는 로그 파일을 확인해주세요: `output/video2doc.log`")
        
        # 다시 시도 버튼
        if st.button("🔄 다시 시도"):
            st.session_state.error_message = None
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 사이드바: 도움말 및 설정
    with st.sidebar:
        st.header("🛠️ 개발 설정")
        
        # Mock 모드 설명
        if MOCK_MODE:
            st.success("🧪 **Mock 모드 활성화**")
            st.markdown("""
            **Mock 모드 특징:**
            - ✅ 백엔드 없이 UI 테스트 가능
            - ✅ 빠른 응답 시간 (1-3초)
            - ✅ 샘플 보고서 생성
            - ⚠️ 실제 콘텐츠 분석 안됨
            
            **개발용도:**
            - 프론트엔드 UI/UX 검증
            - 다양한 옵션 조합 테스트
            - 에러 핸들링 테스트
            """)
        else:
            st.info("🔧 **실제 모드**")
            st.markdown("""
            실제 Video2Doc 백엔드를 사용합니다.
            
            **요구사항:**
            - ✅ 백엔드 모듈 설치 필요
            - ✅ FFmpeg, Whisper 모델 필요
            - ✅ 실제 처리 시간 소요
            """)
        
        st.markdown("---")
        
        st.header("📚 사용 가이드")
        
        st.markdown("""
        ### 🎯 지원 형식
        **오디오/비디오:**
        - MP4, MP3, AVI, MOV, MKV
        - YouTube URL
        
        **참조 문서:**
        - PDF, PowerPoint, Word, Excel
        - 이미지 (JPG, PNG 등)
        - 텍스트 파일
        
        ### 📋 보고서 유형
        - **요약**: 핵심 내용 중심
        - **상세 분석**: 심층 분석 포함
        - **프레젠테이션**: 발표용 구조
        
        ### ⏱️ 예상 처리 시간
        """)
        
        if MOCK_MODE:
            st.markdown("""
            - Mock 모드: 1-3초
            - 모든 옵션 동일한 속도
            """)
        else:
            st.markdown("""
            - 10분 동영상: 2-5분
            - YouTube 다운로드: +1-2분
            - 참조 문서 많을수록: +시간
            """)
        
        st.markdown("""
        ### 🔧 문제 해결
        - 처리 실패 시 로그 확인
        - 파일 크기 제한: 2GB
        - 인터넷 연결 필요 (YouTube)
        """)
        
        st.markdown("---")
        st.markdown("**Video2Doc v1.0**")
        st.markdown("TDD 기반 리팩토링 완료 ✅")
        if MOCK_MODE:
            st.markdown("🧪 Mock 모드로 실행 중")

if __name__ == "__main__":
    main()