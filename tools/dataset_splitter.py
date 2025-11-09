"""
데이터셋 분할 도구
raw 폴더의 이미지를 train/val/test로 분할

멀티 게임 지원:
- 기본(default): 기존 경로 사용 (datasets/raw -> datasets/images, datasets/labels)
- --game MP 또는 ML 지정 시: datasets/<GAME>/raw -> datasets/<GAME>/images, datasets/<GAME>/labels

예)
    py tools/dataset_splitter.py --game MP
    py tools/dataset_splitter.py --game ML --train 0.85 --val 0.1 --test 0.05
"""

import random
import shutil
from pathlib import Path
import argparse


def split_dataset(raw_dir='datasets/raw',
                  output_dir='datasets',
                  train_ratio=0.8,
                  val_ratio=0.1,
                  test_ratio=0.1):
    """
    raw 폴더의 이미지를 train/val/test로 분할
    
    Args:
        raw_dir (str): 원본 이미지 디렉토리
        output_dir (str): 출력 디렉토리
        train_ratio (float): 학습 데이터 비율
        val_ratio (float): 검증 데이터 비율
        test_ratio (float): 테스트 데이터 비율
    """
    raw_path = Path(raw_dir)
    output_path = Path(output_dir)
    
    # 비율 검증
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001, \
        "비율의 합이 1.0이 아닙니다."
    
    print("=" * 60)
    print("📂 데이터셋 분할 도구")
    print("=" * 60)
    print(f"원본 디렉토리: {raw_path}")
    print(f"출력 디렉토리: {output_path}")
    print(f"분할 비율: Train {train_ratio*100:.0f}% / Val {val_ratio*100:.0f}% / Test {test_ratio*100:.0f}%")
    print("=" * 60)
    
    # 클래스별로 처리 (클래스별 하위 폴더 기준)
    classes = [d.name for d in raw_path.iterdir() if d.is_dir()]
    
    total_images = 0
    split_counts = {'train': 0, 'val': 0, 'test': 0}
    
    for cls in classes:
        cls_path = raw_path / cls
        images = list(cls_path.glob('*.png')) + list(cls_path.glob('*.jpg'))
        
        if len(images) == 0:
            print(f"⚠️  {cls}: 이미지 없음")
            continue
        
        # 랜덤 섞기
        random.shuffle(images)
        
        # 분할 계산
        total = len(images)
        train_count = int(total * train_ratio)
        val_count = int(total * val_ratio)
        test_count = total - train_count - val_count
        
        train_images = images[:train_count]
        val_images = images[train_count:train_count + val_count]
        test_images = images[train_count + val_count:]
        
        print(f"\n📁 {cls}")
        print(f"   총 이미지: {total}장")
        print(f"   Train: {len(train_images)}장 / Val: {len(val_images)}장 / Test: {len(test_images)}장")
        
        # 이미지 복사
        for split_name, split_images in [('train', train_images), 
                                          ('val', val_images), 
                                          ('test', test_images)]:
            dest_dir = output_path / 'images' / split_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            for img in split_images:
                dest_file = dest_dir / f"{cls}_{img.name}"
                shutil.copy(img, dest_file)
                split_counts[split_name] += 1
        
        total_images += total
    
    print("\n" + "=" * 60)
    print("✅ 데이터셋 분할 완료!")
    print("=" * 60)
    print(f"총 이미지: {total_images}장")
    print(f"  Train: {split_counts['train']}장")
    print(f"  Val:   {split_counts['val']}장")
    print(f"  Test:  {split_counts['test']}장")
    print("=" * 60)
    print("\n다음 단계:")
    print("1. Roboflow 또는 LabelImg로 라벨링")
    print("2. 라벨 파일(.txt)을 datasets/labels/ 폴더에 저장")
    print("3. YOLO 학습 실행")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLO 데이터셋 분할 도구")
    parser.add_argument("--game", choices=["MP", "ML"], help="게임 코드 (MP 또는 ML). 생략 시 기본 경로 사용")
    parser.add_argument("--train", type=float, default=0.8, help="train 비율 (기본 0.8)")
    parser.add_argument("--val", type=float, default=0.1, help="val 비율 (기본 0.1)")
    parser.add_argument("--test", type=float, default=0.1, help="test 비율 (기본 0.1)")

    args = parser.parse_args()

    if args.game:
        raw = f"datasets/{args.game}/raw"
        out = f"datasets/{args.game}"
    else:
        raw = "datasets/raw"
        out = "datasets"

    split_dataset(
        raw_dir=raw,
        output_dir=out,
        train_ratio=args.train,
        val_ratio=args.val,
        test_ratio=args.test,
    )
