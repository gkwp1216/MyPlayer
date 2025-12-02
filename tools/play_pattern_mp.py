"""
MP 게임 패턴 실행 스크립트
녹화된 패턴을 자동으로 재생하는 간단한 인터페이스

사용법: python tools/play_pattern_mp.py [옵션]
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pattern_player_mp import HumanlikePatternPlayer, load_latest_pattern


def list_patterns():
    """저장된 패턴 목록 출력"""
    pattern_dir = Path("datasets/mp_patterns")
    if not pattern_dir.exists() or not list(pattern_dir.glob("*.json")):
        print("❌ 저장된 패턴이 없습니다!")
        print("   먼저 'python tools/record_pattern_mp.py'로 녹화하세요")
        return []
    
    pattern_files = sorted(pattern_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    print("\n📁 저장된 패턴 목록:")
    print("=" * 60)
    for i, pfile in enumerate(pattern_files, 1):
        # 파일 크기
        size_kb = pfile.stat().st_size / 1024
        print(f"{i}. {pfile.name} ({size_kb:.1f} KB)")
    print("=" * 60)
    
    return pattern_files


def select_pattern_interactive(pattern_files):
    """대화형 패턴 선택"""
    if not pattern_files:
        return None
    
    while True:
        try:
            choice = input(f"\n패턴 번호를 입력하세요 (1-{len(pattern_files)}, Enter=최신): ").strip()
            
            if not choice:  # 엔터 = 최신 패턴
                return pattern_files[0]
            
            idx = int(choice) - 1
            if 0 <= idx < len(pattern_files):
                return pattern_files[idx]
            else:
                print(f"❌ 1~{len(pattern_files)} 사이의 숫자를 입력하세요")
        except ValueError:
            print("❌ 숫자를 입력하세요")


def main():
    parser = argparse.ArgumentParser(description="MP 게임 패턴 실행")
    parser.add_argument("--pattern", "-p", help="패턴 파일 경로")
    parser.add_argument("--humanlike", "-h", type=float, default=0.15, 
                        help="휴먼라이크 변형 강도 (0.0~1.0, 기본 0.15)")
    parser.add_argument("--loop", "-l", action="store_true", help="반복 재생 (ESC로 중지)")
    parser.add_argument("--list", "-ls", action="store_true", help="패턴 목록만 출력")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎮 MP 게임 패턴 플레이어")
    print("=" * 60)
    
    # 패턴 목록만 출력
    if args.list:
        list_patterns()
        return
    
    # 패턴 파일 결정
    if args.pattern:
        pattern_file = Path(args.pattern)
        if not pattern_file.exists():
            print(f"❌ 패턴 파일이 없습니다: {pattern_file}")
            return
    else:
        # 대화형 선택
        pattern_files = list_patterns()
        if not pattern_files:
            return
        
        pattern_file = select_pattern_interactive(pattern_files)
        if not pattern_file:
            print("❌ 패턴이 선택되지 않았습니다")
            return
    
    print(f"\n✅ 선택된 패턴: {pattern_file.name}")
    print(f"🎭 휴먼라이크 레벨: {args.humanlike * 100:.0f}%")
    if args.loop:
        print("🔁 반복 모드 활성화")
    
    # 패턴 재생
    try:
        player = HumanlikePatternPlayer(pattern_file, humanlike_level=args.humanlike)
        player.play_pattern(loop=args.loop)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n💡 팁:")
    print("  - 휴먼라이크 레벨을 높이면 더 자연스럽지만 덜 정확해집니다")
    print("  - 반복 모드(-l)로 장시간 사냥 가능합니다")
    print("  - ESC 키로 언제든 중지할 수 있습니다")


if __name__ == "__main__":
    main()
