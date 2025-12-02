"""
실시간 강화학습 환경 - 공통 베이스 클래스
화면 캡처, 프레임 처리 등 게임 공통 로직
"""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import cv2
import mss
import time
from collections import deque
import keyboard
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.config_loader import load_config


class BaseRealtimeEnv(gym.Env):
    """실시간 게임 플레이 환경 베이스 클래스"""
    
    metadata = {'render.modes': ['human']}
    
    def __init__(self, game, frame_width=84, frame_height=84, frame_stack=4, frame_skip=4):
        super().__init__()
        
        self.game = game
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_stack = frame_stack
        self.frame_skip = frame_skip
        
        # 설정 로드
        self.config = load_config(game=game)
        self.keybindings = self.config.get('keybindings', {})
        
        # 행동/관측 공간은 자식 클래스에서 정의
        self.action_space = None
        self.observation_space = None
        
        # 화면 캡처
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]
        
        # 프레임 버퍼
        self.frame_buffer = deque(maxlen=frame_stack)
        
        # 상태 추적
        self.last_frame = None
        self.step_count = 0
        self.episode_reward = 0
        
        # 행동 이력
        self.action_history = deque(maxlen=10)
        self.last_action = None
        self.last_action_time = 0
        
        # ROI 설정 로드
        self.roi_settings = self._load_roi_settings()
        
        print(f"✅ {game} 환경 베이스 초기화 완료")
        if self.roi_settings:
            print(f"📍 ROI 설정 로드: {list(self.roi_settings.keys())}")
    
    def _load_roi_settings(self):
        """ROI 설정 로드"""
        config_path = Path("configs/roi_settings.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return None
    
    def _load_template(self, path):
        """템플릿 이미지 로드"""
        template_path = Path(path)
        if template_path.exists():
            template = cv2.imread(str(template_path))
            if template is not None:
                return template
        return None
    
    def _preprocess_frame(self, frame):
        """프레임 전처리 (그레이스케일 + 리사이즈)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (self.frame_width, self.frame_height))
        return resized
    
    def _get_observation(self):
        """현재 관측 반환"""
        return np.array(self.frame_buffer, dtype=np.uint8)
    
    def _capture_frame(self):
        """화면 캡처 및 전처리"""
        screenshot = self.sct.grab(self.monitor)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame
    
    def reset(self, seed=None, options=None):
        """환경 초기화 (자식 클래스에서 오버라이드)"""
        super().reset(seed=seed)
        
        self.step_count = 0
        self.episode_reward = 0
        self.action_history.clear()
        
        # 초기 프레임 캡처
        frame = self._capture_frame()
        processed = self._preprocess_frame(frame)
        
        self.frame_buffer.clear()
        for _ in range(self.frame_stack):
            self.frame_buffer.append(processed)
        
        self.last_frame = frame.copy()
        
        observation = self._get_observation()
        info = {}
        
        return observation, info
    
    def step(self, action):
        """행동 실행 (자식 클래스에서 오버라이드)"""
        raise NotImplementedError("step() must be implemented by subclass")
    
    def _execute_action(self, action):
        """행동 실행 (자식 클래스에서 오버라이드)"""
        raise NotImplementedError("_execute_action() must be implemented by subclass")
    
    def _calculate_reward(self, action, current_frame):
        """보상 계산 (자식 클래스에서 오버라이드)"""
        raise NotImplementedError("_calculate_reward() must be implemented by subclass")
    
    def close(self):
        """환경 종료"""
        self.sct.close()
        # 모든 키 해제
        common_keys = ['left', 'right', 'up', 'down', 'a', 'v', 'd', 'shift', 'alt', 'home']
        for key in common_keys:
            try:
                keyboard.release(key)
            except:
                pass
