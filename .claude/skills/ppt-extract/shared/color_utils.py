#!/usr/bin/env python3
"""
색상 처리 유틸리티.

PPTX 또는 이미지에서 색상을 추출하고 역할을 분류합니다.
"""

import colorsys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import numpy as np
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class ColorInfo:
    """색상 정보."""
    hex: str
    rgb: Tuple[int, int, int]
    hsl: Tuple[float, float, float]  # hue, saturation, lightness
    role: Optional[str] = None  # primary, secondary, accent, background, text, etc.


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """HEX 색상을 RGB로 변환."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """RGB를 HEX로 변환."""
    return '#{:02X}{:02X}{:02X}'.format(*rgb)


def rgb_to_hsl(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """RGB를 HSL로 변환 (0-1 범위)."""
    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h, s, l)


def get_luminance(rgb: Tuple[int, int, int]) -> float:
    """색상의 밝기(luminance) 계산 (0-1)."""
    r, g, b = [x / 255.0 for x in rgb]
    return 0.299 * r + 0.587 * g + 0.114 * b


def get_saturation(rgb: Tuple[int, int, int]) -> float:
    """색상의 채도 계산 (0-1)."""
    _, s, _ = rgb_to_hsl(rgb)
    return s


def create_color_info(hex_color: str, role: Optional[str] = None) -> ColorInfo:
    """ColorInfo 객체 생성."""
    rgb = hex_to_rgb(hex_color)
    hsl = rgb_to_hsl(rgb)
    return ColorInfo(hex=hex_color.upper(), rgb=rgb, hsl=hsl, role=role)


def map_ooxml_colors_to_theme(ooxml_colors: Dict[str, str]) -> Dict[str, str]:
    """
    OOXML 색상 스킴을 테마 역할로 매핑.

    OOXML 색상:
    - dk1, dk2: 어두운 색 (텍스트용)
    - lt1, lt2: 밝은 색 (배경용)
    - accent1~6: 강조 색상

    테마 역할:
    - primary: 주요 색상 (accent1 또는 dk2)
    - secondary: 보조 색상 (accent2)
    - accent: 강조 색상 (accent3)
    - background: 배경색 (lt1)
    - surface: 표면색 (lt2 또는 #FFFFFF)
    - text: 텍스트색 (dk1)
    - muted: 비활성 텍스트 (accent6 또는 회색)
    """
    theme_colors = {}

    # 텍스트 색상 (dk1)
    theme_colors['text'] = ooxml_colors.get('dk1', '#1A1A1A')

    # 배경 색상 (lt1)
    theme_colors['background'] = ooxml_colors.get('lt1', '#FFFFFF')

    # 표면 색상 (lt2 또는 흰색)
    lt2 = ooxml_colors.get('lt2', '#FFFFFF')
    theme_colors['surface'] = lt2 if lt2 != theme_colors['background'] else '#FFFFFF'

    # 주요 색상 (accent1 우선, 없으면 dk2)
    if 'accent1' in ooxml_colors:
        theme_colors['primary'] = ooxml_colors['accent1']
    elif 'dk2' in ooxml_colors:
        theme_colors['primary'] = ooxml_colors['dk2']
    else:
        theme_colors['primary'] = '#0066CC'

    # 보조 색상 (accent2)
    theme_colors['secondary'] = ooxml_colors.get('accent2', theme_colors['primary'])

    # 강조 색상 (accent3 또는 accent4)
    theme_colors['accent'] = ooxml_colors.get('accent3', ooxml_colors.get('accent4', theme_colors['secondary']))

    # 비활성 텍스트 (accent6 또는 중간 회색)
    if 'accent6' in ooxml_colors:
        theme_colors['muted'] = ooxml_colors['accent6']
    else:
        theme_colors['muted'] = '#6B7280'

    return theme_colors


def extract_colors_from_image(
    image_path: Path,
    n_colors: int = 8
) -> List[ColorInfo]:
    """
    이미지에서 주요 색상 추출 (K-means 클러스터링).

    Args:
        image_path: 이미지 경로
        n_colors: 추출할 색상 수

    Returns:
        ColorInfo 리스트 (빈도순)
    """
    if not HAS_PIL:
        raise ImportError("Pillow가 필요합니다: pip install Pillow")
    if not HAS_SKLEARN:
        raise ImportError("scikit-learn이 필요합니다: pip install scikit-learn numpy")

    # 이미지 로드 및 리사이즈 (성능 최적화)
    img = Image.open(image_path)
    img = img.convert('RGB')
    img.thumbnail((200, 200))  # 작은 크기로 축소

    # 픽셀 데이터 추출
    pixels = np.array(img).reshape(-1, 3)

    # K-means 클러스터링
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    kmeans.fit(pixels)

    # 클러스터 중심 (색상) 및 빈도 계산
    colors = kmeans.cluster_centers_.astype(int)
    labels, counts = np.unique(kmeans.labels_, return_counts=True)

    # 빈도순 정렬
    sorted_indices = np.argsort(-counts)

    result = []
    for idx in sorted_indices:
        rgb = tuple(colors[idx])
        hex_color = rgb_to_hex(rgb)
        hsl = rgb_to_hsl(rgb)
        result.append(ColorInfo(hex=hex_color, rgb=rgb, hsl=hsl))

    return result


def classify_colors_by_role(colors: List[ColorInfo]) -> Dict[str, str]:
    """
    추출된 색상에 역할 자동 부여.

    분류 기준:
    - 가장 밝음 (luminance > 0.9) → background
    - 가장 어두움 (luminance < 0.2) → text
    - 높은 채도 + 중간 밝기 → primary, accent
    - 나머지 → secondary, muted
    """
    if not colors:
        return {}

    # 밝기/채도 계산 및 정렬
    color_with_metrics = []
    for c in colors:
        lum = get_luminance(c.rgb)
        sat = get_saturation(c.rgb)
        color_with_metrics.append((c, lum, sat))

    # 역할 할당
    theme = {}
    used = set()

    # 1. 배경 (가장 밝음)
    sorted_by_lum = sorted(color_with_metrics, key=lambda x: -x[1])
    for c, lum, sat in sorted_by_lum:
        if lum > 0.85 and c.hex not in used:
            theme['background'] = c.hex
            used.add(c.hex)
            break
    if 'background' not in theme:
        theme['background'] = '#FFFFFF'

    # 2. 텍스트 (가장 어두움)
    sorted_by_lum_asc = sorted(color_with_metrics, key=lambda x: x[1])
    for c, lum, sat in sorted_by_lum_asc:
        if lum < 0.3 and c.hex not in used:
            theme['text'] = c.hex
            used.add(c.hex)
            break
    if 'text' not in theme:
        theme['text'] = '#1A1A1A'

    # 3. Primary (높은 채도, 중간 밝기)
    sorted_by_sat = sorted(color_with_metrics, key=lambda x: (-x[2], abs(x[1] - 0.5)))
    for c, lum, sat in sorted_by_sat:
        if sat > 0.3 and 0.2 < lum < 0.8 and c.hex not in used:
            theme['primary'] = c.hex
            used.add(c.hex)
            break
    if 'primary' not in theme:
        # 채도가 가장 높은 색상 사용
        for c, lum, sat in sorted_by_sat:
            if c.hex not in used:
                theme['primary'] = c.hex
                used.add(c.hex)
                break

    # 4. Secondary, Accent (다음으로 채도 높은 색)
    for c, lum, sat in sorted_by_sat:
        if c.hex not in used:
            if 'secondary' not in theme:
                theme['secondary'] = c.hex
                used.add(c.hex)
            elif 'accent' not in theme:
                theme['accent'] = c.hex
                used.add(c.hex)
                break

    # 5. Surface, Muted (나머지)
    for c, lum, sat in sorted_by_lum:
        if c.hex not in used:
            if 'surface' not in theme and lum > 0.7:
                theme['surface'] = c.hex
                used.add(c.hex)
            elif 'muted' not in theme and 0.3 < lum < 0.7:
                theme['muted'] = c.hex
                used.add(c.hex)

    # 기본값 설정
    theme.setdefault('surface', '#FFFFFF')
    theme.setdefault('secondary', theme.get('primary', '#0066CC'))
    theme.setdefault('accent', theme.get('secondary', '#0066CC'))
    theme.setdefault('muted', '#6B7280')

    return theme


def generate_palette_thumbnail(
    colors: Dict[str, str],
    output_path: Path,
    width: int = 320,
    height: int = 180
) -> None:
    """
    색상 팔레트 썸네일 생성.

    Args:
        colors: 색상 딕셔너리 (역할 → HEX)
        output_path: 출력 경로
        width: 너비
        height: 높이
    """
    if not HAS_PIL:
        raise ImportError("Pillow가 필요합니다: pip install Pillow")

    # 이미지 생성
    img = Image.new('RGB', (width, height), '#FFFFFF')

    # 색상 블록 그리기
    color_list = list(colors.values())
    n_colors = len(color_list)

    if n_colors == 0:
        return

    block_width = width // n_colors

    for i, hex_color in enumerate(color_list):
        rgb = hex_to_rgb(hex_color)
        x_start = i * block_width
        x_end = (i + 1) * block_width if i < n_colors - 1 else width

        for x in range(x_start, x_end):
            for y in range(height):
                img.putpixel((x, y), rgb)

    # 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
