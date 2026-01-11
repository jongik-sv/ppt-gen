#!/usr/bin/env python3
"""
Pattern Matcher.

유사한 슬라이드를 하나의 가변 템플릿으로 통합하기 위한 패턴 매칭 모듈.

패턴 통합 조건:
- 같은 문서 템플릿(출처)
- 같은 카테고리
- 같은 레이아웃 타입 (grid, list 등)
- 같은 요소 구조 (icon+title+desc)
- 스타일 힌트 유사 (border-radius, shadow 등)

달라도 됨:
- 요소 개수 (2개, 3개, 4개)
- 간격 (gap)
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PatternSignature:
    """
    패턴 시그니처.

    슬라이드의 구조적 특성을 추출하여 통합 가능 여부를 판단하는 데 사용.
    """
    category: str                          # body, team, schedule, grid 등
    layout_type: str                       # grid, list, title-body, single 등
    element_structure: str                 # 요소 구조 (icon+title+desc, image-only 등)
    element_count: int                     # 반복 요소 개수
    style_hints: Dict[str, Any] = field(default_factory=dict)  # 스타일 힌트
    source_document: Optional[str] = None  # 원본 문서 ID


@dataclass
class VariantInfo:
    """
    변형 정보.

    통합된 템플릿의 각 변형(variant)을 정의.
    """
    count: int                             # 요소 개수
    layout: Dict[str, Any] = field(default_factory=dict)  # columns, gap, rows 등
    source_slide: int = 0                  # 원본 슬라이드 번호 (1-based)


class PatternMatcher:
    """
    패턴 매처.

    슬라이드 패턴을 분석하여 통합 가능 여부를 판단.
    """

    # 유사도 임계값 (이 값 이상이면 통합)
    DEFAULT_MERGE_THRESHOLD = 0.75

    # 유사도 계산 가중치
    WEIGHTS = {
        'category': 0.25,           # 카테고리 일치
        'layout_type': 0.30,        # 레이아웃 타입 일치
        'element_structure': 0.30,  # 요소 구조 일치
        'style_hints': 0.15,        # 스타일 힌트 유사
    }

    def __init__(self, merge_threshold: float = DEFAULT_MERGE_THRESHOLD):
        """
        Args:
            merge_threshold: 통합 판단 임계값 (0.0~1.0)
        """
        self.merge_threshold = merge_threshold

    def extract_signature(
        self,
        shapes: List[Any],
        category: str,
        pattern: str,
        source_document: Optional[str] = None
    ) -> PatternSignature:
        """
        도형 목록에서 패턴 시그니처를 추출합니다.

        Args:
            shapes: 도형 정보 목록 (ShapeInfo)
            category: 카테고리
            pattern: 감지된 패턴 (grid-4, title-body 등)
            source_document: 원본 문서 ID

        Returns:
            추출된 PatternSignature
        """
        # 레이아웃 타입 추출 (grid-4 → grid)
        layout_type = self._extract_layout_type(pattern)

        # 요소 개수 추출 (grid-4 → 4, title-body → 0)
        element_count = self._extract_element_count(pattern, shapes)

        # 요소 구조 분석
        element_structure = self._analyze_element_structure(shapes)

        # 스타일 힌트 추출
        style_hints = self._extract_style_hints(shapes)

        return PatternSignature(
            category=category,
            layout_type=layout_type,
            element_structure=element_structure,
            element_count=element_count,
            style_hints=style_hints,
            source_document=source_document
        )

    def compare_signatures(
        self,
        sig1: PatternSignature,
        sig2: PatternSignature
    ) -> float:
        """
        두 패턴 시그니처의 유사도를 계산합니다.

        Args:
            sig1: 첫 번째 시그니처
            sig2: 두 번째 시그니처

        Returns:
            유사도 (0.0~1.0)
        """
        score = 0.0

        # 1. 출처가 다르면 통합 불가 (즉시 0 반환)
        if sig1.source_document != sig2.source_document:
            return 0.0

        # 2. 카테고리 비교
        if sig1.category == sig2.category:
            score += self.WEIGHTS['category']

        # 3. 레이아웃 타입 비교
        if sig1.layout_type == sig2.layout_type:
            score += self.WEIGHTS['layout_type']

        # 4. 요소 구조 비교
        structure_sim = self._compare_structures(
            sig1.element_structure,
            sig2.element_structure
        )
        score += self.WEIGHTS['element_structure'] * structure_sim

        # 5. 스타일 힌트 비교
        style_sim = self._compare_style_hints(sig1.style_hints, sig2.style_hints)
        score += self.WEIGHTS['style_hints'] * style_sim

        return score

    def should_merge(
        self,
        sig1: PatternSignature,
        sig2: PatternSignature,
        threshold: Optional[float] = None
    ) -> bool:
        """
        두 패턴을 통합해야 하는지 판단합니다.

        Args:
            sig1: 첫 번째 시그니처
            sig2: 두 번째 시그니처
            threshold: 임계값 (기본: merge_threshold)

        Returns:
            통합 여부
        """
        if threshold is None:
            threshold = self.merge_threshold

        similarity = self.compare_signatures(sig1, sig2)
        return similarity >= threshold

    def create_variant(
        self,
        signature: PatternSignature,
        slide_index: int,
        shapes: List[Any]
    ) -> VariantInfo:
        """
        시그니처에서 VariantInfo를 생성합니다.

        Args:
            signature: 패턴 시그니처
            slide_index: 슬라이드 인덱스 (0-based)
            shapes: 도형 목록

        Returns:
            VariantInfo
        """
        # 레이아웃 정보 추출
        layout = self._extract_layout_info(signature, shapes)

        return VariantInfo(
            count=signature.element_count,
            layout=layout,
            source_slide=slide_index + 1  # 1-based
        )

    def _extract_layout_type(self, pattern: str) -> str:
        """패턴에서 레이아웃 타입 추출."""
        if not pattern:
            return 'unknown'

        # grid-4 → grid
        # multi-image-3 → multi-image
        # title-body → title-body
        parts = pattern.rsplit('-', 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0]
        return pattern

    def _extract_element_count(self, pattern: str, shapes: List[Any]) -> int:
        """패턴 또는 도형에서 요소 개수 추출."""
        # 패턴에서 숫자 추출 (grid-4 → 4)
        if pattern:
            parts = pattern.rsplit('-', 1)
            if len(parts) == 2 and parts[1].isdigit():
                return int(parts[1])

        # 도형 개수로 추정
        # 이미지 개수
        image_count = len([s for s in shapes if getattr(s, 'type', '') == 'image'])
        if image_count >= 2:
            return image_count

        # 텍스트 개수 (제목 제외)
        text_shapes = [s for s in shapes if getattr(s, 'text', None)]
        if len(text_shapes) >= 2:
            return len(text_shapes) - 1  # 제목 제외

        return 0

    def _analyze_element_structure(self, shapes: List[Any]) -> str:
        """도형 구조 분석."""
        types = set()

        for shape in shapes:
            shape_type = getattr(shape, 'type', 'unknown')
            types.add(shape_type)

        # 구조 문자열 생성
        structure_parts = []
        if 'image' in types:
            structure_parts.append('image')
        if 'text' in types or 'placeholder' in types:
            structure_parts.append('text')
        if 'shape' in types:
            structure_parts.append('shape')
        if 'chart' in types:
            structure_parts.append('chart')
        if 'table' in types:
            structure_parts.append('table')

        return '+'.join(sorted(structure_parts)) if structure_parts else 'empty'

    def _extract_style_hints(self, shapes: List[Any]) -> Dict[str, Any]:
        """스타일 힌트 추출."""
        hints = {}

        for shape in shapes:
            style = getattr(shape, 'style', {})
            if not style:
                continue

            # 채우기 색상
            if 'fill_color' in style and 'fill_color' not in hints:
                hints['fill_color'] = style['fill_color']

            # 폰트 크기 (대표값)
            if 'font_size' in style:
                if 'font_sizes' not in hints:
                    hints['font_sizes'] = []
                hints['font_sizes'].append(style['font_size'])

        # 폰트 크기 범위로 정리
        if 'font_sizes' in hints:
            sizes = hints['font_sizes']
            hints['font_size_range'] = (min(sizes), max(sizes))
            del hints['font_sizes']

        return hints

    def _compare_structures(self, struct1: str, struct2: str) -> float:
        """구조 문자열 비교."""
        if struct1 == struct2:
            return 1.0

        # 부분 일치
        parts1 = set(struct1.split('+'))
        parts2 = set(struct2.split('+'))

        if not parts1 or not parts2:
            return 0.0

        intersection = len(parts1 & parts2)
        union = len(parts1 | parts2)

        return intersection / union  # Jaccard 유사도

    def _compare_style_hints(
        self,
        hints1: Dict[str, Any],
        hints2: Dict[str, Any]
    ) -> float:
        """스타일 힌트 비교."""
        if not hints1 and not hints2:
            return 1.0  # 둘 다 없으면 동일
        if not hints1 or not hints2:
            return 0.5  # 하나만 있으면 중간

        matches = 0
        total = 0

        # 채우기 색상 비교
        if 'fill_color' in hints1 and 'fill_color' in hints2:
            total += 1
            if hints1['fill_color'] == hints2['fill_color']:
                matches += 1

        # 폰트 크기 범위 비교
        if 'font_size_range' in hints1 and 'font_size_range' in hints2:
            total += 1
            r1 = hints1['font_size_range']
            r2 = hints2['font_size_range']
            # 범위 겹침 확인
            if r1[0] <= r2[1] and r2[0] <= r1[1]:
                matches += 1

        return matches / total if total > 0 else 1.0

    def _extract_layout_info(
        self,
        signature: PatternSignature,
        shapes: List[Any]
    ) -> Dict[str, Any]:
        """레이아웃 정보 추출."""
        layout = {}

        count = signature.element_count
        if count > 0:
            # 컬럼 수 추정 (그리드 패턴)
            if signature.layout_type == 'grid':
                if count <= 2:
                    layout['columns'] = count
                elif count <= 4:
                    layout['columns'] = count
                elif count <= 6:
                    layout['columns'] = 3
                else:
                    layout['columns'] = 4

            # 간격 추정 (개수에 반비례)
            if count >= 2:
                base_gap = 8  # 기본 간격 %
                layout['gap'] = f"{max(1, base_gap - count)}%"

        # 도형 위치에서 행 수 추정
        if shapes:
            y_positions = set()
            for s in shapes:
                pos = getattr(s, 'position', {})
                y = pos.get('y', 0)
                # 10% 단위로 그룹화
                y_positions.add(round(y / 10) * 10)

            if len(y_positions) >= 2:
                layout['rows'] = len(y_positions)

        return layout


def merge_variants(
    base_variants: List[VariantInfo],
    new_variant: VariantInfo
) -> List[VariantInfo]:
    """
    variants 목록에 새 variant를 추가합니다.

    같은 count가 이미 있으면 업데이트, 없으면 추가.

    Args:
        base_variants: 기존 variants 목록
        new_variant: 추가할 variant

    Returns:
        업데이트된 variants 목록
    """
    result = list(base_variants)

    # 같은 count가 있는지 확인
    for i, v in enumerate(result):
        if v.count == new_variant.count:
            # 기존 것 유지 (또는 업데이트 정책에 따라 변경)
            return result

    # 새로 추가
    result.append(new_variant)

    # count 순으로 정렬
    result.sort(key=lambda v: v.count)

    return result


def calculate_element_count_range(variants: List[VariantInfo]) -> str:
    """
    variants에서 element_count 범위 문자열 생성.

    Args:
        variants: variants 목록

    Returns:
        범위 문자열 (예: "2-6")
    """
    if not variants:
        return ""

    counts = [v.count for v in variants if v.count > 0]
    if not counts:
        return ""

    min_count = min(counts)
    max_count = max(counts)

    if min_count == max_count:
        return str(min_count)

    return f"{min_count}-{max_count}"
