"""
학습된 픽셀 기반 RL 에이전트 테스트 GUI
실시간 게임 플레이 시연 및 통계 표시
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import sys
import time
import cv2
import numpy as np
import mss
from PIL import Image, ImageTk
from collections import deque

sys.path.insert(0, str(Path(__file__).parent.parent))

from stable_baselines3 import PPO, DQN, A2C
from src.utils.config_loader import load_config
import keyboard


class SimpleActionController:
    """간단한 행동 제어 (실제 플레이 패턴 기반)"""
    
    def __init__(self, keybindings):
        self.keybindings = keybindings
        self.last_action = None
        self.currently_pressed = set()
        
        # 버프 쿨타임 관리 (초 단위)
        self.buff_cooldowns = {
            5: 120,   # 홀리심볼 (D) - 2분
            6: 180,   # 블레스 (Shift) - 3분
            7: 300,   # 인빈서블 (Alt) - 5분
            10: 150   # 서먼 드래곤 (Home) - 150초
        }
        self.last_buff_time = {5: 0, 6: 0, 7: 0, 10: 0}
        
        # 공격 지속 관리
        self.attack_start_time = None
        self.attack_duration = 0.3  # 공격을 0.3초간 유지
        
    def execute_action(self, action):
        """
        행동 실행 (실제 플레이 패턴 기반)
        
        행동 매핑:
        0: Idle (대기)
        1-2: 좌우 이동 (주력)
        3: 텔레포트 (V) - 몬스터 접근
        4: 공격 (A) - 주력 사냥 (V→A 반복)
        5: 홀리심볼 (D) - 2분 버프 (최우선)
        6: 블레스 (Shift) - 3분 버프
        7: 인빈서블 (Alt) - 5분 버프
        8-9: 예비 (위/아래 이동)
        """
        # 행동별 키 매핑 (단순화됨)
        action_map = {
            0: None,                                        # idle
            1: self.keybindings.get('move_left', 'left'),  # 왼쪽 (주력)
            2: self.keybindings.get('move_right', 'right'),# 오른쪽 (주력)
            3: self.keybindings.get('teleport', 'v'),      # 텔레포트 (접근)
            4: self.keybindings.get('attack', 'a'),        # 공격 (사냥)
            5: self.keybindings.get('buff_holy', 'd'),     # 홀리심볼 (2분)
            6: self.keybindings.get('buff_bless', 'shift'),# 블레스 (3분)
            7: self.keybindings.get('buff_invin', 'alt'),  # 인빈서블 (5분)
            8: self.keybindings.get('move_up', 'up'),      # 위 (로프/사다리)
            9: self.keybindings.get('move_down', 'down'),  # 아래 (로프/사다리)
            10: self.keybindings.get('summon_dragon', 'home') # 서먼 드래곤 (150초)
        }
        
        # 이동 행동 (1-2, 8-9)은 계속 누르고, 다른 행동은 탭
        is_movement = action in [1, 2, 8, 9]  # 좌우, 위아래
        is_buff = action in [5, 6, 7, 10]  # 버프 스킬
        is_attack = action == 4  # 공격
        
        try:
            # 버프 쿨타임 체크
            if is_buff:
                current_time = time.time()
                cooldown = self.buff_cooldowns[action]
                last_time = self.last_buff_time[action]
                
                if current_time - last_time < cooldown:
                    # 쿨타임 중이면 무시 (idle로 처리)
                    return
                else:
                    # 쿨타임 끝났으면 사용하고 시간 기록
                    self.last_buff_time[action] = current_time
            
            # 이전에 눌렀던 키 중 현재 행동이 아닌 것은 해제
            if is_movement:
                for pressed_key in list(self.currently_pressed):
                    keyboard.release(pressed_key)
                self.currently_pressed.clear()
            
            key = action_map.get(action)
            
            if key:
                if is_movement:
                    # 이동 키는 계속 누름
                    keyboard.press(key)
                    self.currently_pressed.add(key)
                elif is_attack:
                    # 공격은 0.3초간 꾹 누르기 (몬스터 처치까지)
                    keyboard.press(key)
                    time.sleep(self.attack_duration)
                    keyboard.release(key)
                else:
                    # 텔포/버프는 탭 (누르고 바로 떼기)
                    keyboard.press(key)
                    time.sleep(0.05)
                    keyboard.release(key)
            elif action == 0:  # idle
                # 모든 키 해제
                for pressed_key in list(self.currently_pressed):
                    keyboard.release(pressed_key)
                self.currently_pressed.clear()
            
            self.last_action = action
            
        except Exception as e:
            print(f"⚠️  키 입력 오류 (action={action}): {e}")
    
    def release_all(self):
        """모든 눌린 키 해제 (종료 시)"""
        for key in list(self.currently_pressed):
            try:
                keyboard.release(key)
            except:
                pass
        self.currently_pressed.clear()


class AgentTestGUI:
    """에이전트 테스트 GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 RL 에이전트 테스트")
        self.root.geometry("900x700")
        
        # 상태
        self.model = None
        self.agent_thread = None
        self.is_running = False
        self.model_path = None
        
        # 통계
        self.frame_count = 0
        self.start_time = None
        self.action_counts = {i: 0 for i in range(11)}
        self.action_names = [
            "💤 대기",           # 0: Idle
            "⬅️ 왼쪽",           # 1: 왼쪽 이동 (주력)
            "➡️ 오른쪽",         # 2: 오른쪽 이동 (주력)
            "🌀 텔포(V)",        # 3: 접근 (V→A 패턴)
            "⚔️ 공격(A)",        # 4: 사냥 (V→A 패턴)
            "✨ 홀리(D)",        # 5: 2분 버프 (최우선)
            "🙏 블레스(Shift)",  # 6: 3분 버프
            "🛡️ 인빈(Alt)",      # 7: 5분 버프
            "⬆️ 위",             # 8: 로프 위
            "⬇️ 아래",           # 9: 로프 아래
            "🐲 서먼(Home)"       # 10: 서먼 드래곤 (150초)
        ]
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. 모델 선택
        model_frame = tk.LabelFrame(main_container, text="1️⃣ 모델 선택", 
                                    font=("Arial", 12, "bold"), padx=10, pady=10)
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(model_frame, text="모델 파일:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.model_label = tk.Label(model_frame, text="선택되지 않음", 
                                    font=("Arial", 10), fg="red")
        self.model_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        tk.Button(model_frame, text="📂 모델 불러오기", 
                 command=self.load_model, font=("Arial", 10)).grid(row=0, column=2, padx=5)
        
        # 2. 설정
        config_frame = tk.LabelFrame(main_container, text="2️⃣ 실행 설정", 
                                     font=("Arial", 12, "bold"), padx=10, pady=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 게임 선택
        tk.Label(config_frame, text="게임:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.game_var = tk.StringVar(value="ML")
        game_frame = tk.Frame(config_frame)
        game_frame.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5)
        tk.Radiobutton(game_frame, text="ML", variable=self.game_var, value="ML", 
                      font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(game_frame, text="MP", variable=self.game_var, value="MP", 
                      font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # FPS
        tk.Label(config_frame, text="FPS:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.fps_var = tk.IntVar(value=10)
        tk.Spinbox(config_frame, from_=1, to=30, textvariable=self.fps_var, 
                  width=10, font=("Arial", 10)).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # 프레임 크기
        tk.Label(config_frame, text="프레임 크기:", font=("Arial", 10)).grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.frame_size_var = tk.IntVar(value=84)
        tk.Spinbox(config_frame, from_=32, to=128, textvariable=self.frame_size_var, 
                  width=10, font=("Arial", 10)).grid(row=1, column=3, sticky=tk.W, padx=5)
        
        # 프레임 스택
        tk.Label(config_frame, text="프레임 스택:", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.frame_stack_var = tk.IntVar(value=4)
        tk.Spinbox(config_frame, from_=1, to=8, textvariable=self.frame_stack_var, 
                  width=10, font=("Arial", 10)).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # 미리보기 옵션
        self.show_preview_var = tk.BooleanVar(value=True)
        tk.Checkbutton(config_frame, text="프레임 미리보기 표시", 
                      variable=self.show_preview_var, font=("Arial", 10)).grid(row=2, column=2, columnspan=2, sticky=tk.W, padx=5)
        
        # 3. 제어
        control_frame = tk.LabelFrame(main_container, text="3️⃣ 제어", 
                                      font=("Arial", 12, "bold"), padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        button_frame = tk.Frame(control_frame)
        button_frame.pack()
        
        self.start_button = tk.Button(button_frame, text="🚀 에이전트 시작", 
                                      command=self.start_agent, font=("Arial", 12, "bold"),
                                      bg="#4CAF50", fg="white", padx=20, pady=10)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="⏹️ 에이전트 중지", 
                                     command=self.stop_agent, font=("Arial", 12, "bold"),
                                     bg="#f44336", fg="white", padx=20, pady=10, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 4. 통계
        stats_frame = tk.LabelFrame(main_container, text="4️⃣ 실행 통계", 
                                    font=("Arial", 12, "bold"), padx=10, pady=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # 상단 통계
        top_stats = tk.Frame(stats_frame)
        top_stats.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(top_stats, text="⏱️ 실행 시간:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.time_label = tk.Label(top_stats, text="0.0초", font=("Arial", 10))
        self.time_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        tk.Label(top_stats, text="🎞️ 프레임:", font=("Arial", 10, "bold")).grid(row=0, column=2, sticky=tk.W, padx=5)
        self.frame_label = tk.Label(top_stats, text="0개", font=("Arial", 10))
        self.frame_label.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        tk.Label(top_stats, text="📈 평균 FPS:", font=("Arial", 10, "bold")).grid(row=0, column=4, sticky=tk.W, padx=5)
        self.fps_label = tk.Label(top_stats, text="0.0", font=("Arial", 10))
        self.fps_label.grid(row=0, column=5, sticky=tk.W, padx=5)
        
        # 현재 행동
        tk.Label(stats_frame, text="🎮 현재 행동:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.current_action_label = tk.Label(stats_frame, text="대기 중...", 
                                             font=("Arial", 14, "bold"), fg="#2196F3")
        self.current_action_label.pack(pady=5)
        
        # 상태 로그
        tk.Label(stats_frame, text="📝 상태 로그:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        log_frame = tk.Frame(stats_frame)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        log_scrollbar = tk.Scrollbar(log_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=5, font=("Consolas", 9), 
                               yscrollcommand=log_scrollbar.set, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)
        
        # 행동 분포
        tk.Label(stats_frame, text="📊 행동 분포:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        # 스크롤 가능한 행동 분포 표시
        action_canvas = tk.Canvas(stats_frame, height=200)
        action_scrollbar = tk.Scrollbar(stats_frame, orient="vertical", command=action_canvas.yview)
        self.action_dist_frame = tk.Frame(action_canvas)
        
        action_canvas.create_window((0, 0), window=self.action_dist_frame, anchor="nw")
        action_canvas.configure(yscrollcommand=action_scrollbar.set)
        
        action_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        action_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.action_dist_frame.bind("<Configure>", 
                                    lambda e: action_canvas.configure(scrollregion=action_canvas.bbox("all")))
        
        # 행동별 레이블 생성
        self.action_labels = {}
        for i, name in enumerate(self.action_names):
            frame = tk.Frame(self.action_dist_frame)
            frame.pack(fill=tk.X, pady=2)
            
            tk.Label(frame, text=name, font=("Arial", 9), width=15, anchor=tk.W).pack(side=tk.LEFT, padx=5)
            
            bar_frame = tk.Frame(frame, bg="#e0e0e0", height=20, width=300)
            bar_frame.pack(side=tk.LEFT, padx=5)
            bar_frame.pack_propagate(False)
            
            bar = tk.Frame(bar_frame, bg="#4CAF50", height=20)
            bar.place(x=0, y=0, relheight=1)
            
            count_label = tk.Label(frame, text="0 (0.0%)", font=("Arial", 9))
            count_label.pack(side=tk.LEFT, padx=5)
            
            self.action_labels[i] = (bar, count_label, bar_frame)
        
    def load_model(self):
        """모델 불러오기"""
        filepath = filedialog.askopenfilename(
            title="모델 선택",
            initialdir="models/rl_pixel",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            self.log_status("모델 로딩 중...")
            
            # 알고리즘 감지
            filepath_lower = filepath.lower()
            if 'ppo' in filepath_lower:
                self.model = PPO.load(filepath)
                algorithm = "PPO"
            elif 'dqn' in filepath_lower:
                self.model = DQN.load(filepath)
                algorithm = "DQN"
            elif 'a2c' in filepath_lower:
                self.model = A2C.load(filepath)
                algorithm = "A2C"
            else:
                self.model = PPO.load(filepath)
                algorithm = "PPO (추정)"
            
            self.model_path = filepath
            self.model_label.config(text=f"{Path(filepath).name} ({algorithm})", fg="green")
            self.log_status(f"✅ {algorithm} 모델 로드 완료")
            
        except Exception as e:
            messagebox.showerror("오류", f"모델 로드 실패:\n{str(e)}")
            self.log_status(f"❌ 모델 로드 실패: {str(e)}")
    
    def log_status(self, message):
        """상태 로그 출력"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_agent(self):
        """에이전트 시작"""
        if not self.model:
            messagebox.showwarning("경고", "먼저 모델을 불러오세요.")
            return
        
        if self.is_running:
            messagebox.showwarning("경고", "이미 실행 중입니다.")
            return
        
        # 통계 초기화
        self.frame_count = 0
        self.start_time = time.time()
        self.action_counts = {i: 0 for i in range(11)}
        
        # 버튼 상태 변경
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_running = True
        
        self.log_status("🚀 에이전트 시작!")
        self.log_status(f"⚙️ 설정: {self.game_var.get()} | FPS: {self.fps_var.get()} | 프레임 크기: {self.frame_size_var.get()}")
        
        # 에이전트 스레드 시작
        self.agent_thread = threading.Thread(target=self.run_agent, daemon=True)
        self.agent_thread.start()
        
        # 통계 업데이트 시작
        self.update_stats()
        
        self.log_status("🚀 에이전트 시작!")
    
    def stop_agent(self):
        """에이전트 중지"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_status("⏹️ 에이전트 중지")
    
    def run_agent(self):
        """에이전트 실행 (백그라운드 스레드)"""
        try:
            # 설정
            game = self.game_var.get()
            fps = self.fps_var.get()
            frame_size = self.frame_size_var.get()
            frame_stack = self.frame_stack_var.get()
            show_preview = self.show_preview_var.get()
            
            # 컨트롤러 초기화
            config = load_config(game=game)
            keybindings = config.get('keybindings', {
                'move_left': 'left',
                'move_right': 'right',
                'move_up': 'up',
                'move_down': 'down',
                'jump': 'space',
                'attack': 'a',
                'skill1': 's',
                'skill2': 'd',
                'potion': 'p'
            })
            controller = SimpleActionController(keybindings)
            
            # 화면 캡처 초기화
            sct = mss.mss()
            monitor = sct.monitors[1]
            
            # 프레임 버퍼
            frame_buffer = deque(maxlen=frame_stack)
            
            # 첫 프레임으로 버퍼 초기화
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (frame_size, frame_size))
            
            for _ in range(frame_stack):
                frame_buffer.append(resized)
            
            frame_delay = 1.0 / fps
            
            self.root.after(0, self.log_status, "📹 화면 캡처 시작")
            self.root.after(0, self.log_status, f"🎯 타겟 FPS: {fps}")
            
            last_log_time = time.time()
            
            while self.is_running:
                loop_start = time.time()
                
                # 화면 캡처
                screenshot = sct.grab(monitor)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # 전처리
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                resized = cv2.resize(gray, (frame_size, frame_size))
                frame_buffer.append(resized)
                
                # 관측
                observation = np.array(frame_buffer, dtype=np.uint8)
                
                # 행동 예측
                action, _states = self.model.predict(observation, deterministic=False)
                action = int(action)
                
                # 행동 실행
                controller.execute_action(action)
                
                # 통계 업데이트
                self.action_counts[action] += 1
                self.frame_count += 1
                
                # 현재 행동 표시 (GUI 스레드에서)
                self.root.after(0, self.update_current_action, action)
                
                # 5초마다 진행 상황 로그
                current_time = time.time()
                if current_time - last_log_time >= 5.0:
                    elapsed_total = current_time - self.start_time
                    actual_fps = self.frame_count / elapsed_total if elapsed_total > 0 else 0
                    self.root.after(0, self.log_status, 
                                  f"⏱️ {elapsed_total:.1f}초 | 프레임: {self.frame_count} | FPS: {actual_fps:.1f} | 현재: {self.action_names[action]}")
                    last_log_time = current_time
                
                # FPS 유지
                elapsed = time.time() - loop_start
                if elapsed < frame_delay:
                    time.sleep(frame_delay - elapsed)
            
            # 종료 시 모든 키 해제
            controller.release_all()
            sct.close()
            
            # 최종 통계 로그
            elapsed_total = time.time() - self.start_time
            avg_fps = self.frame_count / elapsed_total if elapsed_total > 0 else 0
            self.root.after(0, self.log_status, f"✅ 종료: {self.frame_count}개 프레임 ({elapsed_total:.1f}초, 평균 {avg_fps:.1f} FPS)")
            
        except Exception as e:
            self.root.after(0, self.log_status, f"❌ 에러: {str(e)}")
            self.is_running = False
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
    
    def update_current_action(self, action):
        """현재 행동 표시 업데이트"""
        self.current_action_label.config(text=self.action_names[action])
    
    def update_stats(self):
        """통계 업데이트"""
        if not self.is_running:
            return
        
        # 시간 및 프레임
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.time_label.config(text=f"{elapsed:.1f}초")
            
            if self.frame_count > 0:
                avg_fps = self.frame_count / elapsed
                self.fps_label.config(text=f"{avg_fps:.1f}")
        
        self.frame_label.config(text=f"{self.frame_count}개")
        
        # 행동 분포
        total = self.frame_count if self.frame_count > 0 else 1
        for action_id, (bar, label, bar_frame) in self.action_labels.items():
            count = self.action_counts[action_id]
            percentage = (count / total) * 100
            
            # 막대 그래프
            bar_width = int((count / total) * 300)
            bar.config(width=bar_width)
            
            # 텍스트
            label.config(text=f"{count} ({percentage:.1f}%)")
        
        # 100ms 후 다시 업데이트
        self.root.after(100, self.update_stats)
    
    def log_status(self, message):
        """상태 로그 (콘솔)"""
        print(message)


def main():
    root = tk.Tk()
    app = AgentTestGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
