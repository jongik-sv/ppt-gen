"""
공유 경로 설정 모듈
ppt-extract, ppt-gen 스킬에서 공통 사용

모든 경로는 이 모듈을 기준으로 상대 경로로 계산됨
"""

from pathlib import Path

# 기준 경로: shared/ 디렉토리
SHARED_DIR = Path(__file__).parent

# 스킬 디렉토리
SKILLS_DIR = SHARED_DIR.parent
PPT_EXTRACT_DIR = SKILLS_DIR / 'ppt-extract'
PPT_GEN_DIR = SKILLS_DIR / 'ppt-gen'

# 프로젝트 루트 (docs/)
PROJECT_ROOT = SKILLS_DIR.parent.parent

# 템플릿 디렉토리 구조
TEMPLATES_DIR = PROJECT_ROOT / 'templates'
THEMES_DIR = TEMPLATES_DIR / 'themes'
CONTENTS_DIR = TEMPLATES_DIR / 'contents'
DOCUMENTS_DIR = TEMPLATES_DIR / 'documents'
ASSETS_DIR = TEMPLATES_DIR / 'assets'

# 출력 디렉토리
OUTPUT_DIR = PROJECT_ROOT / 'output'

# 레지스트리 파일 경로
CONTENTS_REGISTRY = CONTENTS_DIR / 'registry.yaml'
ASSETS_REGISTRY = ASSETS_DIR / 'registry.yaml'


def get_document_registry(group: str) -> Path:
    """특정 그룹의 문서 레지스트리 경로 반환"""
    return DOCUMENTS_DIR / group / 'registry.yaml'


def get_theme_path(theme_id: str) -> Path:
    """테마 YAML 파일 경로 반환"""
    return THEMES_DIR / f'{theme_id}.yaml'


def get_content_template_path(category: str, template_id: str) -> Path:
    """콘텐츠 템플릿 파일 경로 반환"""
    return CONTENTS_DIR / 'templates' / category / f'{template_id}.yaml'


def ensure_output_dir(session_id: str) -> Path:
    """세션별 출력 디렉토리 생성 및 경로 반환"""
    session_dir = OUTPUT_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir
