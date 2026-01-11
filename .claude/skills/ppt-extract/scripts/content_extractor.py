#!/usr/bin/env python3
"""
Content Extractor.

PPTX 슬라이드에서 콘텐츠 템플릿을 추출합니다.
3가지 포맷 생성: YAML (슬롯 정의), HTML (Handlebars), OOXML (원본 XML)
"""

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 스크립트 디렉토리를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared.ooxml_parser import OOXMLParser, NAMESPACES, emu_to_percent, emu_to_vmin, calculate_vmin
from shared.yaml_utils import save_yaml
from scripts.thumbnail import convert_pptx_to_images, create_thumbnail, THUMBNAIL_SIZES
from scripts.object_detector import ObjectDetector
from scripts.object_extractor import ObjectExtractor
from scripts.pattern_matcher import (
    PatternMatcher, PatternSignature, VariantInfo,
    merge_variants, calculate_element_count_range
)


@dataclass
class ShapeInfo:
    """도형 정보."""
    id: str
    name: str
    type: str  # shape, text, image, group, chart, table
    text: Optional[str] = None
    position: Dict[str, float] = field(default_factory=dict)  # x, y, width, height (%) - 하위 호환
    geometry: Dict[str, Any] = field(default_factory=dict)  # vmin 기반 좌표 + EMU 원본
    style: Dict[str, Any] = field(default_factory=dict)
    children: List['ShapeInfo'] = field(default_factory=list)


@dataclass
class SlotInfo:
    """슬롯 정보."""
    name: str
    type: str  # text, image, array
    required: bool = True
    shape_ids: List[str] = field(default_factory=list)
    example: Optional[str] = None
    item_schema: Optional[List[Dict]] = None  # array 타입일 때


@dataclass
class ContentTemplate:
    """콘텐츠 템플릿."""
    id: str
    category: str
    pattern: str
    slots: List[SlotInfo]
    shapes: List[ShapeInfo]
    semantic_description: str
    match_keywords: List[str]
    source_document: Optional[str] = None
    source_file: Optional[str] = None
    slide_index: int = 0
    # 패턴 통합용 필드
    variants: List[VariantInfo] = field(default_factory=list)
    signature: Optional[PatternSignature] = None
    output_path: Optional[Path] = None


# 카테고리 키워드 매핑
CATEGORY_KEYWORDS = {
    'cover': ['표지', 'cover', '제목', 'title'],
    'toc': ['목차', '차례', 'contents', 'index'],
    'section': ['섹션', '구분', 'section', 'divider'],
    'grid': ['그리드', 'grid', '카드', 'card', '박스'],
    'list': ['리스트', '목록', 'list', '항목'],
    'timeline': ['타임라인', 'timeline', '일정', '마일스톤'],
    'process': ['프로세스', 'process', '단계', 'step', '흐름'],
    'comparison': ['비교', 'comparison', 'vs', '대비'],
    'chart': ['차트', 'chart', '그래프', 'graph'],
    'diagram': ['다이어그램', 'diagram', '순환', '사이클'],
    'table': ['표', 'table', '테이블'],
    'quote': ['인용', 'quote', '명언'],
    'image': ['이미지', 'image', '사진', 'photo'],
    'team': ['팀', 'team', '조직', '인물'],
    'closing': ['마무리', 'closing', '감사', 'thank'],
}


class ContentExtractor:
    """콘텐츠 추출기."""

    def __init__(
        self,
        input_path: Path,
        slides: Optional[List[int]] = None,
        category: Optional[str] = None,
        output_path: Optional[Path] = None,
        auto_classify: bool = False,
        source_document: Optional[str] = None,
        auto_extract_objects: bool = True,
        enable_pattern_merge: bool = True,
        use_llm: bool = False
    ):
        """
        Args:
            input_path: 입력 PPTX 경로
            slides: 추출할 슬라이드 번호 목록 (1-indexed)
            category: 카테고리 (지정 안 하면 자동 분류)
            output_path: 출력 경로
            auto_classify: 자동 모드 (LLM 없이 규칙 기반)
            source_document: 원본 문서 양식 이름
            auto_extract_objects: 복잡한 도형을 오브젝트로 자동 추출
            enable_pattern_merge: 유사 패턴 통합 활성화
            use_llm: LLM 기반 분류 사용 (Claude API 호출)
        """
        self.input_path = Path(input_path)
        self.slides = slides
        self.category = category
        self.output_path = output_path
        self.auto_classify = auto_classify
        self.source_document = source_document
        self.auto_extract_objects = auto_extract_objects
        self.enable_pattern_merge = enable_pattern_merge
        self.use_llm = use_llm

        self.parser = OOXMLParser(self.input_path)
        self.slide_width, self.slide_height = self.parser.get_slide_size()

        # 오브젝트 감지/추출기 초기화
        self.object_detector = ObjectDetector() if auto_extract_objects else None
        self.object_extractor = ObjectExtractor() if auto_extract_objects else None
        self.extracted_objects: List[Path] = []  # 추출된 오브젝트 경로

        # 패턴 통합 관련
        self.pattern_matcher = PatternMatcher() if enable_pattern_merge else None
        self.pending_templates: Dict[str, ContentTemplate] = {}  # 통합 대기 템플릿

    def run(self) -> List[ContentTemplate]:
        """
        콘텐츠 추출 실행.

        Returns:
            추출된 ContentTemplate 목록
        """
        print(f"\n콘텐츠 추출 시작: {self.input_path.name}")

        # 슬라이드 목록 결정
        total_slides = self.parser.get_slide_count()
        if self.slides:
            slide_indices = [s - 1 for s in self.slides if 1 <= s <= total_slides]
        else:
            slide_indices = list(range(total_slides))

        print(f"  총 슬라이드: {total_slides}개, 추출 대상: {len(slide_indices)}개")

        # 패턴 통합 모드
        if self.enable_pattern_merge:
            print(f"  패턴 통합: 활성화")
            for idx in slide_indices:
                print(f"\n  슬라이드 {idx + 1} 분석 중...")
                template = self._extract_slide(idx)
                if template:
                    self._try_merge_or_queue(template)

            # 대기 중인 템플릿 저장
            templates = self._save_pending_templates()

        else:
            # 기존 방식: 즉시 저장
            templates = []
            for idx in slide_indices:
                print(f"\n  슬라이드 {idx + 1} 분석 중...")
                template = self._extract_slide(idx)
                if template:
                    templates.append(template)
                    self._save_template(template)

        # 레지스트리 업데이트
        print("\n레지스트리 업데이트 중...")
        try:
            from scripts.registry_manager import RegistryManager
            manager = RegistryManager()
            for template in templates:
                if template.output_path:
                    manager.update_content(template.output_path)
        except Exception as e:
            print(f"  Warning: 레지스트리 업데이트 실패: {e}")

        # 결과 출력
        print(f"\n완료: {len(templates)}개 템플릿 추출됨")
        if self.pending_templates:
            merged_count = sum(len(t.variants) for t in templates if t.variants)
            if merged_count > 0:
                print(f"       {merged_count}개 슬라이드가 variants로 통합됨")
        if self.extracted_objects:
            print(f"       {len(self.extracted_objects)}개 오브젝트 자동 추출됨")
            for obj_path in self.extracted_objects:
                print(f"         - {obj_path.name}")

        return templates

    def _extract_slide(self, slide_index: int) -> Optional[ContentTemplate]:
        """단일 슬라이드에서 콘텐츠 추출."""
        slide_path = f'ppt/slides/slide{slide_index + 1}.xml'
        slide_xml = self.parser.read_xml(slide_path)

        if slide_xml is None:
            print(f"    경고: 슬라이드를 읽을 수 없습니다: {slide_path}")
            return None

        # 1. 도형 파싱
        shapes = self._parse_shapes(slide_xml)
        print(f"    도형: {len(shapes)}개")

        if not shapes:
            print(f"    경고: 도형이 없습니다")
            return None

        # 1.5. 오브젝트 자동 감지 및 추출
        if self.object_detector and self.object_extractor:
            shapes = self._detect_and_extract_objects(
                shapes, slide_xml, slide_index
            )

        # 2. 카테고리 분류
        category = self.category or self._classify_category(shapes)
        print(f"    카테고리: {category}")

        # 3. 슬롯 분류
        if self.auto_classify:
            slots = self._classify_slots_auto(shapes)
        else:
            slots = self._classify_slots_llm(shapes)
        print(f"    슬롯: {len(slots)}개")

        # 4. 시맨틱 설명 생성
        semantic_desc = self._generate_semantic_description(shapes, slots)

        # 5. 템플릿 ID 생성
        template_id = self._generate_template_id(category, slide_index)

        # 6. 패턴 감지
        pattern = self._detect_pattern(shapes)

        # 7. 패턴 시그니처 추출 (통합용)
        signature = None
        if self.pattern_matcher:
            signature = self.pattern_matcher.extract_signature(
                shapes=shapes,
                category=category,
                pattern=pattern,
                source_document=self.source_document
            )
            print(f"    패턴: {pattern} (요소 {signature.element_count}개)")

        return ContentTemplate(
            id=template_id,
            category=category,
            pattern=pattern,
            slots=slots,
            shapes=shapes,
            semantic_description=semantic_desc,
            match_keywords=self._extract_keywords(shapes, category),
            source_document=self.source_document,
            source_file=self.input_path.name,
            slide_index=slide_index,
            signature=signature
        )

    def _try_merge_or_queue(self, template: ContentTemplate) -> None:
        """
        패턴 통합을 시도하거나 대기열에 추가합니다.

        Args:
            template: 추출된 템플릿
        """
        if not template.signature:
            # 시그니처 없으면 통합 불가, 즉시 저장
            self._save_template(template)
            return

        # 기존 대기 템플릿과 비교
        for key, existing in self.pending_templates.items():
            if existing.signature and self.pattern_matcher.should_merge(
                template.signature, existing.signature
            ):
                # 통합: variants 배열에 추가
                self._merge_variant(existing, template)
                print(f"    → {existing.id}에 통합됨 (variant count: {template.signature.element_count})")
                return

        # 새 템플릿으로 대기열에 추가
        # 첫 번째 variant로 자신 추가
        if template.signature.element_count > 0:
            initial_variant = self.pattern_matcher.create_variant(
                template.signature,
                template.slide_index,
                template.shapes
            )
            template.variants = [initial_variant]

        # 통합 가능한 ID 생성 (개수 제외)
        merge_key = self._generate_merge_key(template)
        self.pending_templates[merge_key] = template

    def _merge_variant(self, base: ContentTemplate, new: ContentTemplate) -> None:
        """
        새 템플릿을 기존 템플릿의 variant로 통합합니다.

        Args:
            base: 기존 템플릿
            new: 통합할 새 템플릿
        """
        if not new.signature:
            return

        # 새 variant 생성
        new_variant = self.pattern_matcher.create_variant(
            new.signature,
            new.slide_index,
            new.shapes
        )

        # variants 목록에 추가
        base.variants = merge_variants(base.variants, new_variant)

        # 키워드 통합
        for kw in new.match_keywords:
            if kw not in base.match_keywords:
                base.match_keywords.append(kw)

    def _generate_merge_key(self, template: ContentTemplate) -> str:
        """통합용 키 생성 (개수 제외)."""
        if template.signature:
            return f"{template.source_document or 'default'}:{template.category}:{template.signature.layout_type}"
        return template.id

    def _save_pending_templates(self) -> List[ContentTemplate]:
        """
        대기 중인 템플릿을 모두 저장합니다.

        Returns:
            저장된 템플릿 목록
        """
        templates = []

        print(f"\n패턴 통합 결과: {len(self.pending_templates)}개 템플릿")

        for key, template in self.pending_templates.items():
            # variants가 있으면 element_count 범위 업데이트
            if template.variants:
                element_count_range = calculate_element_count_range(template.variants)
                if element_count_range:
                    print(f"  - {template.id}: {len(template.variants)}개 variants (count: {element_count_range})")

            self._save_template(template)
            templates.append(template)

        return templates

    def _detect_and_extract_objects(
        self,
        shapes: List[ShapeInfo],
        slide_xml: ET.Element,
        slide_index: int
    ) -> List[ShapeInfo]:
        """
        오브젝트 자동 감지 및 추출.

        복잡한 도형(다이어그램, 플로우차트 등)을 감지하여
        templates/objects/에 별도 저장하고, 나머지 도형을 반환합니다.

        Args:
            shapes: 원본 도형 목록
            slide_xml: 슬라이드 XML (커넥터 감지용)
            slide_index: 슬라이드 인덱스

        Returns:
            오브젝트로 추출된 도형을 제외한 나머지 도형 목록
        """
        # ShapeInfo를 object_detector의 ShapeInfo로 변환
        from scripts.object_detector import ShapeInfo as DetectorShapeInfo

        detector_shapes = [
            DetectorShapeInfo(
                id=s.id,
                name=s.name,
                type=s.type,
                text=s.text,
                position=s.position,
                style=s.style,
                children=[
                    DetectorShapeInfo(
                        id=c.id, name=c.name, type=c.type,
                        text=c.text, position=c.position, style=c.style
                    )
                    for c in s.children
                ]
            )
            for s in shapes
        ]

        # 오브젝트 감지
        candidates = self.object_detector.detect(detector_shapes, slide_xml)

        if not candidates:
            return shapes

        print(f"    오브젝트 감지: {len(candidates)}개")

        # 추출된 도형 ID 수집
        extracted_ids = set()

        for candidate in candidates:
            print(f"      - {candidate.category.value}: {candidate.reason} (신뢰도 {candidate.confidence:.2f})")

            # 오브젝트 추출
            result = self.object_extractor.extract(
                pptx_path=self.input_path,
                slide_index=slide_index,
                candidate=candidate
            )

            if result:
                self.extracted_objects.append(result)
                # 추출된 도형 ID 수집
                for shape in candidate.shapes:
                    extracted_ids.add(shape.id)

        # 추출된 도형을 제외한 나머지 반환
        remaining_shapes = [s for s in shapes if s.id not in extracted_ids]

        if extracted_ids:
            print(f"    남은 도형: {len(remaining_shapes)}개 (오브젝트 제외)")

        return remaining_shapes

    def _parse_shapes(self, slide_xml: ET.Element) -> List[ShapeInfo]:
        """슬라이드에서 도형 파싱."""
        shapes = []

        # p:sp (일반 도형/텍스트)
        for sp in slide_xml.findall('.//p:sp', NAMESPACES):
            shape = self._parse_sp(sp)
            if shape:
                shapes.append(shape)

        # p:pic (이미지)
        for pic in slide_xml.findall('.//p:pic', NAMESPACES):
            shape = self._parse_pic(pic)
            if shape:
                shapes.append(shape)

        # p:graphicFrame (차트, 표)
        for gf in slide_xml.findall('.//p:graphicFrame', NAMESPACES):
            shape = self._parse_graphic_frame(gf)
            if shape:
                shapes.append(shape)

        # p:grpSp (그룹)
        for grp in slide_xml.findall('.//p:grpSp', NAMESPACES):
            shape = self._parse_group(grp)
            if shape:
                shapes.append(shape)

        return shapes

    def _parse_sp(self, sp: ET.Element) -> Optional[ShapeInfo]:
        """일반 도형/텍스트 파싱."""
        # ID와 이름 추출
        cNvPr = sp.find('.//p:nvSpPr/p:cNvPr', NAMESPACES)
        if cNvPr is None:
            return None

        shape_id = cNvPr.get('id', '')
        name = cNvPr.get('name', '')

        # 위치 추출 (하위 호환)
        position = self._extract_position(sp)

        # geometry 추출 (vmin 기반)
        geometry = self._extract_geometry(sp)

        # 텍스트 추출
        text_parts = []
        for t in sp.findall('.//a:t', NAMESPACES):
            if t.text:
                text_parts.append(t.text)
        text = ''.join(text_parts) if text_parts else None

        # 스타일 추출
        style = self._extract_style(sp)

        # 타입 결정
        ph = sp.find('.//p:ph', NAMESPACES)
        if ph is not None:
            shape_type = 'placeholder'
        elif text:
            shape_type = 'text'
        else:
            shape_type = 'shape'

        return ShapeInfo(
            id=f"shape-{shape_id}",
            name=name,
            type=shape_type,
            text=text,
            position=position,
            geometry=geometry,
            style=style
        )

    def _parse_pic(self, pic: ET.Element) -> Optional[ShapeInfo]:
        """이미지 파싱."""
        cNvPr = pic.find('.//p:nvPicPr/p:cNvPr', NAMESPACES)
        if cNvPr is None:
            return None

        shape_id = cNvPr.get('id', '')
        name = cNvPr.get('name', '')
        position = self._extract_position(pic)
        geometry = self._extract_geometry(pic)

        return ShapeInfo(
            id=f"pic-{shape_id}",
            name=name,
            type='image',
            position=position,
            geometry=geometry
        )

    def _parse_graphic_frame(self, gf: ET.Element) -> Optional[ShapeInfo]:
        """차트/표 파싱."""
        cNvPr = gf.find('.//p:nvGraphicFramePr/p:cNvPr', NAMESPACES)
        if cNvPr is None:
            return None

        shape_id = cNvPr.get('id', '')
        name = cNvPr.get('name', '')
        position = self._extract_position(gf)
        geometry = self._extract_geometry(gf)

        # 차트인지 표인지 구분
        chart = gf.find('.//c:chart', NAMESPACES)
        table = gf.find('.//a:tbl', NAMESPACES)

        if chart is not None:
            shape_type = 'chart'
        elif table is not None:
            shape_type = 'table'
        else:
            shape_type = 'graphic'

        return ShapeInfo(
            id=f"gf-{shape_id}",
            name=name,
            type=shape_type,
            position=position,
            geometry=geometry
        )

    def _parse_group(self, grp: ET.Element) -> Optional[ShapeInfo]:
        """그룹 도형 파싱."""
        cNvPr = grp.find('.//p:nvGrpSpPr/p:cNvPr', NAMESPACES)
        if cNvPr is None:
            return None

        shape_id = cNvPr.get('id', '')
        name = cNvPr.get('name', '')
        position = self._extract_position(grp)
        geometry = self._extract_geometry(grp)

        # 자식 도형 파싱
        children = []
        for sp in grp.findall('./p:sp', NAMESPACES):
            child = self._parse_sp(sp)
            if child:
                children.append(child)

        return ShapeInfo(
            id=f"grp-{shape_id}",
            name=name,
            type='group',
            position=position,
            geometry=geometry,
            children=children
        )

    def _extract_position(self, element: ET.Element) -> Dict[str, float]:
        """도형 위치 추출 (%)."""
        position = {'x': 0, 'y': 0, 'width': 0, 'height': 0}

        # xfrm 찾기 (일반 도형)
        xfrm = element.find('.//p:spPr/a:xfrm', NAMESPACES)
        if xfrm is None:
            xfrm = element.find('.//a:xfrm', NAMESPACES)
        if xfrm is None:
            xfrm = element.find('.//p:xfrm', NAMESPACES)

        if xfrm is not None:
            off = xfrm.find('a:off', NAMESPACES)
            ext = xfrm.find('a:ext', NAMESPACES)

            if off is not None:
                x = int(off.get('x', 0))
                y = int(off.get('y', 0))
                position['x'] = emu_to_percent(x, self.slide_width)
                position['y'] = emu_to_percent(y, self.slide_height)

            if ext is not None:
                cx = int(ext.get('cx', 0))
                cy = int(ext.get('cy', 0))
                position['width'] = emu_to_percent(cx, self.slide_width)
                position['height'] = emu_to_percent(cy, self.slide_height)

        return position

    def _extract_geometry(self, element: ET.Element) -> Dict[str, Any]:
        """도형 geometry 추출 (vmin 기반 + EMU 원본).

        PRD 스키마:
            geometry:
              x: "10vmin"      # vmin 단위 (슬라이드 최소 치수 기준)
              y: "10vmin"
              cx: "20vmin"     # 너비
              cy: "20vmin"     # 높이
              emu:             # 원본 EMU 값 백업 (고품질 OOXML 재현용)
                x: 914400
                y: 914400
                cx: 1828800
                cy: 1828800

        Returns:
            vmin 기반 좌표 및 EMU 원본 백업을 포함하는 딕셔너리
        """
        geometry = {
            'x': '0vmin',
            'y': '0vmin',
            'cx': '0vmin',
            'cy': '0vmin',
            'emu': {'x': 0, 'y': 0, 'cx': 0, 'cy': 0}
        }

        # xfrm 찾기 (일반 도형)
        xfrm = element.find('.//p:spPr/a:xfrm', NAMESPACES)
        if xfrm is None:
            xfrm = element.find('.//a:xfrm', NAMESPACES)
        if xfrm is None:
            xfrm = element.find('.//p:xfrm', NAMESPACES)

        if xfrm is not None:
            off = xfrm.find('a:off', NAMESPACES)
            ext = xfrm.find('a:ext', NAMESPACES)

            if off is not None:
                x_emu = int(off.get('x', 0))
                y_emu = int(off.get('y', 0))
                geometry['x'] = f"{emu_to_vmin(x_emu, self.slide_width, self.slide_height)}vmin"
                geometry['y'] = f"{emu_to_vmin(y_emu, self.slide_width, self.slide_height)}vmin"
                geometry['emu']['x'] = x_emu
                geometry['emu']['y'] = y_emu

            if ext is not None:
                cx_emu = int(ext.get('cx', 0))
                cy_emu = int(ext.get('cy', 0))
                geometry['cx'] = f"{emu_to_vmin(cx_emu, self.slide_width, self.slide_height)}vmin"
                geometry['cy'] = f"{emu_to_vmin(cy_emu, self.slide_width, self.slide_height)}vmin"
                geometry['emu']['cx'] = cx_emu
                geometry['emu']['cy'] = cy_emu

        return geometry

    def _extract_style(self, sp: ET.Element) -> Dict[str, Any]:
        """도형 스타일 추출."""
        style = {}

        # 폰트 크기
        defRPr = sp.find('.//a:defRPr', NAMESPACES)
        if defRPr is not None:
            sz = defRPr.get('sz')
            if sz:
                style['font_size'] = int(sz) / 100  # pt

        # 채우기 색상
        solidFill = sp.find('.//a:solidFill/a:srgbClr', NAMESPACES)
        if solidFill is not None:
            style['fill_color'] = f"#{solidFill.get('val', '')}"

        return style

    def _classify_category(self, shapes: List[ShapeInfo]) -> str:
        """도형 분석으로 카테고리 분류."""
        # 텍스트 수집
        all_text = ' '.join([s.text or '' for s in shapes if s.text])
        all_text_lower = all_text.lower()

        # 키워드 매칭
        for category, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in all_text_lower:
                    return category

        # 도형 타입 분석
        type_counts = {}
        for s in shapes:
            type_counts[s.type] = type_counts.get(s.type, 0) + 1

        # 차트/표가 있으면
        if type_counts.get('chart', 0) > 0:
            return 'chart'
        if type_counts.get('table', 0) > 0:
            return 'table'

        # 이미지가 많으면
        if type_counts.get('image', 0) >= 3:
            return 'grid'

        # 기본값
        return 'body'

    def _classify_slots_auto(self, shapes: List[ShapeInfo]) -> List[SlotInfo]:
        """규칙 기반 슬롯 분류."""
        slots = []
        used_ids = set()

        # 1. 제목 찾기 (상단 20% 영역, 가장 큰 텍스트)
        title_candidates = [
            s for s in shapes
            if s.type in ('text', 'placeholder')
            and s.text
            and s.position.get('y', 100) < 25
        ]

        if title_candidates:
            # 가장 큰 텍스트 선택
            title_candidates.sort(key=lambda s: s.style.get('font_size', 0), reverse=True)
            title = title_candidates[0]
            slots.append(SlotInfo(
                name='title',
                type='text',
                required=True,
                shape_ids=[title.id],
                example=title.text[:50] if title.text else None
            ))
            used_ids.add(title.id)

        # 2. 반복 패턴 감지 (비슷한 위치/크기의 도형들)
        remaining = [s for s in shapes if s.id not in used_ids and s.text]

        # Y 위치로 그룹화
        y_groups = {}
        for s in remaining:
            y_key = round(s.position.get('y', 0) / 10) * 10  # 10% 단위로 그룹화
            if y_key not in y_groups:
                y_groups[y_key] = []
            y_groups[y_key].append(s)

        # 가장 많은 그룹이 반복 패턴일 가능성
        if y_groups:
            max_group_y = max(y_groups.keys(), key=lambda k: len(y_groups[k]))
            items_group = y_groups[max_group_y]

            if len(items_group) >= 2:
                slots.append(SlotInfo(
                    name='items',
                    type='array',
                    required=True,
                    shape_ids=[s.id for s in items_group],
                    item_schema=[{'name': 'text', 'type': 'text'}]
                ))
                for s in items_group:
                    used_ids.add(s.id)

        # 3. 나머지 텍스트
        remaining_text = [s for s in shapes if s.id not in used_ids and s.text]
        for i, s in enumerate(remaining_text):
            slots.append(SlotInfo(
                name=f'text_{i+1}',
                type='text',
                required=False,
                shape_ids=[s.id],
                example=s.text[:30] if s.text else None
            ))

        # 4. 이미지
        images = [s for s in shapes if s.type == 'image' and s.id not in used_ids]
        if images:
            if len(images) == 1:
                slots.append(SlotInfo(
                    name='image',
                    type='image',
                    required=False,
                    shape_ids=[images[0].id]
                ))
            else:
                slots.append(SlotInfo(
                    name='images',
                    type='array',
                    required=False,
                    shape_ids=[s.id for s in images],
                    item_schema=[{'name': 'src', 'type': 'image'}]
                ))

        return slots

    def _classify_slots_llm(self, shapes: List[ShapeInfo]) -> List[SlotInfo]:
        """LLM 기반 슬롯 분류."""
        # LLM 사용 모드
        if self.use_llm:
            try:
                from shared.llm_interface import ClaudeLLM, LLMError
                print("    LLM 분류 시도 중...")

                llm = ClaudeLLM()
                shapes_info = [
                    {
                        'id': s.id,
                        'type': s.type,
                        'text': s.text[:100] if s.text else None,
                        'position': s.position,
                    }
                    for s in shapes
                ]

                result = llm.classify_slots(shapes_info, context=self.category)
                return self._parse_slot_json(result, shapes)

            except (ImportError, LLMError) as e:
                print(f"    LLM 분류 실패: {e}")
                print("    규칙 기반 분류로 폴백...")
                return self._classify_slots_auto(shapes)

        # 자동 모드가 아니면 입력 요청
        if not self.auto_classify:
            print("\n  슬롯 분류를 위한 입력이 필요합니다.")
            print("  도형 목록:")
            for i, s in enumerate(shapes):
                print(f"    [{i}] {s.type}: {s.text[:30] if s.text else '(텍스트 없음)'}")

            print("\n  JSON 형식으로 슬롯을 정의하세요 (자동 분류: Enter):")

            try:
                user_input = input().strip()
                if user_input:
                    data = json.loads(user_input)
                    return self._parse_slot_json(data, shapes)
            except (json.JSONDecodeError, EOFError):
                pass

        # 기본: 자동 분류
        return self._classify_slots_auto(shapes)

    def _parse_slot_json(self, data: Dict, shapes: List[ShapeInfo]) -> List[SlotInfo]:
        """JSON 입력을 SlotInfo 목록으로 변환."""
        slots = []
        for slot_data in data.get('slots', []):
            slot = SlotInfo(
                name=slot_data.get('name', 'unnamed'),
                type=slot_data.get('type', 'text'),
                required=slot_data.get('required', True),
                shape_ids=slot_data.get('shape_ids', []),
                example=slot_data.get('example'),
                item_schema=slot_data.get('item_schema')
            )
            slots.append(slot)
        return slots

    def _detect_pattern(self, shapes: List[ShapeInfo]) -> str:
        """레이아웃 패턴 감지."""
        # 이미지 개수
        image_count = len([s for s in shapes if s.type == 'image'])

        # 텍스트 개수
        text_count = len([s for s in shapes if s.text])

        # 패턴 결정
        if image_count >= 4:
            return f'grid-{image_count}'
        elif image_count >= 2:
            return f'multi-image-{image_count}'
        elif image_count == 1 and text_count >= 2:
            return 'image-with-text'
        elif text_count >= 4:
            return 'text-list'
        elif text_count >= 2:
            return 'title-body'
        else:
            return 'single'

    def _generate_semantic_description(self, shapes: List[ShapeInfo], slots: List[SlotInfo]) -> str:
        """시맨틱 설명 생성."""
        lines = []

        # 슬롯 기반 설명
        for slot in slots:
            if slot.name == 'title':
                lines.append(f"상단에 제목 텍스트 ({slot.type})")
            elif slot.name == 'items':
                count = len(slot.shape_ids)
                lines.append(f"{count}개 항목이 반복되는 구조 ({slot.type})")
            elif slot.type == 'image':
                lines.append(f"이미지 영역: {slot.name}")
            elif slot.type == 'text':
                lines.append(f"텍스트 영역: {slot.name}")

        # 레이아웃 특징
        image_count = len([s for s in shapes if s.type == 'image'])
        if image_count >= 3:
            lines.append(f"그리드 레이아웃 (이미지 {image_count}개)")

        return '\n'.join(lines) if lines else '기본 레이아웃'

    def _extract_keywords(self, shapes: List[ShapeInfo], category: str) -> List[str]:
        """검색 키워드 추출."""
        keywords = [category]

        # 카테고리 관련 키워드
        if category in CATEGORY_KEYWORDS:
            keywords.extend(CATEGORY_KEYWORDS[category][:3])

        # 도형 타입 기반 키워드
        types = set(s.type for s in shapes)
        if 'chart' in types:
            keywords.append('차트')
        if 'table' in types:
            keywords.append('표')
        if 'image' in types:
            keywords.append('이미지')

        return list(set(keywords))

    def _generate_template_id(self, category: str, slide_index: int) -> str:
        """템플릿 ID 생성."""
        prefix = self.source_document or 'default'
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"{prefix}-{category}-{slide_index+1:02d}-{timestamp}"

    def _save_template(self, template: ContentTemplate) -> None:
        """템플릿 저장."""
        # 출력 경로 결정
        if self.output_path:
            output_dir = Path(self.output_path) / template.id
        else:
            output_dir = (
                SCRIPT_DIR.parent.parent.parent
                / 'templates' / 'contents'
                / template.category / template.id
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"    저장 경로: {output_dir}")

        # 1. template.yaml 저장
        self._save_yaml(template, output_dir)

        # 2. template.html 저장
        self._save_html(template, output_dir)

        # 3. template.ooxml 저장
        self._save_ooxml(template, output_dir)

        # 4. thumbnail.png 저장
        self._save_thumbnail(template, output_dir)

    def _save_yaml(self, template: ContentTemplate, output_dir: Path) -> None:
        """template.yaml 저장."""
        # element_count 범위 계산
        element_count = None
        if template.variants:
            element_count = calculate_element_count_range(template.variants)

        # vmin 계산 (슬라이드 최소 치수)
        vmin_emu = calculate_vmin(self.slide_width, self.slide_height)
        vmin_px = int(vmin_emu / 914400 * 96)  # EMU to px (96 DPI)

        # 슬롯별 geometry 찾기 헬퍼
        def get_slot_geometry(slot: SlotInfo) -> Optional[Dict]:
            """슬롯에 해당하는 도형의 geometry 반환."""
            if not slot.shape_ids:
                return None
            for shape in template.shapes:
                if shape.id in slot.shape_ids and shape.geometry:
                    return shape.geometry
            return None

        yaml_data = {
            'id': template.id,
            'category': template.category,
            'pattern': template.pattern,
            'document_style': template.source_document,
            'source_type': 'pptx',
            'has_ooxml': True,
            # vmin 메타데이터
            'slide_size': self.parser.get_aspect_ratio(),
            'vmin': vmin_px,
            'slots': [
                {
                    'name': s.name,
                    'type': s.type,
                    'required': s.required,
                    **(
                        {'geometry': get_slot_geometry(s)} if get_slot_geometry(s) else {}
                    ),
                    **(
                        {'example': s.example} if s.example else {}
                    ),
                    **(
                        {'item_schema': s.item_schema} if s.item_schema else {}
                    )
                }
                for s in template.slots
            ],
            'semantic_description': template.semantic_description,
            'match_keywords': template.match_keywords,
            'source_file': template.source_file,
            'slide_index': template.slide_index + 1,
            'extracted_at': datetime.now().strftime('%Y-%m-%d')
        }

        # element_count 추가
        if element_count:
            yaml_data['element_count'] = element_count

        # variants 추가
        if template.variants:
            yaml_data['variants'] = [
                {
                    'count': v.count,
                    'layout': v.layout,
                    'source_slide': v.source_slide
                }
                for v in template.variants
            ]

        yaml_path = output_dir / 'template.yaml'
        header = f"콘텐츠 템플릿: {template.id}\n카테고리: {template.category}"
        save_yaml(yaml_data, yaml_path, header=header)
        print(f"      YAML: {yaml_path.name}")

    def _save_html(self, template: ContentTemplate, output_dir: Path) -> None:
        """template.html 저장 (Handlebars 템플릿 + vmin 좌표)."""
        # vmin 계산 (슬라이드 최소 치수, px)
        vmin_emu = calculate_vmin(self.slide_width, self.slide_height)
        vmin_px = int(vmin_emu / 914400 * 96)

        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '  <meta charset="UTF-8">',
            '  <style>',
            '    :root {',
            '      --primary: {{theme.primary}};',
            '      --background: {{theme.background}};',
            '      --text: {{theme.text}};',
            f'      --vmin: {vmin_px}px;',
            '    }',
            '    .slide {',
            '      width: 1920px;',
            '      height: 1080px;',
            '      background: var(--background);',
            '      color: var(--text);',
            '      position: relative;',
            '      font-family: sans-serif;',
            '    }',
            '    .element {',
            '      position: absolute;',
            '      box-sizing: border-box;',
            '    }',
            '  </style>',
            '</head>',
            '<body>',
            '  <div class="slide">',
        ]

        # 슬롯별 geometry 찾기 헬퍼
        def find_shape_for_slot(slot: SlotInfo) -> Optional[ShapeInfo]:
            if not slot.shape_ids:
                return None
            for shape in template.shapes:
                if shape.id in slot.shape_ids:
                    return shape
            return None

        # 슬롯 기반 HTML 생성 (geometry 포함)
        for slot in template.slots:
            shape = find_shape_for_slot(slot)
            style_attr = ''

            # geometry가 있으면 vmin 기반 스타일 적용
            if shape and shape.geometry:
                g = shape.geometry
                # vmin 문자열에서 숫자만 추출
                x_val = g.get('x', '0vmin').replace('vmin', '')
                y_val = g.get('y', '0vmin').replace('vmin', '')
                cx_val = g.get('cx', '0vmin').replace('vmin', '')
                cy_val = g.get('cy', '0vmin').replace('vmin', '')
                # calc()로 vmin 변환
                style_attr = (
                    f' style="'
                    f'left: calc({x_val} * var(--vmin) / 100); '
                    f'top: calc({y_val} * var(--vmin) / 100); '
                    f'width: calc({cx_val} * var(--vmin) / 100); '
                    f'height: calc({cy_val} * var(--vmin) / 100);'
                    f'"'
                )

            if slot.type == 'text':
                html_parts.append(f'    <div class="element text-{slot.name}"{style_attr}>{{{{{slot.name}}}}}</div>')
            elif slot.type == 'image':
                html_parts.append(f'    <img class="element img-{slot.name}"{style_attr} src="{{{{{slot.name}}}}}" />')
            elif slot.type == 'array':
                html_parts.append(f'    {{{{#each {slot.name}}}}}')
                html_parts.append(f'    <div class="element item-{slot.name}">{{{{this}}}}</div>')
                html_parts.append('    {{/each}}')

        html_parts.extend([
            '  </div>',
            '</body>',
            '</html>'
        ])

        html_path = output_dir / 'template.html'
        html_path.write_text('\n'.join(html_parts), encoding='utf-8')
        print(f"      HTML: {html_path.name}")

    def _save_ooxml(self, template: ContentTemplate, output_dir: Path) -> None:
        """template.ooxml 저장 (원본 XML + 플레이스홀더 마커)."""
        slide_path = f'ppt/slides/slide{template.slide_index + 1}.xml'

        # 원본 XML 읽기
        xml_content = self.parser.read_xml_string(slide_path, pretty=True)
        if xml_content is None:
            print(f"      OOXML: 스킵 (슬라이드 읽기 실패)")
            return

        # 슬롯 마커 삽입
        for slot in template.slots:
            if slot.type == 'text' and slot.example:
                # 예시 텍스트를 마커로 치환
                marker = f"__{slot.name.upper()}__"
                xml_content = xml_content.replace(slot.example, marker)

        ooxml_path = output_dir / 'template.ooxml'
        ooxml_path.write_text(xml_content, encoding='utf-8')
        print(f"      OOXML: {ooxml_path.name}")

    def _save_thumbnail(self, template: ContentTemplate, output_dir: Path) -> None:
        """thumbnail.png 저장 (슬라이드 썸네일).

        LibreOffice + pdftoppm 필요.
        """
        import tempfile

        thumbnail_path = output_dir / 'thumbnail.png'

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # PPTX → 이미지 변환
                images = convert_pptx_to_images(self.input_path, temp_path)

                # 해당 슬라이드 썸네일 생성
                slide_idx = template.slide_index
                if 0 <= slide_idx < len(images):
                    size = THUMBNAIL_SIZES['content']  # 960x540
                    create_thumbnail(images[slide_idx], size, thumbnail_path)
                    print(f"      썸네일: {thumbnail_path.name}")
                else:
                    print(f"      썸네일: 스킵 (슬라이드 {slide_idx} 없음)")

        except FileNotFoundError:
            print(f"      썸네일: 스킵 (LibreOffice/pdftoppm 미설치)")
        except Exception as e:
            print(f"      썸네일: 스킵 ({e})")
