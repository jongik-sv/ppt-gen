#!/usr/bin/env python3
"""
YAML 유틸리티.

YAML 파일 읽기/쓰기 공통 유틸리티.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class YAMLDumper(yaml.SafeDumper):
    """커스텀 YAML Dumper (한글 지원, 정렬 안 함)."""
    pass


def str_representer(dumper, data):
    """멀티라인 문자열 처리."""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


YAMLDumper.add_representer(str, str_representer)


def save_yaml(data: Any, path: Path, header: Optional[str] = None) -> None:
    """
    YAML 파일 저장.

    Args:
        data: 저장할 데이터
        path: 저장 경로
        header: 파일 상단에 추가할 주석 (선택)
    """
    if not HAS_YAML:
        raise ImportError("PyYAML이 필요합니다: pip install PyYAML")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    content = yaml.dump(
        data,
        Dumper=YAMLDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120
    )

    if header:
        # 주석 추가
        header_lines = [f"# {line}" if line else "#" for line in header.split('\n')]
        content = '\n'.join(header_lines) + '\n\n' + content

    path.write_text(content, encoding='utf-8')


def load_yaml(path: Path) -> Optional[Dict]:
    """
    YAML 파일 로드.

    Args:
        path: 파일 경로

    Returns:
        파싱된 데이터 또는 None
    """
    if not HAS_YAML:
        raise ImportError("PyYAML이 필요합니다: pip install PyYAML")

    path = Path(path)
    if not path.exists():
        return None

    content = path.read_text(encoding='utf-8')
    return yaml.safe_load(content)


def update_registry(
    registry_path: Path,
    template_id: str,
    template_data: Dict,
    replace: bool = False
) -> None:
    """
    레지스트리 파일 업데이트.

    Args:
        registry_path: registry.yaml 경로
        template_id: 템플릿 ID
        template_data: 추가할 템플릿 데이터
        replace: 기존 항목 대체 여부
    """
    registry = load_yaml(registry_path) or {'templates': []}

    # 기존 항목 검색
    templates = registry.get('templates', [])
    existing_idx = None
    for i, t in enumerate(templates):
        if t.get('id') == template_id:
            existing_idx = i
            break

    if existing_idx is not None:
        if replace:
            templates[existing_idx] = template_data
        else:
            raise ValueError(f"템플릿 '{template_id}'가 이미 존재합니다. replace=True로 덮어쓰기 가능")
    else:
        templates.append(template_data)

    registry['templates'] = templates
    registry['updated_at'] = datetime.now().isoformat()

    save_yaml(registry, registry_path)


def remove_from_registry(registry_path: Path, template_id: str) -> bool:
    """
    레지스트리에서 템플릿 제거.

    Args:
        registry_path: registry.yaml 경로
        template_id: 제거할 템플릿 ID

    Returns:
        제거 성공 여부
    """
    registry = load_yaml(registry_path)
    if registry is None:
        return False

    templates = registry.get('templates', [])
    original_count = len(templates)

    templates = [t for t in templates if t.get('id') != template_id]

    if len(templates) == original_count:
        return False

    registry['templates'] = templates
    registry['updated_at'] = datetime.now().isoformat()

    save_yaml(registry, registry_path)
    return True


def find_in_registry(
    registry_path: Path,
    **criteria
) -> List[Dict]:
    """
    레지스트리에서 조건에 맞는 템플릿 검색.

    Args:
        registry_path: registry.yaml 경로
        **criteria: 검색 조건 (예: source_document="dongkuk")

    Returns:
        매칭된 템플릿 목록
    """
    registry = load_yaml(registry_path)
    if registry is None:
        return []

    templates = registry.get('templates', [])
    results = []

    for t in templates:
        match = True
        for key, value in criteria.items():
            if t.get(key) != value:
                match = False
                break
        if match:
            results.append(t)

    return results


def generate_template_yaml(
    doc_id: str,
    doc_name: str,
    group: str,
    source_file: str,
    slide_size: Dict[str, Any],
    layouts: List[Dict],
    master: Dict,
    theme: Dict
) -> Dict:
    """
    template.yaml 데이터 생성.

    Args:
        doc_id: 문서 ID
        doc_name: 문서 이름
        group: 문서 그룹
        source_file: 원본 파일명
        slide_size: 슬라이드 크기 정보
        layouts: 레이아웃 목록
        master: 슬라이드 마스터 정보
        theme: 테마 정보

    Returns:
        template.yaml 형식의 딕셔너리
    """
    return {
        'document': {
            'id': doc_id,
            'name': doc_name,
            'group': group,
            'source_file': source_file,
            'extracted_at': datetime.now().strftime('%Y-%m-%d'),
            'slide_size': slide_size
        },
        'layouts': layouts,
        'master': master,
        'theme': theme
    }
