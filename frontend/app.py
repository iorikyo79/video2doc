"""
Video2Doc Frontend MVP - Streamlit Web Interface

간단하고 직관적인 웹 인터페이스로 Video2Doc 백엔드를 사용할 수 있습니다.
MP4/MP3 파일이나 YouTube URL과 참조 문서들을 업로드하여 구조화된 문서를 생성합니다.
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

# 백엔드 모듈 import를 위한 경로 설정
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    from core.agent import Video2DocAgent
    from utils.youtube import is_youtube_url, extract_video_id_from_url
    from utils.exceptions import Video2DocError
    from config import config
except ImportError as e:
    st.error(f"백엔드 모듈을 찾을 수 없습니다: {e}")
    st.error("frontend/ 디렉토리가 video2doc 프로젝트 루트에 있는지 확인해주세요.")
    st.stop()

# Streamlit 페이지 설정
st.set_page_config(
    page_title="Video2Doc - 동영상/오디오 문서화 도구",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
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
        
        # 간단한 비디오 정보 반환 (실제로는 yt-dlp를 사용하지만 여기서는 기본 정보만)
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

def process_video2doc(audio_path: str, reference_files: List[str], 
                     report_type: str, length: str, model: str) -> str:
    """백엔드를 호출하여 Video2Doc 처리를 수행합니다."""
    
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
    
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🎬 Video2Doc</h1>
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
            model = st.selectbox(
                "AI 모델",
                ["default", "local_qwen", "local_deepseek", "openai_gpt4"],
                format_func=lambda x: {
                    "default": "🤖 기본 (qwen3:custom)",
                    "local_qwen": "🧠 Qwen (로컬)",
                    "local_deepseek": "🔬 DeepSeek (로컬)",
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
        
        if st.button("🎬 문서 생성 시작", disabled=not can_run, type="primary"):
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
        st.subheader("⏳ 처리 중...")
        
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
            
            # 백그라운드 처리 시작
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(
                process_video2doc,
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
        st.subheader("🎉 문서 생성 완료!")
        
        result_path = Path(st.session_state.result_file)
        
        # 파일 정보
        file_size = result_path.stat().st_size
        st.success(f"✅ **{result_path.name}** 생성 완료 ({file_size:,} bytes)")
        
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
        
        # 출력 폴더 열기 링크
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
        st.subheader("❌ 처리 중 오류 발생")
        st.error(st.session_state.error_message)
        
        # 로그 파일 링크
        log_file = Path("output/video2doc.log")
        if log_file.exists():
            st.info("📋 자세한 오류 정보는 로그 파일을 확인해주세요: `output/video2doc.log`")
        
        # 다시 시도 버튼
        if st.button("🔄 다시 시도"):
            st.session_state.error_message = None
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 사이드바: 도움말
    with st.sidebar:
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
        - 10분 동영상: 2-5분
        - YouTube 다운로드: +1-2분
        - 참조 문서 많을수록: +시간
        
        ### 🔧 문제 해결
        - 처리 실패 시 로그 확인
        - 파일 크기 제한: 2GB
        - 인터넷 연결 필요 (YouTube)
        """)
        
        st.markdown("---")
        st.markdown("**Video2Doc v1.0**")
        st.markdown("TDD 기반 리팩토링 완료 ✅")

if __name__ == "__main__":
    main()