"""
로깅 유틸리티
"""

import logging
import sys
from pathlib import Path

def setup_logger(logging_config):
    """
    로거 설정
    
    Args:
        logging_config (dict): 로깅 설정
    
    Returns:
        logging.Logger: 설정된 로거
    """
    # 로그 디렉토리 생성
    log_file = Path(logging_config['file'])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 로그 레벨 설정
    level = getattr(logging, logging_config['level'].upper(), logging.INFO)
    
    # 로거 생성
    logger = logging.getLogger('PerceptiveAI')
    logger.setLevel(level)
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 포맷터 생성
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
