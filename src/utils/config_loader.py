"""공용 설정 로더 유틸리티

- 기본 설정(config.yaml)에 게임별 오버레이(configs/<GAME>.yaml)를 재귀 병합하여 반환
- main.py, 툴 스크립트 등에서 재사용 가능
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


def _deep_merge(base: Dict[str, Any], override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """dict 재귀 병합 (override가 base 값을 덮어씀)

    Args:
        base: 기준 딕셔너리 (변경되지 않음)
        override: 덮어쓸 값이 담긴 딕셔너리 (None 허용)
    Returns:
        병합된 새 딕셔너리
    """
    result: Dict[str, Any] = dict(base)
    if not override:
        return result
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)  # type: ignore[arg-type]
        else:
            result[k] = v
    return result


def load_config(base_config_path: str | Path = "config.yaml", game: Optional[str] = None) -> Dict[str, Any]:
    """설정 파일 로드 (+게임별 오버레이 적용)

    Args:
        base_config_path: 기본 설정 파일 경로
        game: 'MP' 또는 'ML' (없으면 기본 설정만 사용)

    Returns:
        병합된 설정 딕셔너리
    """
    base_path = Path(base_config_path)
    if not base_path.exists():
        raise FileNotFoundError(f"기본 설정 파일을 찾을 수 없습니다: {base_path}")

    with open(base_path, "r", encoding="utf-8") as f:
        base = yaml.safe_load(f) or {}

    if game:
        overlay_path = Path("configs") / f"{game}.yaml"
        if overlay_path.exists():
            with open(overlay_path, "r", encoding="utf-8") as f:
                overlay = yaml.safe_load(f) or {}
            return _deep_merge(base, overlay)
        else:
            print(f"[경고] 게임 오버레이 설정이 없습니다: {overlay_path} (기본 설정만 사용)")
    return base
