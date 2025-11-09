# 🚀 Perceptive-AI 설치 가이드

## ✅ 설치 완료 상태

**현재 설치 상태**: ✅ 완료 (2025-11-06)

| 항목 | 상태 | 버전 |
|------|------|------|
| Python | ✅ | 3.14.0 |
| 의존성 패키지 | ✅ | 전체 설치 완료 |
| 프로젝트 구조 | ✅ | 완성 |
| Phase 2 도구 | ✅ | 준비 완료 |

---

## 1. 환경 설정

### Python 버전
- **Python 3.14.0** 설치 완료 ✅
- 위치: `C:\Users\김기원\AppData\Local\Programs\Python\Python314\`

### 가상 환경 (선택 사항)

현재는 글로벌 환경에 설치되어 있습니다. 가상 환경을 원하면:

```powershell
# 가상 환경 생성
py -m venv venv
## 3. 프로젝트 구조 ✅ 완성 (멀티 게임 확장: MP / ML)
# 가상 환경 활성화 (PowerShell)
├── data.yaml                        # 기본(단일) YOLO 학습 설정 ✅
├── data_MP.yaml                     # MP 게임 전용 데이터 설정
├── data_ML.yaml                     # ML 게임 전용 데이터 설정

├── config.yaml                      # 기본 설정 파일
├── configs/                         # 게임별 오버레이 설정
│   ├── MP.yaml                      # MapleStory 전용 설정
│   └── ML.yaml                      # 두 번째 게임 전용 설정
.\venv\Scripts\activate.bat
├── tools/
```
│   ├── dataset_splitter.py          # 데이터셋 분할 도구 ( --game 지원 ) ✅
│   └── train_yolo.py                # 게임별 YOLO 학습 헬퍼 ✅
## 2. 의존성 설치 ✅ 완료
├── datasets/                        # 기본 단일 게임 데이터셋
├── datasets/MP/                     # MP 게임 데이터셋 (images/, labels/, raw/)
├── datasets/ML/                     # ML 게임 데이터셋 (images/, labels/, raw/)

모든 필수 패키지가 이미 설치되어 있습니다:

```powershell
# 설치 확인
py -m pip list | Select-String -Pattern "pyautogui|numpy|ultralytics|opencv"
```


### 멀티 게임 오버레이 (configs/MP.yaml, configs/ML.yaml)
```yaml
# 예: configs/ML.yaml
timers:
   buff_base: 1500
   buff_variance: 90
   skill_base: 45
   skill_variance: 5
keybindings:
   buff_key: '-'
   skill_key: 'F2'
yolo:
   model_path: 'models/ml_best.pt'
   confidence_threshold: 0.55
```
**설치된 패키지 목록**:
### Phase 1: 타이머 기반 자동화 ✅ (게임 선택 가능)
- numpy 2.3.4
# 기본 실행 (기본 config.yaml)
py main.py

# MP 게임 설정 적용
py main.py --game MP

# ML 게임 설정 적용
py main.py --game ML
- torch 2.9.0
- torchvision 0.24.0
1. **데이터 분할 (단일)**:
- pyyaml 6.0.3
- pillow 12.0.0
- pynput 1.8.1
    **게임별 분할**:
    ```powershell
    py tools/dataset_splitter.py --game MP
    py tools/dataset_splitter.py --game ML --train 0.85 --val 0.1 --test 0.05
    ```

## 3. 프로젝트 구조 ✅ 완성
3. **모델 훈련 (단일)**:
```
MyPlayer/
├── main.py                          # 메인 실행 파일
    **게임별 학습 (헬퍼 스크립트)**:
    ```powershell
    py tools/train_yolo.py --game MP --model yolo11n.pt --epochs 50
    py tools/train_yolo.py --game ML --model yolo11s.pt --epochs 60 --imgsz 640 --batch 16
    ```
├── config.yaml                      # 설정 파일
4. **모델 저장**:
    단일 학습:
├── requirements.txt                 # 의존성 목록
│
├── 📖 문서
    게임별 학습(train_yolo.py 실행 시 자동):
    - MP -> models/mp_best.pt
    - ML -> models/ml_best.pt
├── README.md                        # 프로젝트 개요 및 로드맵
### YOLO 모델 로드 실패
- 단일: `models/best.pt` 파일 존재 확인
- 게임별: `models/mp_best.pt` 또는 `models/ml_best.pt` 존재 확인
- Phase 2가 완료되지 않았다면 정상 (주석 처리됨)
- 경로 오류: `config.yaml` 또는 `configs/<GAME>.yaml` 의 `model_path` 확인
│
1. ✅ **Phase 1 테스트**: `py main.py --game MP` 또는 `--game ML` 실행하여 동작 확인
├── 💾 소스 코드
├── src/
│   ├── __init__.py
│   ├── timer_manager.py             # Phase 1: 타이머 관리
│   ├── action_controller.py         # 행동 제어
│   ├── perception/                  # Phase 2: 인식 (YOLO)
│   │   ├── __init__.py
│   │   └── yolo_detector.py
│   ├── decision/                    # Phase 3: 의사결정
│   │   ├── __init__.py
│   │   └── strategy.py
│   └── utils/                       # 유틸리티
│       ├── __init__.py
│       └── logger.py
│
├── 🛠️ 도구
├── tools/
│   ├── screenshot_helper.py         # 스크린샷 수집 도구 ✅
│   └── dataset_splitter.py          # 데이터셋 분할 도구 ✅
│
├── 📊 데이터셋 (Phase 2)
├── datasets/
│   ├── README.md                    # 데이터셋 구조 설명 ✅
│   ├── raw/                         # 원본 스크린샷 ✅
│   │   ├── skill_cooldown/
│   │   ├── buff_time_low/
│   │   ├── exp_doping_active/
│   │   ├── exp_doping_missing/
│   │   └── skill_ready/
│   ├── images/                      # 학습용 이미지 ✅
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   └── labels/                      # 라벨 파일 ✅
│       ├── train/
│       ├── val/
│       └── test/
│
├── models/                          # YOLO 모델 저장
└── logs/                            # 로그 파일
└── .gitignore

```

## 4. 설정 파일 커스터마이징

`config.yaml` 파일을 열어 다음 항목들을 수정하세요:

### 키 바인딩
```yaml
keybindings:
  buff_key: '='    # 경험치 버프 키 (기본값)
  skill_key: 'F1'  # 설치기 스킬 키 (기본값)
```

### 타이머 조정
```yaml
timers:
  buff_base: 1800       # 30분 = 1800초
  buff_variance: 120    # ±2분 무작위성
  skill_base: 60        # 1분 = 60초
  skill_variance: 5     # ±5초 무작위성
```

### YOLO 설정 (Phase 2 이후)
```yaml
yolo:
  model_path: 'models/best.pt'
  confidence: 0.5
  device: 'cpu'  # 또는 'cuda' (GPU 있으면)
```

---

## 5. 실행

### Phase 1: 타이머 기반 자동화 ✅
```powershell
# 메인 프로그램 실행
py main.py
```

**동작 확인**:
- [ ] 프로그램이 정상 시작되는가?
- [ ] 로그가 출력되는가?
- [ ] 타이머가 무작위로 작동하는가?

### Phase 2: 스크린샷 수집 ✅
```powershell
# 스크린샷 수집 도구 실행
py tools/screenshot_helper.py
```

**단축키**:
- `F5`: 스크린샷 캡처
- `F6`: 다음 클래스
- `F7`: 이전 클래스
- `ESC`: 종료

**수집 목표**: 각 클래스당 50~200장

### 종료 방법
- **Ctrl+C**: 안전한 종료
- **마우스를 화면 왼쪽 상단 모서리로 이동**: 긴급 정지 (FAILSAFE)

---

## 6. Phase 2 준비 사항 (YOLO 모델 학습)

### 스크린샷 수집 완료 후
1. **데이터 분할**:
   ```powershell
   py tools/dataset_splitter.py
   ```
   → raw 이미지를 train/val/test로 8:1:1 분할

2. **라벨링**:
   - `Roboflow` (온라인, 추천 ⭐): https://roboflow.com/
   - `LabelImg` (오프라인): https://github.com/HumanSignal/labelImg

3. **모델 훈련**:
   ```powershell
   yolo detect train data=data.yaml model=yolov8n.pt epochs=50
   ```

4. **모델 저장**:
   ```powershell
   # 학습 완료 후 best.pt를 models/ 폴더로 이동
   Move-Item runs/detect/train/weights/best.pt models/
   ```

**상세 가이드**:
- 빠른 시작: `PHASE2_QUICKSTART.md`
- 라벨링 기준: `PHASE2_LABELING_GUIDE.md`

---

## 7. 병렬 작업 (스크린샷 수집 중)

스크린샷 수집은 시간이 오래 걸립니다. 수집하는 동안 다른 작업을 진행할 수 있습니다:

📖 **자세한 내용**: `PARALLEL_TASKS.md` 참조

**추천 작업**:
1. Phase 1 테스트 및 검증 (30분)
2. 학습 기반 패턴 시스템 구현 (2~3시간)
3. 안전 기능 강화 (1~2시간)
4. YOLO 통합 준비 코드 작성 (1~2시간)

---

## 8. 주의사항

⚠️ **중요**:
- 이 프로그램은 **교육 및 연구 목적**으로만 사용하세요
- 게임 이용약관 위반 가능성을 인지하고 사용하세요
- 봇 탐지 회피를 위해 무작위성이 적용되어 있습니다
- 실제 게임 사용 시 계정 정지 위험이 있습니다

---

## 9. 트러블슈팅

### PyAutoGUI 권한 오류
```powershell
# 관리자 권한으로 PowerShell 실행 후
py main.py
```

### 패키지 설치 오류
```powershell
# numpy 빌드 오류 시
py -m pip install numpy --only-binary :all:

# 전체 재설치
py -m pip uninstall -y pyautogui numpy opencv-python ultralytics
py -m pip install -r requirements.txt
```

### YOLO 모델 로드 실패
- `models/best.pt` 파일 존재 확인
- Phase 2가 완료되지 않았다면 정상 (주석 처리됨)
- 경로 오류: `config.yaml`의 `model_path` 확인

### 스크린샷 도구 오류
```powershell
# pynput 없으면
py -m pip install pynput

# 관리자 권한 필요할 수 있음
```

### 로그 확인
```powershell
# PowerShell
Get-Content logs/perceptive_ai.log -Tail 50

# CMD
type logs\perceptive_ai.log
```

---

## 10. 다음 단계

현재 설치가 완료되었으므로:

1. ✅ **Phase 1 테스트**: `py main.py` 실행하여 동작 확인
2. 🔄 **Phase 2 진행**: 스크린샷 수집 시작
3. ⏳ **병렬 작업**: `PARALLEL_TASKS.md` 참조하여 추가 기능 개발
4. ⏳ **Phase 3 대기**: Phase 2 완료 후 통합 작업

---

## 11. 추가 리소스

- **프로젝트 개요**: `README.md`
- **Phase 2 빠른 시작**: `PHASE2_QUICKSTART.md`
- **라벨링 가이드**: `PHASE2_LABELING_GUIDE.md`
- **병렬 작업**: `PARALLEL_TASKS.md`
- **YOLO 공식 문서**: https://docs.ultralytics.com/
- **PyAutoGUI 문서**: https://pyautogui.readthedocs.io/
