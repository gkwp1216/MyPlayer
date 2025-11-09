"""
게임별(MP/ML) YOLO 학습 헬퍼 스크립트

예)
  # MP 데이터로 학습 (가벼운 모델, 50 epoch)
  py tools/train_yolo.py --game MP --model yolo11n.pt --epochs 50

  # ML 데이터로 학습 (중간 모델)
  py tools/train_yolo.py --game ML --model yolo11s.pt --epochs 60
"""

from pathlib import Path
import argparse
import shutil

from ultralytics import YOLO


def train(game: str, model_name: str, epochs: int, imgsz: int, batch: int):
    data_yaml = Path(f"data_{game}.yaml")
    assert data_yaml.exists(), f"데이터 설정 파일이 없습니다: {data_yaml}"

    # 사전학습 가중치로 모델 로드
    model = YOLO(model_name)

    # runs/<GAME>/train_* 에 결과가 쌓이도록 구분
    project_dir = Path("runs") / game
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=str(project_dir),
        name="train",
    )

    # 최종 best.pt 복사 -> models/<game> 전용 가중치로 보관
    weights = Path(results.save_dir) / "weights" / "best.pt"
    target_dir = Path("models")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / (game.lower() + "_best.pt")
    if weights.exists():
        shutil.copy2(weights, target)
        print(f"✅ 가중치 저장: {target}")
    else:
        print("⚠️ best.pt를 찾지 못했습니다. runs 폴더를 확인하세요.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="게임별 YOLO 학습")
    parser.add_argument("--game", required=True, choices=["MP", "ML"], help="게임 코드")
    parser.add_argument("--model", default="yolo11n.pt", help="사전학습 가중치 (예: yolo11n.pt)")
    parser.add_argument("--epochs", type=int, default=50, help="학습 epoch")
    parser.add_argument("--imgsz", type=int, default=640, help="이미지 크기")
    parser.add_argument("--batch", type=int, default=16, help="배치 크기")

    args = parser.parse_args()
    train(args.game, args.model, args.epochs, args.imgsz, args.batch)
