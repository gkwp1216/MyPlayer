"""
MP 게임 전용 실시간 강화학습 환경
메이플스토리 사냥 전용 행동 및 보상 체계
"""
from gymnasium import spaces
import numpy as np
import cv2
import time
import keyboard
from pathlib import Path

from src.rl_env_base import BaseRealtimeEnv


class MPRealtimeEnv(BaseRealtimeEnv):
    """MP 게임 실시간 환경"""
    
    def __init__(self, frame_width=84, frame_height=84, frame_stack=4, frame_skip=4):
        super().__init__(
            game="MP",
            frame_width=frame_width,
            frame_height=frame_height,
            frame_stack=frame_stack,
            frame_skip=frame_skip
        )
        
        # MP 전용 행동 공간 (기본 8개로 시작)
        # 0: idle, 1: left, 2: right, 3: up, 4: down
        # 5: attack, 6: skill_1, 7: jump
        self.action_space = spaces.Discrete(8)
        
        # 관측 공간: 그레이스케일 프레임 스택
        self.observation_space = spaces.Box(
            low=0, high=255,
            shape=(frame_stack, frame_height, frame_width),
            dtype=np.uint8
        )
        
        # MP 전용 상태
        self.last_move_direction = 'right'
        self.stuck_count = 0
        self.last_exp_pixels = None
        
        print("✅ MP 환경 초기화 완료")
        print("📋 행동 공간: 0=idle, 1=left, 2=right, 3=up, 4=down, 5=attack, 6=skill, 7=jump")
    
    def reset(self, seed=None, options=None):
        """MP 환경 초기화"""
        obs, info = super().reset(seed, options)
        
        # MP 전용 상태 리셋
        self.last_move_direction = 'right'
        self.stuck_count = 0
        self.last_exp_pixels = None
        
        return obs, info
    
    def step(self, action):
        """행동 실행 및 보상 계산"""
        total_reward = 0.0
        done = False
        
        for _ in range(self.frame_skip):
            self._execute_action(action)
            time.sleep(0.01)
            
            current_frame = self._capture_frame()
            
            # 보상 누적
            step_reward = self._calculate_reward(action, current_frame)
            total_reward += step_reward
            
            # 프레임 버퍼 업데이트
            processed = self._preprocess_frame(current_frame)
            self.frame_buffer.append(processed)
            self.last_frame = current_frame.copy()
            
            # 종료 조건
            self.step_count += 1
            if self.step_count >= 1000:
                done = True
                break
        
        self.episode_reward += total_reward
        observation = self._get_observation()
        info = {'step': self.step_count, 'episode_reward': self.episode_reward}
        
        return observation, total_reward, done, False, info
    
    def _execute_action(self, action):
        """MP 전용 행동 실행"""
        action_map = {
            0: None,  # idle
            1: self.keybindings.get('move_left', 'left'),
            2: self.keybindings.get('move_right', 'right'),
            3: self.keybindings.get('move_up', 'up'),
            4: self.keybindings.get('move_down', 'down'),
            5: self.keybindings.get('attack', 'ctrl'),  # MP 기본 공격
            6: self.keybindings.get('skill_key', 'a'),   # 주력 스킬
            7: self.keybindings.get('jump', 'alt')       # 점프
        }
        
        key = action_map.get(action)
        if key:
            if action == 5:  # 공격
                keyboard.press(key)
                time.sleep(0.2)
                keyboard.release(key)
            elif action == 6:  # 스킬
                keyboard.press(key)
                time.sleep(0.15)
                keyboard.release(key)
            elif action == 7:  # 점프
                keyboard.press(key)
                time.sleep(0.1)
                keyboard.release(key)
            elif action in [1, 2, 3, 4]:  # 이동
                keyboard.press(key)
                time.sleep(0.05)
                keyboard.release(key)
                
                # 좌우 방향 기억
                if action == 1:
                    self.last_move_direction = 'left'
                elif action == 2:
                    self.last_move_direction = 'right'
    
    def _calculate_reward(self, action, current_frame):
        """MP 전용 보상 계산"""
        reward = 0.0
        
        # 1. 경험치 획득 (최우선!)
        exp_reward = self._detect_exp_gain(current_frame)
        if exp_reward > 0:
            reward += exp_reward
            print(f"🎉 몬스터 처치! +{exp_reward}")
        
        # 2. 화면 변화 감지
        change_score = 0.0
        if self.last_frame is not None:
            diff = cv2.absdiff(current_frame, self.last_frame)
            change_score = np.mean(diff) / 255.0
            
            # 벽 충돌 감지
            if action in [1, 2] and change_score < 0.03:
                self.stuck_count += 1
                reward -= 0.5
                if self.stuck_count > 3:
                    reward -= 0.8
            else:
                self.stuck_count = max(0, self.stuck_count - 1)
            
            # 공격/스킬 중 타격 이펙트
            if action in [5, 6] and change_score > 0.1:
                reward += 0.3
            
            # 정적 화면 페널티
            if change_score < 0.05 and action not in [5, 6]:
                reward -= 0.08
        
        # 3. 행동 시퀀스 보상
        if len(self.action_history) >= 2:
            prev_action = self.action_history[-1]
            
            # 이동→공격/스킬 (좋은 패턴)
            if prev_action in [1, 2] and action in [5, 6]:
                reward += 0.4
            
            # 공격→이동 (다음 몬스터)
            elif prev_action in [5, 6] and action in [1, 2]:
                reward += 0.2
            
            # 단조로움 페널티
            recent_actions = list(self.action_history)[-5:]
            if len(set(recent_actions)) == 1 and action == recent_actions[0]:
                reward -= 0.12
        
        # 4. 행동별 기본 보상
        if action in [5, 6]:  # 공격/스킬
            reward += 0.5
        elif action in [1, 2]:  # 좌우 이동
            reward += 0.1
        elif action == 7:  # 점프
            reward += 0.05
        elif action == 0:  # idle
            reward -= 0.25
        
        # 행동 이력 업데이트
        self.action_history.append(action)
        self.last_action = action
        self.last_action_time = time.time()
        
        return reward
    
    def _detect_exp_gain(self, frame):
        """경험치 획득 감지 (노란색 바 증가)"""
        if not self.roi_settings or 'exp_bar' not in self.roi_settings:
            return 0.0
        
        roi = self.roi_settings['exp_bar']
        x, y, w, h = roi['x'], roi['y'], roi['w'], roi['h']
        
        exp_roi = frame[y:y+h, x:x+w]
        hsv_roi = cv2.cvtColor(exp_roi, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        mask = cv2.inRange(hsv_roi, lower_yellow, upper_yellow)
        yellow_pixels = np.sum(mask > 0)
        
        reward = 0.0
        if self.last_exp_pixels is not None:
            pixel_diff = yellow_pixels - self.last_exp_pixels
            if pixel_diff > 10:
                reward = 2.0
            elif pixel_diff > 5:
                reward = 0.5
        
        self.last_exp_pixels = yellow_pixels
        return reward


if __name__ == "__main__":
    # 테스트
    env = MPRealtimeEnv()
    obs, info = env.reset()
    
    print("🎮 MP 환경 테스트")
    print(f"관측 공간: {obs.shape}")
    print(f"행동 공간: {env.action_space.n}")
    
    for i in range(5):
        action = env.action_space.sample()
        obs, reward, done, truncated, info = env.step(action)
        print(f"Step {i+1}: action={action}, reward={reward:.3f}")
        
        if done:
            break
    
    env.close()
    print("✅ 테스트 완료")
