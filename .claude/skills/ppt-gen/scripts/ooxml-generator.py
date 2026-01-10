#!/usr/bin/env python3
"""
OOXML 콘텐츠 생성기

콘텐츠 템플릿의 llm_guide/ooxml_export 정의를 기반으로
문서 양식의 content_zone에 삽입할 OOXML 요소를 생성합니다.

Usage:
    python ooxml-generator.py <content_yaml> <document_yaml> <data_json> <output_xml>

Example:
    python ooxml-generator.py \
        templates/contents/templates/grid/deepgreen-grid-3col1.yaml \
        templates/documents/dongkuk-systems/기본양식.yaml \
        data.json \
        output/slide_content.xml
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from xml.etree import ElementTree as ET

import yaml

# OOXML 네임스페이스
NAMESPACES = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}

# EMU 변환 상수
EMU_PER_INCH = 914400
EMU_PER_PT = 12700


@dataclass
class ContentZone:
    """문서 양식의 콘텐츠 삽입 영역"""
    x_emu: int
    y_emu: int
    width_emu: int
    height_emu: int

    @classmethod
    def from_yaml(cls, yaml_data: Dict) -> 'ContentZone':
        """YAML에서 ContentZone 생성"""
        bounds = yaml_data.get('bounds', {})
        return cls(
            x_emu=bounds.get('x_emu', 0),
            y_emu=bounds.get('y_emu', 0),
            width_emu=bounds.get('width_emu', 0),
            height_emu=bounds.get('height_emu', 0),
        )


@dataclass
class StyleTokens:
    """테마 색상 토큰"""
    colors: Dict[str, str]

    def resolve(self, token: str) -> str:
        """토큰을 실제 색상값으로 변환"""
        return self.colors.get(token, token)


class OOXMLGenerator:
    """OOXML 콘텐츠 생성기"""

    def __init__(self, content_yaml: Dict, document_yaml: Dict, theme_colors: Dict[str, str]):
        self.content = content_yaml
        self.document = document_yaml
        self.style_tokens = StyleTokens(colors=theme_colors)

        # content_zone 로드
        self.content_zone = self._load_content_zone()

        # ooxml_export 설정 로드
        self.ooxml_export = content_yaml.get('ooxml_export', {})
        self.llm_guide = content_yaml.get('llm_guide', {})

    def _load_content_zone(self) -> Optional[ContentZone]:
        """문서 양식에서 content_zone 로드"""
        layouts = self.document.get('layouts', [])
        for layout in layouts:
            if 'content_zone' in layout:
                return ContentZone.from_yaml(layout['content_zone'])
        return None

    def generate(self, data: Dict) -> ET.Element:
        """
        데이터를 바인딩하여 OOXML 요소 생성

        Args:
            data: 바인딩할 데이터 (llm_guide.data_slots 스키마에 맞는 데이터)

        Returns:
            ET.Element: spTree에 삽입할 OOXML 요소
        """
        export_type = self.ooxml_export.get('type', 'shapes')

        if export_type == 'grid':
            return self._generate_grid(data)
        elif export_type == 'chart':
            return self._generate_chart(data)
        elif export_type == 'shapes':
            return self._generate_shapes(data)
        else:
            raise ValueError(f"Unknown export type: {export_type}")

    def _generate_grid(self, data: Dict) -> ET.Element:
        """그리드 레이아웃 OOXML 생성"""
        # 그룹 요소 생성
        grp_sp = self._create_group_shape()

        layout = self.ooxml_export.get('layout', {})
        rows = layout.get('rows', 2)
        cols = layout.get('cols', 3)

        cards = data.get('cards', [])
        card_template = self.ooxml_export.get('card_template', {})

        # 각 카드에 대해 도형 생성
        for i, card_data in enumerate(cards):
            if i >= rows * cols:
                break

            row = i // cols
            col = i % cols

            # 카드 위치 계산
            card_bounds = self._calculate_card_bounds(row, col, rows, cols, layout)

            # 카드 도형들 생성
            card_shapes = self._generate_card_shapes(card_data, card_bounds, card_template)
            for shape in card_shapes:
                grp_sp.append(shape)

        return grp_sp

    def _generate_chart(self, data: Dict) -> ET.Element:
        """
        차트 OOXML 생성

        Note: PPTX 차트는 별도 XML 파일(/ppt/charts/chart*.xml)로 저장되어야 합니다.
        이 메서드는 차트 placeholder와 함께 차트 spec을 생성합니다.
        실제 차트 삽입은 insert-ooxml.py에서 처리하거나,
        pptxgenjs를 통해 html2pptx.js에서 처리할 수 있습니다.

        Returns:
            grpSp 요소 (차트 위치에 placeholder 텍스트와 차트 spec 주석 포함)
        """
        chart_config = self.ooxml_export.get('chart_config', {})
        chart_area = self.ooxml_export.get('chart_area', {})
        chart_data = data.get('chart_data', {})

        # 그룹 요소 생성 (차트 영역)
        grp_sp = self._create_group_shape()

        # 차트 배경 영역 (선택적)
        if chart_area.get('position'):
            bg_rect = self._create_chart_background(chart_area)
            grp_sp.append(bg_rect)

        # 차트 타입에 따른 요소 생성
        chart_type = chart_config.get('type', 'c:barChart')

        if chart_type == 'c:barChart':
            chart_shapes = self._generate_bar_chart_shapes(chart_data, chart_config, chart_area)
        elif chart_type == 'c:lineChart':
            chart_shapes = self._generate_line_chart_shapes(chart_data, chart_config, chart_area)
        elif chart_type == 'c:pieChart':
            chart_shapes = self._generate_pie_chart_shapes(chart_data, chart_config, chart_area)
        else:
            # 기본: 막대 차트
            chart_shapes = self._generate_bar_chart_shapes(chart_data, chart_config, chart_area)

        for shape in chart_shapes:
            grp_sp.append(shape)

        # 차트 spec을 JSON comment로 저장 (pptxgenjs 연동용)
        self._chart_spec = {
            'type': chart_config.get('type', 'c:barChart'),
            'subtype': self.ooxml_export.get('subtype', 'bar_chart'),
            'data': chart_data,
            'config': chart_config,
            'area': chart_area,
        }

        return grp_sp

    def _create_chart_background(self, chart_area: Dict) -> ET.Element:
        """차트 배경 사각형 생성"""
        sp = ET.Element(f"{{{NAMESPACES['p']}}}sp")

        nv_sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}nvSpPr")
        c_nv_pr = ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', '3000')
        c_nv_pr.set('name', 'Chart Background')
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvSpPr")
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}nvPr")

        sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}spPr")
        xfrm = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}xfrm")

        pos = chart_area.get('position', {})
        if self.content_zone and pos:
            x = int(self.content_zone.x_emu + self.content_zone.width_emu * pos.get('x_pct', 0) / 100)
            y = int(self.content_zone.y_emu + self.content_zone.height_emu * pos.get('y_pct', 0) / 100)
            w = int(self.content_zone.width_emu * pos.get('w_pct', 100) / 100)
            h = int(self.content_zone.height_emu * pos.get('h_pct', 100) / 100)
            ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off", x=str(x), y=str(y))
            ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext", cx=str(w), cy=str(h))

        prst_geom = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}prstGeom", prst='rect')
        ET.SubElement(prst_geom, f"{{{NAMESPACES['a']}}}avLst")

        # 투명 배경 (차트 영역 표시용)
        no_fill = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}noFill")

        return sp

    def _generate_bar_chart_shapes(self, chart_data: Dict, config: Dict, area: Dict) -> List[ET.Element]:
        """막대 차트를 도형으로 표현 (OOXML 네이티브 차트 대신)"""
        shapes = []

        categories = chart_data.get('categories', [])
        series_list = chart_data.get('series', [])

        if not categories or not series_list:
            return shapes

        # 차트 영역 계산
        pos = area.get('position', {})
        if not self.content_zone or not pos:
            return shapes

        chart_x = int(self.content_zone.x_emu + self.content_zone.width_emu * pos.get('x_pct', 0) / 100)
        chart_y = int(self.content_zone.y_emu + self.content_zone.height_emu * pos.get('y_pct', 0) / 100)
        chart_w = int(self.content_zone.width_emu * pos.get('w_pct', 100) / 100)
        chart_h = int(self.content_zone.height_emu * pos.get('h_pct', 100) / 100)

        # 최대값 찾기 (스케일 계산용)
        max_val = 0
        for series in series_list:
            for val in series.get('values', []):
                if val > max_val:
                    max_val = val

        if max_val == 0:
            max_val = 1

        # 막대 파라미터
        bar_dir = config.get('bar_dir', 'col')  # col: 수직, bar: 수평
        num_categories = len(categories)
        num_series = len(series_list)

        # 영역 분배
        label_height = int(chart_h * 0.12)  # 카테고리 레이블 영역
        value_label_width = int(chart_w * 0.08)  # 값 레이블 영역
        bar_area_w = chart_w - value_label_width
        bar_area_h = chart_h - label_height

        # 각 카테고리별 그룹 너비
        group_width = bar_area_w // num_categories
        bar_width = int(group_width * 0.7 / num_series)
        bar_gap = int(group_width * 0.1)

        # 막대 생성
        for cat_idx, category in enumerate(categories):
            for ser_idx, series in enumerate(series_list):
                values = series.get('values', [])
                if cat_idx >= len(values):
                    continue

                value = values[cat_idx]

                # 막대 위치/크기 계산
                if bar_dir == 'col':
                    # 수직 막대
                    bar_h_ratio = value / max_val
                    bar_height = int(bar_area_h * bar_h_ratio * 0.85)

                    bar_x = chart_x + value_label_width + cat_idx * group_width + bar_gap + ser_idx * bar_width
                    bar_y = chart_y + bar_area_h - bar_height
                    bar_cx = bar_width
                    bar_cy = bar_height
                else:
                    # 수평 막대
                    bar_w_ratio = value / max_val
                    bar_actual_width = int(bar_area_w * bar_w_ratio * 0.85)

                    bar_x = chart_x + value_label_width
                    bar_y = chart_y + cat_idx * (bar_area_h // num_categories) + bar_gap + ser_idx * bar_width
                    bar_cx = bar_actual_width
                    bar_cy = bar_width

                # 막대 도형 생성
                color_token = series.get('color', 'primary')
                bar_shape = self._create_bar_shape(
                    bar_x, bar_y, bar_cx, bar_cy,
                    color_token, f"Bar_{cat_idx}_{ser_idx}"
                )
                shapes.append(bar_shape)

                # 값 레이블 (막대 위에)
                if config.get('data_labels', {}).get('show_value', True):
                    label_shape = self._create_value_label(
                        bar_x, bar_y - int(EMU_PER_PT * 20),  # 막대 위
                        bar_cx, int(EMU_PER_PT * 18),
                        str(value), config.get('data_labels', {})
                    )
                    shapes.append(label_shape)

            # 카테고리 레이블
            cat_label_x = chart_x + value_label_width + cat_idx * group_width
            cat_label_y = chart_y + bar_area_h + int(EMU_PER_PT * 5)
            cat_label_shape = self._create_category_label(
                cat_label_x, cat_label_y, group_width, label_height,
                category, config.get('cat_axis', {})
            )
            shapes.append(cat_label_shape)

        return shapes

    def _create_bar_shape(self, x: int, y: int, cx: int, cy: int,
                          color_token: str, name: str) -> ET.Element:
        """막대 도형 생성"""
        sp = ET.Element(f"{{{NAMESPACES['p']}}}sp")

        nv_sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}nvSpPr")
        c_nv_pr = ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', str(hash(name) % 10000))
        c_nv_pr.set('name', name)
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvSpPr")
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}nvPr")

        sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}spPr")
        xfrm = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}xfrm")
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off", x=str(x), y=str(y))
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext", cx=str(max(cx, 1)), cy=str(max(cy, 1)))

        prst_geom = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}prstGeom", prst='rect')
        ET.SubElement(prst_geom, f"{{{NAMESPACES['a']}}}avLst")

        # 색상 적용
        color = self.style_tokens.resolve(color_token)
        solid_fill = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}solidFill")
        srgb_clr = ET.SubElement(solid_fill, f"{{{NAMESPACES['a']}}}srgbClr")
        srgb_clr.set('val', color.lstrip('#'))

        return sp

    def _create_value_label(self, x: int, y: int, cx: int, cy: int,
                            value: str, label_config: Dict) -> ET.Element:
        """값 레이블 텍스트박스 생성"""
        sp = ET.Element(f"{{{NAMESPACES['p']}}}sp")

        nv_sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}nvSpPr")
        c_nv_pr = ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', str(hash(f"label_{value}") % 10000))
        c_nv_pr.set('name', f'Value Label {value}')
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvSpPr", txBox='1')
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}nvPr")

        sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}spPr")
        xfrm = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}xfrm")
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off", x=str(x), y=str(y))
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext", cx=str(max(cx, 1)), cy=str(max(cy, 1)))

        prst_geom = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}prstGeom", prst='rect')
        ET.SubElement(prst_geom, f"{{{NAMESPACES['a']}}}avLst")

        tx_body = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}txBody")
        body_pr = ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}bodyPr")
        ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}lstStyle")

        p = ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}p")
        p_pr = ET.SubElement(p, f"{{{NAMESPACES['a']}}}pPr", algn='ctr')
        r = ET.SubElement(p, f"{{{NAMESPACES['a']}}}r")

        font_size = label_config.get('font_size_pt', 9)
        r_pr = ET.SubElement(r, f"{{{NAMESPACES['a']}}}rPr", lang='ko-KR')
        r_pr.set('sz', str(int(font_size * 100)))

        t = ET.SubElement(r, f"{{{NAMESPACES['a']}}}t")
        t.text = value

        return sp

    def _create_category_label(self, x: int, y: int, cx: int, cy: int,
                               category: str, axis_config: Dict) -> ET.Element:
        """카테고리 레이블 텍스트박스 생성"""
        sp = ET.Element(f"{{{NAMESPACES['p']}}}sp")

        nv_sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}nvSpPr")
        c_nv_pr = ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', str(hash(f"cat_{category}") % 10000))
        c_nv_pr.set('name', f'Category {category}')
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvSpPr", txBox='1')
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}nvPr")

        sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}spPr")
        xfrm = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}xfrm")
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off", x=str(x), y=str(y))
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext", cx=str(max(cx, 1)), cy=str(max(cy, 1)))

        prst_geom = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}prstGeom", prst='rect')
        ET.SubElement(prst_geom, f"{{{NAMESPACES['a']}}}avLst")

        tx_body = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}txBody")
        body_pr = ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}bodyPr")
        ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}lstStyle")

        p = ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}p")
        p_pr = ET.SubElement(p, f"{{{NAMESPACES['a']}}}pPr", algn='ctr')
        r = ET.SubElement(p, f"{{{NAMESPACES['a']}}}r")

        font_size = axis_config.get('font_size_pt', 10)
        font_color_token = axis_config.get('font_color_token', 'gray')
        color = self.style_tokens.resolve(font_color_token)

        r_pr = ET.SubElement(r, f"{{{NAMESPACES['a']}}}rPr", lang='ko-KR')
        r_pr.set('sz', str(int(font_size * 100)))

        solid_fill = ET.SubElement(r_pr, f"{{{NAMESPACES['a']}}}solidFill")
        srgb_clr = ET.SubElement(solid_fill, f"{{{NAMESPACES['a']}}}srgbClr")
        srgb_clr.set('val', color.lstrip('#'))

        t = ET.SubElement(r, f"{{{NAMESPACES['a']}}}t")
        t.text = category

        return sp

    def _generate_line_chart_shapes(self, chart_data: Dict, config: Dict, area: Dict) -> List[ET.Element]:
        """라인 차트를 도형으로 표현"""
        # 막대 차트와 유사하게 구현하되, 선과 점으로 표현
        # TODO: 상세 구현
        return self._generate_bar_chart_shapes(chart_data, config, area)

    def _generate_pie_chart_shapes(self, chart_data: Dict, config: Dict, area: Dict) -> List[ET.Element]:
        """파이 차트를 도형으로 표현"""
        # TODO: 파이 차트 구현 (원형 세그먼트)
        return []

    def get_chart_spec(self) -> Optional[Dict]:
        """생성된 차트 spec 반환 (pptxgenjs 연동용)"""
        return getattr(self, '_chart_spec', None)

    def _generate_shapes(self, data: Dict) -> ET.Element:
        """일반 도형 OOXML 생성"""
        grp_sp = self._create_group_shape()

        # shapes 정의에서 semantic_role 기반으로 데이터 바인딩
        shapes = self.content.get('shapes', [])

        for shape_def in shapes:
            role = shape_def.get('semantic_role', '')
            shape_type = shape_def.get('type', '')

            if 'text_box' in shape_type:
                shape_el = self._create_textbox(shape_def, data)
            elif 'auto_shape' in shape_type:
                shape_el = self._create_auto_shape(shape_def, data)
            elif 'line' in shape_type:
                shape_el = self._create_line(shape_def)
            else:
                continue

            if shape_el is not None:
                grp_sp.append(shape_el)

        return grp_sp

    def _create_group_shape(self) -> ET.Element:
        """grpSp 요소 생성"""
        ET.register_namespace('a', NAMESPACES['a'])
        ET.register_namespace('p', NAMESPACES['p'])
        ET.register_namespace('r', NAMESPACES['r'])

        grp_sp = ET.Element(f"{{{NAMESPACES['p']}}}grpSp")

        # nvGrpSpPr
        nv_grp_sp_pr = ET.SubElement(grp_sp, f"{{{NAMESPACES['p']}}}nvGrpSpPr")
        c_nv_pr = ET.SubElement(nv_grp_sp_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', '1000')
        c_nv_pr.set('name', 'Generated Content')
        ET.SubElement(nv_grp_sp_pr, f"{{{NAMESPACES['p']}}}cNvGrpSpPr")
        ET.SubElement(nv_grp_sp_pr, f"{{{NAMESPACES['p']}}}nvPr")

        # grpSpPr
        grp_sp_pr = ET.SubElement(grp_sp, f"{{{NAMESPACES['p']}}}grpSpPr")
        xfrm = ET.SubElement(grp_sp_pr, f"{{{NAMESPACES['a']}}}xfrm")

        if self.content_zone:
            ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off",
                         x=str(self.content_zone.x_emu),
                         y=str(self.content_zone.y_emu))
            ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext",
                         cx=str(self.content_zone.width_emu),
                         cy=str(self.content_zone.height_emu))
        else:
            ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off", x='0', y='0')
            ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext", cx='0', cy='0')

        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}chOff", x='0', y='0')
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}chExt", cx='0', cy='0')

        return grp_sp

    def _create_graphic_frame(self) -> ET.Element:
        """graphicFrame 요소 생성 (차트용)"""
        graphic_frame = ET.Element(f"{{{NAMESPACES['p']}}}graphicFrame")

        # nvGraphicFramePr
        nv_pr = ET.SubElement(graphic_frame, f"{{{NAMESPACES['p']}}}nvGraphicFramePr")
        c_nv_pr = ET.SubElement(nv_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', '2000')
        c_nv_pr.set('name', 'Generated Chart')
        ET.SubElement(nv_pr, f"{{{NAMESPACES['p']}}}cNvGraphicFramePr")
        ET.SubElement(nv_pr, f"{{{NAMESPACES['p']}}}nvPr")

        # xfrm
        xfrm = ET.SubElement(graphic_frame, f"{{{NAMESPACES['p']}}}xfrm")
        chart_area = self.ooxml_export.get('chart_area', {}).get('position', {})

        if self.content_zone and chart_area:
            x = int(self.content_zone.x_emu + self.content_zone.width_emu * chart_area.get('x_pct', 0) / 100)
            y = int(self.content_zone.y_emu + self.content_zone.height_emu * chart_area.get('y_pct', 0) / 100)
            w = int(self.content_zone.width_emu * chart_area.get('w_pct', 100) / 100)
            h = int(self.content_zone.height_emu * chart_area.get('h_pct', 100) / 100)

            ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off", x=str(x), y=str(y))
            ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext", cx=str(w), cy=str(h))

        return graphic_frame

    def _create_textbox(self, shape_def: Dict, data: Dict) -> Optional[ET.Element]:
        """텍스트박스 sp 요소 생성"""
        sp = ET.Element(f"{{{NAMESPACES['p']}}}sp")

        # nvSpPr
        nv_sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}nvSpPr")
        c_nv_pr = ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', str(hash(shape_def.get('id', '')) % 10000))
        c_nv_pr.set('name', shape_def.get('name', 'TextBox'))
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvSpPr", txBox='1')
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}nvPr")

        # spPr
        sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}spPr")
        xfrm = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}xfrm")

        geometry = shape_def.get('geometry', {})
        bounds = self._calculate_bounds_from_pct(geometry)

        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off",
                     x=str(bounds['x']), y=str(bounds['y']))
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext",
                     cx=str(bounds['cx']), cy=str(bounds['cy']))

        prst_geom = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}prstGeom", prst='rect')
        ET.SubElement(prst_geom, f"{{{NAMESPACES['a']}}}avLst")

        # txBody
        tx_body = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}txBody")
        body_pr = ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}bodyPr")
        ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}lstStyle")

        # 텍스트 바인딩
        text_content = self._resolve_text_binding(shape_def, data)

        p = ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}p")
        r = ET.SubElement(p, f"{{{NAMESPACES['a']}}}r")

        # 텍스트 스타일
        r_pr = ET.SubElement(r, f"{{{NAMESPACES['a']}}}rPr", lang='ko-KR')
        text_def = shape_def.get('text', {})
        if text_def.get('font_size_pt'):
            r_pr.set('sz', str(int(text_def['font_size_pt'] * 100)))
        if text_def.get('font_color'):
            solid_fill = ET.SubElement(r_pr, f"{{{NAMESPACES['a']}}}solidFill")
            srgb_clr = ET.SubElement(solid_fill, f"{{{NAMESPACES['a']}}}srgbClr")
            color = self.style_tokens.resolve(text_def['font_color'].lstrip('#'))
            srgb_clr.set('val', color.lstrip('#'))

        t = ET.SubElement(r, f"{{{NAMESPACES['a']}}}t")
        t.text = text_content

        return sp

    def _create_auto_shape(self, shape_def: Dict, data: Dict) -> Optional[ET.Element]:
        """자동 도형 sp 요소 생성"""
        sp = ET.Element(f"{{{NAMESPACES['p']}}}sp")

        # nvSpPr
        nv_sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}nvSpPr")
        c_nv_pr = ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', str(hash(shape_def.get('id', '')) % 10000))
        c_nv_pr.set('name', shape_def.get('name', 'AutoShape'))
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvSpPr")
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}nvPr")

        # spPr
        sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}spPr")
        xfrm = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}xfrm")

        geometry = shape_def.get('geometry', {})
        bounds = self._calculate_bounds_from_pct(geometry)

        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off",
                     x=str(bounds['x']), y=str(bounds['y']))
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext",
                     cx=str(bounds['cx']), cy=str(bounds['cy']))

        # 도형 타입 추론
        name = shape_def.get('name', '').lower()
        if '타원' in name or 'ellipse' in name:
            prst = 'ellipse'
        elif '삼각형' in name or 'triangle' in name:
            prst = 'rtTriangle'
        elif '둥근 모서리' in name or 'round' in name:
            prst = 'roundRect'
        else:
            prst = 'rect'

        prst_geom = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}prstGeom", prst=prst)
        ET.SubElement(prst_geom, f"{{{NAMESPACES['a']}}}avLst")

        # 채우기
        style = shape_def.get('style', {})
        fill = style.get('fill', {})
        if fill.get('type') == 'solid' and fill.get('color'):
            solid_fill = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}solidFill")
            srgb_clr = ET.SubElement(solid_fill, f"{{{NAMESPACES['a']}}}srgbClr")
            color = self.style_tokens.resolve(fill['color'].lstrip('#'))
            srgb_clr.set('val', color.lstrip('#'))

        # 텍스트가 있는 경우
        text_def = shape_def.get('text', {})
        if text_def.get('has_text'):
            tx_body = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}txBody")
            body_pr = ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}bodyPr")
            ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}lstStyle")

            text_content = self._resolve_text_binding(shape_def, data)

            p = ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}p")
            r = ET.SubElement(p, f"{{{NAMESPACES['a']}}}r")
            r_pr = ET.SubElement(r, f"{{{NAMESPACES['a']}}}rPr", lang='ko-KR')
            t = ET.SubElement(r, f"{{{NAMESPACES['a']}}}t")
            t.text = text_content

        return sp

    def _create_line(self, shape_def: Dict) -> Optional[ET.Element]:
        """연결선 cxnSp 요소 생성"""
        cxn_sp = ET.Element(f"{{{NAMESPACES['p']}}}cxnSp")

        # nvCxnSpPr
        nv_pr = ET.SubElement(cxn_sp, f"{{{NAMESPACES['p']}}}nvCxnSpPr")
        c_nv_pr = ET.SubElement(nv_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', str(hash(shape_def.get('id', '')) % 10000))
        c_nv_pr.set('name', shape_def.get('name', 'Line'))
        ET.SubElement(nv_pr, f"{{{NAMESPACES['p']}}}cNvCxnSpPr")
        ET.SubElement(nv_pr, f"{{{NAMESPACES['p']}}}nvPr")

        # spPr
        sp_pr = ET.SubElement(cxn_sp, f"{{{NAMESPACES['p']}}}spPr")
        xfrm = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}xfrm")

        geometry = shape_def.get('geometry', {})
        bounds = self._calculate_bounds_from_pct(geometry)

        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off",
                     x=str(bounds['x']), y=str(bounds['y']))
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext",
                     cx=str(bounds['cx']), cy=str(max(bounds['cy'], 1)))

        prst_geom = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}prstGeom", prst='line')
        ET.SubElement(prst_geom, f"{{{NAMESPACES['a']}}}avLst")

        return cxn_sp

    def _calculate_bounds_from_pct(self, geometry: Dict) -> Dict[str, int]:
        """백분율 좌표를 EMU로 변환"""
        if not self.content_zone:
            return {'x': 0, 'y': 0, 'cx': 0, 'cy': 0}

        def parse_pct(val):
            if isinstance(val, str) and val.endswith('%'):
                return float(val.rstrip('%'))
            return float(val) if val else 0

        x_pct = parse_pct(geometry.get('x', 0))
        y_pct = parse_pct(geometry.get('y', 0))
        cx_pct = parse_pct(geometry.get('cx', 0))
        cy_pct = parse_pct(geometry.get('cy', 0))

        return {
            'x': int(self.content_zone.x_emu + self.content_zone.width_emu * x_pct / 100),
            'y': int(self.content_zone.y_emu + self.content_zone.height_emu * y_pct / 100),
            'cx': int(self.content_zone.width_emu * cx_pct / 100),
            'cy': int(self.content_zone.height_emu * cy_pct / 100),
        }

    def _calculate_card_bounds(self, row: int, col: int, rows: int, cols: int, layout: Dict) -> Dict[str, int]:
        """카드 위치 계산"""
        if not self.content_zone:
            return {'x': 0, 'y': 0, 'cx': 0, 'cy': 0}

        margin = layout.get('margin', {})
        gap_x = layout.get('gap_x_pct', 2)
        gap_y = layout.get('gap_y_pct', 3)

        # 사용 가능한 영역 계산
        usable_width = self.content_zone.width_emu
        usable_height = self.content_zone.height_emu

        # 카드 크기 계산
        total_gap_x = (cols - 1) * gap_x
        total_gap_y = (rows - 1) * gap_y
        card_width = int(usable_width * (100 - total_gap_x) / 100 / cols)
        card_height = int(usable_height * (100 - total_gap_y) / 100 / rows)

        # 카드 위치 계산
        x = self.content_zone.x_emu + int(col * (card_width + usable_width * gap_x / 100))
        y = self.content_zone.y_emu + int(row * (card_height + usable_height * gap_y / 100))

        return {'x': x, 'y': y, 'cx': card_width, 'cy': card_height}

    def _generate_card_shapes(self, card_data: Dict, bounds: Dict[str, int], template: Dict) -> List[ET.Element]:
        """카드 도형들 생성"""
        shapes = []
        elements = template.get('elements', [])

        for elem in elements:
            elem_type = elem.get('type', '')

            if elem_type == 'rounded_rect':
                shape = self._create_rounded_rect(bounds, elem)
            elif elem_type == 'ellipse':
                shape = self._create_ellipse_badge(bounds, elem, card_data)
            elif elem_type == 'textbox':
                shape = self._create_card_textbox(bounds, elem, card_data)
            else:
                continue

            if shape is not None:
                shapes.append(shape)

        return shapes

    def _create_rounded_rect(self, bounds: Dict, elem: Dict) -> ET.Element:
        """둥근 모서리 사각형 생성"""
        sp = ET.Element(f"{{{NAMESPACES['p']}}}sp")

        nv_sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}nvSpPr")
        c_nv_pr = ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', str(hash(str(bounds)) % 10000))
        c_nv_pr.set('name', 'Card Background')
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvSpPr")
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}nvPr")

        sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}spPr")
        xfrm = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}xfrm")
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off", x=str(bounds['x']), y=str(bounds['y']))
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext", cx=str(bounds['cx']), cy=str(bounds['cy']))

        prst_geom = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}prstGeom", prst='roundRect')
        ET.SubElement(prst_geom, f"{{{NAMESPACES['a']}}}avLst")

        # 채우기
        fill_token = elem.get('fill_token', 'primary')
        color = self.style_tokens.resolve(fill_token)
        solid_fill = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}solidFill")
        srgb_clr = ET.SubElement(solid_fill, f"{{{NAMESPACES['a']}}}srgbClr")
        srgb_clr.set('val', color.lstrip('#'))

        return sp

    def _create_ellipse_badge(self, bounds: Dict, elem: Dict, card_data: Dict) -> ET.Element:
        """번호 뱃지 타원 생성"""
        sp = ET.Element(f"{{{NAMESPACES['p']}}}sp")

        # 위치 계산
        offset = elem.get('offset', {})
        size = elem.get('size', {})
        x = bounds['x'] + int(bounds['cx'] * float(offset.get('x', 0).rstrip('%')) / 100)
        y = bounds['y'] + int(bounds['cy'] * float(offset.get('y', 0).rstrip('%')) / 100)
        cx = int(bounds['cx'] * float(size.get('w', 10).rstrip('%')) / 100)
        cy = int(bounds['cy'] * float(size.get('h', 10).rstrip('%')) / 100)

        nv_sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}nvSpPr")
        c_nv_pr = ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', str(hash(str(bounds) + 'badge') % 10000))
        c_nv_pr.set('name', 'Number Badge')
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvSpPr")
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}nvPr")

        sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}spPr")
        xfrm = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}xfrm")
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off", x=str(x), y=str(y))
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext", cx=str(cx), cy=str(cy))

        prst_geom = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}prstGeom", prst='ellipse')
        ET.SubElement(prst_geom, f"{{{NAMESPACES['a']}}}avLst")

        fill_token = elem.get('fill_token', 'accent')
        color = self.style_tokens.resolve(fill_token)
        solid_fill = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}solidFill")
        srgb_clr = ET.SubElement(solid_fill, f"{{{NAMESPACES['a']}}}srgbClr")
        srgb_clr.set('val', color.lstrip('#'))

        # 텍스트 (번호)
        tx_body = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}txBody")
        ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}bodyPr")
        ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}lstStyle")

        p = ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}p")
        p_pr = ET.SubElement(p, f"{{{NAMESPACES['a']}}}pPr", algn='ctr')
        r = ET.SubElement(p, f"{{{NAMESPACES['a']}}}r")
        ET.SubElement(r, f"{{{NAMESPACES['a']}}}rPr", lang='ko-KR')
        t = ET.SubElement(r, f"{{{NAMESPACES['a']}}}t")

        text_binding = elem.get('text_binding', 'number')
        t.text = str(card_data.get(text_binding, ''))

        return sp

    def _create_card_textbox(self, bounds: Dict, elem: Dict, card_data: Dict) -> ET.Element:
        """카드 텍스트박스 생성"""
        sp = ET.Element(f"{{{NAMESPACES['p']}}}sp")

        offset = elem.get('offset', {})
        size = elem.get('size', {})
        x = bounds['x'] + int(bounds['cx'] * float(offset.get('x', 0).rstrip('%')) / 100)
        y = bounds['y'] + int(bounds['cy'] * float(offset.get('y', 0).rstrip('%')) / 100)
        cx = int(bounds['cx'] * float(size.get('w', 90).rstrip('%')) / 100)
        cy = int(bounds['cy'] * float(size.get('h', 20).rstrip('%')) / 100)

        nv_sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}nvSpPr")
        c_nv_pr = ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvPr")
        c_nv_pr.set('id', str(hash(str(bounds) + elem.get('role', '')) % 10000))
        c_nv_pr.set('name', elem.get('role', 'TextBox'))
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}cNvSpPr", txBox='1')
        ET.SubElement(nv_sp_pr, f"{{{NAMESPACES['p']}}}nvPr")

        sp_pr = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}spPr")
        xfrm = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}xfrm")
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}off", x=str(x), y=str(y))
        ET.SubElement(xfrm, f"{{{NAMESPACES['a']}}}ext", cx=str(cx), cy=str(cy))

        prst_geom = ET.SubElement(sp_pr, f"{{{NAMESPACES['a']}}}prstGeom", prst='rect')
        ET.SubElement(prst_geom, f"{{{NAMESPACES['a']}}}avLst")

        tx_body = ET.SubElement(sp, f"{{{NAMESPACES['p']}}}txBody")
        ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}bodyPr")
        ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}lstStyle")

        p = ET.SubElement(tx_body, f"{{{NAMESPACES['a']}}}p")
        style = elem.get('style', {})
        if style.get('alignment') == 'left':
            ET.SubElement(p, f"{{{NAMESPACES['a']}}}pPr", algn='l')

        r = ET.SubElement(p, f"{{{NAMESPACES['a']}}}r")
        r_pr = ET.SubElement(r, f"{{{NAMESPACES['a']}}}rPr", lang='ko-KR')
        if style.get('font_size_pt'):
            r_pr.set('sz', str(int(style['font_size_pt'] * 100)))

        t = ET.SubElement(r, f"{{{NAMESPACES['a']}}}t")
        text_binding = elem.get('text_binding', '')
        t.text = str(card_data.get(text_binding, ''))

        return sp

    def _resolve_text_binding(self, shape_def: Dict, data: Dict) -> str:
        """시맨틱 역할 기반 텍스트 바인딩"""
        role = shape_def.get('semantic_role', '')

        # 슬라이드 레벨 바인딩
        if role == 'slide_title':
            return data.get('title', '')
        elif role == 'slide_subtitle':
            return data.get('subtitle', '')

        # 카드 레벨 바인딩
        card_index = shape_def.get('card_index')
        if card_index is not None:
            cards = data.get('cards', [])
            if card_index < len(cards):
                card = cards[card_index]
                if role == 'card_title':
                    return card.get('title', '')
                elif role == 'card_description':
                    return card.get('description', '')
                elif role == 'card_number_badge':
                    return str(card.get('number', card_index + 1))

        # 기본값: 샘플 텍스트
        return shape_def.get('text', {}).get('sample_text', '')


def load_yaml(path: str) -> Dict:
    """YAML 파일 로드"""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_theme_colors(document_yaml: Dict) -> Dict[str, str]:
    """문서 템플릿에서 테마 색상 로드"""
    # 기본 색상
    default_colors = {
        'primary': '#002452',
        'secondary': '#C51F2A',
        'accent': '#A1BFB4',
        'dark': '#153325',
        'dark_text': '#262626',
        'light': '#FFFFFF',
        'gray': '#B6B6B6',
    }

    # 문서 템플릿에서 색상 추출 시도
    # (config.yaml이 있다면 거기서 로드)
    return default_colors


def main():
    parser = argparse.ArgumentParser(description='OOXML 콘텐츠 생성기')
    parser.add_argument('content_yaml', help='콘텐츠 템플릿 YAML 파일')
    parser.add_argument('document_yaml', help='문서 템플릿 YAML 파일')
    parser.add_argument('data_json', help='바인딩할 데이터 JSON 파일')
    parser.add_argument('output_xml', help='출력 XML 파일')

    args = parser.parse_args()

    # 파일 로드
    content_yaml = load_yaml(args.content_yaml)
    document_yaml = load_yaml(args.document_yaml)

    with open(args.data_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 테마 색상 로드
    theme_colors = load_theme_colors(document_yaml)

    # OOXML 생성
    generator = OOXMLGenerator(content_yaml, document_yaml, theme_colors)
    result = generator.generate(data)

    # XML 출력
    tree = ET.ElementTree(result)
    ET.indent(tree, space='  ')
    tree.write(args.output_xml, encoding='unicode', xml_declaration=True)

    print(f"Generated: {args.output_xml}")


if __name__ == '__main__':
    main()
