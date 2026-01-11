"""
공유 YAML 유틸리티 모듈
ppt-extract, ppt-gen 스킬에서 공통 사용
"""

from pathlib import Path
from datetime import datetime
from typing import Any, Optional

import yaml


def load_yaml(path: Path, default: Optional[dict] = None) -> dict:
    """YAML 파일 로드

    Args:
        path: YAML 파일 경로
        default: 파일이 없거나 비어있을 때 반환할 기본값

    Returns:
        파싱된 딕셔너리 또는 기본값
    """
    if default is None:
        default = {}

    if not path.exists():
        return default

    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or default


def save_yaml(
    path: Path,
    data: dict,
    header: str = '',
    add_timestamp: bool = False,
    timestamp_label: str = '마지막 업데이트'
) -> None:
    """YAML 파일 저장

    Args:
        path: 저장할 파일 경로
        data: 저장할 딕셔너리
        header: 파일 상단에 추가할 주석 헤더
        add_timestamp: True면 타임스탬프 주석 자동 추가
        timestamp_label: 타임스탬프 주석 레이블
    """
    # 부모 디렉토리 생성
    path.parent.mkdir(parents=True, exist_ok=True)

    yaml_str = ''

    if header:
        yaml_str = header
        if not header.endswith('\n'):
            yaml_str += '\n'

    if add_timestamp:
        yaml_str += f"# {timestamp_label}: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    yaml_str += yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(yaml_str)


def load_registry(
    path: Path,
    default_keys: Optional[list] = None
) -> dict:
    """레지스트리 YAML 로드 (기본 구조 보장)

    Args:
        path: registry.yaml 경로
        default_keys: 기본으로 포함될 키 리스트 (예: ['templates'], ['icons', 'images'])

    Returns:
        기본 구조가 보장된 딕셔너리
    """
    if default_keys is None:
        default_keys = ['templates']

    default = {key: [] for key in default_keys}

    if not path.exists():
        return default

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    # 기본 키 보장
    for key in default_keys:
        if key not in data or data[key] is None:
            data[key] = []

    return data


def save_registry(
    path: Path,
    data: dict,
    title: str = '레지스트리'
) -> None:
    """레지스트리 YAML 저장 (타임스탬프 포함)

    Args:
        path: 저장할 파일 경로
        data: 저장할 딕셔너리
        title: 파일 제목 (주석에 사용)
    """
    header = f"# {title}\n"
    save_yaml(path, data, header=header, add_timestamp=True)
