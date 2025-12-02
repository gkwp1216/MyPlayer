"""
MP 게임 패턴 재현 엔진
녹화된 패턴을 휴먼라이크하게 변형하여 재생

핵심 기능:
- 타이밍 랜덤화 (±10~20%)
- 행동 순서 변형 (5% 확률)
- 불필요한 행동 삽입 (자연스러움)
"""
import json
import time
import keyboard
import random
from pathlib import Path


class HumanlikePatternPlayer:
    """휴먼라이크 패턴 재생 엔진"""
    
    def __init__(self, pattern_file, humanlike_level=0.15):
        """
        Args:
            pattern_file: 패턴 JSON 파일 경로
            humanlike_level: 휴먼라이크 변형 강도 (0.0~1.0, 기본 0.15 = 15% 변형)
        """
        self.pattern_file = Path(pattern_file)
        self.humanlike_level = humanlike_level
        self.pattern_data = None
        self.metadata = None
        
        self._load_pattern()
        
        print(f"✅ 패턴 로드 완료: {self.metadata['name']}")
        print(f"⏱️  원본 길이: {self.metadata['duration']}초")
        print(f"🎯 총 행동: {self.metadata['total_actions']}개")
        print(f"🎭 휴먼라이크 레벨: {humanlike_level * 100:.0f}%")
    
    def _load_pattern(self):
        """패턴 파일 로드"""
        if not self.pattern_file.exists():
            raise FileNotFoundError(f"패턴 파일 없음: {self.pattern_file}")
        
        with open(self.pattern_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.metadata = data['metadata']
        self.pattern_data = data['pattern']
    
    def _apply_timing_variation(self, original_delay):
        """타이밍에 랜덤 변형 추가"""
        if original_delay < 0.05:  # 너무 짧은 딜레이는 그대로
            return original_delay
        
        # ±humanlike_level 범위로 변형
        variation = random.uniform(-self.humanlike_level, self.humanlike_level)
        new_delay = original_delay * (1 + variation)
        
        # 최소값 보장 (너무 빠르면 부자연스러움)
        return max(0.01, new_delay)
    
    def _should_insert_noise(self):
        """불필요한 행동 삽입 여부 (5% 확률)"""
        return random.random() < 0.05
    
    def _insert_noise_action(self):
        """불필요한 행동 삽입 (사람처럼)"""
        noise_actions = [
            ('left', 0.05),   # 살짝 왼쪽
            ('right', 0.05),  # 살짝 오른쪽
            ('space', 0.05),  # 점프
        ]
        
        action, duration = random.choice(noise_actions)
        keyboard.press(action)
        time.sleep(duration)
        keyboard.release(action)
        print(f"   🎭 노이즈: {action} (자연스러움)")
    
    def _should_skip_action(self):
        """행동 건너뛰기 여부 (3% 확률, 사람 실수)"""
        return random.random() < 0.03
    
    def play_pattern(self, loop=False):
        """패턴 재생"""
        print("\n" + "=" * 60)
        print("🎮 패턴 재생 시작")
        print("=" * 60)
        if loop:
            print("🔁 반복 모드: ESC로 중지")
        print("=" * 60)
        
        input("\n게임 창으로 이동 후 엔터를 누르세요... ")
        
        print("\n⏰ 3초 후 재생 시작...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("\n▶️  재생 중...\n")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                if loop:
                    print(f"\n🔄 반복 {iteration}회 시작...")
                
                self._play_once()
                
                if not loop:
                    break
                
                # 반복 사이 대기 (5~10초 랜덤)
                wait_time = random.uniform(5, 10)
                print(f"\n⏸️  {wait_time:.1f}초 대기 중...")
                time.sleep(wait_time)
                
                # ESC로 중지 확인
                if keyboard.is_pressed('esc'):
                    print("\n⏹️  ESC 감지 - 재생 중지")
                    break
        
        except KeyboardInterrupt:
            print("\n⏹️  Ctrl+C 감지 - 재생 중지")
        finally:
            self._release_all_keys()
            print("\n✅ 재생 완료!")
    
    def _play_once(self):
        """패턴 1회 재생"""
        last_time = 0
        
        for i, action in enumerate(self.pattern_data):
            # ESC로 중지
            if keyboard.is_pressed('esc'):
                print("\n⏹️  ESC 감지 - 재생 중지")
                break
            
            # 딜레이 계산 및 적용
            delay = action['time'] - last_time
            if delay > 0:
                varied_delay = self._apply_timing_variation(delay)
                time.sleep(varied_delay)
            
            # 가끔 행동 건너뛰기 (실수)
            if self._should_skip_action():
                print(f"   🎭 건너뛰기: {action['key']} (사람 실수)")
                last_time = action['time']
                continue
            
            # 행동 실행
            key = action['key']
            action_type = action['type']
            
            if action_type == 'down':
                keyboard.press(key)
                # print(f"⬇️  [{action['time']:.2f}s] {key} 눌림")
            elif action_type == 'up':
                keyboard.release(key)
                # print(f"⬆️  [{action['time']:.2f}s] {key} 뗌")
            
            # 가끔 불필요한 행동 삽입
            if self._should_insert_noise():
                self._insert_noise_action()
            
            last_time = action['time']
    
    def _release_all_keys(self):
        """모든 키 해제"""
        keys_to_release = [
            'left', 'right', 'up', 'down',
            'ctrl', 'a', 's', 'd', 'f', 'q', 'w', 'e', 'r',
            'alt', 'shift', 'space',
            '1', '2', '3', '4', '5',
        ]
        
        for key in keys_to_release:
            try:
                keyboard.release(key)
            except:
                pass


def load_latest_pattern():
    """가장 최근 패턴 파일 로드"""
    pattern_dir = Path("datasets/mp_patterns")
    if not pattern_dir.exists():
        return None
    
    pattern_files = sorted(pattern_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return pattern_files[0] if pattern_files else None


if __name__ == "__main__":
    # 테스트
    import argparse
    
    parser = argparse.ArgumentParser(description="MP 게임 패턴 재생 엔진")
    parser.add_argument("--pattern", "-p", help="패턴 파일 경로 (지정 안하면 최신 파일)")
    parser.add_argument("--humanlike", "-h", type=float, default=0.15, help="휴먼라이크 레벨 (0.0~1.0)")
    parser.add_argument("--loop", "-l", action="store_true", help="반복 재생")
    args = parser.parse_args()
    
    # 패턴 파일 결정
    if args.pattern:
        pattern_file = Path(args.pattern)
    else:
        pattern_file = load_latest_pattern()
        if pattern_file:
            print(f"💡 최신 패턴 자동 선택: {pattern_file.name}")
        else:
            print("❌ 패턴 파일이 없습니다!")
            print("   먼저 'python tools/record_pattern_mp.py'로 녹화하세요")
            exit(1)
    
    # 재생
    player = HumanlikePatternPlayer(pattern_file, humanlike_level=args.humanlike)
    player.play_pattern(loop=args.loop)
