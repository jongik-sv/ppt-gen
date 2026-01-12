"""
PPT Skills 공유 모듈
ppt-extract, ppt-gen 스킬에서 공통 사용

모듈:
- yaml_utils: YAML 파일 I/O (load_yaml, save_yaml, load_registry, save_registry)
- config: 경로 상수 (TEMPLATES_DIR, CONTENTS_DIR, ASSETS_DIR 등)
- xml_utils: OOXML 파일 처리 (extract_ooxml, extract_layout_ooxml 등)
"""

from .yaml_utils import load_yaml, save_yaml, load_registry, save_registry
from .config import (
    PROJECT_ROOT,
    TEMPLATES_DIR,
    THEMES_DIR,
    CONTENTS_DIR,
    DOCUMENTS_DIR,
    ASSETS_DIR,
    OUTPUT_DIR,
)
from .xml_utils import (
    extract_ooxml,
    extract_layout_ooxml,
    extract_layout_rels,
    extract_slide_master_ooxml,
    extract_slide_master_rels,
    extract_theme_ooxml,
    NAMESPACES,
)

__all__ = [
    # yaml_utils
    'load_yaml',
    'save_yaml',
    'load_registry',
    'save_registry',
    # config
    'PROJECT_ROOT',
    'TEMPLATES_DIR',
    'THEMES_DIR',
    'CONTENTS_DIR',
    'DOCUMENTS_DIR',
    'ASSETS_DIR',
    'OUTPUT_DIR',
    # xml_utils
    'extract_ooxml',
    'extract_layout_ooxml',
    'extract_layout_rels',
    'extract_slide_master_ooxml',
    'extract_slide_master_rels',
    'extract_theme_ooxml',
    'NAMESPACES',
]
