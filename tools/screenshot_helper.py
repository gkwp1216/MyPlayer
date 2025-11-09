"""
스크린샷 수집 도우미 도구
게임 화면을 빠르게 캡처하여 클래스별로 저장
"""

import os
import time
from datetime import datetime
from pathlib import Path
import mss
import numpy as np
from PIL import Image
from pynput import keyboard

class ScreenshotHelper:
    """빠른 스크린샷 수집을 위한 도우미"""
    
    def __init__(self, output_dir='datasets/raw'):
        """
        스크린샷 도우미 초기화
        
        Args:
            output_dir (str): 스크린샷 저장 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.sct = mss.mss()
        self.running = False
        
        # 현재 선택된 클래스
        self.current_class = 'skill_cooldown'
        self.classes = [
            'skill_cooldown',
            'buff_time_low',
            'exp_doping_active',
            'exp_doping_missing',
            'skill_ready'
        ]
        self.class_index = 0
        
        # 각 클래스별 카운터
        self.counters = {cls: 0 for cls in self.classes}
        
        # 디렉토리 생성
        for cls in self.classes:
            (self.output_dir / cls).mkdir(parents=True, exist_ok=True)
        
        print("=" * 60)
        print("🎬 스크린샷 수집 도우미")
        print("=" * 60)
        print("\n단축키:")
        print("  F5       : 현재 클래스로 스크린샷 저장")
        print("  F6       : 다음 클래스로 전환")
        print("  F7       : 이전 클래스로 전환")
        print("  F8       : 현재 상태 표시")
        print("  ESC      : 종료")
        print("=" * 60)
        
        self._print_status()
    
    def _print_status(self):
        """현재 상태 출력"""
        print(f"\n📂 현재 클래스: {self.current_class}")
        print(f"📸 저장된 스크린샷: {self.counters[self.current_class]}장")
        print("\n클래스별 수집 현황:")
        for cls in self.classes:
            count = self.counters[cls]
            status = "✅" if count >= 50 else "⏳"
            print(f"  {status} {cls:25s} : {count:3d}장")
    
    def next_class(self):
        """다음 클래스로 전환"""
        self.class_index = (self.class_index + 1) % len(self.classes)
        self.current_class = self.classes[self.class_index]
        print("\n" + "=" * 60)
        self._print_status()
    
    def prev_class(self):
        """이전 클래스로 전환"""
        self.class_index = (self.class_index - 1) % len(self.classes)
        self.current_class = self.classes[self.class_index]
        print("\n" + "=" * 60)
        self._print_status()
    
    def capture_screenshot(self):
        """현재 화면을 캡처하여 저장"""
        # 전체 화면 캡처
        monitor = self.sct.monitors[1]  # 주 모니터
        screenshot = self.sct.grab(monitor)
        
        # PIL 이미지로 변환
        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{self.current_class}_{timestamp}.png"
        filepath = self.output_dir / self.current_class / filename
        
        # 저장
        img.save(filepath)
        
        # 카운터 증가
        self.counters[self.current_class] += 1
        
        print(f"✅ 저장: {filename} ({self.counters[self.current_class]}장)")
        
        # 50장 달성 시 알림
        if self.counters[self.current_class] == 50:
            print(f"\n🎉 축하합니다! {self.current_class} 클래스 50장 달성!")
            print("   다음 클래스로 이동하려면 F6을 누르세요.\n")
    
    def on_press(self, key):
        """키보드 이벤트 핸들러"""
        try:
            if key == keyboard.Key.f5:
                self.capture_screenshot()
            elif key == keyboard.Key.f6:
                self.next_class()
            elif key == keyboard.Key.f7:
                self.prev_class()
            elif key == keyboard.Key.f8:
                self._print_status()
            elif key == keyboard.Key.esc:
                print("\n👋 스크린샷 수집을 종료합니다.")
                self.running = False
                return False
        except Exception as e:
            print(f"❌ 오류: {e}")
    
    def start(self):
        """스크린샷 수집 시작"""
        self.running = True
        
        print("\n✅ 스크린샷 수집 시작!")
        print("   메이플스토리를 실행하고 F5 키로 스크린샷을 저장하세요.\n")
        
        # 키보드 리스너 시작
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()
        
        # 최종 통계
        print("\n" + "=" * 60)
        print("📊 최종 수집 통계")
        print("=" * 60)
        total = 0
        for cls in self.classes:
            count = self.counters[cls]
            total += count
            status = "✅" if count >= 50 else "⚠️"
            print(f"{status} {cls:25s} : {count:3d}장")
        print("=" * 60)
        print(f"총 수집: {total}장")
        print("=" * 60)


def main():
    """메인 함수"""
    helper = ScreenshotHelper()
    helper.start()


if __name__ == "__main__":
    main()
