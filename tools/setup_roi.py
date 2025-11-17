"""
ROI 설정 도구 (Tkinter GUI)
게임 화면에서 경험치 바, HP 바 위치를 마우스로 선택

사용법: py tools/setup_roi.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import mss
import json
from pathlib import Path
import win32gui
import numpy as np


def draw_rectangle(event, x, y, flags, param):
    """마우스 이벤트 핸들러"""
    global ix, iy, drawing, temp_img, current_roi_name, roi_boxes
    
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img_copy = temp_img.copy()
            cv2.rectangle(img_copy, (ix, iy), (x, y), (0, 255, 0), 2)
            cv2.imshow('ROI Setup', img_copy)
            
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.rectangle(temp_img, (ix, iy), (x, y), (0, 255, 0), 2)
        cv2.imshow('ROI Setup', temp_img)
        
        # ROI 저장
        x1, y1 = min(ix, x), min(iy, y)
        x2, y2 = max(ix, x), max(iy, y)
        w, h = x2 - x1, y2 - y1
        
        if current_roi_name:
            # 창 오프셋 추가 (전체 화면 좌표로 변환)
            global_x1 = x1 + window_offset['x']
            global_y1 = y1 + window_offset['y']
            
            roi_boxes[current_roi_name] = {
                'x': global_x1, 'y': global_y1, 'w': w, 'h': h
            }
            print(f"✅ {current_roi_name} 설정: x={global_x1}, y={global_y1}, w={w}, h={h}")


def list_windows():
    """열린 창 목록 표시"""
    windows = []
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append((hwnd, title))
    win32gui.EnumWindows(callback, windows)
    return windows


def capture_window(hwnd):
    """특정 창 캡처 (mss 사용)"""
    try:
        # 창 위치와 크기 가져오기
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        
        print(f"📐 창 위치: x={left}, y={top}, w={width}, h={height}")
        
        # mss로 해당 영역만 캡처
        with mss.mss() as sct:
            monitor = {
                'left': left,
                'top': top,
                'width': width,
                'height': height
            }
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        return img, left, top
    except Exception as e:
        print(f"⚠️ 창 캡처 실패: {e}")
        return None, 0, 0


def main():
    global temp_img, current_roi_name, roi_boxes, window_offset
    
    print("=" * 60)
    print("🎯 ROI 설정 도구")
    print("=" * 60)
    print("게임 화면에서 중요한 영역을 마우스로 드래그하여 선택하세요")
    print()
    
    # 창 목록 표시
    windows = list_windows()
    
    # 먼저 게임 창 찾기
    game_windows = [w for w in windows if 'ML' in w[1] or '메이플' in w[1] or 'MapleStory' in w[1].lower()]
    
    if game_windows:
        print("🎮 게임 창 감지:")
        for i, (hwnd, title) in enumerate(game_windows):
            print(f"  [{i+1}] {title}")
        print(f"  [0] 전체 화면 캡처")
        
        choice = input(f"\n선택 (0-{len(game_windows)}, 엔터=1): ").strip()
        
        if choice == '0':
            print("✅ 전체 화면 캡처 선택")
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            window_offset = {'x': 0, 'y': 0}
        else:
            idx = int(choice) - 1 if choice else 0
            hwnd, title = game_windows[idx]
            print(f"✅ 선택: {title}")
            
            # 선택한 창 캡처
            frame, left, top = capture_window(hwnd)
            if frame is None:
                print("❌ 창 캡처 실패, 전체 화면으로 진행합니다")
                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    left, top = 0, 0
            
            window_offset = {'x': left, 'y': top}
    else:
        print("⚠️ 게임 창을 자동으로 찾을 수 없습니다.")
        print("\n📋 모든 열린 창:")
        visible_windows = [(i, w) for i, w in enumerate(windows) if len(w[1]) > 2][:20]  # 상위 20개
        for i, (hwnd, title) in visible_windows:
            print(f"  [{i+1}] {title[:60]}")
        print(f"  [0] 전체 화면 캡처")
        
        choice = input(f"\n선택 (0-{len(visible_windows)}, 엔터=0): ").strip()
        
        if not choice or choice == '0':
            print("✅ 전체 화면 캡처")
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            window_offset = {'x': 0, 'y': 0}
        else:
            idx = int(choice) - 1
            hwnd, title = visible_windows[idx][1]
            print(f"✅ 선택: {title}")
            
            frame, left, top = capture_window(hwnd)
            if frame is None:
                print("❌ 창 캡처 실패, 전체 화면으로 진행합니다")
                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    left, top = 0, 0
            
            window_offset = {'x': left, 'y': top}
    
    temp_img = frame.copy()
    
    cv2.namedWindow('ROI Setup')
    cv2.setMouseCallback('ROI Setup', draw_rectangle)
    
    print("📝 설정할 ROI:")
    print("  1. 경험치 바 (노란색/파란색 바)")
    print("  2. HP 바 (빨간색 바)")
    print("  3. 플레이어 위치 (캐릭터 중심)")
    print()
    
    roi_names = ['exp_bar', 'hp_bar', 'player']
    roi_descriptions = {
        'exp_bar': '경험치 바를 드래그하세요',
        'hp_bar': 'HP 바를 드래그하세요',
        'player': '플레이어 캐릭터를 드래그하세요'
    }
    
    for roi_name in roi_names:
        current_roi_name = roi_name
        temp_img = frame.copy()
        
        # 이전 ROI 표시
        for name, box in roi_boxes.items():
            cv2.rectangle(temp_img, 
                         (box['x'], box['y']), 
                         (box['x'] + box['w'], box['y'] + box['h']), 
                         (255, 0, 0), 2)
            cv2.putText(temp_img, name, 
                       (box['x'], box['y'] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        print(f"\n📍 {roi_descriptions[roi_name]}")
        print("   드래그 후 엔터를 누르세요 (건너뛰기: s)")
        
        cv2.imshow('ROI Setup', temp_img)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 13:  # Enter
                break
            elif key == ord('s'):  # Skip
                print(f"⏭️  {roi_name} 건너뜀")
                break
            elif key == 27:  # ESC
                print("\n❌ 취소됨")
                cv2.destroyAllWindows()
                return
    
    cv2.destroyAllWindows()
    
    # 저장
    if roi_boxes:
        config_path = Path("configs/roi_settings.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(roi_boxes, f, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ ROI 설정 저장 완료!")
        print(f"📁 저장 위치: {config_path}")
        print("=" * 60)
        print("\n설정된 ROI:")
        for name, box in roi_boxes.items():
            print(f"  {name}: x={box['x']}, y={box['y']}, w={box['w']}, h={box['h']}")
        
        print("\n💡 다음 단계:")
        print("  1. 게임을 실행하고 캐릭터를 안전한 위치에 배치")
        print("  2. py tools/train_realtime_rl.py --timesteps 10000 실행")
    else:
        print("\n⚠️  설정된 ROI가 없습니다")


if __name__ == "__main__":
    main()
