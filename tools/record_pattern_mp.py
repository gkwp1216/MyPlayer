"""
MP 게임 플레이 패턴 녹화 도구
사용자의 키보드 입력을 실시간으로 기록하여 패턴 파일로 저장

사용법: python tools/record_pattern_mp.py --duration 300 --output my_pattern
"""
import argparse
import keyboard
import time
import json
from pathlib import Path
from datetime import datetime


class PatternRecorder:
    """키보드 입력 패턴 녹화"""
    
    def __init__(self, output_name="pattern"):
        self.output_name = output_name
        self.pattern_data = []
        self.start_time = None
        self.recording = False
        
        # 녹화할 키 목록 (메이플스토리 기본 키)
        self.monitored_keys = [
            'left', 'right', 'up', 'down',  # 이동
            'ctrl', 'a', 's', 'd', 'f', 'q', 'w', 'e', 'r',  # 스킬
            'alt', 'shift', 'space',  # 점프/기타
            '1', '2', '3', '4', '5',  # 퀵슬롯
        ]
        
        # 키 상태 추적 (중복 방지)
        self.key_states = {key: False for key in self.monitored_keys}
        
        print("✅ 패턴 녹화기 초기화 완료")
        print(f"📝 모니터링 키: {', '.join(self.monitored_keys)}")
    
    def on_key_event(self, event):
        """키 이벤트 핸들러"""
        if not self.recording:
            return
        
        if event.name not in self.monitored_keys:
            return
        
        current_time = time.time() - self.start_time
        
        # 키 다운 이벤트만 기록 (중복 방지)
        if event.event_type == 'down':
            if not self.key_states[event.name]:
                self.key_states[event.name] = True
                action = {
                    'time': round(current_time, 3),
                    'key': event.name,
                    'type': 'down'
                }
                self.pattern_data.append(action)
                print(f"⬇️  [{current_time:.2f}s] {event.name} 눌림")
        
        # 키 업 이벤트 기록
        elif event.event_type == 'up':
            if self.key_states[event.name]:
                self.key_states[event.name] = False
                action = {
                    'time': round(current_time, 3),
                    'key': event.name,
                    'type': 'up'
                }
                self.pattern_data.append(action)
                print(f"⬆️  [{current_time:.2f}s] {event.name} 뗌")
    
    def start_recording(self, duration=None):
        """녹화 시작"""
        print("\n" + "=" * 60)
        print("🎬 패턴 녹화 시작!")
        print("=" * 60)
        if duration:
            print(f"⏱️  녹화 시간: {duration}초")
        print("⏹️  ESC 키로 중지")
        print("=" * 60)
        
        input("\n게임 창으로 이동 후 엔터를 누르세요... ")
        
        print("\n⏰ 3초 후 녹화 시작...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("\n🔴 녹화 중... 평소처럼 플레이하세요!\n")
        
        self.recording = True
        self.start_time = time.time()
        
        # 키보드 훅 등록
        keyboard.hook(self.on_key_event)
        
        # 녹화 시간만큼 대기 (또는 ESC까지)
        try:
            if duration:
                start = time.time()
                while time.time() - start < duration:
                    if keyboard.is_pressed('esc'):
                        print("\n⏹️  ESC 감지 - 녹화 중지")
                        break
                    time.sleep(0.1)
            else:
                keyboard.wait('esc')
                print("\n⏹️  ESC 감지 - 녹화 중지")
        except KeyboardInterrupt:
            print("\n⏹️  Ctrl+C 감지 - 녹화 중지")
        finally:
            self.recording = False
            keyboard.unhook_all()
    
    def save_pattern(self):
        """패턴 데이터 저장"""
        if not self.pattern_data:
            print("\n❌ 녹화된 데이터가 없습니다!")
            return
        
        # 저장 경로 생성
        output_dir = Path("datasets/mp_patterns")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_name}_{timestamp}.json"
        output_path = output_dir / filename
        
        # 메타데이터 추가
        pattern_file = {
            'metadata': {
                'name': self.output_name,
                'recorded_at': timestamp,
                'duration': round(self.pattern_data[-1]['time'], 2) if self.pattern_data else 0,
                'total_actions': len(self.pattern_data),
                'keys_used': list(set([a['key'] for a in self.pattern_data]))
            },
            'pattern': self.pattern_data
        }
        
        # JSON 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(pattern_file, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print("✅ 패턴 저장 완료!")
        print("=" * 60)
        print(f"📁 파일: {output_path}")
        print(f"⏱️  녹화 시간: {pattern_file['metadata']['duration']}초")
        print(f"🎯 총 행동: {pattern_file['metadata']['total_actions']}개")
        print(f"🎹 사용된 키: {', '.join(pattern_file['metadata']['keys_used'])}")
        print("=" * 60)
        
        # 통계 출력
        key_counts = {}
        for action in self.pattern_data:
            if action['type'] == 'down':
                key_counts[action['key']] = key_counts.get(action['key'], 0) + 1
        
        print("\n📊 키 사용 통계:")
        for key, count in sorted(key_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {key}: {count}회")


def main():
    parser = argparse.ArgumentParser(description="MP 게임 플레이 패턴 녹화")
    parser.add_argument("--output", "-o", default="pattern", help="출력 파일명 (기본: pattern)")
    parser.add_argument("--duration", "-d", type=int, help="녹화 시간 (초, 지정 안하면 ESC까지)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 MP 게임 패턴 녹화기")
    print("=" * 60)
    print(f"📝 출력 파일: {args.output}")
    if args.duration:
        print(f"⏱️  녹화 시간: {args.duration}초")
    else:
        print("⏱️  녹화 시간: ESC를 누를 때까지")
    print("=" * 60)
    
    print("\n⚠️  주의사항:")
    print("  1. 메이플스토리가 실행 중이어야 합니다")
    print("  2. 녹화 중에는 평소처럼 플레이하세요")
    print("  3. 자주 사용하는 루틴을 반복하세요")
    print("  4. ESC로 언제든 중지 가능")
    print()
    
    recorder = PatternRecorder(output_name=args.output)
    recorder.start_recording(duration=args.duration)
    recorder.save_pattern()
    
    print("\n💡 다음 단계:")
    print("   python tools/play_pattern_mp.py --pattern datasets/mp_patterns/[파일명].json")


if __name__ == "__main__":
    main()
