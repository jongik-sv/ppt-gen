#!/usr/bin/env python3
"""
PPTX 또는 이미지에서 테마 스타일(색상, 폰트) 추출.

PPTX: theme1.xml에서 색상 스킴과 폰트 스킴 추출
이미지: 주요 색상 추출 (K-means 클러스터링)

Usage:
    # PPTX에서 테마 추출
    python style-extractor.py input.pptx --output themes/new-theme/theme.yaml

    # 이미지에서 색상 추출
    python style-extractor.py reference.png --output themes/new-theme/theme.yaml
"""

import argparse
import colorsys
import json
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

try:
    from PIL import Image
    import numpy as np
    from sklearn.cluster import KMeans
    HAS_IMAGE_DEPS = True
except ImportError:
    HAS_IMAGE_DEPS = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# OOXML 네임스페이스
NAMESPACES = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
}


@dataclass
class ColorPalette:
    """색상 팔레트"""
    primary: str = "#1a5f4a"
    secondary: str = "#2d7a5e"
    accent: str = "#4a9d7f"
    background: str = "#ffffff"
    surface: str = "#f5f9f7"
    text: str = "#1a1a1a"
    muted: str = "#6b7c74"


@dataclass
class FontScheme:
    """폰트 스킴"""
    major: str = "맑은 고딕"  # 제목용
    minor: str = "맑은 고딕"  # 본문용


@dataclass
class StyleHints:
    """스타일 힌트"""
    border_radius: str = "8px"
    shadow: str = "0 4px 12px rgba(0,0,0,0.08)"


@dataclass
class Theme:
    """테마 정의"""
    id: str
    name: str
    colors: ColorPalette = field(default_factory=ColorPalette)
    fonts: FontScheme = field(default_factory=FontScheme)
    style_hints: StyleHints = field(default_factory=StyleHints)
    source_file: Optional[str] = None


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """HEX 색상을 RGB 튜플로 변환"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGB를 HEX 색상으로 변환"""
    return f"#{r:02x}{g:02x}{b:02x}"


def get_color_luminance(hex_color: str) -> float:
    """색상의 휘도(luminance) 계산"""
    r, g, b = hex_to_rgb(hex_color)
    return 0.299 * r + 0.587 * g + 0.114 * b


def get_color_saturation(hex_color: str) -> float:
    """색상의 채도(saturation) 계산"""
    r, g, b = hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return s


def classify_colors(colors: List[str]) -> ColorPalette:
    """추출된 색상들을 역할별로 분류"""
    if not colors:
        return ColorPalette()

    # 색상을 밝기순으로 정렬
    sorted_by_lum = sorted(colors, key=get_color_luminance)

    # 채도가 높은 색상 찾기 (primary, accent 후보)
    saturated = sorted([c for c in colors if get_color_saturation(c) > 0.3],
                       key=get_color_saturation, reverse=True)

    # 가장 어두운 색상 = text
    text = sorted_by_lum[0] if len(sorted_by_lum) > 0 else "#1a1a1a"

    # 가장 밝은 색상 = background
    background = sorted_by_lum[-1] if len(sorted_by_lum) > 0 else "#ffffff"

    # 채도가 가장 높은 색상 = primary
    primary = saturated[0] if len(saturated) > 0 else "#1a5f4a"

    # 두 번째로 채도가 높은 색상 = accent
    accent = saturated[1] if len(saturated) > 1 else primary

    # primary보다 약간 밝은 색상 = secondary
    primary_lum = get_color_luminance(primary)
    secondary_candidates = [c for c in colors
                           if abs(get_color_luminance(c) - primary_lum) < 50
                           and c != primary]
    secondary = secondary_candidates[0] if secondary_candidates else primary

    # 중간 밝기 = surface
    mid_idx = len(sorted_by_lum) // 2
    surface = sorted_by_lum[mid_idx] if len(sorted_by_lum) > 2 else "#f5f9f7"

    # muted (낮은 채도, 중간 밝기)
    muted_candidates = [c for c in colors if get_color_saturation(c) < 0.3]
    muted = muted_candidates[0] if muted_candidates else "#6b7c74"

    return ColorPalette(
        primary=primary,
        secondary=secondary,
        accent=accent,
        background=background,
        surface=surface,
        text=text,
        muted=muted
    )


def extract_colors_from_image(image_path: Path, n_colors: int = 8) -> List[str]:
    """이미지에서 주요 색상 추출 (K-means)"""
    if not HAS_IMAGE_DEPS:
        raise ImportError("이미지 처리를 위해 PIL, numpy, sklearn이 필요합니다")

    img = Image.open(image_path)
    img = img.convert('RGB')

    # 이미지 리사이즈 (성능 최적화)
    img.thumbnail((200, 200))

    # numpy 배열로 변환
    pixels = np.array(img).reshape(-1, 3)

    # K-means 클러스터링
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    kmeans.fit(pixels)

    # 클러스터 중심 색상 추출
    colors = []
    for center in kmeans.cluster_centers_:
        r, g, b = int(center[0]), int(center[1]), int(center[2])
        colors.append(rgb_to_hex(r, g, b))

    return colors


def extract_theme_from_pptx(pptx_path: Path) -> Theme:
    """PPTX 파일에서 테마 추출"""

    theme_id = pptx_path.stem.lower().replace(' ', '-').replace('_', '-')
    theme = Theme(
        id=theme_id,
        name=f"{pptx_path.stem} 테마",
        source_file=str(pptx_path.name)
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        # PPTX 압축 해제
        with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # theme1.xml 찾기
        theme_path = Path(temp_dir) / "ppt" / "theme" / "theme1.xml"
        if not theme_path.exists():
            print(f"Warning: theme1.xml을 찾을 수 없습니다")
            return theme

        tree = ET.parse(theme_path)
        root = tree.getroot()

        # 색상 스킴 추출
        clr_scheme = root.find('.//a:clrScheme', NAMESPACES)
        if clr_scheme is not None:
            colors = extract_color_scheme(clr_scheme)
            theme.colors = colors

        # 폰트 스킴 추출
        font_scheme = root.find('.//a:fontScheme', NAMESPACES)
        if font_scheme is not None:
            fonts = extract_font_scheme(font_scheme)
            theme.fonts = fonts

    return theme


def extract_color_scheme(clr_scheme) -> ColorPalette:
    """OOXML 색상 스킴에서 ColorPalette 추출"""
    colors = ColorPalette()

    # 색상 매핑 (OOXML -> ColorPalette)
    color_mapping = {
        'dk1': 'text',      # 어두운 색상 1 (주로 텍스트)
        'dk2': 'primary',   # 어두운 색상 2
        'lt1': 'background', # 밝은 색상 1 (주로 배경)
        'lt2': 'surface',   # 밝은 색상 2
        'accent1': 'accent', # 강조색 1
        'accent2': 'secondary', # 강조색 2
    }

    for child in clr_scheme:
        tag = child.tag.split('}')[-1]

        if tag in color_mapping:
            color_value = get_color_from_element(child)
            if color_value:
                setattr(colors, color_mapping[tag], color_value)

    return colors


def get_color_from_element(element) -> Optional[str]:
    """OOXML 색상 요소에서 HEX 색상 추출"""
    # srgbClr 찾기
    srgb = element.find('.//a:srgbClr', NAMESPACES)
    if srgb is not None and 'val' in srgb.attrib:
        return f"#{srgb.attrib['val']}"

    # sysClr 찾기 (시스템 색상)
    sys_clr = element.find('.//a:sysClr', NAMESPACES)
    if sys_clr is not None and 'lastClr' in sys_clr.attrib:
        return f"#{sys_clr.attrib['lastClr']}"

    return None


def extract_font_scheme(font_scheme) -> FontScheme:
    """OOXML 폰트 스킴에서 FontScheme 추출"""
    fonts = FontScheme()

    # majorFont (제목용)
    major_font = font_scheme.find('.//a:majorFont', NAMESPACES)
    if major_font is not None:
        latin = major_font.find('a:latin', NAMESPACES)
        if latin is not None and 'typeface' in latin.attrib:
            fonts.major = latin.attrib['typeface']

        # 한글 폰트 확인
        ea = major_font.find('a:ea', NAMESPACES)
        if ea is not None and 'typeface' in ea.attrib:
            fonts.major = ea.attrib['typeface']

    # minorFont (본문용)
    minor_font = font_scheme.find('.//a:minorFont', NAMESPACES)
    if minor_font is not None:
        latin = minor_font.find('a:latin', NAMESPACES)
        if latin is not None and 'typeface' in latin.attrib:
            fonts.minor = latin.attrib['typeface']

        # 한글 폰트 확인
        ea = minor_font.find('a:ea', NAMESPACES)
        if ea is not None and 'typeface' in ea.attrib:
            fonts.minor = ea.attrib['typeface']

    return fonts


def extract_theme_from_image(image_path: Path) -> Theme:
    """이미지에서 테마 추출"""
    theme_id = image_path.stem.lower().replace(' ', '-').replace('_', '-')

    # 색상 추출
    colors = extract_colors_from_image(image_path)

    # 색상 분류
    palette = classify_colors(colors)

    return Theme(
        id=theme_id,
        name=f"{image_path.stem} 테마",
        colors=palette,
        source_file=str(image_path.name)
    )


def save_theme(theme: Theme, output_path: Path):
    """테마를 YAML 파일로 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # dataclass를 dict로 변환
    data = {
        'id': theme.id,
        'name': theme.name,
        'colors': asdict(theme.colors),
        'fonts': asdict(theme.fonts),
        'style_hints': asdict(theme.style_hints)
    }

    if theme.source_file:
        data['source_file'] = theme.source_file

    if HAS_YAML:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    else:
        # YAML 없으면 JSON으로
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Warning: YAML 모듈 없음, JSON으로 저장됨: {json_path}")
        return

    print(f"저장됨: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="PPTX 또는 이미지에서 테마 스타일 추출"
    )
    parser.add_argument("input", help="입력 파일 (PPTX 또는 이미지)")
    parser.add_argument("--output", "-o", required=True, help="출력 YAML 파일")
    parser.add_argument("--name", help="테마 이름 (기본: 파일명)")
    parser.add_argument("--id", help="테마 ID (기본: 파일명)")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: 파일을 찾을 수 없습니다: {args.input}")
        sys.exit(1)

    output_path = Path(args.output)

    try:
        # 파일 타입에 따라 처리
        suffix = input_path.suffix.lower()

        if suffix == '.pptx':
            theme = extract_theme_from_pptx(input_path)
        elif suffix in ['.png', '.jpg', '.jpeg', '.webp', '.bmp']:
            if not HAS_IMAGE_DEPS:
                print("Error: 이미지 처리를 위해 다음 패키지가 필요합니다:")
                print("  pip install Pillow numpy scikit-learn")
                sys.exit(1)
            theme = extract_theme_from_image(input_path)
        else:
            print(f"Error: 지원하지 않는 파일 형식: {suffix}")
            print("지원 형식: .pptx, .png, .jpg, .jpeg, .webp, .bmp")
            sys.exit(1)

        # 이름/ID 덮어쓰기
        if args.name:
            theme.name = args.name
        if args.id:
            theme.id = args.id

        # 저장
        save_theme(theme, output_path)

        # 결과 출력
        print(f"\n테마 추출 완료:")
        print(f"  ID: {theme.id}")
        print(f"  이름: {theme.name}")
        print(f"  Primary: {theme.colors.primary}")
        print(f"  Accent: {theme.colors.accent}")
        print(f"  폰트: {theme.fonts.major} / {theme.fonts.minor}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
