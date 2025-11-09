"""
전략 엔진 모듈
Phase 3: The Brain
"""

import numpy as np

class StrategyEngine:
    """의사결정 엔진 - 최적의 스킬 사용 위치 계산"""
    
    def __init__(self):
        """전략 엔진 초기화"""
        print("[Phase 3 준비] 전략 엔진은 Phase 3에서 활성화됩니다.")
    
    def calculate_best_position(self, detections):
        """
        탐지된 객체들을 분석하여 최적의 스킬 사용 위치 계산
        
        Args:
            detections (list): YOLO로 탐지된 객체 목록
        
        Returns:
            tuple or None: (x, y) 최적 위치 또는 None
        """
        # Phase 3 구현
        # 몬스터만 필터링
        # monsters = [d for d in detections if d['class'] == 'monster']
        # 
        # if not monsters:
        #     return None
        # 
        # # 몬스터들의 중심점 계산
        # centers = []
        # for monster in monsters:
        #     x1, y1, x2, y2 = monster['bbox']
        #     center_x = (x1 + x2) / 2
        #     center_y = (y1 + y2) / 2
        #     centers.append([center_x, center_y])
        # 
        # # 몬스터 밀집도가 가장 높은 위치 계산 (평균 중심)
        # centers_array = np.array(centers)
        # best_position = np.mean(centers_array, axis=0)
        # 
        # return tuple(best_position.astype(int))
        
        return None
    
    def should_use_skill(self, detections, min_monster_count=1):
        """
        스킬을 사용할지 여부 판단
        
        Args:
            detections (list): 탐지된 객체 목록
            min_monster_count (int): 스킬 사용을 위한 최소 몬스터 수
        
        Returns:
            bool: 스킬 사용 여부
        """
        # Phase 3 구현
        # monsters = [d for d in detections if d['class'] == 'monster']
        # return len(monsters) >= min_monster_count
        return False
