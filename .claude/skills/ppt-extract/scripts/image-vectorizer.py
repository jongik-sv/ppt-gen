#!/usr/bin/env python3
"""
이미지에서 디자인 스타일 추출 (style-extractor.py와 연계).

이미지 분석을 통해:
1. 색상 팔레트 추출 (K-means)
2. 타이포그래피 힌트 감지 (OCR 없이 영역 분석)
3. 레이아웃 패턴 감지 (엣지/컨투어 분석)
4. 스타일 힌트 추출 (둥근 모서리, 그림자 등)

Usage:
    python image-vectorizer.py reference.png --output themes/new-theme/theme.yaml
    python image-vectorizer.py screenshot.png --analyze-only
"""

import argparse
import colorsys
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image, ImageFilter, ImageStat
    import numpy as np
    from sklearn.cluster import KMeans
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class ExtractedColor:
    """추출된 색상"""
    hex: str
    rgb: Tuple[int, int, int]
    percentage: float  # 이미지 내 비중
    role: Optional[str] = None  # primary, secondary, accent, background, text


@dataclass
class LayoutHint:
    """레이아웃 힌트"""
    type: str  # grid, list, centered, asymmetric
    columns: Optional[int] = None
    rows: Optional[int] = None
    has_header: bool = False
    has_sidebar: bool = False


@dataclass
class StyleHint:
    """스타일 힌트"""
    border_radius: str = "0px"
    has_shadows: bool = False
    has_gradients: bool = False
    mood: str = "neutral"  # modern, classic, playful, minimal


@dataclass
class ImageAnalysis:
    """이미지 분석 결과"""
    colors: List[ExtractedColor]
    layout: LayoutHint
    style: StyleHint
    dominant_hue: str  # warm, cool, neutral
    contrast_level: str  # high, medium, low


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGB를 HEX로 변환"""
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """HEX를 RGB로 변환"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_luminance(r: int, g: int, b: int) -> float:
    """상대 휘도 계산"""
    return 0.299 * r + 0.587 * g + 0.114 * b


def get_saturation(r: int, g: int, b: int) -> float:
    """채도 계산"""
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return s


def get_hue(r: int, g: int, b: int) -> float:
    """색조(Hue) 계산 (0-360)"""
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return h * 360


def classify_hue_temperature(colors: List[ExtractedColor]) -> str:
    """색상 온도 분류"""
    warm_count = 0
    cool_count = 0

    for color in colors:
        hue = get_hue(*color.rgb)
        sat = get_saturation(*color.rgb)

        if sat < 0.1:  # 무채색은 제외
            continue

        # 따뜻한 색: 0-60 (빨강~노랑) 또는 300-360 (마젠타)
        if hue < 60 or hue > 300:
            warm_count += color.percentage
        # 차가운 색: 180-300 (청록~보라)
        elif 180 <= hue <= 300:
            cool_count += color.percentage

    if warm_count > cool_count * 1.5:
        return "warm"
    elif cool_count > warm_count * 1.5:
        return "cool"
    return "neutral"


def extract_colors_kmeans(image: Image.Image, n_colors: int = 8) -> List[ExtractedColor]:
    """K-means로 주요 색상 추출"""
    # 이미지 리사이즈
    img = image.copy()
    img.thumbnail((200, 200))
    img = img.convert('RGB')

    # numpy 배열로 변환
    pixels = np.array(img).reshape(-1, 3)

    # K-means 클러스터링
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    kmeans.fit(pixels)

    # 클러스터 비중 계산
    labels, counts = np.unique(kmeans.labels_, return_counts=True)
    total_pixels = len(pixels)

    colors = []
    for i, center in enumerate(kmeans.cluster_centers_):
        r, g, b = int(center[0]), int(center[1]), int(center[2])
        percentage = counts[i] / total_pixels if i < len(counts) else 0

        colors.append(ExtractedColor(
            hex=rgb_to_hex(r, g, b),
            rgb=(r, g, b),
            percentage=round(percentage * 100, 1)
        ))

    # 비중 순으로 정렬
    colors.sort(key=lambda c: c.percentage, reverse=True)
    return colors


def assign_color_roles(colors: List[ExtractedColor]) -> List[ExtractedColor]:
    """색상에 역할 부여"""
    if not colors:
        return colors

    # 복사본 생성
    result = [ExtractedColor(**asdict(c)) for c in colors]

    # 가장 밝은 색 → background
    brightest = max(result, key=lambda c: get_luminance(*c.rgb))
    brightest.role = "background"

    # 가장 어두운 색 → text
    darkest = min(result, key=lambda c: get_luminance(*c.rgb))
    if darkest != brightest:
        darkest.role = "text"

    # 가장 채도가 높은 색 → primary (background, text 제외)
    saturated = [c for c in result if c.role is None]
    if saturated:
        most_saturated = max(saturated, key=lambda c: get_saturation(*c.rgb))
        most_saturated.role = "primary"

        # 두 번째로 채도가 높은 색 → accent
        remaining = [c for c in saturated if c.role is None]
        if remaining:
            second_saturated = max(remaining, key=lambda c: get_saturation(*c.rgb))
            second_saturated.role = "accent"

    # 나머지 → secondary
    for c in result:
        if c.role is None:
            c.role = "secondary"
            break

    return result


def analyze_layout(image: Image.Image) -> LayoutHint:
    """레이아웃 패턴 분석 (엣지 감지 기반)"""
    # 그레이스케일 변환
    gray = image.convert('L')
    gray = gray.resize((100, 100))

    # 엣지 감지
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_array = np.array(edges)

    # 수평/수직 엣지 분석
    h_edges = np.sum(edge_array, axis=1)  # 행별 합 (수평 라인)
    v_edges = np.sum(edge_array, axis=0)  # 열별 합 (수직 라인)

    # 강한 수평 라인 개수 (헤더 감지)
    h_threshold = np.percentile(h_edges, 90)
    strong_h_lines = np.sum(h_edges > h_threshold)

    # 강한 수직 라인 개수 (그리드/컬럼 감지)
    v_threshold = np.percentile(v_edges, 90)
    strong_v_lines = np.sum(v_edges > v_threshold)

    # 레이아웃 타입 추정
    has_header = strong_h_lines > 5 and h_edges[:20].max() > h_threshold

    if strong_v_lines > 15:
        layout_type = "grid"
        columns = min(strong_v_lines // 5, 6)
    elif strong_h_lines > 10:
        layout_type = "list"
        columns = 1
    else:
        layout_type = "centered"
        columns = None

    return LayoutHint(
        type=layout_type,
        columns=columns,
        has_header=has_header
    )


def analyze_style(image: Image.Image, colors: List[ExtractedColor]) -> StyleHint:
    """스타일 힌트 분석"""

    # 그라데이션 감지 (인접 픽셀 색상 변화)
    img = image.resize((50, 50)).convert('RGB')
    pixels = np.array(img)

    # 인접 픽셀 차이 계산
    h_diff = np.abs(np.diff(pixels, axis=1)).mean()
    v_diff = np.abs(np.diff(pixels, axis=0)).mean()
    has_gradients = h_diff > 5 or v_diff > 5

    # 대비 분석
    if colors:
        luminances = [get_luminance(*c.rgb) for c in colors[:4]]
        contrast_range = max(luminances) - min(luminances)
    else:
        contrast_range = 0

    # 분위기 추정
    if contrast_range > 150:
        mood = "modern"
    elif contrast_range < 50:
        mood = "minimal"
    else:
        mood = "classic"

    # 채도 기반 분위기 보정
    avg_saturation = np.mean([get_saturation(*c.rgb) for c in colors[:4]]) if colors else 0
    if avg_saturation > 0.6:
        mood = "playful"

    return StyleHint(
        border_radius="16px" if mood in ["modern", "playful"] else "4px",
        has_shadows=mood in ["modern", "classic"],
        has_gradients=has_gradients,
        mood=mood
    )


def calculate_contrast_level(colors: List[ExtractedColor]) -> str:
    """대비 수준 계산"""
    if len(colors) < 2:
        return "medium"

    luminances = sorted([get_luminance(*c.rgb) for c in colors])
    contrast = luminances[-1] - luminances[0]

    if contrast > 180:
        return "high"
    elif contrast > 100:
        return "medium"
    return "low"


def analyze_image(image_path: Path) -> ImageAnalysis:
    """이미지 전체 분석"""
    if not HAS_DEPS:
        raise ImportError("필요한 패키지: pip install Pillow numpy scikit-learn")

    img = Image.open(image_path)

    # 색상 추출
    colors = extract_colors_kmeans(img)
    colors = assign_color_roles(colors)

    # 레이아웃 분석
    layout = analyze_layout(img)

    # 스타일 분석
    style = analyze_style(img, colors)

    # 색조 분류
    dominant_hue = classify_hue_temperature(colors)

    # 대비 수준
    contrast_level = calculate_contrast_level(colors)

    return ImageAnalysis(
        colors=colors,
        layout=layout,
        style=style,
        dominant_hue=dominant_hue,
        contrast_level=contrast_level
    )


def analysis_to_theme(analysis: ImageAnalysis, name: str) -> Dict:
    """분석 결과를 테마 형식으로 변환"""

    # 색상 역할별 매핑
    color_map = {}
    for color in analysis.colors:
        if color.role and color.role not in color_map:
            color_map[color.role] = color.hex

    return {
        "id": name.lower().replace(" ", "-").replace("_", "-"),
        "name": f"{name} 테마",
        "colors": {
            "primary": color_map.get("primary", "#1a5f4a"),
            "secondary": color_map.get("secondary", "#2d7a5e"),
            "accent": color_map.get("accent", "#4a9d7f"),
            "background": color_map.get("background", "#ffffff"),
            "surface": color_map.get("secondary", "#f5f9f7"),
            "text": color_map.get("text", "#1a1a1a"),
            "muted": "#6b7c74",
        },
        "style_hints": {
            "border_radius": analysis.style.border_radius,
            "shadow": "0 4px 12px rgba(0,0,0,0.08)" if analysis.style.has_shadows else "none",
            "mood": analysis.style.mood,
        },
        "analysis": {
            "dominant_hue": analysis.dominant_hue,
            "contrast_level": analysis.contrast_level,
            "layout_type": analysis.layout.type,
        }
    }


def dataclass_to_dict(obj) -> Any:
    """dataclass를 dict로 변환"""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: dataclass_to_dict(v) for k, v in asdict(obj).items()}
    elif isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, tuple):
        return list(obj)
    else:
        return obj


def main():
    parser = argparse.ArgumentParser(
        description="이미지에서 디자인 스타일 추출"
    )
    parser.add_argument("input", help="입력 이미지 파일")
    parser.add_argument("--output", "-o", help="출력 파일 (YAML 또는 JSON)")
    parser.add_argument("--analyze-only", action="store_true", help="분석 결과만 출력")
    parser.add_argument("--name", help="테마 이름 (기본: 파일명)")
    parser.add_argument("--colors", type=int, default=8, help="추출할 색상 개수")

    args = parser.parse_args()

    if not HAS_DEPS:
        print("Error: 필요한 패키지를 설치하세요:")
        print("  pip install Pillow numpy scikit-learn")
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: 파일을 찾을 수 없습니다: {args.input}")
        sys.exit(1)

    try:
        analysis = analyze_image(input_path)

        if args.analyze_only:
            print(json.dumps(dataclass_to_dict(analysis), indent=2, ensure_ascii=False))
        else:
            name = args.name or input_path.stem
            theme = analysis_to_theme(analysis, name)

            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if output_path.suffix in ['.yaml', '.yml'] and HAS_YAML:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        yaml.dump(theme, f, allow_unicode=True, default_flow_style=False)
                else:
                    json_path = output_path.with_suffix('.json') if not output_path.suffix == '.json' else output_path
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(theme, f, indent=2, ensure_ascii=False)

                print(f"저장됨: {output_path}")
            else:
                print(json.dumps(theme, indent=2, ensure_ascii=False))

            # 요약 출력
            print(f"\n분석 결과:")
            print(f"  분위기: {analysis.style.mood}")
            print(f"  색조: {analysis.dominant_hue}")
            print(f"  대비: {analysis.contrast_level}")
            print(f"  레이아웃: {analysis.layout.type}")
            print(f"  주요 색상: {', '.join(c.hex for c in analysis.colors[:4])}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
