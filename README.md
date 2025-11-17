# MyPlayer 🎮

**실시간 강화학습을 통한 자동 게임 플레이 AI**

## 📊 현재 상태

| 구성요소 | 상태 | 설명 |
|---------|------|------|
| **실시간 RL 환경** | ✅ 완료 | 게임 직접 제어 + 보상 감지 |
| **보상 감지 시스템** | ✅ 완료 | 경험치/HP 픽셀 감지 |
| **ROI 설정 도구** | ✅ 완료 | 마우스 드래그 방식 |
| **학습 스크립트** | ✅ 완료 | PPO + 실시간 피드백 |
| **테스트 도구** | ✅ 완료 | GUI/CLI 테스트 지원 |

**최근 업데이트**: 2025-11-18
- ✅ 오프라인 RL → 실시간 RL로 전환 (몬스터 추적 문제 해결)
- ✅ 경험치/HP 바 픽셀 감지를 통한 실시간 보상 시스템
- ✅ 버프 쿨타임 관리 + 공격 지속 시간 개선
- ✅ TensorBoard 모니터링 + ESC 안전 중지
- 🎯 **다음 단계**: ROI 설정 → 실시간 학습 시작

---

## 🎯 프로젝트 개요

**MyPlayer**는 실제 게임과 상호작용하며 학습하는 강화학습 기반 게임 봇입니다.

### 핵심 특징
- 🎮 **실시간 학습**: 에이전트가 직접 게임을 플레이
- 📊 **보상 감지**: 경험치 바 증가 → 몬스터 처치 성공
- 💚 **피해 감지**: HP 바 감소 → 위험 신호
- 🎯 **목표 지향**: 행동-결과 인과관계 학습
- ⏱️ **쿨타임 관리**: 버프 스킬 효율적 사용

### 기술 스택
- **강화학습**: Stable-Baselines3 PPO
- **환경**: Gymnasium + 실시간 게임 제어
- **화면 캡처**: mss (스레드 안전)
- **입력 제어**: keyboard 라이브러리
- **보상 감지**: OpenCV HSV 색상 분석

## 🚀 빠른 시작

### 1단계: 환경 설정
```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 패키지 설치 (최초 1회)
pip install -r requirements.txt
```
- **게임 실행 후** 화면 캡처
- 마우스 드래그로 영역 지정:
  - 경험치 바 (노란색/파란색 바)
  - HP 바 (빨간색 바)
  - 플레이어 위치 (선택사항)
- `configs/roi_settings.json` 자동 생성

### 3단계: 실시간 학습 (1-2시간)
```powershell
# 캐릭터를 안전한 사냥터에 배치 후
py tools/train_realtime_rl.py --timesteps 50000

# 백그라운드 모니터링 (다른 터미널)
tensorboard --logdir logs/realtime/ML
```

**⚠️ 학습 중 주의사항:**
- 게임 창을 최상단 유지
- 마우스/키보드 건드리지 말 것
- 자동 포션 설정 권장
- ESC로 안전 중지 가능

### 4단계: 테스트
```powershell
py tools/test_agent_gui.py
# → models/realtime/ML/ML_ppo_realtime_final.zip 선택
```

---

## 📊 보상 함수 설계

### 즉각 보상 (게임 상태 변화)
| 상황 | 보상 | 의미 |
|------|------|------|
| 경험치 획득 | +1.0 | 몬스터 처치 성공 ✅ |
| HP 감소 | -0.5 | 피격 (위험) ⚠️ |
| 공격 타격 이펙트 | +0.3 | 타격 확인 |
| 텔레포트 이동 | +0.2 | 성공적 이동 |
| 정지 상태 | -0.05 | 행동 유도 |

### 행동별 보상
| 행동 | 보상 | 설명 |
|------|------|------|
| 공격/텔포 | +0.1 | 적극적 행동 장려 |
| 이동 | +0.05 | 탐험 장려 |
| Idle | -0.1 | 정지 방지 |
| 버프 (쿨타임) | 무시 | 쿨타임 중 스킵 |

### 버프 쿨타임 관리
- D (홀리심볼): 2분
- Shift (블레스): 3분
- Alt (인빈서블): 5분
- Home (서먼 드래곤): 150초

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────┐
│     실시간 RL 게임 봇 시스템          │
└─────────────────────────────────────┘
    │
    ├─ 게임 상태 감지 (reward_detector.py)
    │  ├─ 경험치 바 감지 (HSV 노란색)
    │  ├─ HP 바 감지 (HSV 빨간색)
    │  └─ 화면 변화 감지 (이펙트)
    │
    ├─ 실시간 환경 (rl_env_realtime.py)
    │  ├─ Observation: 84x84x4 그레이스케일
    │  ├─ Action Space: 11개 행동
    │  │   0: Idle
    │  │   1-2: 좌/우 이동
    │  │   3: 텔레포트
    │  │   4: 공격
    │  │   5-7: 버프 (쿨타임 관리)
    │  │   8-9: 상/하 이동
    │  │   10: 서먼
    │  ├─ Reward: 실시간 피드백
    │  └─ Episode: 1000 스텝 (약 2분)
    │
    ├─ PPO 에이전트 (train_realtime_rl.py)
    │  ├─ CnnPolicy (512x512)
    │  ├─ Learning Rate: 0.0001
    │  ├─ TensorBoard 모니터링
    │  └─ Checkpoint (5000 스텝마다)
    │
    └─ 테스트 도구
       ├─ test_agent_gui.py (GUI)
       └─ test_pixel_agent.py (CLI)
```

---

## 📁 프로젝트 구조

```
MyPlayer/
├── tools/
│   ├── setup_roi.py           # ROI 설정 도구
│   ├── train_realtime_rl.py   # 실시간 학습
│   ├── test_agent_gui.py      # GUI 테스트
│   └── test_pixel_agent.py    # CLI 테스트
│
├── src/
│   ├── rl_env_realtime.py     # 실시간 RL 환경
│   ├── reward_detector.py     # 보상 감지
│   └── utils/
│       ├── config_loader.py   # 설정 로더
│       └── logger.py          # 로깅
│
├── configs/
│   ├── ML.yaml                # 게임 설정
│   └── roi_settings.json      # ROI 좌표 (자동생성)
│
├── models/
│   └── realtime/ML/           # 학습된 모델
│
├── logs/
│   └── realtime/ML/           # TensorBoard 로그
│
└── docs/
    └── REALTIME_RL_DESIGN.md  # 상세 설계 문서
```

---

## 📈 학습 진행 단계

### Phase 1: 탐험 (0-20k 스텝)
- **탐험률**: 30% 랜덤 행동
- **목표**: 다양한 상황 경험
- **예상 결과**: 불규칙한 움직임, 낮은 보상

### Phase 2: 활용 (20k-40k 스텝)
- **탐험률**: 10% 랜덤 행동
- **목표**: V→A 패턴 확립
- **예상 결과**: 몬스터 처치 시작

### Phase 3: 최적화 (40k+ 스텝)
- **탐험률**: 5% 랜덤 행동
- **목표**: 효율적인 사냥
- **예상 결과**: 안정적인 플레이

**예상 총 학습 시간**: 6-9시간 (50k 스텝)

---

## 🔧 설정 파일

### configs/ML.yaml
```yaml
name: ML
window_title: "ML"
keybindings:
  move_left: 'left'
  move_right: 'right'
  move_up: 'up'
  move_down: 'down'
  attack: 'a'
  teleport: 'v'
  buff_holy: 'd'        # 2분 쿨타임
  buff_bless: 'shift'   # 3분 쿨타임
  buff_invin: 'alt'     # 5분 쿨타임
  summon_dragon: 'home' # 150초 쿨타임
```

### configs/roi_settings.json (setup_roi.py 실행 시 생성)
```json
{
  "exp_bar": {"x": 100, "y": 950, "w": 500, "h": 20},
  "hp_bar": {"x": 100, "y": 920, "w": 200, "h": 20},
  "player": {"x": 800, "y": 400, "w": 100, "h": 150}
}
```

---

## 🧪 실험 결과 (예상)

### 성공 지표
- ✅ 몬스터 추적 및 처치
- ✅ V→A 사냥 패턴 확립
- ✅ 버프 주기적 사용
- ✅ 피해 최소화 (HP 유지)

### 보상 그래프 (TensorBoard)
- 초기: 평균 보상 -5 ~ 0
- 20k 스텝: 평균 보상 5 ~ 10
- 50k 스텝: 평균 보상 15 ~ 25

---

## 🐛 문제 해결

### Q: ROI 설정이 작동하지 않아요
**A**: `py tools/setup_roi.py` 재실행 후 정확히 드래그. 경험치 바 전체를 포함해야 합니다.

### Q: 학습 중 에이전트가 멈춰요
**A**: ESC로 중지 후 게임 상태 확인 (사망/버그). 체크포인트에서 재시작 가능.

### Q: 경험치 감지가 안 돼요
**A**: ROI가 노란색 바를 정확히 캡처하는지 확인. HSV 범위 조정이 필요할 수 있습니다.

### Q: 키 입력이 안 돼요
**A**: 관리자 권한으로 실행 필요할 수 있습니다.

### Q: 학습이 너무 느려요
**A**: `--timesteps 10000`으로 테스트 실행. `frame_delay` 조정 (기본 0.1초).

---

## 📚 참고 자료

- [Stable-Baselines3 공식 문서](https://stable-baselines3.readthedocs.io/)
- [실시간 RL 설계 문서](docs/REALTIME_RL_DESIGN.md)
- [PPO 알고리즘 논문](https://arxiv.org/abs/1707.06347)

---

## ⚠️ 면책 조항

이 프로젝트는 **교육 목적**으로 제작되었습니다.
게임 이용약관을 준수하여 사용하세요.

---

**Last Updated**: 2025-11-18  
**Version**: 3.0 (실시간 RL)  
**Status**: ✅ 개발 완료, 학습 준비 완료

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

### 멀티 게임(MP/ML) 간단 사용법
두 게임의 데이터/설정/로그를 분리해서 운영할 수 있습니다. 자세한 워크플로우는 `SETUP.md`에 정리되어 있습니다.

```powershell
# 실행 (게임별 설정 적용)
py main.py --game MP
py main.py --game ML

# 데이터 분할 (게임별)
py tools/dataset_splitter.py --game MP
py tools/dataset_splitter.py --game ML --train 0.85 --val 0.1 --test 0.05

# YOLO 학습 (헬퍼 스크립트)
py tools/train_yolo.py --game MP --model yolo11n.pt --epochs 50
py tools/train_yolo.py --game ML --model yolo11s.pt --epochs 60

# 직접 YOLO CLI 사용 시 (데이터 파일 분리)
yolo detect train data=data_MP.yaml model=yolo11n.pt epochs=50
yolo detect train data=data_ML.yaml model=yolo11s.pt epochs=60
```

참고:
- 게임별 로그 파일: `logs/perceptive_ai_MP.log`, `logs/perceptive_ai_ML.log`
- 게임별 모델 저장: `models/mp_best.pt`, `models/ml_best.pt` (train_yolo.py가 자동 복사)
- 데이터 루트: `datasets/MP/`, `datasets/ML/`

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