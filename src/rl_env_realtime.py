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

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.config_loader import load_config


class RealtimeGameEnv(gym.Env):
    """실시간 게임 플레이 환경"""
    
    metadata = {'render.modes': ['human']}
    
    def __init__(self, game="ML", frame_width=84, frame_height=84, frame_stack=4):
        super().__init__()
        
        self.game = game
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_stack = frame_stack
        
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
        
        # ROI 설정 로드
        self.roi_settings = self._load_roi_settings()
        
        # 경험치 감지
        self.last_exp_pixels = None
        self.last_hp_pixels = None
        
        print("✅ 실시간 RL 환경 초기화 완료")
        if self.roi_settings:
            print(f"📍 ROI 설정 로드: {list(self.roi_settings.keys())}")
        else:
            print("⚠️  ROI 미설정 (기본 보상 함수 사용)")
    
    def _load_roi_settings(self):
        """ROI 설정 로드"""
        config_path = Path("configs/roi_settings.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return None
    
    def reset(self, seed=None, options=None):
        """환경 초기화"""
        super().reset(seed=seed)
        
        self.step_count = 0
        self.episode_reward = 0
        self.last_buff_time = {5: 0, 6: 0, 7: 0, 10: 0}
        
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
        # 1. 행동 실행
        self._execute_action(action)
        
        # 2. 약간의 대기 (게임이 반응할 시간)
        time.sleep(0.1)
        
        # 3. 다음 프레임 캡처
        screenshot = self.sct.grab(self.monitor)
        current_frame = np.array(screenshot)
        current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGRA2BGR)
        
        # 4. 보상 계산 (화면 변화 기반)
        reward = self._calculate_reward(action, current_frame)
        
        # 5. 프레임 버퍼 업데이트
        processed = self._preprocess_frame(current_frame)
        self.frame_buffer.append(processed)
        self.last_frame = current_frame.copy()
        
        # 6. 종료 조건 (일정 스텝 후)
        self.step_count += 1
        self.episode_reward += reward
        done = self.step_count >= 1000  # 1000 스텝 = 1 에피소드
        
        observation = self._get_observation()
        info = {'step': self.step_count, 'episode_reward': self.episode_reward}
        
        return observation, reward, done, False, info
    
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
        action_map = {
            0: None,
            1: self.keybindings.get('move_left', 'left'),
            2: self.keybindings.get('move_right', 'right'),
            3: self.keybindings.get('teleport', 'v'),
            4: self.keybindings.get('attack', 'a'),
            5: self.keybindings.get('buff_holy', 'd'),
            6: self.keybindings.get('buff_bless', 'shift'),
            7: self.keybindings.get('buff_invin', 'alt'),
            8: self.keybindings.get('move_up', 'up'),
            9: self.keybindings.get('move_down', 'down'),
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
            elif action in [1, 2, 8, 9]:  # 이동은 짧게
                keyboard.press(key)
                time.sleep(0.05)
                keyboard.release(key)
            else:  # 텔포/버프는 탭
                keyboard.press(key)
                time.sleep(0.05)
                keyboard.release(key)
    
    def _calculate_reward(self, action, current_frame):
        """보상 계산 (화면 변화 + 경험치/HP 감지)"""
        reward = 0.0
        
        # 1. 경험치 획득 감지 (가장 중요!)
        exp_reward = self._detect_exp_gain(current_frame)
        if exp_reward > 0:
            reward += exp_reward
            print(f"🎉 경험치 획득! +{exp_reward}")
        
        # 2. HP 감소 감지
        hp_penalty = self._detect_hp_loss(current_frame)
        if hp_penalty < 0:
            reward += hp_penalty
            print(f"💥 피격! {hp_penalty}")
        
        # 3. 화면 변화 감지 (움직임/전투)
        if self.last_frame is not None:
            diff = cv2.absdiff(current_frame, self.last_frame)
            change_score = np.mean(diff) / 255.0
            
            # 공격 중 화면 변화 많으면 보상 (몬스터 타격/이펙트)
            if action == 4 and change_score > 0.1:
                reward += 0.3
            
            # 텔포 후 화면 변화 (이동 성공)
            if action == 3 and change_score > 0.2:
                reward += 0.2
            
            # 너무 정적이면 패널티 (멈춰있음)
            if change_score < 0.05:
                reward -= 0.05
        
        # 4. 행동별 기본 보상
        if action in [3, 4]:  # 텔포, 공격
            reward += 0.1
        elif action in [1, 2]:  # 이동
            reward += 0.05
        elif action == 0:  # idle
            reward -= 0.1
        
        return reward
    
    def _detect_exp_gain(self, frame):
        """경험치 획득 감지 (노란색 바 증가)"""
        if not self.roi_settings or 'exp_bar' not in self.roi_settings:
            return 0.0
        
        roi = self.roi_settings['exp_bar']
        x, y, w, h = roi['x'], roi['y'], roi['w'], roi['h']
        
        # 경험치 바 영역 추출
        exp_roi = frame[y:y+h, x:x+w]
        
        # 노란색 픽셀 카운트
        hsv = cv2.cvtColor(exp_roi, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        yellow_pixels = np.sum(mask > 0)
        
        # 이전 프레임과 비교
        reward = 0.0
        if self.last_exp_pixels is not None:
            pixel_diff = yellow_pixels - self.last_exp_pixels
            if pixel_diff > 50:  # 충분한 증가
                reward = 1.0  # 큰 보상! (몬스터 처치)
        
        self.last_exp_pixels = yellow_pixels
        return reward
    
    def _detect_hp_loss(self, frame):
        """HP 감소 감지 (빨간색 바 감소)"""
        if not self.roi_settings or 'hp_bar' not in self.roi_settings:
            return 0.0
        
        roi = self.roi_settings['hp_bar']
        x, y, w, h = roi['x'], roi['y'], roi['w'], roi['h']
        
        # HP 바 영역 추출
        hp_roi = frame[y:y+h, x:x+w]
        
        # 빨간색 픽셀 카운트
        hsv = cv2.cvtColor(hp_roi, cv2.COLOR_BGR2HSV)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        red_pixels = np.sum(mask > 0)
        
        # 이전 프레임과 비교
        penalty = 0.0
        if self.last_hp_pixels is not None:
            pixel_diff = red_pixels - self.last_hp_pixels
            if pixel_diff < -50:  # HP 감소
                penalty = -0.5
            elif red_pixels < 100:  # HP 매우 낮음
                penalty = -1.0
        
        self.last_hp_pixels = red_pixels
        return penalty
    
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
