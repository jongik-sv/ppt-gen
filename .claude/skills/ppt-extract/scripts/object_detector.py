#!/usr/bin/env python3
"""
Object Detector.

슬라이드에서 복잡한 도형(다이어그램, 플로우차트 등)을 자동 감지합니다.
content-extract 중 오브젝트로 분리 저장할 대상을 식별합니다.

감지 조건 (5가지):
1. 도형 그룹 5개+ - 연결된 도형이 5개 이상
2. 비선형 배치 - 원형, 방사형, 지그재그 등
3. 커넥터 포함 - 화살표/선으로 연결된 도형
4. 수치 데이터 시각화 - 축/범례가 있는 차트
5. 벤/매트릭스 - 겹침/그리드 구조
"""

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ShapeInfo import를 위해 경로 추가
import sys
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared.ooxml_parser import NAMESPACES


class DetectionType(Enum):
    """감지 유형."""
    GROUP_5PLUS = "group_5plus"      # 도형 그룹 5개 이상
    NONLINEAR = "nonlinear"          # 비선형 배치
    CONNECTOR = "connector"          # 커넥터 포함
    CHART = "chart"                  # 차트/데이터 시각화
    MATRIX = "matrix"                # 벤/매트릭스 구조


class ObjectCategory(Enum):
    """오브젝트 카테고리."""
    DIAGRAM = "diagram"    # 순환도, 벤다이어그램
    PROCESS = "process"    # 플로우차트, 프로세스
    CHART = "chart"        # 막대, 선, 파이 차트


@dataclass
class ShapeInfo:
    """도형 정보 (content_extractor와 호환)."""
    id: str
    name: str
    type: str  # shape, text, image, group, chart, table, connector
    text: Optional[str] = None
    position: Dict[str, float] = field(default_factory=dict)  # x, y, width, height (%)
    style: Dict[str, Any] = field(default_factory=dict)
    children: List['ShapeInfo'] = field(default_factory=list)
    # 추가 속성
    is_connector: bool = False
    connected_shapes: List[str] = field(default_factory=list)  # 연결된 도형 ID


@dataclass
class ObjectCandidate:
    """오브젝트 후보."""
    shapes: List[ShapeInfo]           # 감지된 도형들
    detection_type: DetectionType     # 감지 유형
    confidence: float                 # 신뢰도 (0.0~1.0)
    bounding_box: Tuple[float, float, float, float]  # (x, y, width, height) %
    category: ObjectCategory          # 추천 카테고리
    reason: str                       # 감지 이유


class ObjectDetector:
    """오브젝트 감지기."""

    # 감지 임계값
    MIN_GROUP_SHAPES = 5              # 최소 그룹 도형 수
    NONLINEAR_VARIANCE_THRESHOLD = 15  # 비선형 판정 분산 (%)
    OVERLAP_THRESHOLD = 0.2           # 겹침 판정 비율 (20%)
    GRID_TOLERANCE = 5                # 그리드 정렬 허용오차 (%)

    def __init__(self):
        """초기화."""
        pass

    def detect(
        self,
        shapes: List[ShapeInfo],
        slide_xml: Optional[ET.Element] = None
    ) -> List[ObjectCandidate]:
        """
        도형 목록에서 오브젝트 후보를 감지합니다.

        Args:
            shapes: 도형 정보 목록
            slide_xml: 원본 슬라이드 XML (커넥터 감지용, 선택)

        Returns:
            감지된 오브젝트 후보 목록
        """
        candidates = []

        # 1. 차트 감지 (우선순위 최고)
        chart_candidate = self._check_chart_elements(shapes)
        if chart_candidate:
            candidates.append(chart_candidate)
            # 차트에 포함된 도형은 제외
            shapes = self._exclude_shapes(shapes, chart_candidate.shapes)

        # 2. 커넥터 포함 감지
        if slide_xml is not None:
            connector_candidate = self._check_connectors(shapes, slide_xml)
            if connector_candidate:
                candidates.append(connector_candidate)
                shapes = self._exclude_shapes(shapes, connector_candidate.shapes)

        # 3. 그룹 도형 5개 이상 감지
        group_candidate = self._check_group_threshold(shapes)
        if group_candidate:
            candidates.append(group_candidate)
            shapes = self._exclude_shapes(shapes, group_candidate.shapes)

        # 4. 비선형 배치 감지
        nonlinear_candidate = self._check_nonlinear_layout(shapes)
        if nonlinear_candidate:
            candidates.append(nonlinear_candidate)
            shapes = self._exclude_shapes(shapes, nonlinear_candidate.shapes)

        # 5. 매트릭스/벤다이어그램 감지
        matrix_candidate = self._check_matrix_pattern(shapes)
        if matrix_candidate:
            candidates.append(matrix_candidate)

        return candidates

    def _check_group_threshold(self, shapes: List[ShapeInfo]) -> Optional[ObjectCandidate]:
        """
        도형 그룹 5개 이상 감지.

        그룹 도형(p:grpSp)의 자식이 5개 이상이면 오브젝트로 판정.
        """
        for shape in shapes:
            if shape.type == 'group' and len(shape.children) >= self.MIN_GROUP_SHAPES:
                # 바운딩 박스 계산
                bbox = self._calculate_bounding_box([shape] + shape.children)

                # 신뢰도: 자식 수에 비례
                confidence = min(len(shape.children) / 10, 1.0)

                # 카테고리 추론
                category = self._infer_category_from_shapes(shape.children)

                return ObjectCandidate(
                    shapes=[shape] + shape.children,
                    detection_type=DetectionType.GROUP_5PLUS,
                    confidence=confidence,
                    bounding_box=bbox,
                    category=category,
                    reason=f"그룹 도형 내 {len(shape.children)}개 자식 포함"
                )

        return None

    def _check_nonlinear_layout(self, shapes: List[ShapeInfo]) -> Optional[ObjectCandidate]:
        """
        비선형 배치 감지 (원형, 방사형, 지그재그).

        도형들의 중심점이 원형 또는 방사형 패턴을 이루는지 검사.
        """
        # 텍스트 또는 도형 타입만 필터링 (이미지, 차트 제외)
        shape_candidates = [
            s for s in shapes
            if s.type in ('shape', 'text', 'placeholder')
            and s.position.get('width', 0) > 0
        ]

        if len(shape_candidates) < self.MIN_GROUP_SHAPES:
            return None

        # 중심점 계산
        centers = []
        for s in shape_candidates:
            cx = s.position.get('x', 0) + s.position.get('width', 0) / 2
            cy = s.position.get('y', 0) + s.position.get('height', 0) / 2
            centers.append((cx, cy))

        # 원형 배치 검사
        is_circular, circle_confidence = self._check_circular_layout(centers)
        if is_circular:
            bbox = self._calculate_bounding_box(shape_candidates)
            return ObjectCandidate(
                shapes=shape_candidates,
                detection_type=DetectionType.NONLINEAR,
                confidence=circle_confidence,
                bounding_box=bbox,
                category=ObjectCategory.DIAGRAM,
                reason="원형/방사형 배치 감지"
            )

        # 지그재그 배치 검사
        is_zigzag, zigzag_confidence = self._check_zigzag_layout(centers)
        if is_zigzag:
            bbox = self._calculate_bounding_box(shape_candidates)
            return ObjectCandidate(
                shapes=shape_candidates,
                detection_type=DetectionType.NONLINEAR,
                confidence=zigzag_confidence,
                bounding_box=bbox,
                category=ObjectCategory.PROCESS,
                reason="지그재그 배치 감지"
            )

        return None

    def _check_circular_layout(self, centers: List[Tuple[float, float]]) -> Tuple[bool, float]:
        """원형 배치 검사."""
        if len(centers) < 4:
            return False, 0.0

        # 전체 중심 계산
        avg_x = sum(c[0] for c in centers) / len(centers)
        avg_y = sum(c[1] for c in centers) / len(centers)

        # 각 점까지의 거리 계산
        distances = [
            math.sqrt((c[0] - avg_x) ** 2 + (c[1] - avg_y) ** 2)
            for c in centers
        ]

        # 거리의 표준편차가 작으면 원형 배치
        mean_dist = sum(distances) / len(distances)
        if mean_dist < 5:  # 너무 가까우면 원형 아님
            return False, 0.0

        variance = sum((d - mean_dist) ** 2 for d in distances) / len(distances)
        std_dev = math.sqrt(variance)

        # 표준편차가 평균의 30% 이하면 원형
        if std_dev / mean_dist < 0.3:
            confidence = 1.0 - (std_dev / mean_dist)
            return True, confidence

        return False, 0.0

    def _check_zigzag_layout(self, centers: List[Tuple[float, float]]) -> Tuple[bool, float]:
        """지그재그 배치 검사."""
        if len(centers) < 4:
            return False, 0.0

        # X 좌표로 정렬
        sorted_centers = sorted(centers, key=lambda c: c[0])

        # Y 좌표가 교대로 높/낮이면 지그재그
        y_changes = []
        for i in range(1, len(sorted_centers)):
            diff = sorted_centers[i][1] - sorted_centers[i-1][1]
            y_changes.append(diff)

        # 부호가 교대로 바뀌는지 확인
        sign_changes = 0
        for i in range(1, len(y_changes)):
            if y_changes[i] * y_changes[i-1] < 0:  # 부호가 다름
                sign_changes += 1

        # 60% 이상이 교대면 지그재그
        if sign_changes / (len(y_changes) - 1) > 0.6 if len(y_changes) > 1 else False:
            confidence = sign_changes / (len(y_changes) - 1)
            return True, confidence

        return False, 0.0

    def _check_connectors(
        self,
        shapes: List[ShapeInfo],
        slide_xml: ET.Element
    ) -> Optional[ObjectCandidate]:
        """
        커넥터 포함 감지.

        p:cxnSp (커넥터 도형)이 있으면 연결된 도형들을 오브젝트로 판정.
        """
        # 커넥터 찾기
        connectors = slide_xml.findall('.//p:cxnSp', NAMESPACES)

        if not connectors:
            return None

        # 커넥터가 연결하는 도형 ID 수집
        connected_ids = set()
        for cxn in connectors:
            # 시작점 연결
            st_cxn = cxn.find('.//a:stCxn', NAMESPACES)
            if st_cxn is not None:
                connected_ids.add(st_cxn.get('id', ''))

            # 끝점 연결
            end_cxn = cxn.find('.//a:endCxn', NAMESPACES)
            if end_cxn is not None:
                connected_ids.add(end_cxn.get('id', ''))

        # 연결된 도형 필터링
        connected_shapes = []
        for shape in shapes:
            # shape ID에서 숫자 부분 추출
            shape_num = shape.id.replace('shape-', '').replace('grp-', '').replace('pic-', '')
            if shape_num in connected_ids:
                connected_shapes.append(shape)

        # 커넥터 자체도 ShapeInfo로 추가
        for cxn in connectors:
            cNvPr = cxn.find('.//p:nvCxnSpPr/p:cNvPr', NAMESPACES)
            if cNvPr is not None:
                cxn_shape = ShapeInfo(
                    id=f"cxn-{cNvPr.get('id', '')}",
                    name=cNvPr.get('name', ''),
                    type='connector',
                    is_connector=True
                )
                connected_shapes.append(cxn_shape)

        # 커넥터가 3개 이상이면 플로우차트로 판정
        if len(connectors) >= 2 and len(connected_shapes) >= 3:
            bbox = self._calculate_bounding_box([s for s in connected_shapes if not s.is_connector])
            confidence = min(len(connectors) / 5, 1.0)

            return ObjectCandidate(
                shapes=connected_shapes,
                detection_type=DetectionType.CONNECTOR,
                confidence=confidence,
                bounding_box=bbox,
                category=ObjectCategory.PROCESS,
                reason=f"커넥터 {len(connectors)}개로 연결된 도형"
            )

        return None

    def _check_chart_elements(self, shapes: List[ShapeInfo]) -> Optional[ObjectCandidate]:
        """
        차트/데이터 시각화 감지.

        chart 타입 도형이 있으면 오브젝트로 판정.
        """
        charts = [s for s in shapes if s.type == 'chart']

        if not charts:
            return None

        # 차트 주변 레이블(범례, 축)도 포함
        related_shapes = list(charts)
        for chart in charts:
            chart_bbox = (
                chart.position.get('x', 0),
                chart.position.get('y', 0),
                chart.position.get('x', 0) + chart.position.get('width', 0),
                chart.position.get('y', 0) + chart.position.get('height', 0)
            )

            # 차트 근처 텍스트 도형 포함
            for shape in shapes:
                if shape in related_shapes:
                    continue
                if shape.type in ('text', 'placeholder') and shape.text:
                    # 차트 영역의 20% 확장 범위 내에 있는지 확인
                    margin = max(chart.position.get('width', 0), chart.position.get('height', 0)) * 0.2
                    sx = shape.position.get('x', 0)
                    sy = shape.position.get('y', 0)
                    if (chart_bbox[0] - margin <= sx <= chart_bbox[2] + margin and
                        chart_bbox[1] - margin <= sy <= chart_bbox[3] + margin):
                        related_shapes.append(shape)

        bbox = self._calculate_bounding_box(related_shapes)
        confidence = 0.95  # 차트는 높은 신뢰도

        return ObjectCandidate(
            shapes=related_shapes,
            detection_type=DetectionType.CHART,
            confidence=confidence,
            bounding_box=bbox,
            category=ObjectCategory.CHART,
            reason=f"차트 {len(charts)}개 감지"
        )

    def _check_matrix_pattern(self, shapes: List[ShapeInfo]) -> Optional[ObjectCandidate]:
        """
        매트릭스/벤다이어그램 감지.

        - 2x2, 3x3 등 그리드 구조
        - 겹치는 원/사각형 (벤다이어그램)
        """
        # 도형만 필터링
        shape_candidates = [
            s for s in shapes
            if s.type in ('shape', 'placeholder')
            and s.position.get('width', 0) > 5  # 너무 작은 도형 제외
        ]

        if len(shape_candidates) < 3:
            return None

        # 1. 겹침 검사 (벤다이어그램)
        overlapping = self._find_overlapping_shapes(shape_candidates)
        if len(overlapping) >= 2:
            all_overlapping = set()
            for pair in overlapping:
                all_overlapping.update(pair)

            overlapping_shapes = [s for i, s in enumerate(shape_candidates) if i in all_overlapping]
            if len(overlapping_shapes) >= 2:
                bbox = self._calculate_bounding_box(overlapping_shapes)
                confidence = min(len(overlapping_shapes) / 4, 0.9)

                return ObjectCandidate(
                    shapes=overlapping_shapes,
                    detection_type=DetectionType.MATRIX,
                    confidence=confidence,
                    bounding_box=bbox,
                    category=ObjectCategory.DIAGRAM,
                    reason=f"겹치는 도형 {len(overlapping_shapes)}개 (벤다이어그램)"
                )

        # 2. 그리드 구조 검사
        grid_shapes = self._find_grid_pattern(shape_candidates)
        if grid_shapes and len(grid_shapes) >= 4:
            bbox = self._calculate_bounding_box(grid_shapes)
            rows, cols = self._estimate_grid_dimensions(grid_shapes)
            confidence = 0.8 if rows >= 2 and cols >= 2 else 0.6

            return ObjectCandidate(
                shapes=grid_shapes,
                detection_type=DetectionType.MATRIX,
                confidence=confidence,
                bounding_box=bbox,
                category=ObjectCategory.DIAGRAM,
                reason=f"{rows}x{cols} 그리드 매트릭스"
            )

        return None

    def _find_overlapping_shapes(self, shapes: List[ShapeInfo]) -> List[Tuple[int, int]]:
        """겹치는 도형 쌍 찾기."""
        overlapping = []

        for i, s1 in enumerate(shapes):
            for j, s2 in enumerate(shapes):
                if i >= j:
                    continue

                # 바운딩 박스 겹침 검사
                x1, y1 = s1.position.get('x', 0), s1.position.get('y', 0)
                w1, h1 = s1.position.get('width', 0), s1.position.get('height', 0)
                x2, y2 = s2.position.get('x', 0), s2.position.get('y', 0)
                w2, h2 = s2.position.get('width', 0), s2.position.get('height', 0)

                # 겹치는 영역 계산
                overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = overlap_x * overlap_y

                # 두 도형 중 작은 쪽 면적
                area1 = w1 * h1
                area2 = w2 * h2
                min_area = min(area1, area2) if min(area1, area2) > 0 else 1

                # 겹침 비율이 임계값 이상이면
                if overlap_area / min_area > self.OVERLAP_THRESHOLD:
                    overlapping.append((i, j))

        return overlapping

    def _find_grid_pattern(self, shapes: List[ShapeInfo]) -> Optional[List[ShapeInfo]]:
        """그리드 패턴 찾기."""
        if len(shapes) < 4:
            return None

        # X, Y 좌표 그룹화
        x_positions = sorted(set(
            round(s.position.get('x', 0) / self.GRID_TOLERANCE) * self.GRID_TOLERANCE
            for s in shapes
        ))
        y_positions = sorted(set(
            round(s.position.get('y', 0) / self.GRID_TOLERANCE) * self.GRID_TOLERANCE
            for s in shapes
        ))

        # 그리드 형태 (2개 이상 행/열)이면
        if len(x_positions) >= 2 and len(y_positions) >= 2:
            return shapes

        return None

    def _estimate_grid_dimensions(self, shapes: List[ShapeInfo]) -> Tuple[int, int]:
        """그리드 차원 추정."""
        x_positions = sorted(set(
            round(s.position.get('x', 0) / self.GRID_TOLERANCE) * self.GRID_TOLERANCE
            for s in shapes
        ))
        y_positions = sorted(set(
            round(s.position.get('y', 0) / self.GRID_TOLERANCE) * self.GRID_TOLERANCE
            for s in shapes
        ))
        return len(y_positions), len(x_positions)

    def _calculate_bounding_box(
        self,
        shapes: List[ShapeInfo]
    ) -> Tuple[float, float, float, float]:
        """도형들의 바운딩 박스 계산."""
        if not shapes:
            return (0, 0, 0, 0)

        min_x = min(s.position.get('x', 100) for s in shapes)
        min_y = min(s.position.get('y', 100) for s in shapes)
        max_x = max(
            s.position.get('x', 0) + s.position.get('width', 0)
            for s in shapes
        )
        max_y = max(
            s.position.get('y', 0) + s.position.get('height', 0)
            for s in shapes
        )

        return (min_x, min_y, max_x - min_x, max_y - min_y)

    def _infer_category_from_shapes(self, shapes: List[ShapeInfo]) -> ObjectCategory:
        """도형 특성에서 카테고리 추론."""
        # 텍스트 분석
        all_text = ' '.join(s.text or '' for s in shapes).lower()

        # 키워드 기반 분류
        process_keywords = ['단계', 'step', '프로세스', 'process', '흐름', 'flow']
        chart_keywords = ['차트', 'chart', '%', '데이터', 'data']
        diagram_keywords = ['순환', 'cycle', '벤', 'venn', '매트릭스', 'matrix']

        for kw in chart_keywords:
            if kw in all_text:
                return ObjectCategory.CHART

        for kw in process_keywords:
            if kw in all_text:
                return ObjectCategory.PROCESS

        for kw in diagram_keywords:
            if kw in all_text:
                return ObjectCategory.DIAGRAM

        # 기본값
        return ObjectCategory.DIAGRAM

    def _exclude_shapes(
        self,
        shapes: List[ShapeInfo],
        to_exclude: List[ShapeInfo]
    ) -> List[ShapeInfo]:
        """도형 목록에서 제외."""
        exclude_ids = {s.id for s in to_exclude}
        return [s for s in shapes if s.id not in exclude_ids]
