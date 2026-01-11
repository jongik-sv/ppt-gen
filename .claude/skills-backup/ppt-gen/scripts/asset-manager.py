#!/usr/bin/env python3
"""
Asset Manager - 에셋 저장/검색/삭제/크롤링 CLI

PPT 생성에 사용할 아이콘, 이미지 등의 에셋을 관리합니다.
네이버 블로그 등 보호된 사이트에서도 이미지를 크롤링할 수 있습니다.

Usage:
    python asset-manager.py add <file> --id <id> --tags "tag1,tag2"
    python asset-manager.py add <url> --id <id> --browser  # 보호된 사이트
    python asset-manager.py crawl <url> --prefix <prefix>  # 페이지 내 모든 이미지
    python asset-manager.py search "chart"
    python asset-manager.py list --type icons
    python asset-manager.py delete <id>
    python asset-manager.py info <id>

Examples:
    # 아이콘 추가
    python asset-manager.py add icon.svg --id chart-line --tags "chart,analytics"

    # URL에서 이미지 추가
    python asset-manager.py add "https://example.com/bg.png" --id hero-bg --tags "background,hero"

    # 네이버 블로그 이미지 (브라우저 모드)
    python asset-manager.py add "https://postfiles.pstatic.net/..." --id naver-img --browser

    # 웹페이지 전체 이미지 크롤링
    python asset-manager.py crawl "https://blog.naver.com/..." --prefix design-ref --tags "reference"

    # 크롤링 미리보기
    python asset-manager.py crawl "https://blog.naver.com/..." --prefix test --preview

    # 검색
    python asset-manager.py search chart
    python asset-manager.py search --tags background

    # 목록
    python asset-manager.py list
    python asset-manager.py list --type icons --format table

    # 삭제
    python asset-manager.py delete chart-line

Dependencies:
    pip install requests pyyaml
    pip install playwright && playwright install chromium  # 크롤링용
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import yaml

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# 공유 모듈 import
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent.parent / 'shared'))
from config import TEMPLATES_DIR, ASSETS_DIR, CONTENTS_DIR, THEMES_DIR
from yaml_utils import load_registry as _load_registry, save_registry as _save_registry

# 레지스트리 경로
REGISTRY_PATH = ASSETS_DIR / 'registry.yaml'


def load_registry() -> dict:
    """registry.yaml 로드 (에셋용 래퍼)"""
    return _load_registry(REGISTRY_PATH, ['icons', 'images'])


def save_registry(registry: dict) -> None:
    """registry.yaml 저장 (에셋용 래퍼)"""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    _save_registry(REGISTRY_PATH, registry, '공용 에셋 레지스트리')


def get_all_assets(registry: dict) -> list:
    """모든 에셋 목록 반환 (type 필드 포함)"""
    assets = []
    for item in registry.get('icons', []):
        item_copy = dict(item)
        item_copy['_type'] = 'icon'
        assets.append(item_copy)
    for item in registry.get('images', []):
        item_copy = dict(item)
        item_copy['_type'] = 'image'
        assets.append(item_copy)
    return assets


def find_asset(registry: dict, asset_id: str) -> tuple:
    """ID로 에셋 찾기 → (asset_dict, asset_type, index)"""
    for idx, item in enumerate(registry.get('icons', [])):
        if item.get('id') == asset_id:
            return item, 'icons', idx
    for idx, item in enumerate(registry.get('images', [])):
        if item.get('id') == asset_id:
            return item, 'images', idx
    return None, None, -1


def detect_asset_type(file_path: str) -> str:
    """파일 확장자로 에셋 타입 감지"""
    path = Path(file_path)
    ext = path.suffix.lower()

    icon_exts = {'.svg', '.ico'}
    if ext in icon_exts:
        return 'icons'
    return 'images'


def is_url(path: str) -> bool:
    """URL인지 확인"""
    parsed = urlparse(path)
    return parsed.scheme in ('http', 'https')


# ============================================================
# Site Handlers - 사이트별 크롤링 로직
# ============================================================

class SiteHandler:
    """사이트별 크롤링 로직 베이스 클래스"""

    @staticmethod
    def matches(url: str) -> bool:
        """이 핸들러가 URL을 처리할 수 있는지 확인"""
        raise NotImplementedError

    def get_referer(self) -> str:
        """적절한 Referer 헤더 반환"""
        return ""

    def prepare_page(self, page):
        """사이트별 페이지 준비 (iframe 전환 등)"""
        return page

    def extract_images(self, page) -> list:
        """페이지에서 이미지 URL 추출"""
        raise NotImplementedError


class NaverBlogHandler(SiteHandler):
    """네이버 블로그/카페 핸들러"""

    @staticmethod
    def matches(url: str) -> bool:
        return 'blog.naver.com' in url or 'cafe.naver.com' in url or 'post.naver.com' in url

    def get_referer(self) -> str:
        return 'https://blog.naver.com/'

    def prepare_page(self, page):
        """mainFrame iframe으로 전환"""
        try:
            frame = page.frame('mainFrame')
            if frame:
                return frame
        except Exception:
            pass
        return page

    def extract_images(self, page) -> list:
        """네이버 블로그 이미지 추출 (lazy-load 처리)"""
        return page.evaluate('''() => {
            const images = [];
            document.querySelectorAll('img').forEach(img => {
                const src = img.dataset.lazySrc || img.dataset.src || img.src;
                if (src && !src.startsWith('data:') && !src.includes('static.naver.net')) {
                    images.push({
                        src: src,
                        alt: img.alt || '',
                        width: img.naturalWidth || img.width || 0,
                        height: img.naturalHeight || img.height || 0
                    });
                }
            });
            return images;
        }''')


class GenericHandler(SiteHandler):
    """일반 웹사이트 핸들러"""

    @staticmethod
    def matches(url: str) -> bool:
        return True  # 폴백 핸들러

    def get_referer(self) -> str:
        parsed = urlparse('')
        return ""

    def extract_images(self, page) -> list:
        """일반 이미지 추출"""
        return page.evaluate('''() => {
            return Array.from(document.querySelectorAll('img'))
                .map(img => ({
                    src: img.src,
                    alt: img.alt || '',
                    width: img.naturalWidth || img.width || 0,
                    height: img.naturalHeight || img.height || 0
                }))
                .filter(img => img.src && !img.src.startsWith('data:'));
        }''')


def get_site_handler(url: str) -> SiteHandler:
    """URL에 맞는 사이트 핸들러 반환"""
    handlers = [NaverBlogHandler(), GenericHandler()]
    for handler in handlers:
        if handler.matches(url):
            return handler
    return GenericHandler()


def scroll_page(page_or_frame, scroll_count: int = 5, delay: int = 500):
    """페이지 스크롤하여 lazy loading 트리거"""
    for i in range(scroll_count):
        page_or_frame.evaluate('window.scrollBy(0, window.innerHeight)')
        page_or_frame.wait_for_timeout(delay)
    # 맨 위로 스크롤
    page_or_frame.evaluate('window.scrollTo(0, 0)')


# ============================================================
# Download Functions
# ============================================================

def download_file(url: str, dest_path: Path) -> bool:
    """URL에서 파일 다운로드"""
    if not HAS_REQUESTS:
        print("Error: requests 모듈이 필요합니다. pip install requests")
        return False

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error: 다운로드 실패 - {e}")
        return False


def download_with_browser(url: str, dest_path: Path, referer: str = None) -> bool:
    """Playwright 브라우저로 이미지 다운로드"""
    if not HAS_PLAYWRIGHT:
        print("Error: playwright 모듈이 필요합니다.")
        print("  pip install playwright")
        print("  playwright install chromium")
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                           '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='ko-KR',
                timezone_id='Asia/Seoul',
                extra_http_headers={'Referer': referer} if referer else {}
            )
            page = context.new_page()

            # 이미지 URL로 직접 이동
            response = page.goto(url, wait_until='networkidle', timeout=30000)

            if response and response.ok:
                content = response.body()
                with open(dest_path, 'wb') as f:
                    f.write(content)
                browser.close()
                return True

            browser.close()
            return False
    except Exception as e:
        print(f"Error: 브라우저 다운로드 실패 - {e}")
        return False


def download_file_smart(url: str, dest_path: Path, use_browser: bool = False) -> bool:
    """스마트 다운로드 (requests → browser fallback)"""
    handler = get_site_handler(url)

    if not use_browser:
        # Tier 1: requests + 헤더
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': handler.get_referer() if handler else '',
            }
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                with open(dest_path, 'wb') as f:
                    f.write(response.content)
                return True

            # 차단된 경우 브라우저로 시도
            if response.status_code in (401, 403, 429):
                print("  -> 차단됨, 브라우저로 재시도...")
                use_browser = True
        except Exception as e:
            print(f"  -> requests 실패: {e}, 브라우저로 재시도...")
            use_browser = True

    # Tier 2: 브라우저 다운로드
    if use_browser:
        referer = handler.get_referer() if handler else None
        return download_with_browser(url, dest_path, referer)

    return False


def cmd_add(args) -> int:
    """에셋 추가"""
    source = args.source
    asset_id = args.id
    name = args.name or asset_id
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else []
    use_browser = getattr(args, 'browser', False)

    registry = load_registry()

    # ID 중복 확인
    existing, _, _ = find_asset(registry, asset_id)
    if existing:
        print(f"Error: ID '{asset_id}'가 이미 존재합니다.")
        return 1

    # URL vs 로컬 파일 처리
    if is_url(source):
        # URL에서 파일명 추출
        parsed = urlparse(source)
        filename = Path(parsed.path).name
        if not filename or '.' not in filename:
            filename = f"{asset_id}.png"

        asset_type = args.type or detect_asset_type(filename)
        dest_dir = ASSETS_DIR / asset_type
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename

        print(f"[1/3] 다운로드: {source}")
        if use_browser:
            print("  (브라우저 모드)")
        if not download_file_smart(source, dest_path, use_browser):
            return 1

        source_type = 'downloaded'
        original_url = source
    else:
        # 로컬 파일
        src_path = Path(source)
        if not src_path.exists():
            print(f"Error: 파일을 찾을 수 없습니다 - {source}")
            return 1

        asset_type = args.type or detect_asset_type(source)
        dest_dir = ASSETS_DIR / asset_type
        dest_dir.mkdir(parents=True, exist_ok=True)

        filename = src_path.name
        dest_path = dest_dir / filename

        print(f"[1/3] 복사: {src_path} → {dest_path}")
        shutil.copy2(src_path, dest_path)

        source_type = 'local'
        original_url = None

    # 레지스트리에 추가
    asset_entry = {
        'id': asset_id,
        'name': name,
        'file': f"{asset_type}/{filename}",
        'source': source_type,
        'tags': tags,
        'created': datetime.now().strftime('%Y-%m-%d'),
    }
    if original_url:
        asset_entry['original_url'] = original_url

    print(f"[2/3] 레지스트리 업데이트...")
    registry[asset_type].append(asset_entry)
    save_registry(registry)

    print(f"[3/3] 완료!")
    print(f"  ID: {asset_id}")
    print(f"  Type: {asset_type}")
    print(f"  File: {dest_path}")
    print(f"  Tags: {', '.join(tags) if tags else '(없음)'}")

    return 0


def cmd_search(args) -> int:
    """에셋 검색"""
    query = args.query.lower() if args.query else ''
    tag_filter = args.tags.lower() if args.tags else ''

    registry = load_registry()
    assets = get_all_assets(registry)

    results = []
    for asset in assets:
        # 이름, ID에서 검색
        name_match = query in asset.get('name', '').lower() or query in asset.get('id', '').lower()

        # 태그에서 검색
        asset_tags = [t.lower() for t in asset.get('tags', [])]
        tag_match = any(query in t for t in asset_tags) if query else True

        # 태그 필터
        if tag_filter:
            tag_match = tag_match and any(tag_filter in t for t in asset_tags)

        if name_match or (query and tag_match) or (not query and tag_filter and tag_match):
            results.append(asset)

    if not results:
        print(f"검색 결과 없음: '{query or tag_filter}'")
        return 0

    print(f"검색 결과: {len(results)}개")
    print("-" * 60)
    for asset in results:
        tags_str = ', '.join(asset.get('tags', []))
        print(f"  [{asset['_type']}] {asset['id']}: {asset['name']}")
        print(f"         File: {asset.get('file', '')}")
        if tags_str:
            print(f"         Tags: {tags_str}")

    return 0


def cmd_list(args) -> int:
    """에셋 목록"""
    registry = load_registry()

    # 타입 필터
    if args.type == 'icons':
        assets = [dict(a, _type='icon') for a in registry.get('icons', [])]
    elif args.type == 'images':
        assets = [dict(a, _type='image') for a in registry.get('images', [])]
    else:
        assets = get_all_assets(registry)

    if not assets:
        print("등록된 에셋이 없습니다.")
        return 0

    # 출력 형식
    if args.format == 'json':
        import json
        output = [dict((k, v) for k, v in a.items() if not k.startswith('_')) for a in assets]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif args.format == 'yaml':
        output = [dict((k, v) for k, v in a.items() if not k.startswith('_')) for a in assets]
        print(yaml.dump(output, allow_unicode=True, default_flow_style=False))
    else:
        # table 형식
        print(f"에셋 목록: {len(assets)}개")
        print("-" * 70)
        print(f"{'Type':<8} {'ID':<20} {'Name':<25} {'Tags'}")
        print("-" * 70)
        for asset in assets:
            tags_str = ', '.join(asset.get('tags', [])[:3])
            if len(asset.get('tags', [])) > 3:
                tags_str += '...'
            print(f"{asset['_type']:<8} {asset['id']:<20} {asset['name'][:25]:<25} {tags_str}")

    return 0


def cmd_info(args) -> int:
    """에셋 상세 정보"""
    asset_id = args.id
    registry = load_registry()

    asset, asset_type, _ = find_asset(registry, asset_id)
    if not asset:
        print(f"Error: 에셋을 찾을 수 없습니다 - {asset_id}")
        return 1

    print(f"에셋 정보: {asset_id}")
    print("-" * 40)
    print(f"  ID: {asset.get('id')}")
    print(f"  Name: {asset.get('name')}")
    print(f"  Type: {asset_type}")
    print(f"  File: {asset.get('file')}")
    print(f"  Source: {asset.get('source')}")
    print(f"  Tags: {', '.join(asset.get('tags', [])) or '(없음)'}")
    print(f"  Created: {asset.get('created', '?')}")
    if asset.get('original_url'):
        print(f"  URL: {asset.get('original_url')}")

    # 파일 존재 확인
    file_path = ASSETS_DIR / asset.get('file', '')
    if file_path.exists():
        size_kb = file_path.stat().st_size / 1024
        print(f"  Size: {size_kb:.1f} KB")
    else:
        print(f"  Warning: 파일이 존재하지 않습니다!")

    return 0


def cmd_delete(args) -> int:
    """에셋 삭제"""
    asset_id = args.id
    registry = load_registry()

    asset, asset_type, idx = find_asset(registry, asset_id)
    if not asset:
        print(f"Error: 에셋을 찾을 수 없습니다 - {asset_id}")
        return 1

    # 확인
    if not args.force:
        confirm = input(f"정말 삭제하시겠습니까? [{asset_id}] (y/N): ")
        if confirm.lower() != 'y':
            print("취소됨")
            return 0

    # 파일 삭제
    file_path = ASSETS_DIR / asset.get('file', '')
    if file_path.exists():
        print(f"[1/2] 파일 삭제: {file_path}")
        file_path.unlink()
    else:
        print(f"[1/2] 파일 없음 (skip)")

    # 레지스트리에서 제거
    print(f"[2/2] 레지스트리 업데이트...")
    del registry[asset_type][idx]
    save_registry(registry)

    print(f"삭제 완료: {asset_id}")
    return 0


def cmd_crawl(args) -> int:
    """웹페이지에서 이미지 크롤링"""
    url = args.url
    prefix = args.prefix
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else []
    min_size = args.min_size
    max_images = args.max_images
    preview_only = args.preview

    if not HAS_PLAYWRIGHT:
        print("Error: playwright 모듈이 필요합니다.")
        print("  pip install playwright")
        print("  playwright install chromium")
        return 1

    print(f"[1/4] 페이지 로드: {url}")

    # 사이트 핸들러 선택
    handler = get_site_handler(url)
    print(f"  핸들러: {type(handler).__name__}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                           '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='ko-KR',
                timezone_id='Asia/Seoul',
            )
            page = context.new_page()

            # Referer 설정
            if handler.get_referer():
                page.set_extra_http_headers({'Referer': handler.get_referer()})

            page.goto(url, wait_until='networkidle', timeout=60000)

            # 사이트별 페이지 준비
            target = handler.prepare_page(page)

            # 스크롤하여 lazy 이미지 로드
            print("[2/4] 스크롤하여 이미지 로드...")
            scroll_page(target)

            # 이미지 추출
            print("[3/4] 이미지 추출...")
            images = handler.extract_images(target)

            browser.close()
    except Exception as e:
        print(f"Error: 페이지 로드 실패 - {e}")
        return 1

    # 이미지 필터링
    filtered = []
    seen_urls = set()
    for img in images:
        src = img.get('src', '')

        # 중복 제거
        if src in seen_urls:
            continue
        seen_urls.add(src)

        # 크기 필터
        if min_size:
            width = img.get('width', 0)
            height = img.get('height', 0)
            if width < min_size and height < min_size:
                continue

        # 일반적인 비콘텐츠 이미지 제외
        skip_patterns = ['logo', 'icon', 'avatar', 'profile', 'button', 'banner', 'ad', 'pixel']
        if any(pattern in src.lower() for pattern in skip_patterns):
            continue

        filtered.append(img)

    # 최대 개수 제한
    if max_images and len(filtered) > max_images:
        filtered = filtered[:max_images]

    print(f"  발견: {len(images)}개, 필터링: {len(filtered)}개")

    # 미리보기 모드
    if preview_only:
        print("\n--- 미리보기 ---")
        for i, img in enumerate(filtered):
            src = img['src']
            display_src = src[:80] + '...' if len(src) > 80 else src
            print(f"  [{i+1}] {display_src}")
            print(f"       크기: {img.get('width', '?')}x{img.get('height', '?')}")
        return 0

    # 다운로드
    print(f"\n[4/4] {len(filtered)}개 이미지 다운로드...")
    registry = load_registry()
    success_count = 0

    for i, img in enumerate(filtered):
        src = img['src']
        asset_id = f"{prefix}-{i+1:03d}"

        # 기존 ID 확인
        existing, _, _ = find_asset(registry, asset_id)
        if existing:
            print(f"  Skip: {asset_id} (이미 존재)")
            continue

        # 파일명 결정
        parsed = urlparse(src)
        ext = Path(parsed.path).suffix or '.png'
        if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']:
            ext = '.png'
        filename = f"{asset_id}{ext}"

        dest_dir = ASSETS_DIR / 'images'
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename

        # 다운로드
        print(f"  [{i+1}/{len(filtered)}] {asset_id}...", end=' ', flush=True)
        if download_file_smart(src, dest_path, use_browser=True):
            # 레지스트리에 추가
            asset_entry = {
                'id': asset_id,
                'name': img.get('alt') or asset_id,
                'file': f"images/{filename}",
                'source': 'crawled',
                'tags': tags,
                'created': datetime.now().strftime('%Y-%m-%d'),
                'original_url': src,
            }
            registry['images'].append(asset_entry)
            success_count += 1
            print("OK")
        else:
            print("FAILED")

    save_registry(registry)
    print(f"\n완료: {success_count}/{len(filtered)}개 이미지 저장됨")
    print(f"  위치: {ASSETS_DIR / 'images'}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='PPT 에셋 관리 CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 추가
  python asset-manager.py add icon.svg --id chart-line --tags "chart,data"
  python asset-manager.py add "https://example.com/bg.png" --id hero-bg

  # 검색
  python asset-manager.py search chart
  python asset-manager.py search --tags background

  # 목록
  python asset-manager.py list
  python asset-manager.py list --type icons --format table

  # 정보
  python asset-manager.py info chart-line

  # 삭제
  python asset-manager.py delete chart-line
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='명령')

    # add 명령
    add_parser = subparsers.add_parser('add', help='에셋 추가')
    add_parser.add_argument('source', help='파일 경로 또는 URL')
    add_parser.add_argument('--id', required=True, help='에셋 ID')
    add_parser.add_argument('--name', help='표시 이름 (기본: ID)')
    add_parser.add_argument('--tags', help='태그 (쉼표 구분)')
    add_parser.add_argument('--type', choices=['icons', 'images'],
                            help='에셋 타입 (자동 감지)')
    add_parser.add_argument('--browser', '-b', action='store_true',
                            help='브라우저 다운로드 강제 (보호된 사이트용)')
    add_parser.set_defaults(func=cmd_add)

    # search 명령
    search_parser = subparsers.add_parser('search', help='에셋 검색')
    search_parser.add_argument('query', nargs='?', default='', help='검색어')
    search_parser.add_argument('--tags', help='태그 필터')
    search_parser.set_defaults(func=cmd_search)

    # list 명령
    list_parser = subparsers.add_parser('list', help='에셋 목록')
    list_parser.add_argument('--type', choices=['icons', 'images', 'all'],
                             default='all', help='타입 필터')
    list_parser.add_argument('--format', choices=['table', 'json', 'yaml'],
                             default='table', help='출력 형식')
    list_parser.set_defaults(func=cmd_list)

    # info 명령
    info_parser = subparsers.add_parser('info', help='에셋 상세 정보')
    info_parser.add_argument('id', help='에셋 ID')
    info_parser.set_defaults(func=cmd_info)

    # delete 명령
    delete_parser = subparsers.add_parser('delete', help='에셋 삭제')
    delete_parser.add_argument('id', help='에셋 ID')
    delete_parser.add_argument('-f', '--force', action='store_true',
                               help='확인 없이 삭제')
    delete_parser.set_defaults(func=cmd_delete)

    # crawl 명령
    crawl_parser = subparsers.add_parser('crawl', help='웹페이지 이미지 크롤링')
    crawl_parser.add_argument('url', help='웹페이지 URL')
    crawl_parser.add_argument('--prefix', '-p', required=True,
                              help='에셋 ID 접두사 (예: naver-ref)')
    crawl_parser.add_argument('--tags', '-t', help='태그 (쉼표 구분)')
    crawl_parser.add_argument('--min-size', type=int, default=100,
                              help='최소 이미지 크기 픽셀 (기본: 100)')
    crawl_parser.add_argument('--max-images', '-m', type=int, default=20,
                              help='최대 이미지 개수 (기본: 20)')
    crawl_parser.add_argument('--preview', action='store_true',
                              help='미리보기만 (다운로드 안 함)')
    crawl_parser.set_defaults(func=cmd_crawl)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
