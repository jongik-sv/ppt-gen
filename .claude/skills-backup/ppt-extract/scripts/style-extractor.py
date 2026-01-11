#!/usr/bin/env python3
"""
Style Extractor - 이미지에서 색상/레이아웃 추출

이미지에서 주요 색상을 추출하여 PPT 스타일 가이드로 변환합니다.

Usage:
    python style-extractor.py <image> --output <style.yaml>
    python style-extractor.py reference.png --colors-only --count 5
    python style-extractor.py reference.png --format css

Examples:
    # 기본 스타일 추출 (YAML)
    python style-extractor.py design.png --output style.yaml

    # 색상만 추출
    python style-extractor.py design.png --colors-only --count 6

    # CSS 변수로 출력
    python style-extractor.py design.png --format css

    # JSON 출력 (stdout)
    python style-extractor.py design.png --format json

Dependencies:
    pip install Pillow numpy
    pip install colorthief  # 선택 (없으면 K-means 사용)
"""

import argparse
import sys
from pathlib import Path
from collections import Counter

import yaml

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from colorthief import ColorThief
    HAS_COLORTHIEF = True
except ImportError:
    HAS_COLORTHIEF = False


def rgb_to_hex(rgb: tuple) -> str:
    """RGB를 HEX로 변환 (# 없이)"""
    return '{:02X}{:02X}{:02X}'.format(rgb[0], rgb[1], rgb[2])


def hex_to_rgb(hex_color: str) -> tuple:
    """HEX를 RGB로 변환"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_brightness(rgb: tuple) -> float:
    """색상 밝기 계산 (0-255)"""
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def get_saturation(rgb: tuple) -> float:
    """색상 채도 계산 (0-1)"""
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    if max_c == 0:
        return 0
    return (max_c - min_c) / max_c


def extract_colors_colorthief(image_path: str, count: int) -> list:
    """ColorThief로 색상 추출"""
    ct = ColorThief(image_path)
    palette = ct.get_palette(color_count=count + 2, quality=1)
    return [rgb_to_hex(c) for c in palette[:count]]


def extract_colors_kmeans(image_path: str, count: int) -> list:
    """K-means로 색상 추출 (Pillow + NumPy)"""
    img = Image.open(image_path)
    img = img.convert('RGB')

    # 리사이즈로 속도 향상
    img.thumbnail((150, 150))

    # 픽셀 데이터
    pixels = list(img.getdata())

    # 간단한 빈도 기반 추출 (K-means 대신)
    # 색상을 양자화하여 그룹화
    quantized = []
    for r, g, b in pixels:
        # 32단계로 양자화
        qr = (r // 32) * 32
        qg = (g // 32) * 32
        qb = (b // 32) * 32
        quantized.append((qr, qg, qb))

    # 빈도 계산
    counter = Counter(quantized)
    most_common = counter.most_common(count * 2)

    # 너무 어둡거나 너무 밝은 색상 필터링
    filtered = []
    for color, freq in most_common:
        brightness = get_brightness(color)
        if 30 < brightness < 245:
            filtered.append(color)
        if len(filtered) >= count:
            break

    # 부족하면 원본에서 추가
    if len(filtered) < count:
        for color, freq in most_common:
            if color not in filtered:
                filtered.append(color)
            if len(filtered) >= count:
                break

    return [rgb_to_hex(c) for c in filtered[:count]]


def extract_colors(image_path: str, count: int = 5) -> list:
    """이미지에서 주요 색상 추출"""
    if HAS_COLORTHIEF:
        return extract_colors_colorthief(image_path, count)
    elif HAS_PIL and HAS_NUMPY:
        return extract_colors_kmeans(image_path, count)
    elif HAS_PIL:
        return extract_colors_kmeans(image_path, count)
    else:
        print("Error: Pillow가 필요합니다. pip install Pillow")
        return []


def classify_colors(colors: list) -> dict:
    """색상을 역할별로 분류"""
    if not colors:
        return {}

    classified = {
        'primary': None,
        'secondary': None,
        'accent': None,
        'background': None,
        'text': None,
    }

    # RGB로 변환하여 분석
    color_data = []
    for hex_color in colors:
        rgb = hex_to_rgb(hex_color)
        brightness = get_brightness(rgb)
        saturation = get_saturation(rgb)
        color_data.append({
            'hex': hex_color,
            'rgb': rgb,
            'brightness': brightness,
            'saturation': saturation,
        })

    # 밝기순 정렬
    by_brightness = sorted(color_data, key=lambda x: x['brightness'])

    # 채도순 정렬
    by_saturation = sorted(color_data, key=lambda x: x['saturation'], reverse=True)

    # 가장 어두운 것 → text
    classified['text'] = by_brightness[0]['hex']

    # 가장 밝은 것 → background
    classified['background'] = by_brightness[-1]['hex']

    # 채도가 가장 높은 것 → primary
    for c in by_saturation:
        if c['hex'] not in [classified['text'], classified['background']]:
            classified['primary'] = c['hex']
            break

    # 두 번째로 채도가 높은 것 → secondary
    for c in by_saturation:
        if c['hex'] not in [classified['text'], classified['background'], classified['primary']]:
            classified['secondary'] = c['hex']
            break

    # 나머지 중 하나 → accent
    for c in color_data:
        if c['hex'] not in [classified['text'], classified['background'],
                           classified['primary'], classified['secondary']]:
            classified['accent'] = c['hex']
            break

    # None인 항목 제거
    return {k: v for k, v in classified.items() if v}


def generate_style_yaml(colors: list, classified: dict, source: str) -> str:
    """YAML 스타일 가이드 생성"""
    from datetime import datetime

    data = {
        'style': {
            'name': Path(source).stem,
            'source': source,
            'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        },
        'colors': {
            'palette': colors,
            'roles': classified,
        },
        'pptx_colors': {
            'primary': classified.get('primary', colors[0] if colors else 'FFFFFF'),
            'secondary': classified.get('secondary', colors[1] if len(colors) > 1 else 'CCCCCC'),
            'accent': classified.get('accent', colors[2] if len(colors) > 2 else '333333'),
            'background': classified.get('background', 'FFFFFF'),
            'text': classified.get('text', '333333'),
        },
        'chart_colors': colors[:4] if len(colors) >= 4 else colors,
    }

    yaml_str = f"""# 스타일 가이드
# 원본: {source}
# 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}

"""
    yaml_str += yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return yaml_str


def generate_css_vars(colors: list, classified: dict) -> str:
    """CSS 변수 출력"""
    lines = [':root {']

    # 역할별 색상
    for role, color in classified.items():
        if color:
            lines.append(f'  --color-{role}: #{color};')

    lines.append('')

    # 팔레트
    for i, color in enumerate(colors):
        lines.append(f'  --palette-{i + 1}: #{color};')

    lines.append('}')
    return '\n'.join(lines)


def generate_json(colors: list, classified: dict, source: str) -> str:
    """JSON 출력"""
    import json
    data = {
        'source': source,
        'palette': colors,
        'roles': classified,
        'pptx_colors': {
            'primary': classified.get('primary', colors[0] if colors else 'FFFFFF'),
            'secondary': classified.get('secondary', colors[1] if len(colors) > 1 else 'CCCCCC'),
            'background': classified.get('background', 'FFFFFF'),
            'text': classified.get('text', '333333'),
        }
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def cmd_extract(args) -> int:
    """색상 추출 실행"""
    image_path = args.image
    count = args.count
    output_format = args.format
    output_file = args.output
    colors_only = args.colors_only

    # 파일 확인
    if not Path(image_path).exists():
        print(f"Error: 파일을 찾을 수 없습니다 - {image_path}")
        return 1

    print(f"이미지 분석: {image_path}")
    print(f"추출 색상 수: {count}")
    print()

    # 색상 추출
    print("[1/2] 색상 추출...")
    colors = extract_colors(image_path, count)

    if not colors:
        print("Error: 색상 추출 실패")
        return 1

    print(f"  추출된 색상: {len(colors)}개")
    for i, c in enumerate(colors):
        rgb = hex_to_rgb(c)
        print(f"    {i + 1}. #{c} (R:{rgb[0]}, G:{rgb[1]}, B:{rgb[2]})")

    # 색상만 출력 모드
    if colors_only:
        print("\n색상 팔레트:")
        for c in colors:
            print(f"  #{c}")
        return 0

    # 색상 분류
    print("\n[2/2] 색상 분류...")
    classified = classify_colors(colors)
    for role, color in classified.items():
        if color:
            print(f"  {role}: #{color}")

    # 출력 생성
    print()
    if output_format == 'yaml':
        output = generate_style_yaml(colors, classified, image_path)
    elif output_format == 'css':
        output = generate_css_vars(colors, classified)
    elif output_format == 'json':
        output = generate_json(colors, classified, image_path)
    else:
        output = generate_style_yaml(colors, classified, image_path)

    # 파일 저장 또는 stdout
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"저장됨: {output_file}")
    else:
        print("--- 출력 ---")
        print(output)

    return 0


def main():
    if not HAS_PIL:
        print("Error: Pillow가 필요합니다.")
        print("  pip install Pillow")
        return 1

    parser = argparse.ArgumentParser(
        description='이미지에서 PPT 스타일 추출',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # YAML 스타일 가이드 생성
  python style-extractor.py design.png --output style.yaml

  # 색상만 추출 (6개)
  python style-extractor.py design.png --colors-only --count 6

  # CSS 변수로 출력
  python style-extractor.py design.png --format css

  # JSON 출력
  python style-extractor.py design.png --format json
        """
    )

    parser.add_argument('image', help='입력 이미지 파일')
    parser.add_argument('--output', '-o', help='출력 파일 경로')
    parser.add_argument('--count', '-n', type=int, default=5,
                        help='추출할 색상 수 (기본: 5)')
    parser.add_argument('--format', '-f', choices=['yaml', 'json', 'css'],
                        default='yaml', help='출력 형식 (기본: yaml)')
    parser.add_argument('--colors-only', action='store_true',
                        help='색상만 출력 (분류 없이)')

    args = parser.parse_args()
    return cmd_extract(args)


if __name__ == '__main__':
    sys.exit(main())
