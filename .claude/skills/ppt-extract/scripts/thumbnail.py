#!/usr/bin/env python3
"""
PPTX 슬라이드 썸네일 생성.

슬라이드를 이미지로 변환하여 썸네일 생성.
- 단일 슬라이드: 960x540 (콘텐츠 템플릿용)
- 그리드 보기: 여러 슬라이드를 하나의 이미지로

Usage:
    # 단일 슬라이드 썸네일
    python thumbnail.py input.pptx --slide 3 --output thumbnails/slide-03.png

    # 모든 슬라이드 개별 썸네일
    python thumbnail.py input.pptx --all --output-dir thumbnails/

    # 그리드 뷰
    python thumbnail.py input.pptx --grid --output grid.jpg --cols 4
"""

import argparse
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from pptx import Presentation
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

# Windows PowerPoint COM 자동화
HAS_WIN32 = False
if platform.system() == 'Windows':
    try:
        import win32com.client
        HAS_WIN32 = True
    except ImportError:
        pass


# 썸네일 크기
THUMBNAIL_SIZES = {
    'content': (960, 540),     # 콘텐츠 템플릿용
    'document': (480, 270),    # 문서 레이아웃용
    'theme': (320, 180),       # 테마 미리보기용
    'grid': (300, 169),        # 그리드 뷰 개별 항목
}

# 변환 설정
CONVERSION_DPI = 150
JPEG_QUALITY = 95


def convert_pptx_to_images_win32(pptx_path: Path, output_dir: Path, width: int = 1920) -> List[Path]:
    """Windows PowerPoint COM 자동화로 PPTX를 이미지로 변환."""
    if not HAS_WIN32:
        raise ImportError("pywin32가 필요합니다: pip install pywin32")

    import win32com.client

    # 절대 경로로 변환
    pptx_path = Path(pptx_path).resolve()
    output_dir = Path(output_dir).resolve()

    powerpoint = None
    presentation = None

    try:
        # PowerPoint 인스턴스 생성
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")

        # 프레젠테이션 열기 (ReadOnly, WithWindow=False)
        presentation = powerpoint.Presentations.Open(
            str(pptx_path),
            ReadOnly=True,
            Untitled=False,
            WithWindow=False
        )

        images = []
        for i, slide in enumerate(presentation.Slides):
            output_file = output_dir / f"slide-{i:02d}.png"
            # Export(Path, FilterName, ScaleWidth, ScaleHeight)
            slide.Export(str(output_file), "PNG", width)
            images.append(output_file)

        return images

    finally:
        if presentation:
            presentation.Close()
        if powerpoint:
            powerpoint.Quit()


def convert_pptx_to_images_libreoffice(pptx_path: Path, output_dir: Path, dpi: int = CONVERSION_DPI) -> List[Path]:
    """LibreOffice + pdftoppm으로 PPTX를 이미지로 변환."""
    # PDF로 변환
    pdf_path = output_dir / f"{pptx_path.stem}.pdf"

    result = subprocess.run([
        "soffice", "--headless",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(pptx_path)
    ], capture_output=True, text=True)

    if result.returncode != 0 or not pdf_path.exists():
        raise RuntimeError(f"PDF 변환 실패: {result.stderr}")

    # PDF를 이미지로 변환
    result = subprocess.run([
        "pdftoppm", "-png", "-r", str(dpi),
        str(pdf_path), str(output_dir / "slide")
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"이미지 변환 실패: {result.stderr}")

    # 생성된 이미지 목록
    images = sorted(output_dir.glob("slide-*.png"))
    return images


def convert_pptx_to_images(pptx_path: Path, output_dir: Path, dpi: int = CONVERSION_DPI) -> List[Path]:
    """PPTX를 이미지로 변환.

    Windows에서는 PowerPoint COM 자동화를 먼저 시도하고,
    실패하면 LibreOffice를 사용합니다.
    """
    # Windows + pywin32 사용 가능시 PowerPoint COM 시도
    if HAS_WIN32:
        try:
            return convert_pptx_to_images_win32(pptx_path, output_dir)
        except Exception as e:
            print(f"  PowerPoint COM 실패: {e}, LibreOffice 시도...")

    # LibreOffice 폴백
    return convert_pptx_to_images_libreoffice(pptx_path, output_dir, dpi)


def create_thumbnail(image_path: Path, size: tuple, output_path: Path):
    """썸네일 생성"""
    if not HAS_PIL:
        raise ImportError("PIL이 필요합니다: pip install Pillow")

    with Image.open(image_path) as img:
        # 비율 유지하며 리사이즈
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # 배경 생성 (여백이 있을 경우)
        background = Image.new('RGB', size, 'white')

        # 중앙 정렬
        x = (size[0] - img.width) // 2
        y = (size[1] - img.height) // 2
        background.paste(img, (x, y))

        # 저장
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix.lower() in ['.jpg', '.jpeg']:
            background.save(output_path, 'JPEG', quality=JPEG_QUALITY)
        else:
            background.save(output_path, 'PNG')


def create_grid_view(
    image_paths: List[Path],
    output_path: Path,
    cols: int = 5,
    thumb_width: int = 300,
    padding: int = 20
):
    """그리드 뷰 생성"""
    if not HAS_PIL:
        raise ImportError("PIL이 필요합니다: pip install Pillow")

    if not image_paths:
        raise ValueError("이미지가 없습니다")

    # 첫 이미지에서 비율 계산
    with Image.open(image_paths[0]) as img:
        aspect = img.height / img.width

    thumb_height = int(thumb_width * aspect)

    # 그리드 크기 계산
    rows = (len(image_paths) + cols - 1) // cols
    font_size = int(thumb_width * 0.12)
    label_height = font_size + padding

    grid_width = cols * thumb_width + (cols + 1) * padding
    grid_height = rows * (thumb_height + label_height) + (rows + 1) * padding

    # 그리드 이미지 생성
    grid = Image.new('RGB', (grid_width, grid_height), 'white')
    draw = ImageDraw.Draw(grid)

    try:
        font = ImageFont.load_default(size=font_size)
    except Exception:
        font = ImageFont.load_default()

    # 썸네일 배치
    for i, img_path in enumerate(image_paths):
        row = i // cols
        col = i % cols

        x = col * thumb_width + (col + 1) * padding
        y = row * (thumb_height + label_height) + (row + 1) * padding

        # 라벨
        label = str(i)
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((x + (thumb_width - text_width) // 2, y), label, fill='black', font=font)

        # 썸네일
        thumb_y = y + label_height
        with Image.open(img_path) as img:
            img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            tx = x + (thumb_width - img.width) // 2
            ty = thumb_y + (thumb_height - img.height) // 2
            grid.paste(img, (tx, ty))

            # 테두리
            draw.rectangle(
                [(tx - 1, ty - 1), (tx + img.width, ty + img.height)],
                outline='gray', width=1
            )

    # 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    grid.save(output_path, quality=JPEG_QUALITY)


def main():
    parser = argparse.ArgumentParser(
        description="PPTX 슬라이드 썸네일 생성"
    )
    parser.add_argument("input", help="입력 PPTX 파일")
    parser.add_argument("--slide", type=int, help="특정 슬라이드 번호 (0-based)")
    parser.add_argument("--all", action="store_true", help="모든 슬라이드 개별 썸네일")
    parser.add_argument("--grid", action="store_true", help="그리드 뷰 생성")
    parser.add_argument("--output", "-o", help="출력 파일 (단일 썸네일 또는 그리드)")
    parser.add_argument("--output-dir", help="출력 디렉토리 (--all 옵션용)")
    parser.add_argument("--size", choices=['content', 'document', 'theme'], default='content',
                       help="썸네일 크기 프리셋")
    parser.add_argument("--cols", type=int, default=5, help="그리드 열 개수")
    parser.add_argument("--dpi", type=int, default=CONVERSION_DPI, help="변환 DPI")

    args = parser.parse_args()

    if not HAS_PIL:
        print("Error: Pillow가 필요합니다: pip install Pillow")
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: 파일을 찾을 수 없습니다: {args.input}")
        sys.exit(1)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # PPTX → 이미지 변환
            print(f"변환 중: {args.input}")
            images = convert_pptx_to_images(input_path, temp_path, args.dpi)
            print(f"슬라이드 {len(images)}개 발견")

            if args.grid:
                # 그리드 뷰
                output_path = Path(args.output) if args.output else Path(f"{input_path.stem}-grid.jpg")
                print(f"그리드 생성 중...")
                create_grid_view(images, output_path, cols=args.cols)
                print(f"저장됨: {output_path}")

            elif args.all:
                # 모든 슬라이드 개별 썸네일
                output_dir = Path(args.output_dir) if args.output_dir else Path("thumbnails")
                size = THUMBNAIL_SIZES[args.size]

                for i, img_path in enumerate(images):
                    output_path = output_dir / f"slide-{i:02d}.png"
                    create_thumbnail(img_path, size, output_path)
                    print(f"저장됨: {output_path}")

            elif args.slide is not None:
                # 단일 슬라이드
                if args.slide < 0 or args.slide >= len(images):
                    print(f"Error: 슬라이드 {args.slide}가 존재하지 않습니다 (0-{len(images)-1})")
                    sys.exit(1)

                output_path = Path(args.output) if args.output else Path(f"slide-{args.slide:02d}.png")
                size = THUMBNAIL_SIZES[args.size]
                create_thumbnail(images[args.slide], size, output_path)
                print(f"저장됨: {output_path}")

            else:
                print("Error: --slide, --all, 또는 --grid 옵션을 지정하세요")
                sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
