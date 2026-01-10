#!/usr/bin/env python3
"""
Registry Sync Script - 개별 템플릿 YAML → 분리형 registry 파일 생성

개별 템플릿 YAML 파일에서 메타데이터를 추출하여 카테고리별 registry 파일을 생성합니다.
개별 YAML이 source of truth(원본)이며, registry는 자동 생성됩니다.

Usage:
    python sync_registry.py [--dry-run] [--test QUERY]

기능:
1. templates/contents/templates/**/*.yaml 스캔
2. 카테고리별로 그룹화
3. 각 카테고리별 registry-{category}.yaml 생성
4. 마스터 registry.yaml 업데이트 (인덱스 + 통계)

Examples:
    # 전체 동기화
    python sync_registry.py

    # 미리보기 (실제 파일 수정 없음)
    python sync_registry.py --dry-run

    # 키워드 검색 테스트
    python sync_registry.py --test "비교 슬라이드"
"""

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

# 공유 모듈 import
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent.parent / 'shared'))
from config import CONTENTS_DIR
from yaml_utils import load_yaml, save_yaml

# 카테고리 정보 (한글 이름, 설명)
CATEGORY_INFO = {
    'chart': {'name': '차트', 'description': '차트/그래프 레이아웃'},
    'closing': {'name': '마무리', 'description': '마무리/클로징 슬라이드'},
    'comparison': {'name': '비교', 'description': '비교 레이아웃'},
    'content': {'name': '콘텐츠', 'description': '일반 텍스트 레이아웃'},
    'cycle': {'name': '사이클', 'description': '순환 구조 레이아웃'},
    'diagram': {'name': '다이어그램', 'description': '관계도/구조도 레이아웃'},
    'grid': {'name': '그리드', 'description': '다열 그리드 레이아웃'},
    'hierarchy': {'name': '계층', 'description': '계층 구조 레이아웃'},
    'matrix': {'name': '매트릭스', 'description': '2x2, 3x3 매트릭스 레이아웃'},
    'process': {'name': '프로세스', 'description': '단계별 프로세스 레이아웃'},
    'stats': {'name': '통계', 'description': '통계/수치 레이아웃'},
    'table': {'name': '테이블', 'description': '표 형식 레이아웃'},
    'timeline': {'name': '타임라인', 'description': '시간순 진행 레이아웃'},
}


def merge_keywords(template_data: dict) -> list:
    """use_for + keywords + prompt_keywords 통합 (중복 제거, 순서 유지)"""
    all_keywords = []

    # 1. prompt_keywords (가장 중요 - 검색에 직접 매칭)
    all_keywords.extend(template_data.get('prompt_keywords', []))

    # 2. use_for (용도 설명)
    all_keywords.extend(template_data.get('use_for', []))

    # 3. keywords (보조 키워드)
    all_keywords.extend(template_data.get('keywords', []))

    # 중복 제거 (순서 유지)
    seen = set()
    result = []
    for kw in all_keywords:
        if kw is None:
            continue
        kw_lower = str(kw).lower().strip()
        if kw_lower and kw_lower not in seen:
            seen.add(kw_lower)
            result.append(str(kw).strip())

    return result


def extract_description(expected_prompt: str) -> str:
    """expected_prompt에서 첫 문장을 description으로 추출"""
    if not expected_prompt:
        return ""

    # 첫 줄 추출
    first_line = expected_prompt.strip().split('\n')[0]

    # "~슬라이드를 만들어줘." 패턴을 간결하게 변환
    desc = first_line.replace('슬라이드를 만들어줘.', '슬라이드')
    desc = desc.replace('슬라이드를 만들어줘', '슬라이드')
    desc = desc.strip()

    # 마침표가 없으면 추가
    if desc and not desc.endswith('.'):
        desc += '.'

    return desc


def scan_template_files() -> list:
    """모든 템플릿 YAML 파일 스캔"""
    templates_dir = CONTENTS_DIR / 'templates'
    templates = []

    for yaml_file in templates_dir.rglob('*.yaml'):
        # 카테고리 추출 (부모 디렉토리 이름)
        category = yaml_file.parent.name

        try:
            data = load_yaml(yaml_file)
            if not data:
                continue

            # content_template 구조 확인
            ct = data.get('content_template', {})
            template_id = ct.get('id', yaml_file.stem)
            name = ct.get('name', template_id)
            source_slide_index = ct.get('source_slide_index', 0)

            # 검색 메타데이터 추출
            expected_prompt = data.get('expected_prompt', '')
            match_keywords = merge_keywords(data)
            description = extract_description(expected_prompt)

            # description이 없으면 name 사용
            if not description:
                description = name

            templates.append({
                'id': template_id,
                'name': name,
                'file': f'templates/{category}/{yaml_file.name}',
                'thumbnail': f'thumbnails/{category}/{yaml_file.stem}.png',
                'category': category,
                'source_slide_index': source_slide_index,
                'description': description,
                'match_keywords': match_keywords,
                'expected_prompt': expected_prompt.strip() if expected_prompt else None,
                '_yaml_path': yaml_file,  # 내부용
            })

        except Exception as e:
            print(f"Warning: Failed to parse {yaml_file}: {e}")
            continue

    return templates


def group_by_category(templates: list) -> dict:
    """카테고리별로 그룹화"""
    by_category = defaultdict(list)

    for t in templates:
        category = t['category']
        by_category[category].append(t)

    # 각 카테고리 내에서 id로 정렬
    for category in by_category:
        by_category[category].sort(key=lambda x: x['id'])

    return dict(by_category)


def write_category_registry(category: str, items: list, dry_run: bool = False) -> Path:
    """카테고리별 registry 파일 생성"""
    registry_path = CONTENTS_DIR / f'registry-{category}.yaml'

    # 템플릿 데이터 준비 (내부 필드 제거)
    templates = []
    for item in items:
        t = {k: v for k, v in item.items() if not k.startswith('_')}
        # category 필드는 카테고리 파일에서는 불필요 (중복)
        t.pop('category', None)
        # expected_prompt가 None이면 제거
        if t.get('expected_prompt') is None:
            t.pop('expected_prompt', None)
        templates.append(t)

    # 카테고리 정보
    cat_info = CATEGORY_INFO.get(category, {'name': category, 'description': ''})

    registry_data = {
        'category': category,
        'name': cat_info['name'],
        'description': cat_info['description'],
        'version': '4.1',
        'updated_at': datetime.now().strftime('%Y-%m-%d'),
        'templates': templates,
    }

    if dry_run:
        print(f"\n[DRY-RUN] Would write: {registry_path}")
        print(f"  - Templates: {len(templates)}")
    else:
        save_yaml(registry_path, registry_data)
        print(f"Written: {registry_path} ({len(templates)} templates)")

    return registry_path


def write_master_registry(by_category: dict, dry_run: bool = False) -> Path:
    """마스터 registry.yaml 생성"""
    registry_path = CONTENTS_DIR / 'registry.yaml'

    # 카테고리별 정보 구성
    categories = {}
    total_count = 0

    for category in sorted(by_category.keys()):
        items = by_category[category]
        count = len(items)
        total_count += count

        cat_info = CATEGORY_INFO.get(category, {'name': category, 'description': ''})

        categories[category] = {
            'name': cat_info['name'],
            'description': cat_info['description'],
            'file': f'registry-{category}.yaml',
            'count': count,
        }

    registry_data = {
        'version': '4.1',
        'type': 'index',
        'source': 'PPT기본양식_병합_수정(선별).pptx',
        'updated_at': datetime.now().strftime('%Y-%m-%d'),
        'categories': categories,
        'stats': {
            'total_templates': total_count,
            'total_categories': len(categories),
        },
    }

    if dry_run:
        print(f"\n[DRY-RUN] Would write: {registry_path}")
        print(f"  - Categories: {len(categories)}")
        print(f"  - Total templates: {total_count}")
    else:
        save_yaml(registry_path, registry_data)
        print(f"Written: {registry_path} (index, {total_count} total templates)")

    return registry_path


def sync_registries(dry_run: bool = False):
    """전체 동기화 실행"""
    print("=" * 60)
    print("Registry Sync - 개별 템플릿 YAML → 분리형 registry 생성")
    print("=" * 60)

    # 1. 모든 템플릿 YAML 스캔
    print("\n[1/4] Scanning template files...")
    templates = scan_template_files()
    print(f"  Found {len(templates)} templates")

    if not templates:
        print("  No templates found. Exiting.")
        return

    # 2. 카테고리별 그룹화
    print("\n[2/4] Grouping by category...")
    by_category = group_by_category(templates)
    for cat, items in sorted(by_category.items()):
        print(f"  {cat}: {len(items)} templates")

    # 3. 각 카테고리별 registry 파일 생성
    print("\n[3/4] Writing category registries...")
    for category, items in sorted(by_category.items()):
        write_category_registry(category, items, dry_run)

    # 4. 마스터 registry.yaml 업데이트
    print("\n[4/4] Writing master registry...")
    write_master_registry(by_category, dry_run)

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY-RUN complete. No files were modified.")
    else:
        print("Sync complete!")
    print("=" * 60)


def test_search(query: str):
    """키워드 검색 테스트"""
    print(f"\nSearching for: '{query}'")
    print("-" * 40)

    # 마스터 레지스트리 로드
    master_path = CONTENTS_DIR / 'registry.yaml'
    if not master_path.exists():
        print("Error: Master registry not found. Run sync first.")
        return

    master = load_yaml(master_path)
    if master.get('type') != 'index':
        print("Error: Master registry is not index type.")
        return

    query_lower = query.lower()
    matches = []

    # 각 카테고리 검색
    for cat_id, cat_info in master['categories'].items():
        cat_registry_path = CONTENTS_DIR / cat_info['file']
        if not cat_registry_path.exists():
            continue

        cat_registry = load_yaml(cat_registry_path)
        for t in cat_registry.get('templates', []):
            # match_keywords에서 검색
            keywords = t.get('match_keywords', [])
            score = 0
            matched_kws = []

            for kw in keywords:
                if query_lower in kw.lower():
                    score += 2  # 부분 매칭
                    matched_kws.append(kw)
                elif kw.lower() in query_lower:
                    score += 1  # 역방향 부분 매칭
                    matched_kws.append(kw)

            # description에서도 검색
            desc = t.get('description', '')
            if query_lower in desc.lower():
                score += 1

            if score > 0:
                matches.append({
                    'id': t['id'],
                    'name': t['name'],
                    'category': cat_id,
                    'description': t.get('description', ''),
                    'score': score,
                    'matched_keywords': matched_kws,
                })

    # 점수순 정렬
    matches.sort(key=lambda x: -x['score'])

    if matches:
        print(f"Found {len(matches)} matches:\n")
        for i, m in enumerate(matches[:10], 1):
            print(f"{i}. [{m['category']}] {m['id']} (score: {m['score']})")
            print(f"   Name: {m['name']}")
            print(f"   Description: {m['description']}")
            if m['matched_keywords']:
                print(f"   Matched: {', '.join(m['matched_keywords'])}")
            print()
    else:
        print("No matches found.")


def main():
    parser = argparse.ArgumentParser(
        description='Registry Sync - 개별 템플릿 YAML → 분리형 registry 생성'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='미리보기 모드 (실제 파일 수정 없음)'
    )
    parser.add_argument(
        '--test', '-t',
        type=str,
        metavar='QUERY',
        help='키워드 검색 테스트'
    )

    args = parser.parse_args()

    if args.test:
        test_search(args.test)
    else:
        sync_registries(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
