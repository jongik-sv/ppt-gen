#!/usr/bin/env python3
"""
Image Vectorizer - 이미지를 SVG로 변환

래스터 이미지(PNG, JPG 등)를 벡터 그래픽(SVG)으로 변환합니다.
VTracer 라이브러리를 사용하여 고품질 벡터화를 수행합니다.

Usage:
    python image-vectorizer.py <image> --output <output.svg>
    python image-vectorizer.py icon.png --preset icon
    python image-vectorizer.py diagram.png --preset diagram --output result.svg

Examples:
    # 기본 변환 (자동 프리셋)
    python image-vectorizer.py icon.png --output icon.svg

    # 아이콘 프리셋 (최고 품질)
    python image-vectorizer.py logo.png --preset icon --output logo.svg

    # 다이어그램 프리셋
    python image-vectorizer.py flowchart.png --preset diagram

    # 텍스트 제거 후 변환
    python image-vectorizer.py diagram.png --remove-text --output clean.svg

    # 매끄러운 곡선 (smooth 프리셋)
    python image-vectorizer.py logo.png --preset smooth

    # 배치 변환 (디렉토리)
    python image-vectorizer.py ./images/ --output ./svgs/ --preset logo

    # 커스텀 옵션
    python image-vectorizer.py image.png --color-precision 8 --corner-threshold 45

Dependencies:
    pip install vtracer Pillow
    pip install opencv-python easyocr  # 텍스트 제거용 (선택)
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import vtracer
    HAS_VTRACER = True
except ImportError:
    HAS_VTRACER = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False


def remove_text_from_image(
    image_path: str,
    output_path: str = None,
    return_placeholders: bool = True
) -> Dict[str, Any]:
    """
    이미지에서 텍스트를 감지하고 인페인팅으로 제거
    텍스트 위치를 플레이스홀더로 반환

    Args:
        image_path: 입력 이미지 경로
        output_path: 출력 이미지 경로 (None이면 자동 생성)
        return_placeholders: True면 텍스트 위치 정보 반환

    Returns:
        {
            'image_path': 텍스트 제거된 이미지 경로,
            'placeholders': [
                {
                    'type': 'text',
                    'bbox': [x1, y1, x2, y2],  # 픽셀 좌표
                    'bbox_percent': [x%, y%, w%, h%],  # 퍼센트 좌표
                    'content': '원본 텍스트',
                    'confidence': 0.95
                },
                ...
            ]
        }
    """
    if not HAS_CV2:
        raise ImportError("opencv-python이 필요합니다. pip install opencv-python")
    if not HAS_EASYOCR:
        raise ImportError("easyocr가 필요합니다. pip install easyocr")

    # 이미지 로드
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")

    img_height, img_width = img.shape[:2]

    # EasyOCR로 텍스트 감지
    print("  텍스트 감지 중 (EasyOCR)...")
    reader = easyocr.Reader(['en', 'ko'], gpu=False, verbose=False)
    results = reader.readtext(image_path)

    # 마스크 생성 및 플레이스홀더 수집
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    placeholders = []

    for (bbox, text, prob) in results:
        if prob > 0.3:  # 신뢰도 30% 이상
            # 바운딩 박스 좌표 (4 포인트 → 사각형)
            pts = np.array(bbox, dtype=np.int32)
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            x1, y1 = min(x_coords), min(y_coords)
            x2, y2 = max(x_coords), max(y_coords)

            # 플레이스홀더 정보 저장
            placeholders.append({
                'type': 'text',
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'bbox_percent': {
                    'x': round(x1 / img_width * 100, 2),
                    'y': round(y1 / img_height * 100, 2),
                    'width': round((x2 - x1) / img_width * 100, 2),
                    'height': round((y2 - y1) / img_height * 100, 2),
                },
                'content': text,
                'confidence': round(prob, 3),
            })

            # 마스크에 텍스트 영역 채우기
            cv2.fillPoly(mask, [pts], 255)

    # 마스크 확장 (텍스트 주변 여백 포함)
    if np.any(mask):
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)

    # 인페인팅 (텍스트 영역 채우기)
    if np.any(mask):
        print(f"  {len(placeholders)}개 텍스트 영역 인페인팅...")
        result = cv2.inpaint(img, mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)
    else:
        result = img
        print("  경고: 텍스트가 감지되지 않았습니다.")

    # 출력 경로 설정
    if output_path is None:
        p = Path(image_path)
        output_path = str(p.parent / f"{p.stem}_notext{p.suffix}")

    cv2.imwrite(output_path, result)

    return {
        'image_path': output_path,
        'original_size': {'width': img_width, 'height': img_height},
        'placeholders': placeholders,
    }


def detect_icons_by_color(image_path: str, min_size: int = 20, max_size: int = 100) -> list:
    """
    색상 기반으로 아이콘 영역 감지 (흰색/단색 아이콘)

    Args:
        image_path: 입력 이미지 경로
        min_size: 최소 아이콘 크기 (픽셀)
        max_size: 최대 아이콘 크기 (픽셀)

    Returns:
        [{'bbox': [x1, y1, x2, y2], 'type': 'icon'}, ...]
    """
    if not HAS_CV2:
        return []

    img = cv2.imread(image_path)
    if img is None:
        return []

    img_height, img_width = img.shape[:2]

    # 흰색 영역 감지 (아이콘이 보통 흰색)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 흰색/밝은색 마스크
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    white_mask = cv2.inRange(hsv, lower_white, upper_white)

    # 작은 노이즈 제거
    kernel = np.ones((3, 3), np.uint8)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)

    # 컨투어 찾기
    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    icons = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)

        # 크기 필터
        if min_size <= w <= max_size and min_size <= h <= max_size:
            # 정사각형에 가까운 것만 (아이콘 특성)
            aspect_ratio = w / h if h > 0 else 0
            if 0.5 <= aspect_ratio <= 2.0 and area > min_size * min_size * 0.3:
                icons.append({
                    'type': 'icon',
                    'bbox': [x, y, x + w, y + h],
                    'bbox_percent': {
                        'x': round(x / img_width * 100, 2),
                        'y': round(y / img_height * 100, 2),
                        'width': round(w / img_width * 100, 2),
                        'height': round(h / img_height * 100, 2),
                    },
                    'estimated_size': max(w, h),
                })

    return icons


def remove_icons_from_image(
    image_path: str,
    output_path: str = None,
    min_size: int = 15,
    max_size: int = 150,
    min_segment_area: int = 5000,
    return_placeholders: bool = True
) -> Dict[str, Any]:
    """
    이미지에서 컬러 세그먼트 내부의 흰색 아이콘을 감지하고 인페인팅으로 제거
    아이콘 위치를 플레이스홀더로 반환

    Args:
        image_path: 입력 이미지 경로
        output_path: 출력 이미지 경로 (None이면 자동 생성)
        min_size: 최소 아이콘 크기 (픽셀)
        max_size: 최대 아이콘 크기 (픽셀)
        min_segment_area: 최소 세그먼트 면적 (픽셀²)
        return_placeholders: True면 아이콘 위치 정보 반환

    Returns:
        {
            'image_path': 아이콘 제거된 이미지 경로,
            'placeholders': [{type, bbox, bbox_percent}, ...]
        }
    """
    if not HAS_CV2:
        print("[경고] opencv-python이 설치되지 않음. 아이콘 제거 불가")
        return {'image_path': image_path, 'placeholders': []}

    img = cv2.imread(image_path)
    if img is None:
        return {'image_path': image_path, 'placeholders': []}

    img_height, img_width = img.shape[:2]
    print(f"  아이콘 감지 중...")

    # HSV로 변환
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 1. 컬러(채도 있는) 영역 마스크 생성
    lower_colored = np.array([0, 60, 80])
    upper_colored = np.array([180, 255, 255])
    colored_mask = cv2.inRange(hsv, lower_colored, upper_colored)

    # 2. 컬러 영역의 컨투어 찾기 (세그먼트)
    contours, _ = cv2.findContours(colored_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # 큰 컬러 영역들만 필터링 (세그먼트)
    segments = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_segment_area:
            x, y, w, h = cv2.boundingRect(cnt)
            segments.append({'contour': cnt, 'bbox': (x, y, w, h), 'area': area})

    print(f"  컬러 세그먼트: {len(segments)}개")

    # 3. 각 세그먼트 내부에서 흰색 아이콘 찾기
    inpaint_mask = np.zeros((img_height, img_width), dtype=np.uint8)
    placeholders = []
    seen_positions = set()  # 중복 방지

    for seg in segments:
        x, y, w, h = seg['bbox']

        # 세그먼트 영역 자르기
        roi_hsv = hsv[y:y+h, x:x+w]

        # 세그먼트 마스크 생성
        seg_mask = np.zeros((h, w), dtype=np.uint8)
        shifted_cnt = seg['contour'] - [x, y]
        cv2.drawContours(seg_mask, [shifted_cnt], -1, 255, -1)

        # 흰색 영역 찾기
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 50, 255])
        white_in_roi = cv2.inRange(roi_hsv, lower_white, upper_white)
        white_in_seg = cv2.bitwise_and(white_in_roi, seg_mask)

        # 흰색 컨투어 찾기
        white_cnts, _ = cv2.findContours(white_in_seg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for wc in white_cnts:
            wa = cv2.contourArea(wc)
            wx, wy, ww, wh = cv2.boundingRect(wc)

            # 크기 필터
            if min_size <= ww <= max_size and min_size <= wh <= max_size and wa > min_size * min_size * 0.3:
                # 전역 좌표로 변환
                gx, gy = wx + x, wy + y

                # 중복 체크 (근처에 이미 감지된 아이콘이 있는지)
                pos_key = (gx // 20, gy // 20)
                if pos_key in seen_positions:
                    continue
                seen_positions.add(pos_key)

                # 인페인팅 마스크에 추가
                padding = 5
                x1 = max(0, gx - padding)
                y1 = max(0, gy - padding)
                x2 = min(img_width, gx + ww + padding)
                y2 = min(img_height, gy + wh + padding)
                cv2.rectangle(inpaint_mask, (x1, y1), (x2, y2), 255, -1)

                placeholders.append({
                    'type': 'icon',
                    'bbox': [gx, gy, gx + ww, gy + wh],
                    'bbox_percent': {
                        'x': round(gx / img_width * 100, 2),
                        'y': round(gy / img_height * 100, 2),
                        'width': round(ww / img_width * 100, 2),
                        'height': round(wh / img_height * 100, 2),
                    },
                    'estimated_size': max(ww, wh),
                })

    print(f"  아이콘 {len(placeholders)}개 감지/제거됨")

    if len(placeholders) == 0:
        return {'image_path': image_path, 'placeholders': []}

    # 인페인팅 (NS 알고리즘 - 더 부드러운 결과)
    result = cv2.inpaint(img, inpaint_mask, inpaintRadius=10, flags=cv2.INPAINT_NS)

    # 저장
    if output_path is None:
        base = Path(image_path).stem
        output_path = str(Path(image_path).parent / f"{base}_noicons.png")

    cv2.imwrite(output_path, result)
    print(f"  임시 파일: {Path(output_path).name}")

    return {
        'image_path': output_path,
        'placeholders': placeholders,
    }


# 품질 우선 프리셋 정의
PRESETS: Dict[str, Dict[str, Any]] = {
    'icon': {
        # 아이콘: 최고 품질, 세밀한 디테일 보존
        'colormode': 'color',
        'hierarchical': 'stacked',
        'mode': 'spline',
        'filter_speckle': 2,          # 노이즈 최소 제거
        'color_precision': 8,         # 최대 색상 정밀도
        'layer_difference': 16,
        'corner_threshold': 60,       # 코너 보존
        'length_threshold': 2.0,      # 짧은 세그먼트도 유지
        'max_iterations': 15,         # 곡선 피팅 정밀도 ↑
        'splice_threshold': 45,
        'path_precision': 4,          # 좌표 정밀도 ↑
    },
    'logo': {
        # 로고: 높은 품질 + 선명한 엣지
        'colormode': 'color',
        'hierarchical': 'stacked',
        'mode': 'spline',
        'filter_speckle': 1,          # 노이즈 거의 안 제거
        'color_precision': 8,
        'layer_difference': 6,        # 레이어 분리 정밀
        'corner_threshold': 45,       # 날카로운 코너 보존
        'length_threshold': 2.0,
        'max_iterations': 15,
        'splice_threshold': 45,
        'path_precision': 4,
    },
    'diagram': {
        # 다이어그램: 직선/곡선 혼합
        'colormode': 'color',
        'hierarchical': 'stacked',
        'mode': 'spline',             # 부드러운 곡선
        'filter_speckle': 3,
        'color_precision': 6,
        'layer_difference': 16,
        'corner_threshold': 75,       # 직각 코너 보존
        'length_threshold': 3.0,
        'max_iterations': 10,
        'splice_threshold': 45,
        'path_precision': 3,
    },
    'chart': {
        # 차트: 정확한 형태 보존, 직각 우선
        'colormode': 'color',
        'hierarchical': 'stacked',
        'mode': 'polygon',            # 다각형 모드
        'filter_speckle': 2,
        'color_precision': 6,
        'layer_difference': 16,
        'corner_threshold': 90,       # 직각 최대 보존
        'length_threshold': 4.0,
        'max_iterations': 10,
        'splice_threshold': 45,
        'path_precision': 3,
    },
    'default': {
        # 기본: 균형 잡힌 설정
        'colormode': 'color',
        'hierarchical': 'stacked',
        'mode': 'spline',
        'filter_speckle': 4,
        'color_precision': 6,
        'layer_difference': 16,
        'corner_threshold': 60,
        'length_threshold': 4.0,
        'max_iterations': 10,
        'splice_threshold': 45,
        'path_precision': 3,
    },
    'smooth': {
        # 매끄러운 곡선: 부드러운 베지어 곡선 우선
        'colormode': 'color',
        'hierarchical': 'stacked',
        'mode': 'spline',             # 스플라인 모드 필수
        'filter_speckle': 4,          # 노이즈 제거
        'color_precision': 6,
        'layer_difference': 16,
        'corner_threshold': 120,      # 높음 = 더 적은 코너, 더 부드러운 곡선
        'length_threshold': 6.0,      # 짧은 세그먼트 병합
        'max_iterations': 20,         # 더 많은 반복 = 더 정밀한 피팅
        'splice_threshold': 90,       # 경로 연결 부드럽게
        'path_precision': 4,          # 좌표 정밀도
    },
    'ultra_smooth': {
        # 초매끄러운: 최대한 부드러운 곡선 (디테일 손실 가능)
        'colormode': 'color',
        'hierarchical': 'stacked',
        'mode': 'spline',
        'filter_speckle': 8,          # 더 많은 노이즈 제거
        'color_precision': 4,         # 색상 단순화
        'layer_difference': 24,
        'corner_threshold': 150,      # 거의 코너 없음
        'length_threshold': 10.0,     # 긴 세그먼트만
        'max_iterations': 25,         # 최대 반복
        'splice_threshold': 120,      # 최대 병합
        'path_precision': 3,
    },
}


def get_image_info(image_path: str) -> Dict[str, Any]:
    """이미지 정보 추출"""
    if not HAS_PIL:
        return {'width': 0, 'height': 0, 'format': 'unknown'}

    try:
        with Image.open(image_path) as img:
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
            }
    except Exception as e:
        return {'error': str(e)}


def detect_preset(image_path: str) -> str:
    """이미지 특성에 따라 자동 프리셋 선택"""
    info = get_image_info(image_path)

    if 'error' in info:
        return 'default'

    width = info.get('width', 0)
    height = info.get('height', 0)

    # 작은 이미지 (아이콘 가능성)
    if width <= 256 and height <= 256:
        return 'icon'

    # 정사각형에 가까운 이미지 (로고 가능성)
    aspect_ratio = width / height if height > 0 else 1
    if 0.8 <= aspect_ratio <= 1.2 and width <= 512:
        return 'logo'

    # 넓은 이미지 (다이어그램/차트 가능성)
    if aspect_ratio > 1.5:
        return 'diagram'

    return 'default'


def vectorize_image(
    input_path: str,
    output_path: Optional[str] = None,
    preset: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> str:
    """
    이미지를 SVG로 변환

    Args:
        input_path: 입력 이미지 경로
        output_path: 출력 SVG 경로 (None이면 SVG 문자열만 반환)
        preset: 프리셋 이름 (icon, logo, diagram, chart, default)
        options: 커스텀 옵션 (프리셋 위에 덮어쓰기)

    Returns:
        SVG 문자열
    """
    if not HAS_VTRACER:
        raise ImportError("vtracer가 필요합니다. pip install vtracer")

    # 프리셋 결정
    if preset is None:
        preset = detect_preset(input_path)

    # 기본 옵션 로드
    base_options = PRESETS.get(preset, PRESETS['default']).copy()

    # 커스텀 옵션 적용
    if options:
        base_options.update(options)

    # 출력 경로 설정
    if output_path is None:
        output_path = str(Path(input_path).with_suffix('.svg'))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # VTracer 실행 (out_path 필수)
    vtracer.convert_image_to_svg_py(
        input_path,
        output_path,
        colormode=base_options.get('colormode', 'color'),
        hierarchical=base_options.get('hierarchical', 'stacked'),
        mode=base_options.get('mode', 'spline'),
        filter_speckle=base_options.get('filter_speckle', 4),
        color_precision=base_options.get('color_precision', 6),
        layer_difference=base_options.get('layer_difference', 16),
        corner_threshold=base_options.get('corner_threshold', 60),
        length_threshold=base_options.get('length_threshold', 4.0),
        max_iterations=base_options.get('max_iterations', 10),
        splice_threshold=base_options.get('splice_threshold', 45),
        path_precision=base_options.get('path_precision', 3),
    )

    # SVG 파일 읽기
    with open(output_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()

    return svg_str


def vectorize_directory(
    input_dir: str,
    output_dir: str,
    preset: Optional[str] = None,
    extensions: tuple = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
) -> Dict[str, str]:
    """
    디렉토리 내 모든 이미지를 SVG로 변환

    Args:
        input_dir: 입력 디렉토리
        output_dir: 출력 디렉토리
        preset: 프리셋 이름
        extensions: 처리할 확장자 목록

    Returns:
        {입력파일: 출력파일} 딕셔너리
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}

    for img_file in input_path.iterdir():
        if img_file.suffix.lower() in extensions:
            svg_file = output_path / (img_file.stem + '.svg')
            try:
                vectorize_image(
                    str(img_file),
                    str(svg_file),
                    preset=preset
                )
                results[str(img_file)] = str(svg_file)
            except Exception as e:
                results[str(img_file)] = f"Error: {e}"

    return results


def get_svg_stats(svg_str: str) -> Dict[str, Any]:
    """SVG 통계 정보 추출"""
    path_count = svg_str.count('<path')
    circle_count = svg_str.count('<circle')
    rect_count = svg_str.count('<rect')
    size_bytes = len(svg_str.encode('utf-8'))

    return {
        'size_bytes': size_bytes,
        'size_kb': round(size_bytes / 1024, 2),
        'path_count': path_count,
        'circle_count': circle_count,
        'rect_count': rect_count,
        'total_elements': path_count + circle_count + rect_count,
    }


def cmd_vectorize(args) -> int:
    """벡터화 실행"""
    input_path = args.input
    output_path = args.output
    preset = args.preset
    remove_text = getattr(args, 'remove_text', False)
    detect_icons = getattr(args, 'detect_icons', False)
    remove_icons = getattr(args, 'remove_icons', False)
    icon_min_size = getattr(args, 'icon_min_size', 20)
    icon_max_size = getattr(args, 'icon_max_size', 300)

    # 입력 확인
    if not Path(input_path).exists():
        print(f"Error: 파일/디렉토리를 찾을 수 없습니다 - {input_path}")
        return 1

    # 커스텀 옵션 수집
    custom_options = {}
    if args.color_precision is not None:
        custom_options['color_precision'] = args.color_precision
    if args.corner_threshold is not None:
        custom_options['corner_threshold'] = args.corner_threshold
    if args.filter_speckle is not None:
        custom_options['filter_speckle'] = args.filter_speckle
    if args.mode is not None:
        custom_options['mode'] = args.mode

    # 디렉토리 처리
    if Path(input_path).is_dir():
        if not output_path:
            output_path = str(Path(input_path) / 'svg')

        print(f"디렉토리 변환: {input_path}")
        print(f"출력 디렉토리: {output_path}")
        print(f"프리셋: {preset or 'auto'}")
        print()

        results = vectorize_directory(input_path, output_path, preset)

        success = sum(1 for v in results.values() if not v.startswith('Error'))
        failed = len(results) - success

        print(f"\n결과: {success}개 성공, {failed}개 실패")
        for src, dst in results.items():
            status = "✓" if not dst.startswith('Error') else "✗"
            print(f"  {status} {Path(src).name} → {Path(dst).name if not dst.startswith('Error') else dst}")

        return 0 if failed == 0 else 1

    # 단일 파일 처리
    if not output_path:
        output_path = str(Path(input_path).with_suffix('.svg'))

    # 자동 프리셋 감지
    detected_preset = preset or detect_preset(input_path)

    print(f"이미지 변환: {input_path}")
    print(f"출력: {output_path}")
    print(f"프리셋: {detected_preset}" + (" (자동)" if not preset else ""))

    # 이미지 정보
    info = get_image_info(input_path)
    if 'error' not in info:
        print(f"크기: {info['width']}x{info['height']} ({info.get('format', 'unknown')})")
    print()

    # 플레이스홀더 수집
    all_placeholders = []
    actual_input = input_path

    # 텍스트 제거 옵션
    if remove_text:
        print("[전처리] 텍스트 제거 중...")
        try:
            result = remove_text_from_image(input_path)
            actual_input = result['image_path']
            all_placeholders.extend(result['placeholders'])
            print(f"  텍스트 {len(result['placeholders'])}개 감지/제거됨")
            print(f"  임시 파일: {actual_input}")
        except ImportError as e:
            print(f"  경고: {e}")
            print("  텍스트 제거 생략 (opencv-python, easyocr 필요)")
        except Exception as e:
            print(f"  경고: 텍스트 제거 실패 - {e}")

    # 아이콘 감지 옵션 (감지만)
    if detect_icons and not remove_icons:
        print("[전처리] 아이콘 감지 중...")
        try:
            icons = detect_icons_by_color(input_path)
            all_placeholders.extend(icons)
            print(f"  아이콘 {len(icons)}개 감지됨")
        except Exception as e:
            print(f"  경고: 아이콘 감지 실패 - {e}")

    # 아이콘 제거 옵션 (감지 + 제거)
    if remove_icons:
        print(f"[전처리] 아이콘 제거 중... (크기: {icon_min_size}-{icon_max_size}px)")
        try:
            result = remove_icons_from_image(actual_input, min_size=icon_min_size, max_size=icon_max_size)
            actual_input = result['image_path']
            all_placeholders.extend(result['placeholders'])
            print(f"  아이콘 {len(result['placeholders'])}개 감지/제거됨")
            if result['placeholders']:
                print(f"  임시 파일: {actual_input}")
        except ImportError as e:
            print(f"  경고: {e}")
            print("  아이콘 제거 생략 (opencv-python 필요)")
        except Exception as e:
            print(f"  경고: 아이콘 제거 실패 - {e}")

    # 변환 실행
    step = 1
    total_steps = 2 + (1 if all_placeholders else 0)

    print(f"[{step}/{total_steps}] 벡터화 중...")
    try:
        svg_str = vectorize_image(
            actual_input,
            output_path,
            preset=detected_preset,
            options=custom_options if custom_options else None
        )
    except Exception as e:
        print(f"Error: 변환 실패 - {e}")
        return 1

    step += 1
    print(f"[{step}/{total_steps}] 완료!")
    stats = get_svg_stats(svg_str)
    print(f"  SVG 크기: {stats['size_kb']} KB")
    print(f"  경로 수: {stats['path_count']}")
    print(f"  총 요소: {stats['total_elements']}")

    # 플레이스홀더 YAML 출력
    if all_placeholders:
        step += 1
        yaml_path = str(Path(output_path).with_suffix('.placeholders.yaml'))
        print(f"[{step}/{total_steps}] 플레이스홀더 저장 중...")

        import yaml
        placeholder_data = {
            'source_image': input_path,
            'svg_output': output_path,
            'original_size': info if 'error' not in info else {},
            'placeholders': all_placeholders,
        }

        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(placeholder_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        print(f"  플레이스홀더: {len(all_placeholders)}개")
        print(f"  저장됨: {yaml_path}")

        # 플레이스홀더 미리보기
        print("\n플레이스홀더 미리보기:")
        for i, ph in enumerate(all_placeholders[:5]):  # 최대 5개만 표시
            bbox = ph['bbox_percent']
            content = ph.get('content', '')[:30] if ph.get('content') else ''
            print(f"  [{i+1}] {ph['type']}: ({bbox['x']:.1f}%, {bbox['y']:.1f}%) "
                  f"{bbox['width']:.1f}x{bbox['height']:.1f}% "
                  f"{'- ' + content if content else ''}")
        if len(all_placeholders) > 5:
            print(f"  ... 외 {len(all_placeholders) - 5}개")

    print()
    print(f"저장됨: {output_path}")

    # 임시 파일 정리
    if remove_text and actual_input != input_path:
        try:
            Path(actual_input).unlink()
            print(f"임시 파일 삭제됨: {actual_input}")
        except:
            pass

    return 0


def cmd_presets(args) -> int:
    """프리셋 목록 출력"""
    print("사용 가능한 프리셋:\n")

    for name, options in PRESETS.items():
        print(f"  {name}:")
        print(f"    mode: {options.get('mode', 'spline')}")
        print(f"    color_precision: {options.get('color_precision', 6)}")
        print(f"    corner_threshold: {options.get('corner_threshold', 60)}")
        print(f"    filter_speckle: {options.get('filter_speckle', 4)}")
        print()

    return 0


def main():
    if not HAS_VTRACER:
        print("Error: vtracer가 필요합니다.")
        print("  pip install vtracer")
        print()
        print("VTracer는 Rust 기반으로 빠르고 고품질 벡터화를 제공합니다.")
        return 1

    parser = argparse.ArgumentParser(
        description='이미지를 SVG로 변환 (VTracer 기반)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 기본 변환 (자동 프리셋)
  python image-vectorizer.py icon.png

  # 아이콘 프리셋
  python image-vectorizer.py logo.png --preset icon --output logo.svg

  # 다이어그램 프리셋
  python image-vectorizer.py flowchart.png --preset diagram

  # 배치 변환
  python image-vectorizer.py ./images/ --output ./svgs/

  # 프리셋 목록
  python image-vectorizer.py --list-presets
        """
    )

    parser.add_argument('input', nargs='?', help='입력 이미지 또는 디렉토리')
    parser.add_argument('--output', '-o', help='출력 SVG 파일 또는 디렉토리')
    parser.add_argument('--preset', '-p',
                        choices=list(PRESETS.keys()),
                        help='프리셋 (icon, logo, diagram, chart, default)')
    parser.add_argument('--list-presets', action='store_true',
                        help='프리셋 목록 출력')

    # 전처리 옵션
    preprocess = parser.add_argument_group('전처리 옵션')
    preprocess.add_argument('--remove-text', action='store_true',
                            help='텍스트 감지 및 제거 (위치 정보 YAML 출력)')
    preprocess.add_argument('--remove-icons', action='store_true',
                            help='흰색 아이콘 감지 및 제거 (위치 정보 YAML 출력)')
    preprocess.add_argument('--icon-min-size', type=int, default=20,
                            help='아이콘 최소 크기 (픽셀, 기본값: 20)')
    preprocess.add_argument('--icon-max-size', type=int, default=300,
                            help='아이콘 최대 크기 (픽셀, 기본값: 300)')
    preprocess.add_argument('--detect-icons', action='store_true',
                            help='아이콘 영역 감지 (위치 정보 YAML 출력)')

    # 고급 옵션
    advanced = parser.add_argument_group('고급 옵션')
    advanced.add_argument('--color-precision', type=int, choices=range(1, 9),
                          help='색상 정밀도 (1-8, 높을수록 정밀)')
    advanced.add_argument('--corner-threshold', type=int, choices=range(0, 181),
                          help='코너 감지 임계값 (0-180, 높을수록 둥글게)')
    advanced.add_argument('--filter-speckle', type=int,
                          help='노이즈 제거 크기 (작을수록 디테일 보존)')
    advanced.add_argument('--mode', choices=['spline', 'polygon', 'none'],
                          help='경로 모드 (spline: 곡선, polygon: 직선)')

    args = parser.parse_args()

    if args.list_presets:
        return cmd_presets(args)

    if not args.input:
        parser.print_help()
        return 0

    return cmd_vectorize(args)


if __name__ == '__main__':
    sys.exit(main())
