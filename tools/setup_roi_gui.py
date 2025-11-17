"""
ROI 설정 도구 (Tkinter GUI)
게임 화면에서 경험치 바, HP 바 위치를 직관적으로 선택

사용법: py tools/setup_roi_gui.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import mss
import json
from pathlib import Path
import win32gui


class ROISetupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 ROI 설정 도구")
        self.root.geometry("1400x900")
        
        # 변수
        self.screenshot = None
        self.photo = None
        self.draw_image = None
        self.canvas = None
        self.roi_boxes = {}
        self.current_roi = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.window_offset = {'x': 0, 'y': 0}
        self.scale_factor = 1.0
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        # 상단 프레임
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="🎯 ROI 설정 도구", font=("Arial", 16, "bold")).pack()
        ttk.Label(top_frame, text="게임 창을 선택하고 경험치 바, HP 바를 드래그하세요").pack()
        
        # 컨트롤 프레임
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        # 왼쪽: 창 선택
        left_frame = ttk.Frame(control_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_frame, text="1️⃣ 게임 창 선택:").pack(anchor=tk.W)
        
        window_frame = ttk.Frame(left_frame)
        window_frame.pack(fill=tk.X, pady=5)
        
        self.window_listbox = tk.Listbox(window_frame, height=5)
        self.window_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(window_frame, orient=tk.VERTICAL, command=self.window_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.window_listbox.config(yscrollcommand=scrollbar.set)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="🔄 새로고침", command=self.refresh_windows).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📸 캡처", command=self.capture_window).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🖥️ 전체 화면", command=self.capture_fullscreen).pack(side=tk.LEFT, padx=2)
        
        # 오른쪽: ROI 설정
        right_frame = ttk.Frame(control_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))
        
        ttk.Label(right_frame, text="2️⃣ ROI 드래그:").pack(anchor=tk.W)
        
        roi_btn_frame = ttk.Frame(right_frame)
        roi_btn_frame.pack(fill=tk.X, pady=5)
        
        self.btn_exp = ttk.Button(roi_btn_frame, text="📊 경험치 바", command=lambda: self.set_roi_mode('exp_bar'), width=15)
        self.btn_exp.pack(side=tk.LEFT, padx=2)
        
        self.btn_hp = ttk.Button(roi_btn_frame, text="❤️ HP 바", command=lambda: self.set_roi_mode('hp_bar'), width=15)
        self.btn_hp.pack(side=tk.LEFT, padx=2)
        
        self.btn_player = ttk.Button(roi_btn_frame, text="🧙 플레이어", command=lambda: self.set_roi_mode('player'), width=15)
        self.btn_player.pack(side=tk.LEFT, padx=2)
        
        # ROI 정보 표시
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.roi_info_label = ttk.Label(info_frame, text="ROI를 선택하고 드래그하세요", foreground="blue")
        self.roi_info_label.pack()
        
        # 하단: 저장/취소
        bottom_frame = ttk.Frame(right_frame)
        bottom_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(bottom_frame, text="💾 저장", command=self.save_roi, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text="🗑️ 초기화", command=self.clear_all_roi, width=15).pack(side=tk.LEFT, padx=2)
        
        # 캔버스 프레임
        canvas_frame = ttk.Frame(self.root, padding="10")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 캔버스 (스크롤바 포함)
        self.canvas = tk.Canvas(canvas_frame, bg="gray", cursor="cross")
        
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # 마우스 이벤트
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # 상태바
        self.status_label = ttk.Label(self.root, text="창 목록을 새로고침하세요", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 초기 창 목록 로드
        self.refresh_windows()
        
    def refresh_windows(self):
        """창 목록 새로고침"""
        self.window_listbox.delete(0, tk.END)
        self.windows = []
        
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 3:
                    windows.append((hwnd, title))
        
        win32gui.EnumWindows(callback, self.windows)
        
        # 게임 창 우선 표시
        game_windows = [(h, t) for h, t in self.windows if 'ML' in t or '메이플' in t or 'MapleStory' in t.lower() or 'Mapleland' in t]
        other_windows = [(h, t) for h, t in self.windows if (h, t) not in game_windows]
        
        for hwnd, title in game_windows:
            self.window_listbox.insert(tk.END, f"🎮 {title}")
            
        for hwnd, title in other_windows[:30]:  # 상위 30개
            self.window_listbox.insert(tk.END, title)
        
        self.windows = game_windows + other_windows[:30]
        
        if game_windows:
            self.window_listbox.select_set(0)
            self.status_label.config(text=f"✅ {len(game_windows)}개 게임 창 감지됨")
        else:
            self.status_label.config(text="⚠️ 게임 창을 찾을 수 없습니다. 수동으로 선택하세요")
    
    def capture_window(self):
        """선택한 창 캡처"""
        selection = self.window_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "창을 선택하세요")
            return
        
        idx = selection[0]
        hwnd, title = self.windows[idx]
        
        try:
            # 창 위치와 크기
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # mss로 캡처
            with mss.mss() as sct:
                monitor = {
                    'left': left,
                    'top': top,
                    'width': width,
                    'height': height
                }
                screenshot = sct.grab(monitor)
                self.screenshot = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            self.window_offset = {'x': left, 'y': top}
            self.display_screenshot()
            self.status_label.config(text=f"✅ '{title}' 캡처 완료 (x={left}, y={top}, w={width}, h={height})")
            
        except Exception as e:
            messagebox.showerror("오류", f"창 캡처 실패: {e}")
            self.status_label.config(text=f"❌ 캡처 실패: {e}")
    
    def capture_fullscreen(self):
        """전체 화면 캡처"""
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                self.screenshot = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            self.window_offset = {'x': 0, 'y': 0}
            self.display_screenshot()
            self.status_label.config(text="✅ 전체 화면 캡처 완료")
            
        except Exception as e:
            messagebox.showerror("오류", f"화면 캡처 실패: {e}")
    
    def display_screenshot(self):
        """스크린샷 표시"""
        if self.screenshot is None:
            return
        
        # 캔버스 크기에 맞게 스케일
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width, canvas_height = 1200, 600
        
        img_width, img_height = self.screenshot.size
        
        scale_w = canvas_width / img_width
        scale_h = canvas_height / img_height
        self.scale_factor = min(scale_w, scale_h, 1.0)  # 최대 1.0 (원본 크기)
        
        new_width = int(img_width * self.scale_factor)
        new_height = int(img_height * self.scale_factor)
        
        self.draw_image = self.screenshot.copy()
        self.draw_image = self.draw_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 기존 ROI 그리기
        self.redraw_rois()
        
        self.photo = ImageTk.PhotoImage(self.draw_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))
    
    def redraw_rois(self):
        """기존 ROI 다시 그리기"""
        if self.draw_image is None:
            return
        
        draw = ImageDraw.Draw(self.draw_image)
        
        colors = {
            'exp_bar': 'yellow',
            'hp_bar': 'red',
            'player': 'cyan'
        }
        
        labels = {
            'exp_bar': '📊 경험치 바',
            'hp_bar': '❤️ HP 바',
            'player': '🧙 플레이어'
        }
        
        for name, box in self.roi_boxes.items():
            # 전역 좌표를 로컬 좌표로 변환
            local_x = (box['x'] - self.window_offset['x']) * self.scale_factor
            local_y = (box['y'] - self.window_offset['y']) * self.scale_factor
            local_w = box['w'] * self.scale_factor
            local_h = box['h'] * self.scale_factor
            
            color = colors.get(name, 'green')
            draw.rectangle(
                [local_x, local_y, local_x + local_w, local_y + local_h],
                outline=color,
                width=3
            )
            
            # 레이블
            label = labels.get(name, name)
            draw.text((local_x + 5, local_y - 20), label, fill=color)
    
    def set_roi_mode(self, roi_name):
        """ROI 설정 모드"""
        if self.screenshot is None:
            messagebox.showwarning("경고", "먼저 화면을 캡처하세요")
            return
        
        self.current_roi = roi_name
        
        labels = {
            'exp_bar': '📊 경험치 바를 드래그하세요 (노란색/파란색 바)',
            'hp_bar': '❤️ HP 바를 드래그하세요 (빨간색 바)',
            'player': '🧙 플레이어 캐릭터를 드래그하세요'
        }
        
        self.roi_info_label.config(text=labels.get(roi_name, "드래그하세요"), foreground="blue")
        self.status_label.config(text=f"✏️ {labels.get(roi_name, '')} 드래그 중...")
        
        # 버튼 색상
        self.btn_exp.config(style="")
        self.btn_hp.config(style="")
        self.btn_player.config(style="")
        
        if roi_name == 'exp_bar':
            self.btn_exp.config(style="Accent.TButton")
        elif roi_name == 'hp_bar':
            self.btn_hp.config(style="Accent.TButton")
        elif roi_name == 'player':
            self.btn_player.config(style="Accent.TButton")
    
    def on_press(self, event):
        """마우스 누름"""
        if self.current_roi is None:
            return
        
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='lime', width=3, dash=(5, 5)
        )
    
    def on_drag(self, event):
        """마우스 드래그"""
        if self.start_x is None or self.rect_id is None:
            return
        
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)
    
    def on_release(self, event):
        """마우스 놓음"""
        if self.start_x is None or self.current_roi is None:
            return
        
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # 최소 크기 체크
        if abs(end_x - self.start_x) < 10 or abs(end_y - self.start_y) < 10:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
            self.start_x = None
            self.start_y = None
            return
        
        # 스케일 보정 및 전역 좌표로 변환
        x1 = int(min(self.start_x, end_x) / self.scale_factor) + self.window_offset['x']
        y1 = int(min(self.start_y, end_y) / self.scale_factor) + self.window_offset['y']
        w = int(abs(end_x - self.start_x) / self.scale_factor)
        h = int(abs(end_y - self.start_y) / self.scale_factor)
        
        # ROI 저장
        self.roi_boxes[self.current_roi] = {
            'x': x1,
            'y': y1,
            'w': w,
            'h': h
        }
        
        labels = {
            'exp_bar': '📊 경험치 바',
            'hp_bar': '❤️ HP 바',
            'player': '🧙 플레이어'
        }
        
        label = labels.get(self.current_roi, self.current_roi)
        self.roi_info_label.config(text=f"✅ {label} 설정 완료!", foreground="green")
        self.status_label.config(text=f"✅ {label}: x={x1}, y={y1}, w={w}, h={h}")
        
        # 화면 다시 그리기
        self.display_screenshot()
        
        # 초기화
        self.rect_id = None
        self.start_x = None
        self.start_y = None
        self.current_roi = None
    
    def clear_all_roi(self):
        """모든 ROI 초기화"""
        if messagebox.askyesno("확인", "모든 ROI를 초기화하시겠습니까?"):
            self.roi_boxes.clear()
            self.display_screenshot()
            self.roi_info_label.config(text="ROI를 선택하고 드래그하세요", foreground="blue")
            self.status_label.config(text="🗑️ 모든 ROI 초기화됨")
    
    def save_roi(self):
        """ROI 저장"""
        if not self.roi_boxes:
            messagebox.showwarning("경고", "설정된 ROI가 없습니다")
            return
        
        # 필수 ROI 체크
        if 'exp_bar' not in self.roi_boxes or 'hp_bar' not in self.roi_boxes:
            if not messagebox.askyesno("확인", "경험치 바와 HP 바가 모두 설정되지 않았습니다.\n그래도 저장하시겠습니까?"):
                return
        
        try:
            config_path = Path("configs/roi_settings.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.roi_boxes, f, indent=2, ensure_ascii=False)
            
            msg = "=" * 50 + "\n"
            msg += "✅ ROI 설정 저장 완료!\n"
            msg += "=" * 50 + "\n\n"
            msg += f"📁 저장 위치: {config_path}\n\n"
            msg += "설정된 ROI:\n"
            for name, box in self.roi_boxes.items():
                labels = {
                    'exp_bar': '📊 경험치 바',
                    'hp_bar': '❤️ HP 바',
                    'player': '🧙 플레이어'
                }
                label = labels.get(name, name)
                msg += f"  {label}: x={box['x']}, y={box['y']}, w={box['w']}, h={box['h']}\n"
            
            msg += "\n💡 다음 단계:\n"
            msg += "  1. 게임을 실행하고 캐릭터를 안전한 위치에 배치\n"
            msg += "  2. py tools/train_realtime_rl.py --timesteps 10000 실행"
            
            messagebox.showinfo("저장 완료", msg)
            self.status_label.config(text=f"💾 ROI 설정이 {config_path}에 저장되었습니다")
            
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}")


def main():
    root = tk.Tk()
    app = ROISetupApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
