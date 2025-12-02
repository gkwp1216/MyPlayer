"""
실시간 강화학습 환경
에이전트가 실제 게임과 상호작용하며 학습
"""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import cv2
import mss
import time
from collections import deque
import keyboard
import win32gui
import win32con
from pathlib import Path
import sys
import json
import pyautogui

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.config_loader import load_config


class RealtimeGameEnv(gym.Env):
    """실시간 게임 플레이 환경"""
    
    metadata = {'render.modes': ['human']}
    
    def __init__(self, game="ML", frame_width=84, frame_height=84, frame_stack=4, frame_skip=4):
        super().__init__()
        
        self.game = game
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_stack = frame_stack
        self.frame_skip = frame_skip
        
        # 설정 로드
        self.config = load_config(game=game)
        self.keybindings = self.config.get('keybindings', {})
        
        # 행동 공간: 11개
        self.action_space = spaces.Discrete(11)
        
        # 관측 공간: 그레이스케일 프레임 스택
        self.observation_space = spaces.Box(
            low=0, high=255,
            shape=(frame_stack, frame_height, frame_width),
            dtype=np.uint8
        )
        
        # 화면 캡처
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]
        
        # 프레임 버퍼
        self.frame_buffer = deque(maxlen=frame_stack)
        
        # 상태 추적
        self.last_frame = None
        self.step_count = 0
        self.episode_reward = 0
        
        # 버프 쿨타임
        self.buff_cooldowns = {5: 120, 6: 180, 7: 300, 10: 150}
        self.last_buff_time = {5: 0, 6: 0, 7: 0, 10: 0}
        
        # 텔레포트 방향 기억
        self.last_move_direction = 'right'  # 기본 방향
        
        # 행동 이력 추적 (시퀀스 학습용)
        self.action_history = deque(maxlen=10)  # 최근 10개 행동
        self.last_action = None
        self.last_action_time = 0
        self.stuck_count = 0  # 벽 충돌 감지
        self.last_position_hash = None
        
        # ROI 설정 로드
        self.roi_settings = self._load_roi_settings()
        
        # 경험치 감지만 사용
        self.last_exp_pixels = None
        
        # 안전장치 (템플릿 이미지 로드)
        self.danger_monster_template = self._load_template("assets/WARNING.png")
        self.npc_template = self._load_template("assets/IFWARNINGappearClick.png")
        self.dialog_template = self._load_template("assets/IFWARNINGappearClick_2.png")
        self.last_danger_check = 0
        self.danger_check_interval = 1.0  # 1초마다 체크
        self.danger_detection_count = 0  # 연속 감지 카운터 (오탐지 방지)
        
        print("✅ 실시간 RL 환경 초기화 완료")
        if self.roi_settings:
            print(f"📍 ROI 설정 로드: {list(self.roi_settings.keys())}")
        else:
            print("⚠️  ROI 미설정 (기본 보상 함수 사용)")
        
        # 안전장치 상태 출력
        templates_loaded = sum([
            self.danger_monster_template is not None,
            self.npc_template is not None,
            self.dialog_template is not None
        ])
        if templates_loaded == 3:
            print("🛡️ WARNING 몬스터 회피 시스템 활성화 (3/3 템플릿 로드)")
            print("   → 감지 시: NPC 클릭 → 대화 수락 → 학습 계속")
        elif templates_loaded > 0:
            print(f"⚠️ 일부 템플릿만 로드됨 ({templates_loaded}/3)")
        else:
            print("💡 WARNING 회피 시스템 비활성화 (assets/*.png 없음)")
    
    def _load_roi_settings(self):
        """ROI 설정 로드"""
        config_path = Path("configs/roi_settings.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return None
    
    def _load_template(self, path):
        """템플릿 이미지 로드 (그레이스케일)"""
        template_path = Path(path)
        if template_path.exists():
            template = cv2.imread(str(template_path))
            if template is not None:
                return template  # 컬러로 유지 (더 정확한 매칭)
        return None
    
    def reset(self, seed=None, options=None):
        """환경 초기화"""
        super().reset(seed=seed)
        
        self.step_count = 0
        self.episode_reward = 0
        self.last_buff_time = {5: 0, 6: 0, 7: 0, 10: 0}
        self.last_move_direction = 'right'  # 에피소드마다 초기화
        
        # 초기 프레임 캡처
        screenshot = self.sct.grab(self.monitor)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        processed = self._preprocess_frame(frame)
        
        self.frame_buffer.clear()
        for _ in range(self.frame_stack):
            self.frame_buffer.append(processed)
        
        self.last_frame = frame.copy()
        
        observation = self._get_observation()
        info = {}
        
        return observation, info
    
    def step(self, action):
        """행동 실행 및 보상 계산"""
        # 1. 행동 실행 (프레임 스킵 적용)
        total_reward = 0.0
        done = False
        
        for _ in range(self.frame_skip):
            self._execute_action(action)
            
            # 2. 대기 시간 대폭 단축 (0.1 -> 0.01)
            time.sleep(0.01)
            
            # 3. 프레임 캡처 및 보상 계산
            screenshot = self.sct.grab(self.monitor)
            current_frame = np.array(screenshot)
            current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGRA2BGR)
            
            # 🚨 안전장치 2: 위험 몬스터 감지 (스킵 중에도 체크)
            self._check_danger_monster(current_frame)
            
            # 보상 누적
            step_reward = self._calculate_reward(action, current_frame)
            total_reward += step_reward
            
            # 프레임 버퍼 업데이트 (매 스텝마다)
            processed = self._preprocess_frame(current_frame)
            self.frame_buffer.append(processed)
            self.last_frame = current_frame.copy()
            
            # 종료 조건 체크
            self.step_count += 1
            if self.step_count >= 1000:
                done = True
                break
        
        self.episode_reward += total_reward
        
        observation = self._get_observation()
        info = {'step': self.step_count, 'episode_reward': self.episode_reward}
        
        return observation, total_reward, done, False, info
    
    def _preprocess_frame(self, frame):
        """프레임 전처리"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (self.frame_width, self.frame_height))
        return resized
    
    def _get_observation(self):
        """현재 관측 반환"""
        return np.array(self.frame_buffer, dtype=np.uint8)
    
    def _execute_action(self, action):
        """행동 실행 (키보드 입력)"""
        # 🚨 안전장치 1: 위 방향키 차단 (포탈 방지)
        if action == 8:
            return  # 위 방향키 무시
        
        action_map = {
            0: None,
            1: self.keybindings.get('move_left', 'left'),
            2: self.keybindings.get('move_right', 'right'),
            3: self.keybindings.get('teleport', 'v'),
            4: self.keybindings.get('attack', 'a'),
            5: self.keybindings.get('buff_holy', 'd'),
            6: self.keybindings.get('buff_bless', 'shift'),
            7: self.keybindings.get('buff_invin', 'alt'),
            8: None,  # 위 방향키 비활성화 (포탈 방지)
            9: None,  # 아래 방향키 비활성화 (불필요)
            10: self.keybindings.get('summon_dragon', 'home')
        }
        
        # 버프 쿨타임 체크
        if action in [5, 6, 7, 10]:
            current_time = time.time()
            if current_time - self.last_buff_time[action] < self.buff_cooldowns[action]:
                return
            self.last_buff_time[action] = current_time
        
        key = action_map.get(action)
        if key:
            if action == 4:  # 공격은 길게
                keyboard.press(key)
                time.sleep(0.3)
                keyboard.release(key)
            elif action == 3:  # 텔레포트는 방향키와 함께!
                # 마지막 이동 방향 기억 (없으면 랜덤)
                if not hasattr(self, 'last_move_direction'):
                    self.last_move_direction = 'right'
                
                direction_key = self.keybindings.get(f'move_{self.last_move_direction}', self.last_move_direction)
                
                # 방향키 + V 동시 입력
                keyboard.press(direction_key)
                keyboard.press(key)
                time.sleep(0.1)
                keyboard.release(key)
                keyboard.release(direction_key)
                
            elif action in [1, 2]:  # 좌우 이동만 (위/아래 비활성화)
                keyboard.press(key)
                time.sleep(0.05)
                keyboard.release(key)
                
                # 좌우 이동 시 방향 기억
                if action == 1:
                    self.last_move_direction = 'left'
                elif action == 2:
                    self.last_move_direction = 'right'
                    
            else:  # 버프는 탭
                keyboard.press(key)
                time.sleep(0.05)
                keyboard.release(key)
    
    def _calculate_reward(self, action, current_frame):
        """보상 계산 (경험치 획득 중심 + 행동 패턴 유도)"""
        reward = 0.0
        
        # 1. 경험치 획득 감지 (핵심!)
        exp_reward = self._detect_exp_gain(current_frame)
        if exp_reward > 0:
            reward += exp_reward
            print(f"🎉 몬스터 처치! +{exp_reward}")
        
        # 2. 화면 변화 감지 (움직임/전투/벽 충돌)
        change_score = 0.0
        if self.last_frame is not None:
            diff = cv2.absdiff(current_frame, self.last_frame)
            change_score = np.mean(diff) / 255.0
            
            # 벽 충돌 감지 (이동/텔포 했는데 화면 변화 없음)
            if action in [1, 2, 3] and change_score < 0.03:
                self.stuck_count += 1
                reward -= 0.8  # 벽 충돌 강한 페널티
                if self.stuck_count > 2:
                    reward -= 1.2  # 계속 벽에 박으면 매우 큰 페널티
                print(f"🧱 벽 충돌 감지! (연속 {self.stuck_count}회)")
            else:
                self.stuck_count = max(0, self.stuck_count - 1)  # 회복
            
            # 공격 중 화면 변화 = 타격 이펙트
            if action == 4 and change_score > 0.1:
                reward += 0.4
            
            # 텔포 후 화면 변화 = 이동 성공
            if action == 3 and change_score > 0.2:
                reward += 0.3
            
            # 정적 화면 = 정지 상태 (더 강한 페널티)
            if change_score < 0.05 and action != 4:  # 공격 중이 아닌데 정적
                reward -= 0.1
        
        # 3. 행동 시퀀스 보상 (효율적인 패턴 학습)
        if len(self.action_history) >= 2:
            prev_action = self.action_history[-1]
            
            # 텔레포트 → 공격 콤보 (핵심 패턴!)
            if prev_action == 3 and action == 4:
                reward += 0.8
                print("⚡ 텔포→공격 콤보!")
            
            # 이동 → 공격 (좋은 패턴)
            elif prev_action in [1, 2] and action == 4:
                reward += 0.3
            
            # 공격 → 이동/텔포 (다음 몬스터 찾기)
            elif prev_action == 4 and action in [1, 2, 3]:
                reward += 0.2
            
            # 같은 행동 반복 (다양성 부족)
            recent_actions = list(self.action_history)[-5:]
            if len(set(recent_actions)) == 1 and action == recent_actions[0]:
                reward -= 0.15  # 단조로움 페널티
        
        # 4. 행동별 기본 보상 (적극적 플레이 유도)
        if action == 4:  # 공격
            reward += 0.6  # 공격을 더 장려
        elif action == 3:  # 텔포
            reward += 0.2
        elif action in [1, 2]:  # 이동
            reward += 0.08
        elif action == 0:  # idle
            reward -= 0.3  # idle을 더 강하게 억제
        
        # 행동 이력 업데이트
        self.action_history.append(action)
        self.last_action = action
        self.last_action_time = time.time()
        
        return reward
    
    def _detect_exp_gain(self, frame):
        """경험치 획득 감지 (노란색 바 증가) - 몬스터 처치의 증거!"""
        if not self.roi_settings or 'exp_bar' not in self.roi_settings:
            return 0.0
        
        roi = self.roi_settings['exp_bar']
        x, y, w, h = roi['x'], roi['y'], roi['w'], roi['h']
        
        # 경험치 바 영역 추출
        exp_roi = frame[y:y+h, x:x+w]
        
        # 최적화: ROI만 HSV 변환
        hsv_roi = cv2.cvtColor(exp_roi, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        mask = cv2.inRange(hsv_roi, lower_yellow, upper_yellow)
        yellow_pixels = np.sum(mask > 0)
        
        # 이전 프레임과 비교
        reward = 0.0
        if self.last_exp_pixels is not None:
            pixel_diff = yellow_pixels - self.last_exp_pixels
            if pixel_diff > 10:  # 임계값 낮춤 (경험치통이 큰 경우 대응)
                reward = 2.0  # 매우 큰 보상!
            elif pixel_diff > 5:  # 작은 증가도 감지
                reward = 0.5
        
        self.last_exp_pixels = yellow_pixels
        return reward
    
    def _check_danger_monster(self, frame):
        """위험 몬스터 감지 및 긴급 귀환"""
        current_time = time.time()
        
        # 1초마다 체크 (CPU 부하 방지)
        if current_time - self.last_danger_check < self.danger_check_interval:
            return
        
        self.last_danger_check = current_time
        
        # 템플릿이 없으면 패스
        if self.danger_monster_template is None:
            return
        
        # 템플릿 매칭 (컬러)
        result = cv2.matchTemplate(frame, self.danger_monster_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 디버깅: 매 체크마다 일치도 출력 (10초에 한 번)
        if not hasattr(self, '_last_debug_print'):
            self._last_debug_print = 0
        if current_time - self._last_debug_print > 10:
            print(f"🔍 WARNING 감지 체크 중... (최대 일치도: {max_val:.2f}, 임계값: 0.7)")
            self._last_debug_print = current_time
        
        # 임계값 이상이면 위험 몬스터 감지!
        if max_val > 0.7:  # 70% 이상 일치 (오탐지 방지)
            self.danger_detection_count += 1
            print(f"⚠️  WARNING 감지 ({self.danger_detection_count}/2회, 일치도: {max_val:.2f})")
            
            # 연속 2회 감지 시에만 회피 행동 (오탐지 방지)
            if self.danger_detection_count >= 2:
                print(f"🚨 WARNING 몬스터 확정! 회피 시작...")
                self._emergency_escape(frame)
                self.danger_detection_count = 0  # 카운터 리셋
        else:
            # 감지되지 않으면 카운터 리셋
            if self.danger_detection_count > 0:
                self.danger_detection_count = 0
    
    def _emergency_escape(self, frame):
        """위협 회피 처리 (NPC 클릭 → 대화 수락 → 학습 계속)"""
        print("⚡ 위협 회피 시작...")
        
        # 1단계: NPC 템플릿 매칭 (화면에 항상 존재)
        if self.npc_template is None:
            print("❌ NPC 템플릿 없음")
            return
        
        try:
            result = cv2.matchTemplate(frame, self.npc_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.5:  # NPC 발견 (임계값 낮춤)
                # NPC 중심 좌표 계산
                npc_h, npc_w = self.npc_template.shape[:2]
                npc_x = max_loc[0] + npc_w // 2
                npc_y = max_loc[1] + npc_h // 2
                
                print(f"📍 NPC 클릭 (x={npc_x}, y={npc_y}, 일치도={max_val:.2f})")
                pyautogui.click(npc_x, npc_y)
                time.sleep(0.5)
                
                # 2단계: 대화창 확인 후 수락 버튼 클릭
                screenshot = self.sct.grab(self.monitor)
                new_frame = np.array(screenshot)
                new_frame = cv2.cvtColor(new_frame, cv2.COLOR_BGRA2BGR)
                
                if self.dialog_template is not None:
                    result2 = cv2.matchTemplate(new_frame, self.dialog_template, cv2.TM_CCOEFF_NORMED)
                    min_val2, max_val2, min_loc2, max_loc2 = cv2.minMaxLoc(result2)
                    
                    if max_val2 > 0.5:  # 대화창 발견 (임계값 낮춤)
                        # 수락 버튼 중심 좌표
                        dialog_h, dialog_w = self.dialog_template.shape[:2]
                        dialog_x = max_loc2[0] + dialog_w // 2
                        dialog_y = max_loc2[1] + dialog_h // 2
                        
                        print(f"📍 수락 버튼 클릭 (x={dialog_x}, y={dialog_y}, 일치도={max_val2:.2f})")
                        pyautogui.click(dialog_x, dialog_y)
                        time.sleep(0.5)
                        
                        print("✅ 위협 회피 완료! 학습 계속...")
                    else:
                        print(f"⚠️ 대화창을 찾을 수 없음 (최대 일치도: {max_val2:.2f})")
            else:
                print(f"⚠️ NPC를 찾을 수 없음 (최대 일치도: {max_val:.2f})")
                print(f"   템플릿 크기: {self.npc_template.shape}")
                print(f"   프레임 크기: {frame.shape}")
            
        except Exception as e:
            import traceback
            print(f"❌ 위협 회피 실패: {e}")
            print(traceback.format_exc())
    
    def close(self):
        """환경 종료"""
        self.sct.close()
        # 모든 키 해제
        for key in ['left', 'right', 'up', 'down', 'a', 'v', 'd', 'shift', 'alt', 'home']:
            try:
                keyboard.release(key)
            except:
                pass


if __name__ == "__main__":
    # 테스트
    env = RealtimeGameEnv(game="ML")
    obs, info = env.reset()
    
    print("🎮 실시간 환경 테스트")
    print(f"관측 공간: {obs.shape}")
    print(f"행동 공간: {env.action_space.n}")
    
    for i in range(10):
        action = env.action_space.sample()
        obs, reward, done, truncated, info = env.step(action)
        print(f"Step {i+1}: action={action}, reward={reward:.3f}")
        
        if done:
            break
    
    env.close()
    print("✅ 테스트 완료")
