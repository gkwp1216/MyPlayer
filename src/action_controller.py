"""
행동 제어 모듈
키보드/마우스 입력을 통해 실제 행동 수행
"""

import time
import random
import pyautogui

class ActionController:
    """Phase 1 & 3: 실제 행동(키보드/마우스) 제어"""
    
    def __init__(self, keybindings, action_config):
        """
        행동 제어기 초기화
        
        Args:
            keybindings (dict): 키 바인딩 설정
            action_config (dict): 행동 관련 설정
        """
        self.buff_key = keybindings['buff_key']
        self.skill_key = keybindings['skill_key']
        
        self.mouse_move_duration_min = action_config['mouse_move_duration_min']
        self.mouse_move_duration_max = action_config['mouse_move_duration_max']
        self.skill_cast_delay_min = action_config['skill_cast_delay_min']
        self.skill_cast_delay_max = action_config['skill_cast_delay_max']
        
        # PyAutoGUI 안전 설정
        pyautogui.PAUSE = 0.1  # 각 PyAutoGUI 호출 간 기본 딜레이
        pyautogui.FAILSAFE = True  # 마우스를 화면 모서리로 이동하면 중단
    
    def use_buff(self):
        """
        30분 경험치 버프 사용
        """
        pyautogui.press(self.buff_key)
        # 버프 시전 후 짧은 딜레이
        time.sleep(random.uniform(0.05, 0.15))
    
    def use_skill_simple(self):
        """
        Phase 1: 단순 스킬 사용 (위치 지정 없음)
        """
        pyautogui.press(self.skill_key)
        time.sleep(random.uniform(self.skill_cast_delay_min, self.skill_cast_delay_max))
    
    def use_skill_at_position(self, position):
        """
        Phase 3: 특정 위치에 설치기 스킬 사용
        
        Args:
            position (tuple): (x, y) 화면 좌표
        """
        x, y = position
        
        # 1. 스킬 키 누르기
        pyautogui.press(self.skill_key)
        
        # 2. 스킬 시전 딜레이
        time.sleep(random.uniform(self.skill_cast_delay_min, self.skill_cast_delay_max))
        
        # 3. 인간처럼 마우스 이동
        duration = random.uniform(self.mouse_move_duration_min, self.mouse_move_duration_max)
        pyautogui.moveTo(x, y, duration=duration)
        
        # 4. 클릭
        time.sleep(random.uniform(0.05, 0.1))
        pyautogui.click()
    
    def move_mouse_humanlike(self, x, y):
        """
        인간처럼 마우스 이동
        
        Args:
            x (int): 목표 x 좌표
            y (int): 목표 y 좌표
        """
        duration = random.uniform(self.mouse_move_duration_min, self.mouse_move_duration_max)
        pyautogui.moveTo(x, y, duration=duration)
