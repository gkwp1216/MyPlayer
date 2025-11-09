# 🚀 Phase 2 빠른 시작 가이드

## 📋 클래스별 스크린샷 예시와 라벨링 기준 완료!

모든 준비가 끝났습니다. 이제 바로 스크린샷 수집을 시작할 수 있습니다.

---

## 🎯 5가지 클래스 요약

| 클래스 | 목적 | 탐지 대상 | 위치 |
|--------|------|-----------|------|
| **skill_cooldown** | 스킬 쿨타임 확인 | 어두운 스킬 아이콘 + 숫자 | 화면 하단 퀵슬롯 |
| **buff_time_low** | 버프 만료 임박 | 남은 시간 10초 이하 버프 | 우측/좌측 상단 버프 즐겨찾기 |
| **exp_doping_active** | 경험치 도핑 확인 | 경험치 버프 아이콘 존재 | 좌측 상단 버프 목록 |
| **exp_doping_missing** | 경험치 도핑 부재 | 경험치 버프 아이콘 없음 | 좌측 상단 버프 목록 |
| **skill_ready** | 스킬 사용 가능 | 밝은 스킬 아이콘 | 화면 하단 퀵슬롯 |

---

## 📁 생성된 디렉토리 구조

```
MyPlayer/
├── datasets/
│   ├── raw/                          # ← 여기에 스크린샷 저장
│   │   ├── skill_cooldown/           ✅ 준비 완료
│   │   ├── buff_time_low/            ✅ 준비 완료
│   │   ├── exp_doping_active/        ✅ 준비 완료
│   │   ├── exp_doping_missing/       ✅ 준비 완료
│   │   └── skill_ready/              ✅ 준비 완료
│   │
│   ├── images/                       # 라벨링 후 이미지
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   │
│   └── labels/                       # 라벨링 후 라벨
│       ├── train/
│       ├── val/
│       └── test/
│
├── tools/
│   ├── screenshot_helper.py          # ✨ 스크린샷 수집 도구
│   └── dataset_splitter.py           # 데이터셋 분할 도구
│
├── data.yaml                         # ✅ YOLO 학습 설정 파일
└── PHASE2_LABELING_GUIDE.md          # 📖 상세 라벨링 가이드
```

---

## 🎬 Step 1: 스크린샷 수집 (바로 시작!)

### 방법 1: 자동화 도구 사용 (추천) ⭐

```powershell
# 스크린샷 수집 도구 실행
py tools/screenshot_helper.py
```

**단축키**:
- `F5`: 현재 클래스로 스크린샷 저장
- `F6`: 다음 클래스로 전환
- `F7`: 이전 클래스로 전환
- `F8`: 현재 상태 확인
- `ESC`: 종료

**사용 방법**:
1. 도구 실행
2. 메이플스토리 실행
3. 해당 상황(쿨타임, 버프 임박 등)이 화면에 보일 때 `F5` 누르기
4. 각 클래스당 50장 이상 수집
5. `F6`으로 다음 클래스로 전환하여 반복

### 방법 2: 수동 스크린샷

- Windows: `Win + Shift + S` (부분 캡처)
- 게임 내 스크린샷 기능 사용
- 각 클래스 폴더에 수동으로 저장

---

## 📊 Step 2: 데이터셋 분할

스크린샷 수집이 완료되면:

```powershell
# 자동으로 train/val/test 분할 (8:1:1 비율)
py tools/dataset_splitter.py
```

---

## 🏷️ Step 3: 라벨링

### Roboflow 사용 (온라인, 추천)

1. https://roboflow.com 회원가입
2. **New Project** → **Object Detection**
3. `datasets/images/train/` 폴더의 이미지 업로드
4. 각 이미지에 바운딩 박스 그리기:
   - 스킬 아이콘, 버프 아이콘 등을 박스로 표시
   - 클래스 선택 (skill_cooldown, buff_time_low 등)
5. **Export** → **YOLO v8** 포맷으로 다운로드
6. 다운로드한 라벨 파일(.txt)을 `datasets/labels/train/`에 복사

### LabelImg 사용 (오프라인)

```powershell
# 설치
py -m pip install labelImg

# 실행
labelImg
```

1. **Open Dir**: `datasets/images/train/` 선택
2. **Change Save Dir**: `datasets/labels/train/` 선택
3. **PascalVOC → YOLO** 포맷으로 변경
4. `W` 키로 바운딩 박스 생성
5. 클래스 선택 후 저장

---

## 🧠 Step 4: YOLO 모델 학습

라벨링이 완료되면:

```powershell
# YOLOv8n 모델로 학습 시작 (nano - 가장 빠름)
yolo detect train data=data.yaml model=yolov8n.pt epochs=50 imgsz=640

# 더 정확한 모델 원하면 (속도는 느림)
yolo detect train data=data.yaml model=yolov8s.pt epochs=100 imgsz=640
```

**학습 결과**:
- `runs/detect/train/weights/best.pt` ← 이 파일이 커스텀 모델

---

## 🎯 Step 5: 모델 배포

```powershell
# 학습된 모델을 프로젝트에 복사
Copy-Item runs/detect/train/weights/best.pt models/best.pt
```

이제 `main.py`에서 YOLO 모델을 사용할 수 있습니다!

---

## 📖 자세한 내용

- **라벨링 상세 가이드**: `PHASE2_LABELING_GUIDE.md`
- **데이터셋 구조**: `datasets/README.md`

---

## ✅ 체크리스트

- [ ] Step 1: 각 클래스당 최소 50장 스크린샷 수집
- [ ] Step 2: 데이터셋 분할 (train/val/test)
- [ ] Step 3: 모든 이미지 라벨링 완료
- [ ] Step 4: YOLO 모델 학습 실행
- [ ] Step 5: `best.pt` 모델을 `models/` 폴더에 복사
- [ ] Step 6: `main.py`에서 YOLO 기능 활성화

---

## 💡 팁

### 빠르게 시작하려면
1. 지금 바로 `py tools/screenshot_helper.py` 실행
2. 메이플스토리 실행
3. 각 상황에서 `F5` 연타로 빠르게 수집
4. 각 클래스당 50장이면 충분 (더 많으면 더 좋음)

### 라벨링 시간 절약
- Roboflow의 자동 라벨링 기능 활용
- 비슷한 이미지는 복사 후 조정
- 명확한 이미지만 선별하여 라벨링

---

**바로 시작하세요!** 🚀

```powershell
py tools/screenshot_helper.py
```
