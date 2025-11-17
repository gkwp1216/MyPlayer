"""
OCR 기반 보상 함수
HP, 경험치 변화를 감지하여 실제 보상 계산
"""
import cv2
import numpy as np
from PIL import Image
import pytesseract
import re


class GameStateDetector:
    """게임 상태 감지 (HP, 경험치 등)"""
    
    def __init__(self):
        # Tesseract 경로 설정 (Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # ROI 영역 (게임에 맞게 조정 필요)
        self.hp_roi = None  # (x, y, w, h)
        self.exp_roi = None
        
        self.last_hp = None
        self.last_exp = None
    
    def detect_hp(self, frame):
        """HP 감지"""
        if self.hp_roi is None:
            return None
        
        x, y, w, h = self.hp_roi
        roi = frame[y:y+h, x:x+w]
        
        # 전처리
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # OCR
        text = pytesseract.image_to_string(binary, config='--psm 7 digits')
        
        # 숫자 추출
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        return None
    
    def detect_exp(self, frame):
        """경험치 감지"""
        if self.exp_roi is None:
            return None
        
        x, y, w, h = self.exp_roi
        roi = frame[y:y+h, x:x+w]
        
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        text = pytesseract.image_to_string(binary, config='--psm 7')
        
        # 퍼센트 추출
        match = re.search(r'(\d+\.?\d*)%', text)
        if match:
            return float(match.group(1))
        return None
    
    def calculate_reward(self, frame):
        """프레임에서 보상 계산"""
        reward = 0.0
        
        # HP 변화
        current_hp = self.detect_hp(frame)
        if current_hp is not None and self.last_hp is not None:
            hp_change = current_hp - self.last_hp
            if hp_change < 0:  # HP 감소 (피격)
                reward -= 0.5
            elif hp_change > 0:  # HP 회복
                reward += 0.2
        self.last_hp = current_hp
        
        # 경험치 변화
        current_exp = self.detect_exp(frame)
        if current_exp is not None and self.last_exp is not None:
            exp_change = current_exp - self.last_exp
            if exp_change > 0:  # 경험치 획득 (몬스터 처치!)
                reward += 1.0  # 큰 보상
        self.last_exp = current_exp
        
        return reward
    
    def set_hp_roi(self, x, y, w, h):
        """HP 영역 설정"""
        self.hp_roi = (x, y, w, h)
    
    def set_exp_roi(self, x, y, w, h):
        """경험치 영역 설정"""
        self.exp_roi = (x, y, w, h)


# 더 간단한 방법: 픽셀 색상 기반 감지
class SimpleRewardDetector:
    """픽셀 색상 변화로 간단히 감지"""
    
    def __init__(self):
        self.exp_bar_roi = None  # 경험치 바 영역
        self.last_exp_pixels = None
        
    def set_exp_bar_roi(self, x, y, w, h):
        """경험치 바 영역 설정 (노란색/파란색 바)"""
        self.exp_bar_roi = (x, y, w, h)
    
    def detect_exp_gain(self, frame):
        """경험치 획득 감지 (색상 변화)"""
        if self.exp_bar_roi is None:
            return 0.0
        
        x, y, w, h = self.exp_bar_roi
        roi = frame[y:y+h, x:x+w]
        
        # 노란색 픽셀 카운트 (경험치 바)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        yellow_pixels = np.sum(mask > 0)
        
        # 이전 프레임과 비교
        reward = 0.0
        if self.last_exp_pixels is not None:
            if yellow_pixels > self.last_exp_pixels:
                # 경험치 바 증가 (몬스터 처치!)
                reward = 1.0
        
        self.last_exp_pixels = yellow_pixels
        return reward
    
    def detect_damage_taken(self, frame, player_roi):
        """피격 감지 (빨간색 이펙트)"""
        x, y, w, h = player_roi
        roi = frame[y:y+h, x:x+w]
        
        # 빨간색 픽셀 감지
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        mask = cv2.inRange(hsv, lower_red, upper_red)
        red_pixels = np.sum(mask > 0)
        
        # 빨간색 많으면 피격
        if red_pixels > 100:
            return -0.5
        return 0.0


if __name__ == "__main__":
    print("📊 보상 감지 시스템")
    print("\n사용 방법:")
    print("1. 게임 실행 후 HP/경험치 바 위치 확인")
    print("2. set_hp_roi(x, y, w, h) 로 영역 설정")
    print("3. calculate_reward(frame) 으로 보상 계산")
    print("\n예시:")
    print("  detector = SimpleRewardDetector()")
    print("  detector.set_exp_bar_roi(100, 950, 500, 20)")
    print("  reward = detector.detect_exp_gain(frame)")
