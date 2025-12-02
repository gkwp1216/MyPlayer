"""
ML 게임 전용 실시간 강화학습 환경
비숍 캐릭터 전용 행동 및 보상 체계
"""
from gymnasium import spaces
import numpy as np
import cv2
import time
import keyboard
import pyautogui
from pathlib import Path

from src.rl_env_base import BaseRealtimeEnv


class MLRealtimeEnv(BaseRealtimeEnv):
    """ML 게임 실시간 환경 (비숍)"""
    
    def __init__(self, frame_width=84, frame_height=84, frame_stack=4, frame_skip=4):
        super().__init__(
            game="ML",
            frame_width=frame_width,
            frame_height=frame_height,
            frame_stack=frame_stack,
            frame_skip=frame_skip
        )
        
        # ML 전용 행동 공간: 11개
        # 0: idle, 1: left, 2: right, 3: teleport, 4: attack,
        # 5: buff_holy, 6: buff_bless, 7: buff_invin, 8/9: up/down(disabled), 10: summon_dragon
        self.action_space = spaces.Discrete(11)
        
        # 관측 공간: 그레이스케일 프레임 스택
        self.observation_space = spaces.Box(
            low=0, high=255,
            shape=(frame_stack, frame_height, frame_width),
            dtype=np.uint8
        )
        
        # ML 전용 버프 쿨타임 (비숍 스킬)
        self.buff_cooldowns = {
            5: 120,   # 홀리심볼 (2분)
            6: 180,   # 블레스 (3분)
            7: 300,   # 인빈서블 (5분)
            10: 150   # 서먼 드래곤 (2.5분)
        }
        self.last_buff_time = {5: 0, 6: 0, 7: 0, 10: 0}
        
        # ML 전용 상태
        self.last_move_direction = 'right'
        self.stuck_count = 0
        self.last_exp_pixels = None
        
        # WARNING 몬스터 회피 시스템
        self.danger_monster_template = self._load_template("assets/WARNING.png")
        self.npc_template = self._load_template("assets/IFWARNINGappearClick.png")
        self.dialog_template = self._load_template("assets/IFWARNINGappearClick_2.png")
        self.last_danger_check = 0
        self.danger_check_interval = 1.0
        self.danger_detection_count = 0
        
        templates_loaded = sum([
            self.danger_monster_template is not None,
            self.npc_template is not None,
            self.dialog_template is not None
        ])
        if templates_loaded == 3:
            print("🛡️ WARNING 몬스터 회피 시스템 활성화")
        
        print("✅ ML 환경 초기화 완료 (비숍 전용)")
    
    def reset(self, seed=None, options=None):
        """ML 환경 초기화"""
        obs, info = super().reset(seed, options)
        
        # ML 전용 상태 리셋
        self.last_buff_time = {5: 0, 6: 0, 7: 0, 10: 0}
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
            
            # WARNING 몬스터 감지
            self._check_danger_monster(current_frame)
            
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
        """ML 전용 행동 실행 (비숍 스킬)"""
        # 위 방향키 차단 (포탈 방지)
        if action == 8:
            return
        
        action_map = {
            0: None,
            1: self.keybindings.get('move_left', 'left'),
            2: self.keybindings.get('move_right', 'right'),
            3: self.keybindings.get('teleport', 'v'),
            4: self.keybindings.get('attack', 'a'),
            5: self.keybindings.get('buff_holy', 'd'),
            6: self.keybindings.get('buff_bless', 'shift'),
            7: self.keybindings.get('buff_invin', 'alt'),
            8: None,  # 위 방향키 비활성화
            9: None,  # 아래 방향키 비활성화
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
            if action == 4:  # 공격
                keyboard.press(key)
                time.sleep(0.3)
                keyboard.release(key)
            elif action == 3:  # 텔레포트 (방향키 + V)
                direction_key = self.keybindings.get(f'move_{self.last_move_direction}', self.last_move_direction)
                keyboard.press(direction_key)
                keyboard.press(key)
                time.sleep(0.1)
                keyboard.release(key)
                keyboard.release(direction_key)
            elif action in [1, 2]:  # 좌우 이동
                keyboard.press(key)
                time.sleep(0.05)
                keyboard.release(key)
                
                # 방향 기억
                if action == 1:
                    self.last_move_direction = 'left'
                elif action == 2:
                    self.last_move_direction = 'right'
            else:  # 버프
                keyboard.press(key)
                time.sleep(0.05)
                keyboard.release(key)
    
    def _calculate_reward(self, action, current_frame):
        """ML 전용 보상 계산 (비숍 사냥 패턴)"""
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
            
            # 벽 충돌 감지 (강한 페널티)
            if action in [1, 2, 3] and change_score < 0.03:
                self.stuck_count += 1
                reward -= 0.8
                if self.stuck_count > 2:
                    reward -= 1.2
                print(f"🧱 벽 충돌 감지! (연속 {self.stuck_count}회)")
            else:
                self.stuck_count = max(0, self.stuck_count - 1)
            
            # 공격 중 타격 이펙트
            if action == 4 and change_score > 0.1:
                reward += 0.4
            
            # 텔포 후 이동 성공
            if action == 3 and change_score > 0.2:
                reward += 0.3
            
            # 정적 화면 페널티
            if change_score < 0.05 and action != 4:
                reward -= 0.1
        
        # 3. 행동 시퀀스 보상 (비숍 콤보)
        if len(self.action_history) >= 2:
            prev_action = self.action_history[-1]
            
            # 텔포→공격 콤보 (핵심!)
            if prev_action == 3 and action == 4:
                reward += 0.8
                print("⚡ 텔포→공격 콤보!")
            
            # 이동→공격
            elif prev_action in [1, 2] and action == 4:
                reward += 0.3
            
            # 공격→이동/텔포
            elif prev_action == 4 and action in [1, 2, 3]:
                reward += 0.2
            
            # 단조로움 페널티
            recent_actions = list(self.action_history)[-5:]
            if len(set(recent_actions)) == 1 and action == recent_actions[0]:
                reward -= 0.15
        
        # 4. 행동별 기본 보상
        if action == 4:  # 공격
            reward += 0.6
        elif action == 3:  # 텔포
            reward += 0.2
        elif action in [1, 2]:  # 이동
            reward += 0.08
        elif action == 0:  # idle
            reward -= 0.3
        
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
    
    def _check_danger_monster(self, frame):
        """WARNING 몬스터 감지"""
        current_time = time.time()
        
        if current_time - self.last_danger_check < self.danger_check_interval:
            return
        
        self.last_danger_check = current_time
        
        if self.danger_monster_template is None:
            return
        
        result = cv2.matchTemplate(frame, self.danger_monster_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val > 0.7:
            self.danger_detection_count += 1
            print(f"⚠️  WARNING 감지 ({self.danger_detection_count}/2회, 일치도: {max_val:.2f})")
            
            if self.danger_detection_count >= 2:
                print(f"🚨 WARNING 몬스터 확정! 회피 시작...")
                self._emergency_escape(frame)
                self.danger_detection_count = 0
        else:
            if self.danger_detection_count > 0:
                self.danger_detection_count = 0
    
    def _emergency_escape(self, frame):
        """위협 회피 (NPC 클릭 → 대화 수락)"""
        print("⚡ 위협 회피 시작...")
        
        if self.npc_template is None:
            print("❌ NPC 템플릿 없음")
            return
        
        try:
            result = cv2.matchTemplate(frame, self.npc_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.5:
                npc_h, npc_w = self.npc_template.shape[:2]
                npc_x = max_loc[0] + npc_w // 2
                npc_y = max_loc[1] + npc_h // 2
                
                print(f"📍 NPC 클릭 (x={npc_x}, y={npc_y})")
                pyautogui.click(npc_x, npc_y)
                time.sleep(0.5)
                
                # 대화창 수락
                new_frame = self._capture_frame()
                
                if self.dialog_template is not None:
                    result2 = cv2.matchTemplate(new_frame, self.dialog_template, cv2.TM_CCOEFF_NORMED)
                    min_val2, max_val2, min_loc2, max_loc2 = cv2.minMaxLoc(result2)
                    
                    if max_val2 > 0.5:
                        dialog_h, dialog_w = self.dialog_template.shape[:2]
                        dialog_x = max_loc2[0] + dialog_w // 2
                        dialog_y = max_loc2[1] + dialog_h // 2
                        
                        print(f"📍 수락 버튼 클릭 (x={dialog_x}, y={dialog_y})")
                        pyautogui.click(dialog_x, dialog_y)
                        time.sleep(0.5)
                        print("✅ 위협 회피 완료!")
        
        except Exception as e:
            print(f"❌ 위협 회피 실패: {e}")


if __name__ == "__main__":
    # 테스트
    env = MLRealtimeEnv()
    obs, info = env.reset()
    
    print("🎮 ML 환경 테스트")
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
