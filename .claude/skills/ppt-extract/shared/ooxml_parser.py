#!/usr/bin/env python3
"""
OOXML 파싱 유틸리티.

PPTX 파일에서 XML을 추출하고 파싱하는 공통 유틸리티.
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


# OOXML 네임스페이스
NAMESPACES = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
    'dgm': 'http://schemas.openxmlformats.org/drawingml/2006/diagram',
    'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
}

# ElementTree에 네임스페이스 등록
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


@dataclass
class PlaceholderInfo:
    """플레이스홀더 정보."""
    idx: int
    type: str
    name: Optional[str]
    position: Dict[str, float]  # x, y, width, height (%)


@dataclass
class MediaReference:
    """미디어 파일 참조."""
    rid: str
    target: str
    type: str


class OOXMLParser:
    """OOXML 파서."""

    def __init__(self, pptx_path: Path):
        """
        Args:
            pptx_path: PPTX 파일 경로
        """
        self.pptx_path = Path(pptx_path)
        if not self.pptx_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {pptx_path}")

        self._slide_size: Optional[Tuple[int, int]] = None

    def get_slide_size(self) -> Tuple[int, int]:
        """슬라이드 크기 반환 (EMU 단위)."""
        if self._slide_size is None:
            self._slide_size = self._read_slide_size()
        return self._slide_size

    def _read_slide_size(self) -> Tuple[int, int]:
        """presentation.xml에서 슬라이드 크기 읽기."""
        with zipfile.ZipFile(self.pptx_path, 'r') as zf:
            if 'ppt/presentation.xml' not in zf.namelist():
                # 기본값: 16:9 (EMU)
                return (9144000, 6858000)

            with zf.open('ppt/presentation.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()

            # p:sldSz 요소 찾기
            sld_sz = root.find('.//p:sldSz', NAMESPACES)
            if sld_sz is not None:
                cx = int(sld_sz.get('cx', 9144000))
                cy = int(sld_sz.get('cy', 6858000))
                return (cx, cy)

        return (9144000, 6858000)

    def get_slide_size_px(self, dpi: int = 96) -> Tuple[int, int]:
        """슬라이드 크기 반환 (픽셀 단위)."""
        cx, cy = self.get_slide_size()
        # EMU to inches to pixels
        # 1 inch = 914400 EMU
        width = int(cx / 914400 * dpi)
        height = int(cy / 914400 * dpi)
        return (width, height)

    def get_aspect_ratio(self) -> str:
        """슬라이드 비율 문자열 반환."""
        cx, cy = self.get_slide_size()
        ratio = cx / cy

        if abs(ratio - 16/9) < 0.01:
            return "16:9"
        elif abs(ratio - 4/3) < 0.01:
            return "4:3"
        elif abs(ratio - 16/10) < 0.01:
            return "16:10"
        else:
            return f"{ratio:.2f}:1"

    def list_files(self, pattern: str = "*") -> List[str]:
        """PPTX 내부 파일 목록 반환."""
        with zipfile.ZipFile(self.pptx_path, 'r') as zf:
            all_files = zf.namelist()

        if pattern == "*":
            return all_files

        import fnmatch
        return [f for f in all_files if fnmatch.fnmatch(f, pattern)]

    def read_xml(self, internal_path: str) -> Optional[ET.Element]:
        """XML 파일 읽기."""
        with zipfile.ZipFile(self.pptx_path, 'r') as zf:
            if internal_path not in zf.namelist():
                return None

            with zf.open(internal_path) as f:
                tree = ET.parse(f)
                return tree.getroot()

    def read_xml_string(self, internal_path: str, pretty: bool = True) -> Optional[str]:
        """XML 파일을 문자열로 읽기."""
        with zipfile.ZipFile(self.pptx_path, 'r') as zf:
            if internal_path not in zf.namelist():
                return None

            with zf.open(internal_path) as f:
                content = f.read().decode('utf-8')

            if pretty:
                import xml.dom.minidom
                try:
                    dom = xml.dom.minidom.parseString(content)
                    content = dom.toprettyxml(indent='  ')
                    # 첫 번째 줄(XML 선언) 제거하고 반환
                    lines = content.split('\n')
                    if lines[0].startswith('<?xml'):
                        content = '\n'.join(lines[1:])
                except Exception:
                    pass  # 파싱 실패 시 원본 반환

            return content

    def read_binary(self, internal_path: str) -> Optional[bytes]:
        """바이너리 파일 읽기."""
        with zipfile.ZipFile(self.pptx_path, 'r') as zf:
            if internal_path not in zf.namelist():
                return None

            with zf.open(internal_path) as f:
                return f.read()

    def extract_file(self, internal_path: str, output_path: Path) -> bool:
        """파일 추출."""
        data = self.read_binary(internal_path)
        if data is None:
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(data)
        return True

    def get_layout_count(self) -> int:
        """슬라이드 레이아웃 개수 반환."""
        files = self.list_files('ppt/slideLayouts/*.xml')
        return len([f for f in files if not f.endswith('.rels')])

    def get_slide_count(self) -> int:
        """슬라이드 개수 반환."""
        files = self.list_files('ppt/slides/*.xml')
        return len([f for f in files if not f.endswith('.rels')])

    def parse_rels(self, rels_path: str) -> List[MediaReference]:
        """관계 파일 파싱."""
        root = self.read_xml(rels_path)
        if root is None:
            return []

        refs = []
        for rel in root.findall('.//rel:Relationship', NAMESPACES):
            rid = rel.get('Id', '')
            target = rel.get('Target', '')
            rel_type = rel.get('Type', '')

            # 타입에서 마지막 부분 추출 (image, theme, slideMaster 등)
            type_name = rel_type.split('/')[-1] if rel_type else ''

            refs.append(MediaReference(rid=rid, target=target, type=type_name))

        return refs

    def get_media_files(self) -> List[str]:
        """미디어 파일 목록 반환."""
        return self.list_files('ppt/media/*')

    def extract_placeholders(self, layout_xml: ET.Element) -> List[PlaceholderInfo]:
        """레이아웃에서 플레이스홀더 추출."""
        placeholders = []
        slide_cx, slide_cy = self.get_slide_size()

        # p:sp (shape) 요소 순회
        for sp in layout_xml.findall('.//p:sp', NAMESPACES):
            # 플레이스홀더 정보 찾기
            ph = sp.find('.//p:ph', NAMESPACES)
            if ph is None:
                continue

            idx = int(ph.get('idx', 0))
            ph_type = ph.get('type', 'body')

            # 이름 추출
            nv_sp_pr = sp.find('.//p:nvSpPr/p:nvPr', NAMESPACES)
            name = None
            if nv_sp_pr is not None:
                cNvPr = sp.find('.//p:nvSpPr/p:cNvPr', NAMESPACES)
                if cNvPr is not None:
                    name = cNvPr.get('name')

            # 위치 추출
            xfrm = sp.find('.//p:spPr/a:xfrm', NAMESPACES)
            position = {'x': 0, 'y': 0, 'width': 100, 'height': 100}

            if xfrm is not None:
                off = xfrm.find('a:off', NAMESPACES)
                ext = xfrm.find('a:ext', NAMESPACES)

                if off is not None:
                    x = int(off.get('x', 0))
                    y = int(off.get('y', 0))
                    position['x'] = round((x / slide_cx) * 100, 2)
                    position['y'] = round((y / slide_cy) * 100, 2)

                if ext is not None:
                    cx = int(ext.get('cx', 0))
                    cy = int(ext.get('cy', 0))
                    position['width'] = round((cx / slide_cx) * 100, 2)
                    position['height'] = round((cy / slide_cy) * 100, 2)

            placeholders.append(PlaceholderInfo(
                idx=idx,
                type=ph_type,
                name=name,
                position=position
            ))

        return placeholders

    def extract_theme_colors(self, theme_path: str = 'ppt/theme/theme1.xml') -> Dict[str, str]:
        """테마 색상 추출."""
        root = self.read_xml(theme_path)
        if root is None:
            return {}

        colors = {}
        color_elements = {
            'dk1': 'text_dark',
            'dk2': 'primary',
            'lt1': 'background',
            'lt2': 'surface',
            'accent1': 'accent1',
            'accent2': 'accent2',
            'accent3': 'accent3',
            'accent4': 'accent4',
            'accent5': 'accent5',
            'accent6': 'accent6',
            'hlink': 'hyperlink',
            'folHlink': 'followed_hyperlink',
        }

        clr_scheme = root.find('.//a:clrScheme', NAMESPACES)
        if clr_scheme is not None:
            for child in clr_scheme:
                tag = child.tag.split('}')[-1]
                if tag in color_elements:
                    color = self._get_color_value(child)
                    if color:
                        colors[tag] = color

        return colors

    def _get_color_value(self, element: ET.Element) -> Optional[str]:
        """색상 요소에서 색상값 추출."""
        # srgbClr (RGB 색상)
        srgb = element.find('.//a:srgbClr', NAMESPACES)
        if srgb is not None:
            val = srgb.get('val', '')
            return f"#{val}" if val else None

        # sysClr (시스템 색상)
        sys_clr = element.find('.//a:sysClr', NAMESPACES)
        if sys_clr is not None:
            last_clr = sys_clr.get('lastClr', '')
            return f"#{last_clr}" if last_clr else None

        return None

    def extract_theme_fonts(self, theme_path: str = 'ppt/theme/theme1.xml') -> Dict[str, str]:
        """테마 폰트 추출."""
        root = self.read_xml(theme_path)
        if root is None:
            return {}

        fonts = {}

        font_scheme = root.find('.//a:fontScheme', NAMESPACES)
        if font_scheme is not None:
            # Major font (제목용)
            major = font_scheme.find('.//a:majorFont/a:latin', NAMESPACES)
            if major is not None:
                fonts['major'] = major.get('typeface', '')

            major_ea = font_scheme.find('.//a:majorFont/a:ea', NAMESPACES)
            if major_ea is not None:
                fonts['major_ea'] = major_ea.get('typeface', '')

            # Minor font (본문용)
            minor = font_scheme.find('.//a:minorFont/a:latin', NAMESPACES)
            if minor is not None:
                fonts['minor'] = minor.get('typeface', '')

            minor_ea = font_scheme.find('.//a:minorFont/a:ea', NAMESPACES)
            if minor_ea is not None:
                fonts['minor_ea'] = minor_ea.get('typeface', '')

        return fonts


def emu_to_percent(value: int, total: int) -> float:
    """EMU 값을 퍼센트로 변환."""
    if total == 0:
        return 0.0
    return round((value / total) * 100, 2)


def emu_to_px(value: int, dpi: int = 96) -> int:
    """EMU 값을 픽셀로 변환."""
    # 1 inch = 914400 EMU
    return int(value / 914400 * dpi)


def px_to_emu(value: int, dpi: int = 96) -> int:
    """픽셀을 EMU로 변환."""
    return int(value * 914400 / dpi)


def calculate_vmin(slide_width: int, slide_height: int) -> int:
    """슬라이드의 vmin 값 계산 (EMU).

    vmin = min(width, height)
    슬라이드 비율 변경 시에도 도형 비율 유지를 위한 기준값.

    Args:
        slide_width: 슬라이드 너비 (EMU)
        slide_height: 슬라이드 높이 (EMU)

    Returns:
        vmin 값 (EMU)
    """
    return min(slide_width, slide_height)


def emu_to_vmin(value: int, slide_width: int, slide_height: int) -> float:
    """EMU 값을 vmin 단위로 변환.

    vmin = min(slide_width, slide_height) 기준으로 정규화.
    슬라이드 비율 변경 시에도 도형 비율 유지.

    Args:
        value: EMU 단위의 값
        slide_width: 슬라이드 너비 (EMU)
        slide_height: 슬라이드 높이 (EMU)

    Returns:
        vmin 단위의 값 (0.0 ~ 100.0+)

    Example:
        16:9 (9144000 x 6858000 EMU)에서 vmin = 6858000
        emu_to_vmin(914400, 9144000, 6858000) → 13.33
    """
    vmin = calculate_vmin(slide_width, slide_height)
    if vmin == 0:
        return 0.0
    return round((value / vmin) * 100, 2)


def vmin_to_emu(value: float, slide_width: int, slide_height: int) -> int:
    """vmin 단위를 EMU로 변환.

    Args:
        value: vmin 단위의 값 (0.0 ~ 100.0+)
        slide_width: 슬라이드 너비 (EMU)
        slide_height: 슬라이드 높이 (EMU)

    Returns:
        EMU 단위의 값
    """
    vmin = calculate_vmin(slide_width, slide_height)
    return int((value / 100) * vmin)
