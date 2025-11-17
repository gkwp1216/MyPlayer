# 픽셀 기반 강화학습 가이드 (YOLO 불필요)

이 프로젝트는 **화면 픽셀만으로** 게임 플레이를 학습하는 End-to-End 강화학습 시스템입니다.

## 🎯 핵심 개념

- **YOLO 불필요**: 객체 탐지 없이 화면만으로 학습
- **모방 학습**: 녹화된 게임 플레이로부터 학습
- **CNN 정책**: 화면 픽셀 → 행동 직접 매핑

## 📋 학습 프로세스

### 1단계: 게임 플레이 녹화

```powershell
py tools/record_gui.py
```

**사용 방법**:
1. ML 게임 선택
2. 게임 창 선택 (또는 전체 화면 체크)
3. FPS: 10 (권장)
4. 녹화 시간: 600초 (10분) 이상
5. "🎬 녹화 시작" 클릭
6. 게임을 **정상적으로** 플레이
7. "⏹️ 녹화 중지" 클릭 (또는 자동 종료)

**저장 위치**: `datasets/play_recordings/YYYYMMDD_HHMMSS/`

**팁**:
- 다양한 상황을 플레이하세요 (전투, 이동, 아이템 수집)
- 여러 번 녹화하면 더 좋은 결과
- 최소 10분, 권장 30분

### 2단계: 강화학습 학습

```powershell
py tools/train_pixel_rl.py --game ML --algorithm PPO --timesteps 100000
```

**파라미터**:
- `--game`: 게임 이름 (ML 또는 MP)
- `--algorithm`: RL 알고리즘 (PPO, DQN, A2C)
- `--timesteps`: 학습 스텝 수 (기본: 100000)
- `--frame-width`: 프레임 너비 (기본: 84)
- `--frame-height`: 프레임 높이 (기본: 84)
- `--frame-stack`: 프레임 스택 (기본: 4)
- `--learning-rate`: 학습률 (기본: 0.0001)

**알고리즘 선택**:
- **PPO** (권장): 가장 안정적, 범용적
- **DQN**: 이산 행동에 특화
- **A2C**: 빠른 학습, 낮은 메모리

### 3단계: TensorBoard 모니터링

```powershell
tensorboard --logdir logs/rl_pixel/ML
```

브라우저에서 `http://localhost:6006` 접속하여 학습 진행 상황 확인

### 4단계: 학습된 에이전트 테스트

```powershell
py tools/test_pixel_agent.py --game ML --model models/rl_pixel/ML/ML_ppo_final.zip
```

## 🏗️ 프로젝트 구조

```
MyPlayer/
├── tools/
│   ├── record_gui.py           # 게임 플레이 녹화 (GUI)
│   ├── train_pixel_rl.py       # 픽셀 기반 RL 학습
│   └── test_pixel_agent.py     # 학습된 에이전트 테스트
├── src/
│   └── rl_env_pixel.py         # 픽셀 기반 Gym 환경
├── datasets/
│   └── play_recordings/        # 녹화된 게임 플레이
│       └── YYYYMMDD_HHMMSS/
│           ├── frames/         # 프레임 이미지
│           ├── detections/     # 탐지 결과 (참고용)
│           ├── metadata.json   # 메타데이터
│           └── frames_data.json # 프레임 정보
├── models/
│   └── rl_pixel/               # 학습된 모델
└── logs/
    └── rl_pixel/               # TensorBoard 로그
```

## 🎮 행동 공간

- **0**: idle (아무것도 안 함)
- **1**: 위로 이동
- **2**: 아래로 이동
- **3**: 왼쪽으로 이동
- **4**: 오른쪽으로 이동
- **5**: 점프
- **6**: 공격
- **7**: 스킬1
- **8**: 스킬2
- **9**: 포션

## 📊 관측 공간

- **형태**: (4, 84, 84) - 4개의 그레이스케일 프레임 스택
- **전처리**: 원본 → 그레이스케일 → 84x84 리사이즈
- **프레임 스택**: 시간적 정보 포함 (움직임 방향 학습)

## 🔧 하이퍼파라미터 튜닝

### PPO (기본값)
```python
learning_rate=0.0001
n_steps=2048
batch_size=64
n_epochs=10
gamma=0.99
gae_lambda=0.95
clip_range=0.2
ent_coef=0.01
```

### 학습이 안 될 때
1. **learning_rate 낮추기**: 0.00005
2. **timesteps 늘리기**: 200000+
3. **더 많은 데이터 녹화**: 30분+
4. **frame_stack 늘리기**: 8

### 과적합 방지
1. **여러 세션 녹화**: 다양한 상황
2. **ent_coef 늘리기**: 0.02 (탐색 증가)
3. **clip_range 줄이기**: 0.1 (안정성)

## 🚀 고급 사용법

### 여러 녹화 데이터 사용
녹화 데이터가 여러 개 있으면 자동으로 모두 사용합니다.

### 체크포인트에서 재개
```powershell
# 중단된 학습 재개
py tools/train_pixel_rl.py --game ML --model models/rl_pixel/ML/ML_ppo_interrupted.zip
```

### 멀티게임 학습
MP와 ML 게임을 각각 학습:
```powershell
py tools/train_pixel_rl.py --game MP --timesteps 100000
py tools/train_pixel_rl.py --game ML --timesteps 100000
```

## ❓ FAQ

**Q: YOLO 모델이 필요한가요?**  
A: 아니요! 픽셀만으로 학습합니다.

**Q: 라벨링이 필요한가요?**  
A: 아니요! 게임 플레이만 녹화하면 됩니다.

**Q: 얼마나 녹화해야 하나요?**  
A: 최소 10분, 권장 30분 이상

**Q: GPU가 필요한가요?**  
A: CPU만으로도 학습 가능하지만, GPU가 있으면 훨씬 빠릅니다.

**Q: 학습 시간은?**  
A: CPU 기준 100,000 timesteps에 약 30분~1시간

**Q: 게임 화면이 달라지면?**  
A: 새로 녹화하고 재학습하면 됩니다.

## 📝 예상 결과

- **초기 (0-20k steps)**: 무작위 행동
- **중기 (20k-50k steps)**: 기본 이동 학습
- **후기 (50k+ steps)**: 전투 패턴, 회피 등

## 🐛 트러블슈팅

### 녹화 데이터가 없다는 오류
```
❌ 녹화 데이터가 없습니다: datasets/play_recordings
```
→ `py tools/record_gui.py`로 게임 플레이 녹화

### 메모리 부족
→ `--frame-width 64 --frame-height 64`로 해상도 낮추기

### 학습이 안 됨 (보상 증가 없음)
→ 더 많은 데이터 녹화, learning_rate 조정

### 창 선택 오류
→ 게임을 창모드로 실행하고 리스트에서 선택
