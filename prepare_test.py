#!/usr/bin/env python3
"""
Video2Doc 테스트 준비 스크립트

테스트에 필요한 샘플 파일을 준비합니다.
실제 S2_02.mp4 파일이 없는 경우 더미 파일을 생성합니다.
"""

import os
import subprocess
from pathlib import Path

def create_dummy_video():
    """테스트용 더미 비디오 파일 생성"""
    input_dir = Path("input")
    input_dir.mkdir(exist_ok=True)
    
    video_file = input_dir / "S2_02.mp4"
    
    if video_file.exists():
        print(f"✅ 비디오 파일이 이미 존재합니다: {video_file}")
        return str(video_file)
    
    print("🎬 테스트용 더미 비디오 파일 생성 중...")
    
    try:
        # FFmpeg로 10초짜리 테스트 비디오 생성 (음성 포함)
        cmd = [
            "ffmpeg", "-f", "lavfi", 
            "-i", "testsrc2=duration=10:size=320x240:rate=30",
            "-f", "lavfi", 
            "-i", "sine=frequency=1000:duration=10",
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest", str(video_file), "-y"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and video_file.exists():
            file_size = video_file.stat().st_size
            print(f"✅ 더미 비디오 파일 생성 완료: {video_file} (크기: {file_size:,} bytes)")
            return str(video_file)
        else:
            print(f"❌ FFmpeg 실행 실패: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print("❌ FFmpeg가 설치되지 않았습니다.")
        print("   실제 S2_02.mp4 파일을 input/ 디렉토리에 배치해주세요.")
        return None
    except Exception as e:
        print(f"❌ 더미 비디오 생성 실패: {e}")
        return None

def check_reference_files():
    """참조 파일들 확인"""
    print("📋 참조 파일 확인...")
    
    ref_files = [
        "input/Resume.pdf",
        "input/rules.pdf",
        "input/RESULT_GASTRO.xlsx"
    ]
    
    available_files = []
    for ref_file in ref_files:
        if Path(ref_file).exists():
            file_size = Path(ref_file).stat().st_size
            print(f"✅ {ref_file} (크기: {file_size:,} bytes)")
            available_files.append(ref_file)
        else:
            print(f"❌ {ref_file} (없음)")
    
    print(f"📊 사용 가능한 참조 파일: {len(available_files)}/{len(ref_files)}")
    return available_files

def main():
    print("🔧 Video2Doc 테스트 준비")
    print("=" * 30)
    
    # 1. 비디오 파일 준비
    video_file = create_dummy_video()
    
    # 2. 참조 파일 확인
    ref_files = check_reference_files()
    
    # 3. 결과 요약
    print("\n📋 준비 완료 요약:")
    print("-" * 20)
    
    if video_file:
        print(f"🎬 비디오 파일: {video_file}")
    else:
        print("❌ 비디오 파일: 준비되지 않음")
    
    print(f"📄 참조 파일: {len(ref_files)}개")
    for ref_file in ref_files:
        print(f"  - {ref_file}")
    
    if video_file and ref_files:
        print("\n✅ 모든 테스트 파일이 준비되었습니다!")
        print("이제 다음 명령으로 테스트를 실행할 수 있습니다:")
        print("  python test_workflow.py")
        print("  또는")
        print("  ./run_test.sh")
    else:
        print("\n⚠️ 일부 파일이 준비되지 않았습니다.")
        print("테스트는 가능하지만 일부 단계가 제한될 수 있습니다.")

if __name__ == "__main__":
    main()
