"""
MP 게임 패턴 녹화 GUI
간편한 학습 데이터 생성을 위한 그래픽 인터페이스

사용법: python tools/record_pattern_gui.py
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import keyboard
import time
import json
import threading
from pathlib import Path
from datetime import datetime


class PatternRecorderGUI:
    """패턴 녹화 GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MP 패턴 녹화기")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        # 상태 변수
        self.recording = False
        self.pattern_data = []
        self.start_time = None
        self.record_thread = None
        
        # 모든 키 모니터링 (키보드 전체)
        self.key_states = {}
        
        self._setup_ui()
        self._setup_hotkeys()
        
        # 종료 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """UI 구성"""
        # 타이틀
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🎬 MP 패턴 녹화기",
            font=("맑은 고딕", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)
        
        # 메인 컨테이너
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 파일명 입력
        file_frame = tk.LabelFrame(main_frame, text="패턴 이름", font=("맑은 고딕", 10, "bold"), padx=10, pady=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.filename_var = tk.StringVar(value="my_pattern")
        filename_entry = tk.Entry(file_frame, textvariable=self.filename_var, font=("맑은 고딕", 11))
        filename_entry.pack(fill=tk.X)
        
        # 녹화 설정
        settings_frame = tk.LabelFrame(main_frame, text="녹화 설정", font=("맑은 고딕", 10, "bold"), padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        duration_frame = tk.Frame(settings_frame)
        duration_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(duration_frame, text="녹화 시간:", font=("맑은 고딕", 10)).pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="300")
        duration_spinbox = tk.Spinbox(
            duration_frame,
            from_=10,
            to=3600,
            increment=10,
            textvariable=self.duration_var,
            width=10,
            font=("맑은 고딕", 10)
        )
        duration_spinbox.pack(side=tk.LEFT, padx=10)
        tk.Label(duration_frame, text="초", font=("맑은 고딕", 10)).pack(side=tk.LEFT)
        
        self.unlimited_var = tk.BooleanVar(value=False)
        unlimited_check = tk.Checkbutton(
            duration_frame,
            text="무제한 (7로 종료)",
            variable=self.unlimited_var,
            font=("맑은 고딕", 9),
            command=self._toggle_duration
        )
        unlimited_check.pack(side=tk.RIGHT)
        
        # 상태 표시
        status_frame = tk.LabelFrame(main_frame, text="녹화 상태", font=("맑은 고딕", 10, "bold"), padx=10, pady=10)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.status_label = tk.Label(
            status_frame,
            text="대기 중...",
            font=("맑은 고딕", 12, "bold"),
            fg="#95a5a6"
        )
        self.status_label.pack(pady=10)
        
        self.timer_label = tk.Label(
            status_frame,
            text="00:00",
            font=("맑은 고딕", 24, "bold"),
            fg="#34495e"
        )
        self.timer_label.pack(pady=10)
        
        self.action_count_label = tk.Label(
            status_frame,
            text="행동: 0개",
            font=("맑은 고딕", 11),
            fg="#7f8c8d"
        )
        self.action_count_label.pack(pady=5)
        
        # 로그 영역
        log_frame = tk.LabelFrame(main_frame, text="최근 행동", font=("맑은 고딕", 9), padx=5, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.log_text = tk.Text(log_frame, height=6, font=("맑은 고딕", 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
        # 버튼
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_button = tk.Button(
            button_frame,
            text="🔴 녹화 시작 (6)",
            font=("맑은 고딕", 12, "bold"),
            bg="#27ae60",
            fg="white",
            height=2,
            command=self._start_recording
        )
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stop_button = tk.Button(
            button_frame,
            text="⏹️ 중지 (7)",
            font=("맑은 고딕", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            height=2,
            command=self._stop_recording,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 하단 정보
        info_label = tk.Label(
            self.root,
            text="💡 6: 녹화 시작 | 7: 녹화 중지 (백그라운드에서도 작동)",
            font=("맑은 고딕", 9),
            fg="#7f8c8d",
            bg="#ecf0f1"
        )
        info_label.pack(fill=tk.X, pady=5)
    
    def _toggle_duration(self):
        """무제한 체크박스 토글"""
        if self.unlimited_var.get():
            self.duration_var.set("∞")
        else:
            self.duration_var.set("300")
    
    def _setup_hotkeys(self):
        """글로벌 핫키 설정 (백그라운드에서도 작동)"""
        keyboard.add_hotkey('6', self._start_recording, suppress=False)
        keyboard.add_hotkey('7', self._stop_recording, suppress=False)
    
    def _log(self, message, color="black"):
        """로그 추가"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 최대 100줄 유지
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 100:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete('1.0', '2.0')
            self.log_text.config(state=tk.DISABLED)
    
    def _update_status(self, status, color):
        """상태 업데이트"""
        self.status_label.config(text=status, fg=color)
    
    def _start_recording(self):
        """녹화 시작"""
        if self.recording:
            return
        
        filename = self.filename_var.get().strip()
        if not filename:
            messagebox.showerror("오류", "패턴 이름을 입력하세요!")
            return
        
        self.recording = True
        self.pattern_data = []
        self.key_states = {}
        
        # UI 업데이트
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self._update_status("🔴 녹화 중...", "#e74c3c")
        self._log("=" * 50)
        self._log("🔴 녹화 시작!", "red")
        
        # 녹화 쓰레드 시작
        self.record_thread = threading.Thread(target=self._recording_loop, daemon=True)
        self.record_thread.start()
    
    def _stop_recording(self):
        """녹화 중지"""
        if not self.recording:
            return
        
        self.recording = False
        
        # UI 업데이트
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self._update_status("⏹️ 중지됨", "#95a5a6")
        self._log("⏹️ 녹화 중지!", "blue")
        
        # 저장
        if self.pattern_data:
            self._save_pattern()
        else:
            messagebox.showwarning("경고", "녹화된 데이터가 없습니다!")
    
    def _recording_loop(self):
        """녹화 루프 (별도 쓰레드)"""
        self.start_time = time.time()
        duration = None if self.unlimited_var.get() else int(self.duration_var.get())
        
        # 키 이벤트 훅 (모든 키보드 입력)
        def on_key_event(event):
            if not self.recording:
                return
            
            current_time = time.time() - self.start_time
            key_name = event.name
            
            if event.event_type == 'down':
                # 중복 방지
                if not self.key_states.get(key_name, False):
                    self.key_states[key_name] = True
                    action = {
                        'time': round(current_time, 3),
                        'key': key_name,
                        'type': 'down'
                    }
                    self.pattern_data.append(action)
                    self._log(f"⬇️ [{current_time:.2f}s] {key_name} 눌림")
                    self.root.after(0, self._update_action_count)
            
            elif event.event_type == 'up':
                if self.key_states.get(key_name, False):
                    self.key_states[key_name] = False
                    action = {
                        'time': round(current_time, 3),
                        'key': key_name,
                        'type': 'up'
                    }
                    self.pattern_data.append(action)
                    self._log(f"⬆️ [{current_time:.2f}s] {key_name} 뗌")
                    self.root.after(0, self._update_action_count)
        
        keyboard.hook(on_key_event)
        
        # 타이머 업데이트
        while self.recording:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.root.after(0, self._update_timer, f"{minutes:02d}:{seconds:02d}")
            
            # 시간 제한 체크
            if duration and elapsed >= duration:
                self.root.after(0, self._stop_recording)
                break
            
            time.sleep(0.1)
        
        keyboard.unhook_all()
        self._setup_hotkeys()  # 핫키 재등록
    
    def _update_timer(self, time_str):
        """타이머 업데이트"""
        self.timer_label.config(text=time_str)
    
    def _update_action_count(self):
        """행동 카운트 업데이트"""
        count = len([a for a in self.pattern_data if a['type'] == 'down'])
        self.action_count_label.config(text=f"행동: {count}개")
    
    def _save_pattern(self):
        """패턴 저장"""
        output_dir = Path("datasets/mp_patterns")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.filename_var.get()}_{timestamp}.json"
        output_path = output_dir / filename
        
        # 메타데이터
        pattern_file = {
            'metadata': {
                'name': self.filename_var.get(),
                'recorded_at': timestamp,
                'duration': round(self.pattern_data[-1]['time'], 2) if self.pattern_data else 0,
                'total_actions': len(self.pattern_data),
                'keys_used': list(set([a['key'] for a in self.pattern_data]))
            },
            'pattern': self.pattern_data
        }
        
        # 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(pattern_file, f, indent=2, ensure_ascii=False)
        
        # 통계
        key_counts = {}
        for action in self.pattern_data:
            if action['type'] == 'down':
                key_counts[action['key']] = key_counts.get(action['key'], 0) + 1
        
        # 결과 메시지
        result_msg = f"""✅ 패턴 저장 완료!

📁 파일: {filename}
⏱️  녹화 시간: {pattern_file['metadata']['duration']}초
🎯 총 행동: {pattern_file['metadata']['total_actions']}개

📊 자주 사용된 키:
"""
        for key, count in sorted(key_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            result_msg += f"  • {key}: {count}회\n"
        
        messagebox.showinfo("저장 완료", result_msg)
        self._log("=" * 50)
        self._log(f"✅ 패턴 저장: {output_path}")
    
    def _on_closing(self):
        """창 닫기"""
        if self.recording:
            if messagebox.askokcancel("확인", "녹화 중입니다. 종료하시겠습니까?"):
                self.recording = False
                time.sleep(0.5)
                keyboard.unhook_all()
                self.root.destroy()
        else:
            keyboard.unhook_all()
            self.root.destroy()
    
    def run(self):
        """GUI 실행"""
        self.root.mainloop()


def main():
    print("=" * 60)
    print("🎬 MP 패턴 녹화기 GUI")
    print("=" * 60)
    print("💡 6: 녹화 시작")
    print("💡 7: 녹화 중지")
    print("💡 백그라운드에서도 핫키 작동!")
    print("=" * 60)
    
    app = PatternRecorderGUI()
    app.run()


if __name__ == "__main__":
    main()
