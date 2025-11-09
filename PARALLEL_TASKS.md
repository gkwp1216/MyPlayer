# 🔄 병렬 작업 가이드

Phase 2의 스크린샷 수집은 시간이 오래 걸립니다. 수집하는 동안 다른 작업을 병렬로 진행할 수 있습니다.

---

## 📊 현재 상황

| 작업 | 상태 | 소요 시간 | 의존성 |
|------|------|-----------|--------|
| **Phase 2 스크린샷 수집** | 🔄 대기 | 2~4시간 | 없음 |
| Phase 1 테스트 | ⏳ 미시작 | 30분 | 없음 |
| 학습 기반 패턴 구현 | ⏳ 미시작 | 2~3시간 | 없음 |
| YOLO 통합 준비 | ⏳ 미시작 | 1~2시간 | 없음 |
| 안전 기능 강화 | ⏳ 미시작 | 1~2시간 | 없음 |
| UI/모니터링 추가 | ⏳ 미시작 | 2~3시간 | 없음 |

---

## 🎯 추천 병렬 작업 순서

### 1️⃣ Phase 1 테스트 및 검증 (30분) ⭐⭐⭐

**목표**: 기본 타이머 기반 자동화가 실제로 작동하는지 확인

**작업 내용**:
```powershell
# config.yaml 설정 확인 및 수정
# - 버프 키 설정
# - 스킬 키 설정

# 테스트 실행
py main.py
```

**확인 사항**:
- [ ] 프로그램이 정상적으로 시작되는가?
- [ ] 로그가 제대로 출력되는가?
- [ ] 30분/1분 타이머가 무작위로 작동하는가?
- [ ] 키 입력이 실제로 게임에 전달되는가?
- [ ] 무작위 딜레이가 적용되는가?

**예상 문제점**:
- config.yaml 설정 오류
- 키 바인딩 불일치
- 권한 문제 (관리자 권한 필요할 수 있음)

**해결 방법**:
```powershell
# 관리자 권한으로 실행
# PowerShell을 관리자로 실행 후
py main.py
```

---

### 2️⃣ 학습 기반 패턴 시스템 구현 (2~3시간) ⭐⭐⭐⭐⭐

**목표**: 실제 플레이를 녹화하여 사냥 패턴을 학습하고 자동 재생

**왜 중요한가?**:
- YOLO 없이도 완전히 작동하는 자동화 시스템
- 개인화된 플레이 스타일 반영
- Phase 2 완료 전에 실제 사용 가능

**작업 단계**:

#### Step 1: 녹화 시스템 구현 (1시간)
```python
# src/recorder/keyboard_recorder.py 구현
# - pynput으로 키보드/마우스 이벤트 캡처
# - 타임스탬프와 함께 JSON 저장
# - F9 키로 녹화 시작/중지
```

**기능**:
- 키 입력 시간 기록
- 마우스 클릭 위치 기록
- 스킬 사용 간격 자동 계산

#### Step 2: 패턴 학습 (30분)
```python
# src/recorder/pattern_learner.py 구현
# - 녹화된 데이터 분석
# - 각 키의 평균 사용 간격 계산
# - 무작위성 범위 자동 추출
```

**출력**: `learned_skills.json`
```json
{
  "skills": [
    {
      "key": "F1",
      "cooldown_base": 62.3,
      "cooldown_variance": 8.5,
      "usage_count": 12
    }
  ]
}
```

#### Step 3: 패턴 재생 (30분)
```python
# src/player/skill_player.py 구현
# - learned_skills.json 로드
# - 학습된 타이밍으로 자동 스킬 사용
# - 무작위성 적용
```

#### Step 4: 통합 및 테스트 (30분)
```powershell
# 1. 녹화
py recorder_main.py
# → 메뉴에서 1번 선택
# → 5분간 평소처럼 플레이
# → F9로 중지

# 2. 학습
# → 메뉴에서 3번 선택
# → 녹화 파일 선택

# 3. 실행
py main.py
# → 자동으로 학습된 패턴대로 실행
```

**예상 결과**:
- ✅ 실제 플레이 패턴을 그대로 재현
- ✅ 각 스킬의 쿨타임을 자동으로 학습
- ✅ 인간처럼 자연스러운 무작위성

---

### 3️⃣ YOLO 통합 준비 코드 작성 (1~2시간) ⭐⭐⭐

**목표**: Phase 2 완료 후 즉시 통합 가능하도록 코드 준비

**작업 내용**:

#### 실시간 화면 캡처 구현
```python
# src/perception/yolo_detector.py 업데이트

def capture_screen_region(self, region=None):
    """특정 영역만 캡처 (버프 영역, 스킬 영역 등)"""
    if region:
        monitor = {
            'top': region['y'],
            'left': region['x'],
            'width': region['width'],
            'height': region['height']
        }
    else:
        monitor = self.sct.monitors[1]
    
    screenshot = self.sct.grab(monitor)
    img = np.array(screenshot)
    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
```

#### 판단 로직 구현
```python
# src/decision/strategy.py 업데이트

def analyze_buff_status(self, detections):
    """버프 상태 분석"""
    # exp_doping_missing 탐지 → 도핑 사용
    # buff_time_low 탐지 → 버프 위치로 이동
    # skill_cooldown 탐지 → 사냥 계속
    pass

def should_use_exp_doping(self, detections):
    """경험치 도핑 사용 여부 판단"""
    for det in detections:
        if det['class'] == 'exp_doping_missing':
            return True
    return False
```

#### 더미 데이터로 테스트
```python
# 테스트용 더미 탐지 결과 생성
dummy_detections = [
    {'class': 'skill_cooldown', 'confidence': 0.9},
    {'class': 'exp_doping_active', 'confidence': 0.85}
]

# 판단 로직 테스트
strategy = StrategyEngine()
action = strategy.decide_action(dummy_detections)
print(f"결정된 행동: {action}")
```

---

### 4️⃣ 안전 기능 강화 (1~2시간) ⭐⭐

**목표**: 봇 탐지 회피 및 안전성 향상

**작업 내용**:

#### 게임 창 포커스 확인
```python
# src/utils/window_manager.py 생성

import win32gui
import win32process

def is_maplestory_focused():
    """메이플스토리가 포커스되어 있는지 확인"""
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    return "MapleStory" in title or "메이플스토리" in title
```

#### 무작위 패턴 고도화
```python
# src/utils/humanizer.py 생성

import random
import time

class Humanizer:
    """인간처럼 행동하는 유틸리티"""
    
    @staticmethod
    def random_delay(base, variance):
        """인간적인 무작위 딜레이"""
        # 정규분포 사용 (더 자연스러움)
        delay = random.gauss(base, variance / 3)
        delay = max(base - variance, min(base + variance, delay))
        return delay
    
    @staticmethod
    def random_mouse_movement(x, y):
        """마우스를 인간처럼 이동"""
        # 베지어 곡선으로 자연스러운 경로 생성
        pass
```

#### 예외 처리
```python
# main.py 업데이트

try:
    while True:
        # 게임 창 확인
        if not is_maplestory_focused():
            logger.warning("메이플스토리가 포커스되어 있지 않습니다.")
            time.sleep(5)
            continue
        
        # 정상 실행
        skill_player.update()
        
except KeyboardInterrupt:
    logger.info("프로그램 종료")
except Exception as e:
    logger.error(f"오류 발생: {e}")
    # 오류 발생 시 안전하게 종료
```

---

### 5️⃣ UI/모니터링 시스템 (2~3시간) ⭐

**목표**: 사용자 친화적인 인터페이스

**작업 내용**:

#### 실시간 상태 표시
```python
# src/ui/status_display.py 생성

from rich.console import Console
from rich.table import Table
from rich.live import Live

def display_status(skill_player):
    """실시간 상태 표시"""
    console = Console()
    
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            table = Table(title="Perceptive-AI 상태")
            table.add_column("스킬", style="cyan")
            table.add_column("다음 실행", style="magenta")
            table.add_column("남은 시간", style="green")
            
            next_skills = skill_player.get_next_skill_info()
            for skill in next_skills[:5]:
                table.add_row(
                    skill['key'],
                    skill['type'],
                    f"{skill['remaining']:.1f}초"
                )
            
            live.update(table)
            time.sleep(1)
```

#### 대시보드 (선택)
- 웹 기반 대시보드 (Flask + Chart.js)
- 통계: 사용한 스킬 횟수, 가동 시간 등
- 원격 제어: 시작/중지/설정 변경

---

## 📋 작업 체크리스트

### 즉시 시작 가능 (Phase 2 독립적)

- [ ] **Phase 1 테스트** (30분)
  - [ ] config.yaml 설정
  - [ ] main.py 실행 테스트
  - [ ] 로그 확인
  - [ ] 실제 게임에서 동작 확인

- [ ] **학습 기반 패턴 구현** (2~3시간)
  - [ ] 녹화 시스템 구현
  - [ ] 패턴 학습 알고리즘
  - [ ] 패턴 재생 시스템
  - [ ] 통합 테스트

- [ ] **YOLO 통합 준비** (1~2시간)
  - [ ] 화면 캡처 함수 구현
  - [ ] 판단 로직 뼈대 작성
  - [ ] 더미 데이터로 테스트

- [ ] **안전 기능 강화** (1~2시간)
  - [ ] 게임 창 포커스 확인
  - [ ] 무작위 패턴 고도화
  - [ ] 예외 처리 강화

- [ ] **UI/모니터링** (2~3시간)
  - [ ] 실시간 상태 표시
  - [ ] 로그 GUI
  - [ ] 대시보드 (선택)

### Phase 2 완료 후 작업

- [ ] **YOLO 모델 통합**
  - [ ] 학습된 모델 로드
  - [ ] 실시간 탐지 연동
  - [ ] 판단 로직 연결

---

## 🚀 추천 시작 순서

### 오늘 할 작업 (우선순위)

1. **Phase 1 테스트** (30분) - 바로 시작 가능
2. **학습 기반 패턴 구현** (2시간) - 가장 실용적
3. **안전 기능 강화** (1시간) - 실제 사용 준비

### 내일 할 작업

4. **YOLO 통합 준비** (1시간) - Phase 2 대비
5. **UI/모니터링** (2시간) - 사용성 개선

---

## 💡 팁

### 효율적인 작업 순서
1. Phase 1 테스트로 **기본 동작 확인**
2. 학습 시스템으로 **실제 사용 가능한 기능** 완성
3. 안전 기능으로 **안정성 확보**
4. YOLO 준비로 **Phase 2 대비**

### 시간 배분
- **Phase 1 테스트**: 지금 바로 30분
- **학습 시스템**: 오늘 2시간
- **나머지**: 시간 날 때마다

---

## 📞 도움이 필요하면

각 작업별로 상세한 구현 가이드를 제공할 수 있습니다.
어떤 작업부터 시작하고 싶으신가요?

**바로 시작하기**:
```powershell
# Phase 1 테스트
py main.py

# 학습 시스템 (구현 필요)
# → 구현 가이드 요청 시 바로 제공 가능
```
