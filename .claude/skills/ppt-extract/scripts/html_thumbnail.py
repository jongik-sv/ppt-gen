#!/usr/bin/env python3
"""
HTML 슬라이드 썸네일 생성.

example.html 파일을 브라우저로 렌더링하여 320x180 썸네일 생성.

Usage:
    # 단일 템플릿
    python html_thumbnail.py templates/contents/cover/cover-centered-01/example.html

    # 모든 템플릿
    python html_thumbnail.py --all templates/contents
"""

import argparse
import asyncio
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# 썸네일 설정
VIEWPORT_WIDTH = 960
VIEWPORT_HEIGHT = 540
THUMBNAIL_WIDTH = 320
THUMBNAIL_HEIGHT = 180


async def capture_html_screenshot(html_path: Path, output_path: Path):
    """HTML 파일을 스크린샷으로 캡처"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={'width': VIEWPORT_WIDTH, 'height': VIEWPORT_HEIGHT}
        )

        # HTML 파일 로드
        file_url = f"file:///{html_path.resolve().as_posix()}"
        await page.goto(file_url, wait_until='networkidle')

        # .slide 요소가 있으면 해당 요소만 캡처
        slide_element = page.locator('.slide')
        if await slide_element.count() > 0:
            # 슬라이드 요소만 캡처
            await slide_element.screenshot(path=str(output_path), scale='css')
        else:
            # 전체 페이지 캡처
            await page.screenshot(path=str(output_path))

        await browser.close()

    # 리사이즈
    try:
        from PIL import Image
        with Image.open(output_path) as img:
            img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
            img.save(output_path, 'PNG')
    except ImportError:
        print("  Warning: Pillow 없음, 원본 크기로 저장됨")


def get_thumbnail_mirror_path(html_path: Path) -> Path:
    """example.html 경로에서 미러 썸네일 경로 계산"""
    # templates/contents/{category}/{id}/example.html
    # → templates/thumbnails/contents/{category}/{id}.png
    parts = html_path.parts
    try:
        contents_idx = parts.index('contents')
        category = parts[contents_idx + 1]
        template_id = parts[contents_idx + 2]

        # templates 폴더 찾기
        templates_idx = parts.index('templates')
        templates_base = Path(*parts[:templates_idx + 1])

        return templates_base / 'thumbnails' / 'contents' / category / f'{template_id}.png'
    except (ValueError, IndexError):
        # 미러 경로 계산 실패 시 원본 폴더에 저장
        return html_path.parent / 'thumbnail.png'


async def process_single(html_path: Path):
    """단일 HTML 파일 처리"""
    output_path = get_thumbnail_mirror_path(html_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"캡처 중: {html_path}")
    await capture_html_screenshot(html_path, output_path)
    print(f"저장됨: {output_path}")


async def process_all(base_dir: Path):
    """모든 example.html 파일 처리"""
    example_files = list(base_dir.rglob('example.html'))
    print(f"발견된 템플릿: {len(example_files)}개")

    for html_path in example_files:
        output_path = get_thumbnail_mirror_path(html_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"캡처 중: {html_path.parent.name}")
        try:
            await capture_html_screenshot(html_path, output_path)
            print(f"  → 저장됨: {output_path.name}")
        except Exception as e:
            print(f"  → 실패: {e}")


def main():
    parser = argparse.ArgumentParser(description="HTML 슬라이드 썸네일 생성")
    parser.add_argument("path", help="HTML 파일 또는 디렉토리")
    parser.add_argument("--all", action="store_true", help="모든 example.html 처리")

    args = parser.parse_args()

    if not HAS_PLAYWRIGHT:
        print("Error: Playwright가 필요합니다")
        print("설치: pip install playwright && playwright install chromium")
        sys.exit(1)

    path = Path(args.path)

    if args.all:
        if not path.is_dir():
            print(f"Error: 디렉토리가 아닙니다: {path}")
            sys.exit(1)
        asyncio.run(process_all(path))
    else:
        if not path.exists():
            print(f"Error: 파일을 찾을 수 없습니다: {path}")
            sys.exit(1)
        asyncio.run(process_single(path))


if __name__ == "__main__":
    main()
