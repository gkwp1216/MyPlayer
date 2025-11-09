# 🍁 Project: "Perceptive-AI" (가제)

## 📊 현재 진행 상황

| Phase | 상태 | 진행률 | 다음 단계 |
|-------|------|--------|-----------|
| **Phase 0** | ✅ 완료 | 100% | - |
| **Phase 1** | ✅ 구조 완성 | 90% | 실제 테스트 필요 |
| **Phase 2** | 🔄 진행 중 | 30% | 스크린샷 수집 중 |
| **Phase 3** | ⏳ 대기 | 0% | Phase 2 완료 후 시작 |

**최근 업데이트**: 2025-11-06
- ✅ 의존성 설치 완료 (Python 3.14, PyTorch, YOLO, OpenCV 등)
- ✅ Phase 2 데이터셋 구조 및 도구 준비 완료
- ✅ 5개 클래스 정의 완료 (스킬 쿨타임, 버프 시간, 경험치 도핑 등)
- 🔄 스크린샷 수집 도구 준비 완료 → 수집 시작 대기

---

## 1. 프로젝트 개요

본 프로젝트는 Python과 **YOLO(You Only Look Once)** 객체 탐지 모델을 활용하여, 메이플스토리 내의 **버프 상태**, **스킬 쿨타임**, **경험치 도핑 상태**를 실시간으로 "인지"하고 "판단"하는 지능형 AI 에이전트 개발을 목표로 합니다.

단순한 입력을 흉내 내는 것이 아니라, YOLO를 "눈"으로 사용하여 게임 UI 상태를 실시간으로 파악하고, 이를 기반으로 최적의 행동(스킬 사용, 버프 사용, 위치 이동)을 결정합니다.

모든 행동 트리거는 **"인간화된 무작위성"**을 기반으로 하여 봇 탐지를 회피하는 것을 최우선 원칙으로 합니다.

## 2. 핵심 목표 (Objectives)

-   [x] **(Phase 0) 프로젝트 구조 및 환경 설정:** 완료 ✅
-   [x] **(최우선) 인간화 (Humanization):** 모든 시간 기반 입력(버프, 스킬)이 고정된 간격이 아닌, 무작위적인 시간 범위 내에서 작동 - 구현 완료 ✅
-   [ ] **(Phase 1) 타이머 기반 자동화:** 약 30분 주기 버프, 1분 주기 설치기를 무작위 간격으로 자동 실행 - 구조 완성 🔄
-   [ ] **(Phase 2) YOLO 기반 UI 상태 인식:** 다음 5가지 상태를 실시간으로 탐지:
    1.  **스킬 쿨타임 확인**: 쿨타임 중인 스킬 탐지 → 사냥 계속
    2.  **버프 지속시간 임박**: 10초 이하 버프 탐지 → 버프 위치로 이동 및 재사용
    3.  **경험치 도핑 활성화**: 도핑 버프 존재 확인 → 정상 진행
    4.  **경험치 도핑 부재**: 도핑 없음 탐지 → 즉시 도핑 사용
    5.  **스킬 사용 가능**: 밝은 스킬 아이콘 탐지 → 즉시 스킬 사용
-   [ ] **(Phase 3) 판단 및 행동 통합:** Phase 1의 타이머와 Phase 2의 YOLO "눈"을 결합하여 지능형 행동 완성

## 3. 기술 스택 (Technology Stack)

### ✅ 설치 완료
-   **언어:** `Python 3.14.0` ✅
-   **핵심 자동화 라이브러리:**
    -   `pyautogui 0.9.54`: 가상 키보드 및 마우스 입력 제어 ✅
    -   `pynput 1.8.1`: 키보드 이벤트 감지 (녹화 기능) ✅
    -   `random`: 모든 시간 간격에 무작위성을 부여 (Python 내장) ✅
    -   `time`: 스크립트 실행 시간 및 딜레이 측정 (Python 내장) ✅
-   **AI / 인식 (Perception):**
    -   **`ultralytics 8.3.225` (YOLOv8):** 실시간 객체 탐지 모델 ✅
    -   **`torch 2.9.0` (PyTorch):** YOLO 실행 엔진 ✅
    -   **`torchvision 0.24.0`:** 컴퓨터 비전 라이브러리 ✅
    -   `mss 10.1.0`: 실시간 화면 캡처 ✅
    -   `opencv-python 4.11.0.86`: 이미지 처리 ✅
    -   `numpy 2.3.4`: 좌표 및 데이터 처리 ✅
-   **설정 및 유틸리티:**
    -   `pyyaml 6.0.3`: 설정 파일 관리 ✅
    -   `pillow 12.0.0`: 이미지 처리 ✅
    -   `matplotlib 3.10.7`: 시각화 (YOLO 학습용) ✅

### 🔧 라벨링 도구 (선택)
-   `Roboflow` (온라인): YOLO 학습을 위한 이미지 라벨링 - 추천 ⭐
-   `LabelImg` (오프라인): 로컬 라벨링 도구

---

## 4. 개발 로드맵 (Roadmap)

### Phase 1: "인간화된" 타이머 골격 (The Heartbeat)

**목표:** AI의 행동을 "트리거"하는 핵심 스케줄러 구현. 봇 탐지를 피하기 위해 모든 주기를 무작위화.

**핵심 로직:**

1.  **30분 경험치 버프를 유지하며, 약 1분가량 지속되는 설치기 2개를 관리하며 통상 공격을 통해 몬스터를 잡아야 함:** `BUFF_BASE = 1800초` + `random.uniform(-120, 120)` (약 28~32분).
2.  **1분 설치기:** `SKILL_BASE = 60초` + `random.uniform(-5, 5)` (약 55~65초).
3.  **지속적 무작위성:** 스킬/버프 사용 후, 다음 실행 딜레이(`_next_delay`) 값을 **매번 새로 뽑아서** 패턴 누적을 방지.

*(이 단계에서는 1분마다 `pyautogui.press('F1')`만 눌러도 되지만, Phase 3에서 AI 로직으로 대체됩니다.)*

---

### Phase 2: 인식 모델 훈련 (The Eyes) - 🔄 진행 중

**목표:** `YOLOv8n` 모델을 커스텀 학습시켜, 메이플스토리 화면에서 **버프 상태**, **스킬 쿨타임**, **경험치 도핑 상태**를 실시간으로 탐지하도록 훈련.

**✅ 완료된 작업:**
-   [x] 5개 클래스 정의 완료
    -   `skill_cooldown`: 스킬 쿨타임 상태
    -   `buff_time_low`: 버프 지속시간 임박 (10초 이하)
    -   `exp_doping_active`: 경험치 도핑 활성화
    -   `exp_doping_missing`: 경험치 도핑 부재
    -   `skill_ready`: 스킬 사용 가능
-   [x] 데이터셋 디렉토리 구조 생성 (`datasets/raw/`, `datasets/images/`, `datasets/labels/`)
-   [x] `data.yaml` 학습 설정 파일 생성
-   [x] 스크린샷 수집 도구 (`tools/screenshot_helper.py`) 생성
-   [x] 데이터셋 분할 도구 (`tools/dataset_splitter.py`) 생성
-   [x] 라벨링 가이드 문서 작성 (`PHASE2_LABELING_GUIDE.md`)

**🔄 진행 중:**
1.  **데이터 수집:** 각 클래스당 50~200장 스크린샷 수집 (수동)
    ```powershell
    py tools/screenshot_helper.py  # F5로 빠른 캡처
    ```
2.  **데이터 라벨링:** `Roboflow` 또는 `LabelImg`를 이용해 바운딩 박스 작업
3.  **모델 훈련:** 라벨링 완료 후 YOLOv8n 모델 학습
    ```powershell
    yolo detect train data=data.yaml model=yolov8n.pt epochs=50
    ```
4.  **결과물:** `best.pt` (커스텀 "눈" 모델) → `models/` 폴더로 이동

**📖 상세 가이드:**
-   빠른 시작: `PHASE2_QUICKSTART.md`
-   라벨링 기준: `PHASE2_LABELING_GUIDE.md`

---

### Phase 3: 판단 및 행동 통합 (The Brain & Hands) - ⏳ 대기

**목표:** Phase 1의 타이머와 Phase 2의 YOLO "눈"을 결합하여 지능형 행동 완성.

**⏳ Phase 2 완료 후 시작**

**통합 의사 코드 (예상 구조):**

```python
import time
import random
import pyautogui
from src.perception.yolo_detector import YOLODetector
from src.decision.strategy import StrategyEngine

# --- Phase 2에서 훈련한 모델 로드 ---
yolo_detector = YOLODetector('models/best.pt')
strategy_engine = StrategyEngine()

# --- Phase 1: 타이머 설정 ---
BUFF_BASE, SKILL_BASE = 1800, 60
last_buff_time, last_skill_time = time.time(), time.time()
buff_next_delay = BUFF_BASE + random.uniform(-120, 120)
skill_next_delay = SKILL_BASE + random.uniform(-5, 5)

while True:
    current_time = time.time()
    
    # 실시간 UI 상태 탐지 (Phase 2)
    detections = yolo_detector.detect()
    
    # 버프 타이머 임박 탐지
    if 'buff_time_low' in [d['class'] for d in detections]:
        # 버프 위치로 이동 후 재사용
        pyautogui.press('=')  # 버프 키
        print("[Log] 버프 시간 임박 - 버프 재사용")
        last_buff_time = current_time
        buff_next_delay = BUFF_BASE + random.uniform(-120, 120)
    
    # 경험치 도핑 확인
    if 'exp_doping_missing' in [d['class'] for d in detections]:
        # 즉시 경험치 도핑 사용
        print("[Log] 경험치 도핑 없음 - 도핑 사용")
        # TODO: 도핑 사용 로직
    
    # 스킬 사용 가능 확인
    if 'skill_ready' in [d['class'] for d in detections]:
        if (current_time - last_skill_time) > skill_next_delay:
            # 의사결정 엔진으로 행동 판단
            action = strategy_engine.decide_skill_action(detections)
            
            if action:
                print(f"[Log] 스킬 사용: {action}")
                # TODO: 스킬 실행 로직
                last_skill_time = current_time
                skill_next_delay = SKILL_BASE + random.uniform(-5, 5)
    
    time.sleep(0.1)  # CPU 사용률 조절
```

**핵심 개선 사항**:
- YOLO 탐지 결과를 기반으로 **상황에 맞는 행동** 실행
- 버프 시간 임박 시 자동 갱신
- 경험치 도핑 상태 실시간 모니터링
- 스킬 쿨타임 확인 후 사용

---

## 5. 프로젝트 구조

```
MyPlayer/
├── 📖 문서
├── README.md                        # 프로젝트 개요 (이 파일)
├── SETUP.md                         # 설치 가이드
├── PHASE2_QUICKSTART.md             # Phase 2 빠른 시작
├── PHASE2_LABELING_GUIDE.md         # 라벨링 상세 가이드
├── PARALLEL_TASKS.md                # 병렬 작업 가이드 ✨
│
├── ⚙️ 설정
├── config.yaml                      # 메인 설정 파일
├── data.yaml                        # YOLO 학습 설정
├── requirements.txt                 # 의존성 목록
│
├── 🚀 실행 파일
├── main.py                          # 메인 실행 파일
│
├── 💾 소스 코드
├── src/
│   ├── timer_manager.py             # Phase 1: 타이머 관리 ✅
│   ├── action_controller.py         # 행동 제어 ✅
│   ├── perception/                  # Phase 2: 인식 (YOLO)
│   │   └── yolo_detector.py         # YOLO 탐지기 (스켈레톤)
│   ├── decision/                    # Phase 3: 의사결정
│   │   └── strategy.py              # 전략 엔진 (스켈레톤)
│   └── utils/                       # 유틸리티
│       └── logger.py                # 로거 ✅
│
├── 🛠️ 도구
├── tools/
│   ├── screenshot_helper.py         # 스크린샷 수집 도구 ✅
│   └── dataset_splitter.py          # 데이터셋 분할 도구 ✅
│
├── 📊 데이터셋
├── datasets/
│   ├── raw/                         # 원본 스크린샷 (클래스별)
│   ├── images/                      # 학습용 이미지 (train/val/test)
│   └── labels/                      # 라벨 파일 (train/val/test)
│
├── models/                          # YOLO 모델 저장
└── logs/                            # 로그 파일
```

---

## 6. 빠른 시작

### Phase 1: 타이머 기반 자동화 테스트
```powershell
# config.yaml 설정 확인 후
py main.py
```

### Phase 2: 스크린샷 수집
```powershell
# 스크린샷 수집 도구 실행
py tools/screenshot_helper.py

# F5: 스크린샷 캡처
# F6: 다음 클래스
# F7: 이전 클래스
# ESC: 종료
```

### Phase 3: 병렬 작업
스크린샷 수집 중에 할 수 있는 다른 작업들은 `PARALLEL_TASKS.md` 참조

---

## 7. 다음 단계

1. **Phase 1 검증**: 실제 게임에서 타이머 동작 테스트
2. **Phase 2 진행**: 스크린샷 수집 및 라벨링 (진행 중)
3. **병렬 작업**: 학습 기반 패턴 시스템 구현
4. **Phase 2 완료**: YOLO 모델 학습 및 검증
5. **Phase 3 통합**: 모든 시스템 통합 및 최종 테스트

---

## 8. 참고 문서

- **설치**: `SETUP.md`
- **Phase 2 빠른 시작**: `PHASE2_QUICKSTART.md`
- **라벨링 가이드**: `PHASE2_LABELING_GUIDE.md`
- **병렬 작업**: `PARALLEL_TASKS.md` ✨

---

## 9. 라이선스 및 주의사항

⚠️ **중요**: 본 프로젝트는 교육 및 연구 목적으로만 사용되어야 합니다. 실제 게임에서의 사용은 게임 이용 약관을 위반할 수 있으며, 계정 정지의 위험이 있습니다.

**봇 탐지 회피 원칙**:
- 모든 타이밍에 무작위성 적용
- 인간처럼 자연스러운 입력 패턴
- 게임 창 포커스 확인
- 예외 상황 안전 처리
        # else:
        #     print("[Log] 몬스터 없음. 스킬 사용 안 함.")
            
        last_skill_time = current_time
        skill_next_delay = SKILL_BASE + random.uniform(-5, 5) # 딜레이 새로 뽑기

    # 메인 루프 딜레이
    time.sleep(random.uniform(0.3, 0.7))