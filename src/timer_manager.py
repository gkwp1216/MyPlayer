"""
타이머 관리 모듈
인간화된 무작위 시간 간격으로 버프 및 스킬 사용 타이밍 관리
"""

import time
import random

class TimerManager:
    """Phase 1: 인간화된 타이머 골격"""
    
    def __init__(self, config):
        """
        타이머 초기화
        
        Args:
            config (dict): 타이머 설정 딕셔너리
        """
        self.buff_base = config['buff_base']
        self.buff_variance = config['buff_variance']
        self.skill_base = config['skill_base']
        self.skill_variance = config['skill_variance']
        
        # 초기 시간 설정
        current_time = time.time()
        self.last_buff_time = current_time
        self.last_skill_time = current_time
        
        # 첫 번째 딜레이 계산 (무작위)
        self.buff_next_delay = self._calculate_buff_delay()
        self.skill_next_delay = self._calculate_skill_delay()
    
    def _calculate_buff_delay(self):
        """버프 사용 다음 딜레이 계산 (무작위)"""
        return self.buff_base + random.uniform(-self.buff_variance, self.buff_variance)
    
    def _calculate_skill_delay(self):
        """스킬 사용 다음 딜레이 계산 (무작위)"""
        return self.skill_base + random.uniform(-self.skill_variance, self.skill_variance)
    
    def should_use_buff(self, current_time):
        """
        버프를 사용할 시간인지 확인
        
        Args:
            current_time (float): 현재 시간 (time.time())
        
        Returns:
            bool: 버프 사용 여부
        """
        return (current_time - self.last_buff_time) >= self.buff_next_delay
    
    def should_use_skill(self, current_time):
        """
        스킬을 사용할 시간인지 확인
        
        Args:
            current_time (float): 현재 시간 (time.time())
        
        Returns:
            bool: 스킬 사용 여부
        """
        return (current_time - self.last_skill_time) >= self.skill_next_delay
    
    def reset_buff_timer(self, current_time):
        """
        버프 타이머 리셋 및 다음 딜레이 재계산
        
        Args:
            current_time (float): 현재 시간 (time.time())
        """
        self.last_buff_time = current_time
        self.buff_next_delay = self._calculate_buff_delay()
    
    def reset_skill_timer(self, current_time):
        """
        스킬 타이머 리셋 및 다음 딜레이 재계산
        
        Args:
            current_time (float): 현재 시간 (time.time())
        """
        self.last_skill_time = current_time
        self.skill_next_delay = self._calculate_skill_delay()
    
    def get_next_buff_delay(self):
        """다음 버프까지 남은 시간 반환"""
        return self.buff_next_delay
    
    def get_next_skill_delay(self):
        """다음 스킬까지 남은 시간 반환"""
        return self.skill_next_delay
