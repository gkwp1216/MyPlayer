"""
Perceptive-AI 메인 실행 파일
메이플스토리 지능형 AI 에이전트
"""

import time
import yaml
import argparse
from pathlib import Path
from src.utils.config_loader import load_config
from src.timer_manager import TimerManager
from src.action_controller import ActionController
from src.perception.yolo_detector import YOLODetector
from src.decision.strategy import StrategyEngine
from src.utils.logger import setup_logger


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="Perceptive-AI 실행")
    parser.add_argument("--game", choices=["MP", "ML"], help="게임 코드 (MP/ML). 생략 시 기본 설정 사용")
    args = parser.parse_args()

    # 설정 로드 (게임별 오버레이 반영)
    config = load_config(game=args.game)
    
    # 로거 설정
    logger = setup_logger(config['logging'])
    logger.info("=" * 60)
    logger.info("Perceptive-AI 시작")
    logger.info("=" * 60)
    
    # 컴포넌트 초기화
    timer_manager = TimerManager(config['timers'])
    action_controller = ActionController(config['keybindings'], config['action'])
    
    # Phase 2 이후 활성화: YOLO 모델 로드
    # yolo_detector = YOLODetector(config['yolo'])
    # strategy_engine = StrategyEngine()
    
    logger.info("모든 컴포넌트 초기화 완료")
    logger.info("AI 에이전트 실행 중... (Ctrl+C로 종료)")
    
    try:
        while True:
            current_time = time.time()
            
            # 30분 버프 체크
            if timer_manager.should_use_buff(current_time):
                logger.info("[버프] 30분 경험치 버프 사용 시작")
                action_controller.use_buff()
                timer_manager.reset_buff_timer(current_time)
                logger.info(f"[버프] 다음 버프까지: {timer_manager.get_next_buff_delay():.1f}초")
            
            # 1분 설치기 체크
            if timer_manager.should_use_skill(current_time):
                logger.info("[설치기] 1분 주기 도래 - 상황 분석 시작")
                
                # Phase 1: 단순 스킬 사용
                action_controller.use_skill_simple()
                logger.info("[설치기] 스킬 사용 완료 (Phase 1 - 단순 모드)")
                
                # Phase 3: YOLO 기반 지능형 스킬 사용 (미래 구현)
                # logger.info("[설치기] 화면 캡처 및 객체 탐지 중...")
                # detections = yolo_detector.detect()
                # target_pos = strategy_engine.calculate_best_position(detections)
                # 
                # if target_pos:
                #     logger.info(f"[설치기] 최적 위치 {target_pos}에 스킬 사용")
                #     action_controller.use_skill_at_position(target_pos)
                # else:
                #     logger.info("[설치기] 몬스터 없음 - 스킬 사용 안 함")
                
                timer_manager.reset_skill_timer(current_time)
                logger.info(f"[설치기] 다음 설치기까지: {timer_manager.get_next_skill_delay():.1f}초")
            
            # 메인 루프 딜레이 (CPU 부하 감소)
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("사용자에 의해 프로그램 종료")
        logger.info("=" * 60)

if __name__ == "__main__":
    main()
