#!/usr/bin/env python3
"""
Video2Doc Agent 메인 실행 스크립트

명령행 인터페이스를 통해 Video2Doc 에이전트를 실행할 수 있습니다.
MP4 동영상 파일과 MP3 오디오 파일을 모두 지원합니다.

사용법:
    python main.py --audio video.mp4 --refs ref1.pdf ref2.pptx --type summary --length mid
    python main.py --audio meeting.mp3 --refs agenda.pdf --type summary --length short
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Optional

from video2doc_agent import Video2DocAgent
from config import config


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, config.LOGGING_CONFIG["level"]),
        format=config.LOGGING_CONFIG["format"],
        handlers=[
            logging.FileHandler(config.LOGGING_CONFIG["file"]),
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_files(audio_path: str, reference_files: Optional[List[str]] = None) -> tuple:
    """입력 파일들의 유효성을 검사합니다."""
    
    # 오디오 파일 검사
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
    
    if not config.is_supported_file(audio_path):
        raise ValueError(f"지원하지 않는 오디오 파일 형식: {audio_path}")
    
    # 참조 파일들 검사
    valid_reference_files = []
    if reference_files:
        for ref_file in reference_files:
            if Path(ref_file).exists():
                if config.is_supported_file(ref_file):
                    valid_reference_files.append(ref_file)
                    print(f"✅ 참조 파일 확인: {ref_file}")
                else:
                    print(f"⚠️ 지원하지 않는 파일 형식, 건너뜀: {ref_file}")
            else:
                print(f"⚠️ 파일을 찾을 수 없음, 건너뜀: {ref_file}")
    
    return audio_path, valid_reference_files if valid_reference_files else None


def main():
    """메인 함수"""
    
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(
        description="Video2Doc Agent - 오디오(MP4/MP3)와 참조 자료로부터 문서 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
    python main.py --audio lecture.mp4 --type summary --length mid
    python main.py --audio meeting.mp3 --type summary --length short
    python main.py --audio presentation.mp4 --refs slides.pptx notes.pdf --type detailed --length long
    python main.py --audio tutorial.mp4 --refs manual.pdf --model local_deepseek --output /path/to/output
        """
    )
    
    # 필수 인자
    parser.add_argument(
        "--audio", "-a",
        required=True,
        help="처리할 오디오 파일 경로 (MP4, MP3)"
    )
    
    # 하위 호환성을 위한 별칭
    parser.add_argument(
        "--video", "-v",
        help="처리할 비디오 파일 경로 (MP4) - audio 옵션과 동일"
    )
    
    # 선택적 인자
    parser.add_argument(
        "--refs", "-r",
        nargs="*",
        help="참조 파일들 경로 (PDF, PPTX, DOCX, 이미지)"
    )
    
    parser.add_argument(
        "--type", "-t",
        choices=["summary", "detailed", "presentation"],
        default="summary",
        help="보고서 유형 (기본값: summary)"
    )
    
    parser.add_argument(
        "--length", "-l",
        choices=["short", "mid", "long"],
        default="mid",
        help="보고서 길이 (기본값: mid)"
    )
    
    parser.add_argument(
        "--model", "-m",
        choices=["default", "local_qwen", "local_deepseek", "openai_gpt4"],
        default="default",
        help="사용할 언어 모델 (기본값: default)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="출력 디렉토리 (기본값: ./output)"
    )
    
    parser.add_argument(
        "--verbose", "-V",
        action="store_true",
        help="상세 로그 출력"
    )
    
    args = parser.parse_args()
    
    # 오디오 파일 경로 결정 (하위 호환성)
    audio_path = args.audio or args.video
    if not audio_path:
        parser.error("--audio 또는 --video 옵션 중 하나는 필수입니다.")
    
    # 로깅 설정
    if args.verbose:
        config.LOGGING_CONFIG["level"] = "DEBUG"
    setup_logging()
    
    logger = logging.getLogger(__name__)
    
    try:
        # 파일 유효성 검사
        logger.info("📋 입력 파일 검사 중...")
        audio_path, reference_files = validate_files(audio_path, args.refs)
        
        # 출력 디렉토리 설정
        if args.output:
            from video2doc_agent import Video2DocWorkflow
            Video2DocWorkflow.output_dir = Path(args.output)
            Video2DocWorkflow.output_dir.mkdir(exist_ok=True)
        
        # 모델 설정
        logger.info(f"🤖 언어 모델 초기화 중... (모델: {args.model})")
        model_config = config.get_model_config(args.model)
        
        # 에이전트 초기화
        logger.info("🚀 Video2Doc 에이전트 초기화 중...")
        agent = Video2DocAgent(model_config=model_config)
        
        # 처리 시작
        logger.info("🎬 Video2Doc 워크플로우 시작...")
        logger.info(f"   🎵 오디오: {audio_path}")
        logger.info(f"   📄 참조 파일: {reference_files or '없음'}")
        logger.info(f"   📊 보고서 유형: {args.type}")
        logger.info(f"   📏 보고서 길이: {args.length}")
        
        result = agent.process_audio_and_references(
            audio_path=audio_path,
            reference_files=reference_files,
            report_type=args.type,
            length=args.length
        )
        
        # 결과 출력
        logger.info("✅ Video2Doc 처리 완료!")
        logger.info(f"📤 결과: {result}")
        
        print("\n" + "="*60)
        print("🎉 Video2Doc 처리가 성공적으로 완료되었습니다!")
        print("="*60)
        print(f"🎵 처리된 오디오: {Path(audio_path).name}")
        print(f"📄 참조 파일 수: {len(reference_files) if reference_files else 0}")
        print(f"📊 생성된 보고서: {args.type} ({args.length})")
        print(f"📂 출력 디렉토리: {args.output or config.OUTPUT_DIR}")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("❌ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ 처리 중 오류 발생: {e}")
        if args.verbose:
            logger.exception("상세 오류 정보:")
        sys.exit(1)


if __name__ == "__main__":
    main()
