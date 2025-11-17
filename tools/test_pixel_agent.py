"""
학습된 픽셀 기반 RL 에이전트 테스트
실시간 게임 플레이 시연
"""
import argparse
from pathlib import Path
import sys
import time
import cv2
import numpy as np
import mss

sys.path.insert(0, str(Path(__file__).parent.parent))

from stable_baselines3 import PPO, DQN, A2C
from src.utils.config_loader import load_config
from collections import deque
import keyboard


class SimpleActionController:
    """간단한 행동 제어 (실제 플레이 패턴 기반)"""
    
    def __init__(self, keybindings):
        self.keybindings = keybindings
        self.currently_pressed = set()
        
        # 버프 쿨타임 관리 (초)
        self.buff_cooldowns = {
            5: 120,   # 홀리심볼 - 2분
            6: 180,   # 블레스 - 3분
            7: 300,   # 인빈서블 - 5분
            10: 150   # 서먼 드래곤 - 150초
        }
        self.last_buff_time = {5: 0, 6: 0, 7: 0, 10: 0}
        self.attack_duration = 0.3  # 공격 지속 시간
        
    def execute_action(self, action):
        """행동 실행 (이동 키는 계속 누름, 스킬은 탭)"""
        action_map = {
            0: None,                                        # idle
            1: self.keybindings.get('move_left', 'left'),  # 왼쪽
            2: self.keybindings.get('move_right', 'right'),# 오른쪽
            3: self.keybindings.get('teleport', 'v'),      # 텔레포트
            4: self.keybindings.get('attack', 'a'),        # 공격
            5: self.keybindings.get('buff_holy', 'd'),     # 홀리심볼
            6: self.keybindings.get('buff_bless', 'shift'),# 블레스
            7: self.keybindings.get('buff_invin', 'alt'),  # 인빈서블
            8: self.keybindings.get('move_up', 'up'),      # 위
            9: self.keybindings.get('move_down', 'down'),  # 아래
            10: self.keybindings.get('summon_dragon', 'home') # 서먼 드래곤
        }
        
        is_movement = action in [1, 2, 8, 9]
        is_buff = action in [5, 6, 7, 10]
        is_attack = action == 4
        
        try:
            # 버프 쿨타임 체크
            if is_buff:
                current_time = time.time()
                cooldown = self.buff_cooldowns[action]
                last_time = self.last_buff_time[action]
                
                if current_time - last_time < cooldown:
                    return  # 쿨타임 중이면 무시
                else:
                    self.last_buff_time[action] = current_time
            
            if is_movement:
                for pressed_key in list(self.currently_pressed):
                    keyboard.release(pressed_key)
                self.currently_pressed.clear()
            
            key = action_map.get(action)
            
            if key:
                if is_movement:
                    keyboard.press(key)
                    self.currently_pressed.add(key)
                elif is_attack:
                    # 공격은 꾹 누르기
                    keyboard.press(key)
                    time.sleep(self.attack_duration)
                    keyboard.release(key)
                else:
                    keyboard.press(key)
                    time.sleep(0.05)
                    keyboard.release(key)
            elif action == 0:
                for pressed_key in list(self.currently_pressed):
                    keyboard.release(pressed_key)
                self.currently_pressed.clear()
                
        except Exception as e:
            print(f"⚠️  키 입력 오류 (action={action}): {e}")
    
    def release_all(self):
        """모든 눌린 키 해제"""
        for key in list(self.currently_pressed):
            try:
                keyboard.release(key)
            except:
                pass
        self.currently_pressed.clear()


def preprocess_frame(frame, width=84, height=84):
    """프레임 전처리 (학습과 동일한 방식)"""
    # 그레이스케일 변환
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 리사이즈
    resized = cv2.resize(gray, (width, height))
    return resized


def main():
    parser = argparse.ArgumentParser(description="학습된 RL 에이전트 테스트")
    parser.add_argument("--game", default="ML", help="게임 이름")
    parser.add_argument("--model", required=True, help="모델 경로 (.zip)")
    parser.add_argument("--frame-width", type=int, default=84, help="프레임 너비")
    parser.add_argument("--frame-height", type=int, default=84, help="프레임 높이")
    parser.add_argument("--frame-stack", type=int, default=4, help="프레임 스택")
    parser.add_argument("--fps", type=int, default=10, help="실행 FPS")
    parser.add_argument("--duration", type=int, default=60, help="실행 시간 (초, 0=무제한)")
    parser.add_argument("--show-preview", action="store_true", help="프레임 미리보기 표시")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🤖 학습된 RL 에이전트 테스트")
    print("=" * 60)
    print(f"게임: {args.game}")
    print(f"모델: {args.model}")
    print(f"프레임: {args.frame_width}x{args.frame_height} (x{args.frame_stack})")
    print(f"FPS: {args.fps}")
    print(f"실행 시간: {args.duration}초" if args.duration > 0 else "실행 시간: 무제한")
    print("-" * 60)
    
    # 모델 로드
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"❌ 모델을 찾을 수 없습니다: {model_path}")
        return
    
    print(f"🔄 모델 로딩 중...")
    
    # 알고리즘 자동 감지
    if 'ppo' in model_path.stem.lower():
        model = PPO.load(str(model_path))
        algorithm = "PPO"
    elif 'dqn' in model_path.stem.lower():
        model = DQN.load(str(model_path))
        algorithm = "DQN"
    elif 'a2c' in model_path.stem.lower():
        model = A2C.load(str(model_path))
        algorithm = "A2C"
    else:
        print("⚠️  알고리즘을 감지할 수 없습니다. PPO로 시도합니다.")
        model = PPO.load(str(model_path))
        algorithm = "PPO"
    
    print(f"✅ {algorithm} 모델 로드 완료")
    
    # 설정 로드
    config = load_config(game=args.game)
    
    # ActionController 초기화 (간단한 버전)
    keybindings = config.get('keybindings', {
        'move_left': 'left',
        'move_right': 'right',
        'move_up': 'up',
        'move_down': 'down',
        'jump': 'space',
        'attack': 'a',
        'skill1': 's',
        'skill2': 'd',
        'potion': 'p'
    })
    
    action_controller = SimpleActionController(keybindings)
    
    # 화면 캡처 초기화
    sct = mss.mss()
    monitor = sct.monitors[1]  # 전체 화면
    
    print(f"📐 화면: {monitor['width']}x{monitor['height']}")
    print()
    print("=" * 60)
    print("🎮 게임을 시작하세요!")
    print("=" * 60)
    print()
    print("제어:")
    print("  ESC    : 종료")
    if args.show_preview:
        print("  Q      : 미리보기 닫기")
    print()
    print(f"⏱️  3초 후 시작...")
    
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print()
    print("🚀 에이전트 실행 시작!")
    print("-" * 60)
    
    # 프레임 버퍼
    frame_buffer = deque(maxlen=args.frame_stack)
    
    # 첫 프레임으로 버퍼 초기화
    screenshot = sct.grab(monitor)
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    processed = preprocess_frame(frame, args.frame_width, args.frame_height)
    
    for _ in range(args.frame_stack):
        frame_buffer.append(processed)
    
    # 행동 매핑 (실제 플레이 패턴)
    action_names = [
        "대기", "왼쪽", "오른쪽", "텔포(V)", "공격(A)",
        "홀리(D)", "블레스(Shift)", "인빈(Alt)", "위", "아래",
        "서먼(Home)"
    ]
    
    # 실행
    frame_delay = 1.0 / args.fps
    start_time = time.time()
    frame_count = 0
    action_counts = {i: 0 for i in range(11)}
    
    try:
        while True:
            loop_start = time.time()
            
            # 화면 캡처
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            # 전처리
            processed = preprocess_frame(frame, args.frame_width, args.frame_height)
            frame_buffer.append(processed)
            
            # 관측 생성
            observation = np.array(frame_buffer, dtype=np.uint8)
            
            # 행동 예측
            action, _states = model.predict(observation, deterministic=False)
            action = int(action)
            
            # 행동 실행
            action_controller.execute_action(action)
            
            # 통계
            action_counts[action] += 1
            frame_count += 1
            
            # 1초마다 상태 출력
            if frame_count % args.fps == 0:
                elapsed = time.time() - start_time
                print(f"⏱️  {elapsed:.1f}초 | 프레임: {frame_count} | 마지막 행동: {action_names[action]}")
            
            # 미리보기
            if args.show_preview:
                # 원본 프레임에 정보 표시
                display_frame = frame.copy()
                cv2.putText(display_frame, f"Action: {action_names[action]}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Frame: {frame_count}", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 전처리된 프레임도 표시 (작게)
                stacked_view = np.hstack([frame_buffer[i] for i in range(args.frame_stack)])
                stacked_view = cv2.resize(stacked_view, (args.frame_stack * 84 * 2, 84 * 2))
                
                cv2.imshow('Agent View', display_frame)
                cv2.imshow('Processed Frames', stacked_view)
                
                key = cv2.waitKey(1)
                if key == ord('q') or key == 27:  # Q or ESC
                    print("\n⏹️  사용자 중단")
                    break
            
            # 시간 제한
            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                print(f"\n⏱️  {args.duration}초 경과 - 자동 종료")
                break
            
            # FPS 유지
            elapsed = time.time() - loop_start
            if elapsed < frame_delay:
                time.sleep(frame_delay - elapsed)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  중단됨")
    
    finally:
        sct.close()
        if args.show_preview:
            cv2.destroyAllWindows()
        
        # 통계 출력
        print()
        print("=" * 60)
        print("📊 실행 통계")
        print("=" * 60)
        elapsed = time.time() - start_time
        print(f"⏱️  총 시간: {elapsed:.1f}초")
        print(f"🎞️  총 프레임: {frame_count}개")
        print(f"📈 평균 FPS: {frame_count / elapsed:.1f}")
        print()
        print("행동 분포:")
        for action_id, count in action_counts.items():
            if count > 0:
                percentage = (count / frame_count) * 100
                print(f"  {action_names[action_id]:8s}: {count:4d}회 ({percentage:5.1f}%)")
        print("=" * 60)


if __name__ == "__main__":
    main()
