#!/usr/bin/env python3
"""
PPT Extract 통합 CLI.

PPTX에서 문서 양식, 테마, 콘텐츠를 추출하는 통합 CLI.

Usage:
    python ppt_extract.py document-extract input.pptx --group dongkuk
    python ppt_extract.py document-update input.pptx --id dongkuk-standard
    python ppt_extract.py document-delete dongkuk-standard
    python ppt_extract.py style-extract input.png --output themes/new/
    python ppt_extract.py content-extract input.pptx --slides 3,5,7
    python ppt_extract.py registry-rebuild

Examples:
    # 문서 양식 추출
    python ppt_extract.py document-extract ppt-sample/동국시스템즈-문서양식.pptx --group dongkuk

    # 기존 템플릿 덮어쓰기
    python ppt_extract.py document-extract input.pptx --group dongkuk --force

    # 문서 업데이트
    python ppt_extract.py document-update new-version.pptx --id dongkuk-standard

    # 문서 삭제
    python ppt_extract.py document-delete dongkuk-standard --cascade
"""

import argparse
import sys
from pathlib import Path

# 스크립트 디렉토리를 경로에 추가
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))


def cmd_document_extract(args):
    """document-extract 명령 처리."""
    from scripts.document_extractor import DocumentExtractor

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: 파일을 찾을 수 없습니다: {args.input}")
        return 1

    # 템플릿 이름 결정
    name = args.name or input_path.stem

    # 출력 경로 결정
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = SCRIPT_DIR.parent.parent.parent / 'templates' / 'documents' / args.group / name

    # 기존 템플릿 확인
    if output_path.exists() and not args.force:
        print(f"Warning: 이미 존재하는 템플릿입니다: {output_path}")
        response = input("덮어쓰시겠습니까? [y/N]: ").strip().lower()
        if response != 'y':
            print("취소되었습니다.")
            return 0

    try:
        extractor = DocumentExtractor(
            input_path=input_path,
            group=args.group,
            name=name,
            output_path=output_path,
            auto_classify=args.auto
        )
        extractor.run()
        print(f"\n완료: {output_path}")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_style_extract(args):
    """style-extract 명령 처리."""
    from scripts.style_extractor import StyleExtractor

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: 파일을 찾을 수 없습니다: {args.input}")
        return 1

    # 지원 형식 확인
    valid_extensions = {'.pptx', '.png', '.jpg', '.jpeg', '.webp', '.bmp'}
    if input_path.suffix.lower() not in valid_extensions:
        print(f"Error: 지원하지 않는 형식입니다: {input_path.suffix}")
        print(f"지원 형식: {', '.join(valid_extensions)}")
        return 1

    # 테마 이름 (필수)
    if not args.name:
        print("Error: --name 옵션이 필수입니다.")
        return 1

    # 출력 경로 결정
    output_path = Path(args.output) if args.output else None

    # 기존 테마 확인
    if output_path is None:
        from scripts.style_extractor import normalize_theme_name
        theme_name = normalize_theme_name(args.name)
        default_path = SCRIPT_DIR.parent.parent.parent / 'templates' / 'themes' / theme_name
        if default_path.exists() and not args.force:
            print(f"Warning: 이미 존재하는 테마입니다: {default_path}")
            try:
                response = input("덮어쓰시겠습니까? [y/N]: ").strip().lower()
                if response != 'y':
                    print("취소되었습니다.")
                    return 0
            except EOFError:
                print("비대화형 모드에서는 --force 옵션을 사용하세요.")
                return 1

    try:
        extractor = StyleExtractor(
            input_path=input_path,
            name=args.name,
            output_path=output_path
        )
        extractor.run()
        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_content_extract(args):
    """content-extract 명령 처리."""
    import json

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: 파일을 찾을 수 없습니다: {args.input}")
        return 1

    # 지원 형식 확인
    valid_extensions = {'.pptx', '.png', '.jpg', '.jpeg', '.webp', '.bmp'}
    if input_path.suffix.lower() not in valid_extensions:
        print(f"Error: 지원하지 않는 형식입니다: {input_path.suffix}")
        print(f"지원 형식: {', '.join(valid_extensions)}")
        return 1

    # 이미지 vs PPTX 분기
    if input_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}:
        # === 이미지 콘텐츠 추출 ===
        from scripts.image_content_extractor import ImageContentExtractor

        # --slots-json 필수 체크
        if not args.slots_json:
            print("Error: 이미지 입력 시 --slots-json 옵션이 필수입니다.")
            print("\nClaude Code 대화에서 슬롯을 먼저 분류하세요.")
            print("예시: --slots-json '{\"category\": \"grid\", \"slots\": [...]}'")
            return 1

        try:
            slots_data = json.loads(args.slots_json)
        except json.JSONDecodeError as e:
            print(f"Error: JSON 파싱 실패: {e}")
            return 1

        # 출력 경로
        output_path = Path(args.output) if args.output else None

        try:
            extractor = ImageContentExtractor(
                input_path=input_path,
                slots_data=slots_data,
                category=args.category,
                output_path=output_path,
                template_name=args.name
            )
            templates = extractor.run()
            print(f"\n추출 완료: {len(templates)}개 템플릿")
            return 0

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return 1

    else:
        # === PPTX 콘텐츠 추출 (기존 로직) ===
        from scripts.content_extractor import ContentExtractor

        # 슬라이드 번호 파싱
        slides = None
        if args.slides:
            try:
                slides = [int(s.strip()) for s in args.slides.split(',')]
            except ValueError:
                print(f"Error: 슬라이드 번호 형식이 잘못되었습니다: {args.slides}")
                return 1

        # 출력 경로
        output_path = Path(args.output) if args.output else None

        try:
            extractor = ContentExtractor(
                input_path=input_path,
                slides=slides,
                category=args.category,
                output_path=output_path,
                auto_classify=args.auto,
                source_document=args.source,
                use_llm=getattr(args, 'llm', False)
            )
            templates = extractor.run()
            print(f"\n추출 완료: {len(templates)}개 템플릿")
            return 0

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return 1


def cmd_document_update(args):
    """document-update 명령 처리."""
    from scripts.registry_manager import RegistryManager
    from scripts.document_extractor import DocumentExtractor

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: 파일을 찾을 수 없습니다: {args.input}")
        return 1

    manager = RegistryManager()

    # 기존 문서 찾기
    doc = None
    if args.id:
        doc = manager.find_document_by_id(args.id)
    else:
        # 파일명으로 자동 매칭
        doc = manager.find_document_by_source(input_path.name)

    if not doc:
        print(f"Error: 업데이트할 문서를 찾을 수 없습니다.")
        if args.id:
            print(f"  지정한 ID: {args.id}")
        else:
            print(f"  파일명으로 검색: {input_path.name}")
        print("\n새 문서로 등록하려면 document-extract를 사용하세요.")
        return 1

    print(f"\n=== 문서 업데이트 ===")
    print(f"대상 문서: {doc['id']}")
    print(f"원본 파일: {doc.get('source_file', 'N/A')}")
    print(f"경로: {doc['path']}")

    # 연관 콘텐츠 검색
    related = manager.find_contents_by_document(doc['id'])
    if related:
        print(f"\n연관 콘텐츠: {len(related)}개")
        for content in related[:5]:
            print(f"  - {content['id']}")
        if len(related) > 5:
            print(f"  ... 외 {len(related) - 5}개")

    # 확인 프롬프트
    if not args.force:
        print("\n⚠️ 업데이트 시 기존 문서가 덮어씌워집니다.")
        if args.cascade and related:
            print(f"   --cascade 옵션: 연관 콘텐츠 {len(related)}개도 삭제됩니다.")

        try:
            if related and not args.cascade:
                print("\n1. 문서만 업데이트 (콘텐츠 유지)")
                print("2. 문서 + 연관 콘텐츠 모두 삭제 후 재추출")
                print("3. 취소")
                response = input("\n선택 [1/2/3]: ").strip()
                if response == '3':
                    print("취소되었습니다.")
                    return 0
                elif response == '2':
                    args.cascade = True
            else:
                response = input("\n계속하시겠습니까? [y/N]: ").strip().lower()
                if response != 'y':
                    print("취소되었습니다.")
                    return 0
        except EOFError:
            print("비대화형 모드에서는 --force 옵션을 사용하세요.")
            return 1

    # 기존 문서 삭제
    templates_root = SCRIPT_DIR.parent.parent.parent / 'templates'
    doc_path = templates_root / doc['path']

    if args.cascade and related:
        print(f"\n연관 콘텐츠 삭제 중...")
        manager.delete_document(doc['id'], cascade=True, dry_run=False)
    else:
        # 문서만 삭제
        import shutil
        if doc_path.exists():
            shutil.rmtree(doc_path)

    # 새 문서 추출
    print(f"\n새 문서 추출 중...")
    try:
        output_path = doc_path
        extractor = DocumentExtractor(
            input_path=input_path,
            group=doc['group'],
            name=doc['name'],
            output_path=output_path,
            auto_classify=True
        )
        extractor.run()

        # 레지스트리 업데이트
        manager.rebuild_all()

        print(f"\n완료: {output_path}")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_document_delete(args):
    """document-delete 명령 처리."""
    from scripts.registry_manager import RegistryManager

    manager = RegistryManager()

    # 문서 찾기
    doc = None
    if args.target:
        doc = manager.find_document_by_id(args.target)
    elif args.group and args.name:
        # group + name 조합으로 검색
        doc_id = f"{args.group}-{args.name}"
        doc = manager.find_document_by_id(doc_id)

    if not doc:
        print(f"Error: 삭제할 문서를 찾을 수 없습니다.")
        if args.target:
            print(f"  지정한 ID: {args.target}")
        elif args.group and args.name:
            print(f"  그룹: {args.group}, 이름: {args.name}")
        return 1

    # 연관 콘텐츠 검색
    related = manager.find_contents_by_document(doc['id'])

    print(f"\n=== 삭제 대상 ===")
    print(f"📁 문서 양식: {doc['id']}")
    print(f"   경로: {doc['path']}")

    if related:
        print(f"\n📄 연관 콘텐츠: {len(related)}개")
        for content in related:
            print(f"   - {content['id']}")

    # dry-run 모드
    if args.dry_run:
        print("\n[dry-run] 실제 삭제는 수행되지 않았습니다.")
        return 0

    # 확인 프롬프트
    if not args.force:
        print("\n⚠️ 이 작업은 되돌릴 수 없습니다.")

        try:
            if related:
                print("\n1. 전체 삭제 (문서 + 콘텐츠)")
                print("2. 문서 양식만 삭제 (콘텐츠 유지)")
                print("3. 취소")
                response = input("\n선택 [1/2/3]: ").strip()
                if response == '3':
                    print("취소되었습니다.")
                    return 0
                elif response == '1':
                    args.cascade = True
                elif response == '2':
                    args.keep_contents = True
            else:
                response = input("\n삭제하시겠습니까? [y/N]: ").strip().lower()
                if response != 'y':
                    print("취소되었습니다.")
                    return 0
        except EOFError:
            print("비대화형 모드에서는 --force 옵션을 사용하세요.")
            return 1

    # 삭제 실행
    cascade = args.cascade and not args.keep_contents
    targets = manager.delete_document(doc['id'], cascade=cascade, dry_run=False)

    print(f"\n=== 삭제 완료 ===")
    print(f"📁 문서: {len(targets['documents'])}개")
    if cascade:
        print(f"📄 콘텐츠: {len(targets['contents'])}개")
        print(f"🖼️ 썸네일: {len(targets['thumbnails'])}개")

    return 0


def cmd_registry_rebuild(args):
    """registry-rebuild 명령 처리."""
    from scripts.registry_manager import RegistryManager

    manager = RegistryManager()
    results = manager.rebuild_all()

    print("\n=== 레지스트리 재빌드 완료 ===")
    for category, count in results.items():
        print(f"  {category}: {count}개")

    return 0


def cmd_content_create(args):
    """content-create 명령 처리."""
    from scripts.content_creator import ContentCreator, TemplateConfig, LIBRARY_INFO

    creator = ContentCreator()

    # 목록 출력 모드
    if args.list:
        creator.list_libraries()
        return 0

    # 필수 옵션 확인
    if not args.library or not args.type or not args.name:
        print("Error: --library, --type, --name 옵션이 필수입니다.")
        print("\n사용 가능한 라이브러리 목록:")
        creator.list_libraries()
        return 1

    config = TemplateConfig(
        library=args.library,
        template_type=args.type,
        name=args.name,
        category=args.category,
        theme_mode=args.theme
    )

    result = creator.create(config)
    return 0 if result else 1


def main():
    parser = argparse.ArgumentParser(
        description="PPT Extract CLI - PPTX에서 템플릿 추출",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python ppt_extract.py document-extract input.pptx --group dongkuk
    python ppt_extract.py document-extract input.pptx --group dongkuk --name "제안서양식"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령')

    # document-extract 서브커맨드
    doc_parser = subparsers.add_parser(
        'document-extract',
        help='문서 양식 추출 (슬라이드 마스터, 레이아웃, 테마)',
        description='PPTX에서 문서 양식을 추출하여 templates/documents/에 저장합니다.'
    )
    doc_parser.add_argument('input', help='입력 PPTX 파일')
    doc_parser.add_argument(
        '--group', '-g',
        required=True,
        help='문서 그룹명 (예: dongkuk, samsung)'
    )
    doc_parser.add_argument(
        '--name', '-n',
        help='템플릿 이름 (기본: 파일명)'
    )
    doc_parser.add_argument(
        '--output', '-o',
        help='출력 경로 (기본: templates/documents/{group}/{name}/)'
    )
    doc_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='기존 템플릿 덮어쓰기'
    )
    doc_parser.add_argument(
        '--auto', '-a',
        action='store_true',
        help='자동 모드 (LLM 입력 없이 규칙 기반 분류 사용)'
    )

    # style-extract 서브커맨드
    style_parser = subparsers.add_parser(
        'style-extract',
        help='테마 스타일 추출 (색상, 폰트)',
        description='PPTX 또는 이미지에서 테마를 추출하여 templates/themes/에 저장합니다.'
    )
    style_parser.add_argument('input', help='입력 이미지 또는 PPTX')
    style_parser.add_argument(
        '--name', '-n',
        required=True,
        help='테마 이름 (케밥케이스로 정규화됨)'
    )
    style_parser.add_argument('--output', '-o', help='출력 경로 (기본: templates/themes/{name}/)')
    style_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='기존 테마 덮어쓰기'
    )

    # content-extract 서브커맨드
    content_parser = subparsers.add_parser(
        'content-extract',
        help='콘텐츠 템플릿 추출 (슬라이드 디자인)',
        description='PPTX 슬라이드 또는 이미지에서 콘텐츠 템플릿을 추출합니다.\n'
                    'PPTX: YAML, HTML, OOXML 3가지 포맷 생성.\n'
                    '이미지: YAML, HTML 2가지 포맷 생성 (--slots-json 필수).'
    )
    content_parser.add_argument('input', help='입력 파일 (PPTX 또는 이미지)')
    content_parser.add_argument(
        '--slides', '-s',
        help='추출할 슬라이드 번호 (예: 3,5,7). PPTX 전용, 미지정 시 전체 추출'
    )
    content_parser.add_argument(
        '--category', '-c',
        help='카테고리 (예: grid, list, timeline). 미지정 시 자동 분류'
    )
    content_parser.add_argument(
        '--output', '-o',
        help='출력 경로 (기본: templates/contents/{category}/{id}/)'
    )
    content_parser.add_argument(
        '--source',
        help='원본 문서 양식 이름 (예: dongkuk). PPTX 전용'
    )
    content_parser.add_argument(
        '--auto', '-a',
        action='store_true',
        help='자동 모드 (LLM 입력 없이 규칙 기반 분류). PPTX 전용'
    )
    content_parser.add_argument(
        '--llm',
        action='store_true',
        help='LLM 기반 분류 (Claude API 호출). PPTX 전용'
    )
    # 이미지 입력용 옵션
    content_parser.add_argument(
        '--slots-json',
        dest='slots_json',
        help='슬롯 정의 JSON (이미지 입력 시 필수). Claude Code가 분석한 결과 전달.\n'
             '예: \'{"category": "grid", "slots": [{"name": "title", "type": "text"}]}\''
    )
    content_parser.add_argument(
        '--name', '-n',
        help='템플릿 이름 (기본: 파일명 + 타임스탬프)'
    )

    # document-update 서브커맨드
    update_parser = subparsers.add_parser(
        'document-update',
        help='기존 문서 양식 업데이트',
        description='기존 문서 양식을 새 PPTX 파일로 업데이트합니다.'
    )
    update_parser.add_argument('input', help='새 버전 PPTX 파일')
    update_parser.add_argument(
        '--id',
        help='업데이트할 문서 ID (미지정 시 파일명으로 자동 매칭)'
    )
    update_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='확인 없이 덮어쓰기'
    )
    update_parser.add_argument(
        '--cascade',
        action='store_true',
        help='연관 콘텐츠도 함께 삭제'
    )
    update_parser.add_argument(
        '--new',
        action='store_true',
        help='기존 유지, 새 ID로 등록'
    )

    # document-delete 서브커맨드
    delete_parser = subparsers.add_parser(
        'document-delete',
        help='문서 양식 삭제',
        description='문서 양식 및 연관 콘텐츠를 삭제합니다.'
    )
    delete_parser.add_argument(
        'target',
        nargs='?',
        help='삭제할 문서 ID'
    )
    delete_parser.add_argument(
        '--group', '-g',
        help='문서 그룹명'
    )
    delete_parser.add_argument(
        '--name', '-n',
        help='문서 이름'
    )
    delete_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='확인 없이 삭제'
    )
    delete_parser.add_argument(
        '--cascade',
        action='store_true',
        help='연관 콘텐츠 모두 삭제'
    )
    delete_parser.add_argument(
        '--keep-contents',
        action='store_true',
        dest='keep_contents',
        help='문서 양식만 삭제 (콘텐츠 유지)'
    )
    delete_parser.add_argument(
        '--dry-run',
        action='store_true',
        dest='dry_run',
        help='삭제하지 않고 대상만 표시'
    )

    # registry-rebuild 서브커맨드
    registry_parser = subparsers.add_parser(
        'registry-rebuild',
        help='레지스트리 재빌드',
        description='모든 템플릿을 스캔하여 registry.yaml을 재빌드합니다.'
    )

    # content-create 서브커맨드
    create_parser = subparsers.add_parser(
        'content-create',
        help='라이브러리 기반 콘텐츠 템플릿 생성',
        description='Chart.js, Mermaid 등 라이브러리를 사용하여 콘텐츠 템플릿을 생성합니다.'
    )
    create_parser.add_argument(
        '--library', '-l',
        choices=['chartjs', 'mermaid', 'apexcharts', 'lucide'],
        help='라이브러리 선택'
    )
    create_parser.add_argument(
        '--type', '-t',
        help='템플릿 타입 (예: bar, pie, line, flowchart, sequence)'
    )
    create_parser.add_argument(
        '--name', '-n',
        help='템플릿 이름 (케밥케이스)'
    )
    create_parser.add_argument(
        '--category', '-c',
        help='카테고리 (기본: 라이브러리 기본값)'
    )
    create_parser.add_argument(
        '--theme',
        choices=['light', 'dark'],
        default='light',
        help='테마 모드'
    )
    create_parser.add_argument(
        '--list',
        action='store_true',
        help='지원 라이브러리 목록 출력'
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    # 명령별 처리
    if args.command == 'document-extract':
        return cmd_document_extract(args)
    elif args.command == 'style-extract':
        return cmd_style_extract(args)
    elif args.command == 'content-extract':
        return cmd_content_extract(args)
    elif args.command == 'document-update':
        return cmd_document_update(args)
    elif args.command == 'document-delete':
        return cmd_document_delete(args)
    elif args.command == 'registry-rebuild':
        return cmd_registry_rebuild(args)
    elif args.command == 'content-create':
        return cmd_content_create(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
