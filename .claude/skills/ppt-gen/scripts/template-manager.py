#!/usr/bin/env python3
"""
Template Manager - 템플릿 목록/삭제/아카이브 CLI

PPT 생성에 사용할 문서 템플릿과 콘텐츠 템플릿을 관리합니다.

Usage:
    python template-manager.py list [--type documents|contents]
    python template-manager.py info <template_id>
    python template-manager.py delete <template_id>
    python template-manager.py archive <template_id>
    python template-manager.py restore <template_id>

Examples:
    # 전체 목록
    python template-manager.py list

    # 문서 템플릿만
    python template-manager.py list --type documents

    # 콘텐츠 템플릿만
    python template-manager.py list --type contents

    # 상세 정보
    python template-manager.py info 제안서1

    # 아카이브 (숨김)
    python template-manager.py archive 제안서1

    # 복원
    python template-manager.py restore 제안서1

    # 삭제
    python template-manager.py delete 제안서1
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

# 공유 모듈 import
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent.parent / 'shared'))
from config import TEMPLATES_DIR, DOCUMENTS_DIR, CONTENTS_DIR
from yaml_utils import load_yaml, save_yaml


def scan_document_templates() -> list:
    """문서 템플릿 스캔 (그룹별)"""
    templates = []

    if not DOCUMENTS_DIR.exists():
        return templates

    for group_dir in DOCUMENTS_DIR.iterdir():
        if not group_dir.is_dir():
            continue

        registry_path = group_dir / 'registry.yaml'
        if not registry_path.exists():
            continue

        registry = load_yaml(registry_path)
        group_id = group_dir.name

        for tpl in registry.get('templates', []):
            templates.append({
                'id': tpl.get('id'),
                'name': tpl.get('name'),
                'type': 'document',
                'group': group_id,
                'file': tpl.get('file'),
                'description': tpl.get('description', ''),
                'created': tpl.get('created', ''),
                'archived': tpl.get('archived', False),
                '_registry_path': registry_path,
                '_file_path': group_dir / tpl.get('file', ''),
            })

    return templates


def scan_content_templates() -> list:
    """콘텐츠 템플릿 스캔"""
    templates = []

    registry_path = CONTENTS_DIR / 'registry.yaml'
    if not registry_path.exists():
        return templates

    registry = load_yaml(registry_path)

    for tpl in registry.get('templates', []):
        templates.append({
            'id': tpl.get('id'),
            'name': tpl.get('name'),
            'type': 'content',
            'category': tpl.get('category', ''),
            'file': tpl.get('file'),
            'description': tpl.get('description', ''),
            'created': tpl.get('created', ''),
            'archived': tpl.get('archived', False),
            '_registry_path': registry_path,
            '_file_path': CONTENTS_DIR / 'templates' / tpl.get('file', ''),
        })

    return templates


def scan_all_templates() -> list:
    """모든 템플릿 스캔"""
    return scan_document_templates() + scan_content_templates()


def find_template(template_id: str) -> dict:
    """ID로 템플릿 찾기"""
    all_templates = scan_all_templates()
    for tpl in all_templates:
        if tpl.get('id') == template_id:
            return tpl
    return None


def update_registry(registry_path: Path, template_id: str, updates: dict) -> bool:
    """레지스트리에서 템플릿 업데이트"""
    registry = load_yaml(registry_path)
    templates = registry.get('templates', [])

    for i, tpl in enumerate(templates):
        if tpl.get('id') == template_id:
            templates[i].update(updates)
            registry['templates'] = templates
            header = f"""# 템플릿 레지스트리
# 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}

"""
            save_yaml(registry_path, registry, header)
            return True

    return False


def remove_from_registry(registry_path: Path, template_id: str) -> bool:
    """레지스트리에서 템플릿 제거"""
    registry = load_yaml(registry_path)
    templates = registry.get('templates', [])

    original_len = len(templates)
    templates = [t for t in templates if t.get('id') != template_id]

    if len(templates) == original_len:
        return False

    registry['templates'] = templates
    header = f"""# 템플릿 레지스트리
# 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}

"""
    save_yaml(registry_path, registry, header)
    return True


def cmd_list(args) -> int:
    """템플릿 목록"""
    show_archived = args.archived

    # 타입 필터
    if args.type == 'documents':
        templates = scan_document_templates()
    elif args.type == 'contents':
        templates = scan_content_templates()
    else:
        templates = scan_all_templates()

    # 아카이브 필터
    if not show_archived:
        templates = [t for t in templates if not t.get('archived')]

    if not templates:
        print("등록된 템플릿이 없습니다.")
        return 0

    # 출력 형식
    if args.format == 'json':
        import json
        output = [{k: v for k, v in t.items() if not k.startswith('_')} for t in templates]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif args.format == 'yaml':
        output = [{k: v for k, v in t.items() if not k.startswith('_')} for t in templates]
        print(yaml.dump(output, allow_unicode=True, default_flow_style=False))
    else:
        # table 형식
        print(f"템플릿 목록: {len(templates)}개")
        print("-" * 80)
        print(f"{'Type':<10} {'ID':<20} {'Name':<25} {'Group/Category':<15} {'Status'}")
        print("-" * 80)

        for tpl in templates:
            tpl_type = tpl['type']
            tpl_id = tpl['id']
            tpl_name = tpl['name'][:25] if tpl['name'] else ''
            group_cat = tpl.get('group') or tpl.get('category', '')
            status = '(archived)' if tpl.get('archived') else ''
            print(f"{tpl_type:<10} {tpl_id:<20} {tpl_name:<25} {group_cat:<15} {status}")

    return 0


def cmd_info(args) -> int:
    """템플릿 상세 정보"""
    template_id = args.id
    tpl = find_template(template_id)

    if not tpl:
        print(f"Error: 템플릿을 찾을 수 없습니다 - {template_id}")
        return 1

    print(f"템플릿 정보: {template_id}")
    print("-" * 50)
    print(f"  ID: {tpl.get('id')}")
    print(f"  Name: {tpl.get('name')}")
    print(f"  Type: {tpl.get('type')}")

    if tpl.get('type') == 'document':
        print(f"  Group: {tpl.get('group')}")
    else:
        print(f"  Category: {tpl.get('category')}")

    print(f"  Description: {tpl.get('description', '(없음)')}")
    print(f"  File: {tpl.get('file')}")
    print(f"  Created: {tpl.get('created', '?')}")
    print(f"  Archived: {'Yes' if tpl.get('archived') else 'No'}")

    # 파일 존재 확인
    file_path = tpl.get('_file_path')
    if file_path and file_path.exists():
        size_kb = file_path.stat().st_size / 1024
        print(f"  Size: {size_kb:.1f} KB")

        # YAML 내용 미리보기
        if args.preview:
            print("\n--- 내용 미리보기 ---")
            content = load_yaml(file_path)
            if content:
                preview = yaml.dump(content, allow_unicode=True, default_flow_style=False)
                lines = preview.split('\n')[:20]
                print('\n'.join(lines))
                if len(preview.split('\n')) > 20:
                    print('... (truncated)')
    else:
        print(f"  Warning: 파일이 존재하지 않습니다!")

    return 0


def cmd_archive(args) -> int:
    """템플릿 아카이브 (숨김)"""
    template_id = args.id
    tpl = find_template(template_id)

    if not tpl:
        print(f"Error: 템플릿을 찾을 수 없습니다 - {template_id}")
        return 1

    if tpl.get('archived'):
        print(f"이미 아카이브된 템플릿입니다: {template_id}")
        return 0

    registry_path = tpl.get('_registry_path')
    if update_registry(registry_path, template_id, {'archived': True}):
        print(f"아카이브 완료: {template_id}")
        print(f"  복원하려면: python template-manager.py restore {template_id}")
        return 0
    else:
        print(f"Error: 업데이트 실패")
        return 1


def cmd_restore(args) -> int:
    """템플릿 복원"""
    template_id = args.id

    # 아카이브된 템플릿 포함하여 검색
    all_templates = scan_all_templates()
    tpl = None
    for t in all_templates:
        if t.get('id') == template_id:
            tpl = t
            break

    if not tpl:
        print(f"Error: 템플릿을 찾을 수 없습니다 - {template_id}")
        return 1

    if not tpl.get('archived'):
        print(f"활성 상태의 템플릿입니다 (아카이브 안됨): {template_id}")
        return 0

    registry_path = tpl.get('_registry_path')
    if update_registry(registry_path, template_id, {'archived': False}):
        print(f"복원 완료: {template_id}")
        return 0
    else:
        print(f"Error: 복원 실패")
        return 1


def cmd_delete(args) -> int:
    """템플릿 삭제"""
    template_id = args.id

    # 모든 템플릿에서 검색 (아카이브 포함)
    all_templates = scan_all_templates()
    tpl = None
    for t in all_templates:
        if t.get('id') == template_id:
            tpl = t
            break

    if not tpl:
        print(f"Error: 템플릿을 찾을 수 없습니다 - {template_id}")
        return 1

    # 확인
    if not args.force:
        print(f"삭제 대상: {template_id}")
        print(f"  Name: {tpl.get('name')}")
        print(f"  Type: {tpl.get('type')}")
        print(f"  File: {tpl.get('file')}")
        confirm = input(f"\n정말 삭제하시겠습니까? (y/N): ")
        if confirm.lower() != 'y':
            print("취소됨")
            return 0

    # 파일 삭제
    file_path = tpl.get('_file_path')
    if file_path and file_path.exists():
        print(f"[1/2] 파일 삭제: {file_path}")
        file_path.unlink()
    else:
        print(f"[1/2] 파일 없음 (skip)")

    # 레지스트리에서 제거
    print(f"[2/2] 레지스트리 업데이트...")
    registry_path = tpl.get('_registry_path')
    if remove_from_registry(registry_path, template_id):
        print(f"삭제 완료: {template_id}")
        return 0
    else:
        print(f"Error: 레지스트리 업데이트 실패")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='PPT 템플릿 관리 CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 목록
  python template-manager.py list
  python template-manager.py list --type documents
  python template-manager.py list --type contents --archived

  # 정보
  python template-manager.py info 제안서1
  python template-manager.py info 제안서1 --preview

  # 아카이브/복원
  python template-manager.py archive 제안서1
  python template-manager.py restore 제안서1

  # 삭제
  python template-manager.py delete 제안서1 -f
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='명령')

    # list 명령
    list_parser = subparsers.add_parser('list', help='템플릿 목록')
    list_parser.add_argument('--type', choices=['documents', 'contents', 'all'],
                             default='all', help='템플릿 타입')
    list_parser.add_argument('--format', choices=['table', 'json', 'yaml'],
                             default='table', help='출력 형식')
    list_parser.add_argument('--archived', action='store_true',
                             help='아카이브된 템플릿 포함')
    list_parser.set_defaults(func=cmd_list)

    # info 명령
    info_parser = subparsers.add_parser('info', help='템플릿 상세 정보')
    info_parser.add_argument('id', help='템플릿 ID')
    info_parser.add_argument('--preview', action='store_true',
                             help='내용 미리보기')
    info_parser.set_defaults(func=cmd_info)

    # archive 명령
    archive_parser = subparsers.add_parser('archive', help='템플릿 아카이브')
    archive_parser.add_argument('id', help='템플릿 ID')
    archive_parser.set_defaults(func=cmd_archive)

    # restore 명령
    restore_parser = subparsers.add_parser('restore', help='템플릿 복원')
    restore_parser.add_argument('id', help='템플릿 ID')
    restore_parser.set_defaults(func=cmd_restore)

    # delete 명령
    delete_parser = subparsers.add_parser('delete', help='템플릿 삭제')
    delete_parser.add_argument('id', help='템플릿 ID')
    delete_parser.add_argument('-f', '--force', action='store_true',
                               help='확인 없이 삭제')
    delete_parser.set_defaults(func=cmd_delete)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
