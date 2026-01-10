#!/usr/bin/env python3
"""
Slide Content Analyzer - 슬라이드 콘텐츠 OOXML 완전 추출

슬라이드의 모든 요소(도형, 이미지, 연결선, SmartArt)를 분석하여
콘텐츠 템플릿 YAML을 생성합니다.

Usage:
    python content-analyzer.py input.pptx --slide 11
    python content-analyzer.py input.pptx --slide 11 --output template.yaml
    python content-analyzer.py input.pptx --all  # 모든 슬라이드 분석

Output:
    - 화면에 YAML 출력 또는 파일 저장
    - 각 도형의 완전한 OOXML 정보 포함
"""

import argparse
import sys
import zipfile
import re
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

# yaml 모듈은 선택적
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# 공유 모듈 import
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent.parent / 'shared'))

try:
    from xml_utils import extract_slide_ooxml, extract_slide_rels, get_slide_count, NAMESPACES
except ImportError:
    # Fallback: 직접 정의
    NAMESPACES = {
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
        'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
        'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
        'dgm': 'http://schemas.openxmlformats.org/drawingml/2006/diagram',
        'asvg': 'http://schemas.microsoft.com/office/drawing/2016/SVG/main',
    }

    def extract_slide_ooxml(pptx_path, slide_num):
        with zipfile.ZipFile(pptx_path, 'r') as zf:
            path = f'ppt/slides/slide{slide_num}.xml'
            if path in zf.namelist():
                return zf.read(path).decode('utf-8')
        return ''

    def extract_slide_rels(pptx_path, slide_num):
        with zipfile.ZipFile(pptx_path, 'r') as zf:
            path = f'ppt/slides/_rels/slide{slide_num}.xml.rels'
            if path in zf.namelist():
                return zf.read(path).decode('utf-8')
        return ''

    def get_slide_count(pptx_path):
        with zipfile.ZipFile(pptx_path, 'r') as zf:
            files = [f for f in zf.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
            return len(files)

# 추가 네임스페이스
NAMESPACES['dgm'] = 'http://schemas.openxmlformats.org/drawingml/2006/diagram'
NAMESPACES['asvg'] = 'http://schemas.microsoft.com/office/drawing/2016/SVG/main'

# 기본 슬라이드 크기 (EMU)
DEFAULT_SLIDE_WIDTH = 12192000  # 16:9 기준
DEFAULT_SLIDE_HEIGHT = 6858000


def register_namespaces():
    """ET에 네임스페이스 등록"""
    for prefix, uri in NAMESPACES.items():
        ET.register_namespace(prefix, uri)


def parse_color(elem):
    """색상 요소에서 색상값 추출"""
    if elem is None:
        return None

    # srgbClr - 직접 RGB
    srgb = elem.find('.//a:srgbClr', NAMESPACES)
    if srgb is not None:
        return f"#{srgb.get('val', '')}"

    # schemeClr - 테마 색상 참조
    scheme = elem.find('.//a:schemeClr', NAMESPACES)
    if scheme is not None:
        val = scheme.get('val', '')
        # lumMod/lumOff 등 변형값 확인
        lum_mod = scheme.find('a:lumMod', NAMESPACES)
        lum_off = scheme.find('a:lumOff', NAMESPACES)
        if lum_mod is not None or lum_off is not None:
            mod = lum_mod.get('val', '100000') if lum_mod is not None else '100000'
            off = lum_off.get('val', '0') if lum_off is not None else '0'
            return f"scheme:{val}:lumMod{mod}:lumOff{off}"
        return f"scheme:{val}"

    # sysClr - 시스템 색상
    sys_clr = elem.find('.//a:sysClr', NAMESPACES)
    if sys_clr is not None:
        return f"#{sys_clr.get('lastClr', '')}"

    return None


def extract_fill(sp_pr):
    """도형의 채우기 정보 추출"""
    if sp_pr is None:
        return None

    fill_info = {}

    # solidFill
    solid = sp_pr.find('a:solidFill', NAMESPACES)
    if solid is not None:
        fill_info['type'] = 'solid'
        fill_info['color'] = parse_color(solid)
        return fill_info

    # gradFill
    grad = sp_pr.find('a:gradFill', NAMESPACES)
    if grad is not None:
        fill_info['type'] = 'gradient'
        fill_info['stops'] = []
        for gs in grad.findall('.//a:gs', NAMESPACES):
            pos = gs.get('pos', '0')
            color = parse_color(gs)
            fill_info['stops'].append({'pos': pos, 'color': color})
        return fill_info

    # noFill
    if sp_pr.find('a:noFill', NAMESPACES) is not None:
        return {'type': 'none'}

    return None


def extract_stroke(sp_pr):
    """도형의 테두리 정보 추출"""
    if sp_pr is None:
        return None

    ln = sp_pr.find('a:ln', NAMESPACES)
    if ln is None:
        return None

    stroke_info = {}

    # 테두리 두께
    width = ln.get('w')
    if width:
        stroke_info['width_emu'] = int(width)

    # 테두리 색상
    solid = ln.find('a:solidFill', NAMESPACES)
    if solid is not None:
        stroke_info['color'] = parse_color(solid)

    # noFill (테두리 없음)
    if ln.find('a:noFill', NAMESPACES) is not None:
        return {'type': 'none'}

    # 점선 스타일
    prstDash = ln.find('a:prstDash', NAMESPACES)
    if prstDash is not None:
        stroke_info['dash'] = prstDash.get('val', 'solid')

    # 화살표 (연결선용)
    headEnd = ln.find('a:headEnd', NAMESPACES)
    tailEnd = ln.find('a:tailEnd', NAMESPACES)
    if headEnd is not None:
        stroke_info['head_end'] = {
            'type': headEnd.get('type', 'none'),
            'w': headEnd.get('w', 'med'),
            'len': headEnd.get('len', 'med')
        }
    if tailEnd is not None:
        stroke_info['tail_end'] = {
            'type': tailEnd.get('type', 'none'),
            'w': tailEnd.get('w', 'med'),
            'len': tailEnd.get('len', 'med')
        }

    return stroke_info if stroke_info else None


def extract_effects(sp_pr):
    """도형의 효과 정보 추출"""
    if sp_pr is None:
        return None

    effect_lst = sp_pr.find('a:effectLst', NAMESPACES)
    if effect_lst is None:
        return None

    effects = []

    # outerShdw (외부 그림자)
    outer_shdw = effect_lst.find('a:outerShdw', NAMESPACES)
    if outer_shdw is not None:
        effects.append({
            'type': 'outerShadow',
            'blur': outer_shdw.get('blurRad', '0'),
            'dist': outer_shdw.get('dist', '0'),
            'dir': outer_shdw.get('dir', '0'),
            'color': parse_color(outer_shdw)
        })

    # innerShdw (내부 그림자)
    inner_shdw = effect_lst.find('a:innerShdw', NAMESPACES)
    if inner_shdw is not None:
        effects.append({
            'type': 'innerShadow',
            'blur': inner_shdw.get('blurRad', '0'),
            'dist': inner_shdw.get('dist', '0'),
            'dir': inner_shdw.get('dir', '0')
        })

    return effects if effects else None


def extract_geometry(xfrm, slide_width=DEFAULT_SLIDE_WIDTH, slide_height=DEFAULT_SLIDE_HEIGHT):
    """위치/크기 정보 추출"""
    if xfrm is None:
        return None

    geom = {}

    off = xfrm.find('a:off', NAMESPACES)
    ext = xfrm.find('a:ext', NAMESPACES)

    if off is not None:
        x_emu = int(off.get('x', 0))
        y_emu = int(off.get('y', 0))
        geom['x_emu'] = x_emu
        geom['y_emu'] = y_emu
        geom['x_pct'] = round(x_emu / slide_width * 100, 2)
        geom['y_pct'] = round(y_emu / slide_height * 100, 2)

    if ext is not None:
        cx_emu = int(ext.get('cx', 0))
        cy_emu = int(ext.get('cy', 0))
        geom['cx_emu'] = cx_emu
        geom['cy_emu'] = cy_emu
        geom['cx_pct'] = round(cx_emu / slide_width * 100, 2)
        geom['cy_pct'] = round(cy_emu / slide_height * 100, 2)

    return geom if geom else None


def extract_preset_geometry(sp_pr):
    """프리셋 도형 타입 추출"""
    if sp_pr is None:
        return None

    prstGeom = sp_pr.find('a:prstGeom', NAMESPACES)
    if prstGeom is not None:
        return prstGeom.get('prst')

    custGeom = sp_pr.find('a:custGeom', NAMESPACES)
    if custGeom is not None:
        return 'customGeometry'

    return None


def extract_text_content(shape):
    """도형 내 텍스트 추출"""
    txBody = shape.find('.//p:txBody', NAMESPACES)
    if txBody is None:
        return None

    text_info = {'paragraphs': []}

    for p in txBody.findall('a:p', NAMESPACES):
        para = {'runs': []}
        for r in p.findall('a:r', NAMESPACES):
            t = r.find('a:t', NAMESPACES)
            if t is not None and t.text:
                para['runs'].append(t.text)
        if para['runs']:
            text_info['paragraphs'].append(para)

    # 단순 텍스트 (한 줄)
    all_text = ' '.join(
        ' '.join(p['runs']) for p in text_info['paragraphs']
    )
    if all_text:
        text_info['plain_text'] = all_text.strip()

    return text_info if text_info.get('plain_text') else None


def extract_shape(shape_elem, index, rels_map=None):
    """p:sp 요소 추출"""
    info = {'type': 'shape', 'index': index}

    # 이름과 ID
    nvSpPr = shape_elem.find('p:nvSpPr', NAMESPACES)
    if nvSpPr is not None:
        cNvPr = nvSpPr.find('p:cNvPr', NAMESPACES)
        if cNvPr is not None:
            info['id'] = cNvPr.get('id', '')
            info['name'] = cNvPr.get('name', '')

    # spPr (도형 속성)
    spPr = shape_elem.find('p:spPr', NAMESPACES)

    # 위치/크기
    xfrm = spPr.find('a:xfrm', NAMESPACES) if spPr is not None else None
    geom = extract_geometry(xfrm)
    if geom:
        info['geometry'] = geom

    # 프리셋 도형
    preset = extract_preset_geometry(spPr)
    if preset:
        info['preset'] = preset

    # 채우기
    fill = extract_fill(spPr)
    if fill:
        info['fill'] = fill

    # 테두리
    stroke = extract_stroke(spPr)
    if stroke:
        info['stroke'] = stroke

    # 효과
    effects = extract_effects(spPr)
    if effects:
        info['effects'] = effects

    # 텍스트
    text = extract_text_content(shape_elem)
    if text:
        info['text'] = text

    # 원본 OOXML (compact)
    info['ooxml_tag'] = 'p:sp'

    return info


def extract_picture(pic_elem, index, rels_map=None):
    """p:pic 요소 추출 (이미지/SVG 아이콘)"""
    info = {'type': 'picture', 'index': index}

    # 이름과 ID
    nvPicPr = pic_elem.find('p:nvPicPr', NAMESPACES)
    if nvPicPr is not None:
        cNvPr = nvPicPr.find('p:cNvPr', NAMESPACES)
        if cNvPr is not None:
            info['id'] = cNvPr.get('id', '')
            info['name'] = cNvPr.get('name', '')
            info['descr'] = cNvPr.get('descr', '')

    # blipFill (이미지 참조)
    blipFill = pic_elem.find('p:blipFill', NAMESPACES)
    if blipFill is not None:
        blip = blipFill.find('a:blip', NAMESPACES)
        if blip is not None:
            r_embed = blip.get(f'{{{NAMESPACES["r"]}}}embed')
            if r_embed:
                info['embed_rId'] = r_embed
                # 관계 파일에서 실제 파일 경로 조회
                if rels_map and r_embed in rels_map:
                    info['target'] = rels_map[r_embed]

            # SVG 아이콘 확인
            svg_blip = blip.find('a:extLst/a:ext/asvg:svgBlip', NAMESPACES)
            if svg_blip is not None:
                svg_embed = svg_blip.get(f'{{{NAMESPACES["r"]}}}embed')
                if svg_embed:
                    info['svg_rId'] = svg_embed
                    info['is_svg'] = True
                    if rels_map and svg_embed in rels_map:
                        info['svg_target'] = rels_map[svg_embed]

    # spPr (위치/크기)
    spPr = pic_elem.find('p:spPr', NAMESPACES)
    if spPr is not None:
        xfrm = spPr.find('a:xfrm', NAMESPACES)
        geom = extract_geometry(xfrm)
        if geom:
            info['geometry'] = geom

    info['ooxml_tag'] = 'p:pic'
    return info


def extract_connector(cxn_elem, index, rels_map=None):
    """p:cxnSp 요소 추출 (연결선)"""
    info = {'type': 'connector', 'index': index}

    # 이름과 ID
    nvCxnSpPr = cxn_elem.find('p:nvCxnSpPr', NAMESPACES)
    if nvCxnSpPr is not None:
        cNvPr = nvCxnSpPr.find('p:cNvPr', NAMESPACES)
        if cNvPr is not None:
            info['id'] = cNvPr.get('id', '')
            info['name'] = cNvPr.get('name', '')

        # 연결 정보
        cNvCxnSpPr = nvCxnSpPr.find('p:cNvCxnSpPr', NAMESPACES)
        if cNvCxnSpPr is not None:
            stCxn = cNvCxnSpPr.find('a:stCxn', NAMESPACES)
            endCxn = cNvCxnSpPr.find('a:endCxn', NAMESPACES)
            if stCxn is not None:
                info['start_connection'] = {
                    'id': stCxn.get('id'),
                    'idx': stCxn.get('idx')
                }
            if endCxn is not None:
                info['end_connection'] = {
                    'id': endCxn.get('id'),
                    'idx': endCxn.get('idx')
                }

    # spPr (속성)
    spPr = cxn_elem.find('p:spPr', NAMESPACES)
    if spPr is not None:
        # 위치/크기
        xfrm = spPr.find('a:xfrm', NAMESPACES)
        geom = extract_geometry(xfrm)
        if geom:
            info['geometry'] = geom

        # 프리셋
        preset = extract_preset_geometry(spPr)
        if preset:
            info['preset'] = preset

        # 테두리 (연결선의 주요 속성)
        stroke = extract_stroke(spPr)
        if stroke:
            info['stroke'] = stroke

    info['ooxml_tag'] = 'p:cxnSp'
    return info


def extract_group(grp_elem, index, rels_map=None):
    """p:grpSp 요소 추출 (그룹 도형)"""
    info = {'type': 'group', 'index': index}

    # 그룹 이름
    nvGrpSpPr = grp_elem.find('p:nvGrpSpPr', NAMESPACES)
    if nvGrpSpPr is not None:
        cNvPr = nvGrpSpPr.find('p:cNvPr', NAMESPACES)
        if cNvPr is not None:
            info['id'] = cNvPr.get('id', '')
            info['name'] = cNvPr.get('name', '')

    # 그룹 속성 (위치/크기)
    grpSpPr = grp_elem.find('p:grpSpPr', NAMESPACES)
    if grpSpPr is not None:
        xfrm = grpSpPr.find('a:xfrm', NAMESPACES)
        if xfrm is not None:
            geom = extract_geometry(xfrm)
            if geom:
                info['geometry'] = geom

            # 그룹 내부 좌표계
            chOff = xfrm.find('a:chOff', NAMESPACES)
            chExt = xfrm.find('a:chExt', NAMESPACES)
            if chOff is not None and chExt is not None:
                info['child_offset'] = {
                    'x': int(chOff.get('x', 0)),
                    'y': int(chOff.get('y', 0))
                }
                info['child_extents'] = {
                    'cx': int(chExt.get('cx', 0)),
                    'cy': int(chExt.get('cy', 0))
                }

    # 하위 요소들
    children = []
    child_index = 0
    for child in grp_elem:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'sp':
            children.append(extract_shape(child, child_index, rels_map))
            child_index += 1
        elif tag == 'pic':
            children.append(extract_picture(child, child_index, rels_map))
            child_index += 1
        elif tag == 'cxnSp':
            children.append(extract_connector(child, child_index, rels_map))
            child_index += 1
        elif tag == 'grpSp':
            children.append(extract_group(child, child_index, rels_map))
            child_index += 1

    if children:
        info['children'] = children

    info['ooxml_tag'] = 'p:grpSp'
    return info


def extract_graphic_frame(gf_elem, index, rels_map=None):
    """p:graphicFrame 요소 추출 (SmartArt, 차트, 표)"""
    info = {'type': 'graphicFrame', 'index': index}

    # 이름
    nvGraphicFramePr = gf_elem.find('p:nvGraphicFramePr', NAMESPACES)
    if nvGraphicFramePr is not None:
        cNvPr = nvGraphicFramePr.find('p:cNvPr', NAMESPACES)
        if cNvPr is not None:
            info['id'] = cNvPr.get('id', '')
            info['name'] = cNvPr.get('name', '')

    # 위치/크기
    xfrm = gf_elem.find('p:xfrm', NAMESPACES)
    geom = extract_geometry(xfrm)
    if geom:
        info['geometry'] = geom

    # 그래픽 데이터 타입 확인
    graphic = gf_elem.find('a:graphic', NAMESPACES)
    if graphic is not None:
        graphicData = graphic.find('a:graphicData', NAMESPACES)
        if graphicData is not None:
            uri = graphicData.get('uri', '')
            info['graphic_uri'] = uri

            # SmartArt (다이어그램)
            if 'diagram' in uri:
                info['graphic_type'] = 'diagram'
                relIds = graphicData.find('dgm:relIds', NAMESPACES)
                if relIds is not None:
                    info['diagram_refs'] = {
                        'dm': relIds.get(f'{{{NAMESPACES["r"]}}}dm'),
                        'lo': relIds.get(f'{{{NAMESPACES["r"]}}}lo'),
                        'qs': relIds.get(f'{{{NAMESPACES["r"]}}}qs'),
                        'cs': relIds.get(f'{{{NAMESPACES["r"]}}}cs'),
                    }

            # 차트
            elif 'chart' in uri:
                info['graphic_type'] = 'chart'
                chart = graphicData.find('c:chart', NAMESPACES)
                if chart is not None:
                    chart_rid = chart.get(f'{{{NAMESPACES["r"]}}}id')
                    if chart_rid:
                        info['chart_rId'] = chart_rid

            # 표
            elif 'table' in uri:
                info['graphic_type'] = 'table'

    info['ooxml_tag'] = 'p:graphicFrame'
    return info


def parse_rels_file(rels_content):
    """관계 파일에서 rId → target 매핑 생성"""
    if not rels_content:
        return {}

    rels_map = {}
    try:
        root = ET.fromstring(rels_content)
        for rel in root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
            rid = rel.get('Id', '')
            target = rel.get('Target', '')
            rel_type = rel.get('Type', '')
            if rid and target:
                rels_map[rid] = {
                    'target': target,
                    'type': rel_type.split('/')[-1] if '/' in rel_type else rel_type
                }
    except ET.ParseError:
        pass

    return rels_map


def analyze_slide(pptx_path, slide_num):
    """슬라이드 분석"""
    result = {
        'slide_num': slide_num,
        'source': str(pptx_path),
        'analyzed_at': datetime.now().isoformat(),
        'elements': []
    }

    # 슬라이드 XML 추출
    slide_xml = extract_slide_ooxml(pptx_path, slide_num)
    if not slide_xml:
        result['error'] = f'Slide {slide_num} not found'
        return result

    # 관계 파일 로드
    rels_content = extract_slide_rels(pptx_path, slide_num)
    rels_map = parse_rels_file(rels_content)

    # XML 파싱
    register_namespaces()
    try:
        root = ET.fromstring(slide_xml)
    except ET.ParseError as e:
        result['error'] = f'XML parse error: {e}'
        return result

    # spTree 찾기
    spTree = root.find('.//p:spTree', NAMESPACES)
    if spTree is None:
        result['error'] = 'spTree not found'
        return result

    # 모든 요소 추출
    element_index = 0
    for child in spTree:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        if tag == 'sp':
            elem = extract_shape(child, element_index, rels_map)
            result['elements'].append(elem)
            element_index += 1
        elif tag == 'pic':
            elem = extract_picture(child, element_index, rels_map)
            result['elements'].append(elem)
            element_index += 1
        elif tag == 'cxnSp':
            elem = extract_connector(child, element_index, rels_map)
            result['elements'].append(elem)
            element_index += 1
        elif tag == 'grpSp':
            elem = extract_group(child, element_index, rels_map)
            result['elements'].append(elem)
            element_index += 1
        elif tag == 'graphicFrame':
            elem = extract_graphic_frame(child, element_index, rels_map)
            result['elements'].append(elem)
            element_index += 1

    # 통계
    result['summary'] = {
        'total_elements': len(result['elements']),
        'shapes': sum(1 for e in result['elements'] if e['type'] == 'shape'),
        'pictures': sum(1 for e in result['elements'] if e['type'] == 'picture'),
        'connectors': sum(1 for e in result['elements'] if e['type'] == 'connector'),
        'groups': sum(1 for e in result['elements'] if e['type'] == 'group'),
        'graphic_frames': sum(1 for e in result['elements'] if e['type'] == 'graphicFrame'),
    }

    # SVG 아이콘 목록
    svg_icons = [e for e in result['elements'] if e.get('is_svg')]
    if svg_icons:
        result['svg_icons'] = [
            {'name': e.get('name'), 'descr': e.get('descr'), 'target': e.get('svg_target')}
            for e in svg_icons
        ]

    return result


def output_yaml(data, output_path=None):
    """결과 출력"""
    if YAML_AVAILABLE:
        yaml_str = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    else:
        # YAML 없으면 간단 포맷
        import json
        yaml_str = json.dumps(data, ensure_ascii=False, indent=2)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_str)
        print(f"Output saved to: {output_path}")
    else:
        print(yaml_str)


def main():
    parser = argparse.ArgumentParser(
        description='슬라이드 콘텐츠 OOXML 분석기',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python content-analyzer.py presentation.pptx --slide 11
  python content-analyzer.py presentation.pptx --slide 11 --output result.yaml
  python content-analyzer.py presentation.pptx --all
        """
    )
    parser.add_argument('pptx_path', help='PPTX 파일 경로')
    parser.add_argument('--slide', '-s', type=int, help='분석할 슬라이드 번호 (1-based)')
    parser.add_argument('--all', '-a', action='store_true', help='모든 슬라이드 분석')
    parser.add_argument('--output', '-o', help='출력 파일 경로 (YAML)')
    parser.add_argument('--summary', action='store_true', help='요약만 출력')

    args = parser.parse_args()

    pptx_path = Path(args.pptx_path)
    if not pptx_path.exists():
        print(f"Error: File not found: {pptx_path}")
        sys.exit(1)

    if args.all:
        # 모든 슬라이드 분석
        slide_count = get_slide_count(pptx_path)
        print(f"Analyzing {slide_count} slides...")

        results = []
        for i in range(1, slide_count + 1):
            result = analyze_slide(pptx_path, i)
            results.append(result)
            if args.summary:
                s = result.get('summary', {})
                print(f"  Slide {i}: {s.get('total_elements', 0)} elements "
                      f"({s.get('shapes', 0)} shapes, {s.get('pictures', 0)} pics, "
                      f"{s.get('connectors', 0)} connectors)")

        if not args.summary:
            output_yaml({'slides': results}, args.output)

    elif args.slide:
        # 단일 슬라이드 분석
        result = analyze_slide(pptx_path, args.slide)
        output_yaml(result, args.output)

    else:
        # 기본: 슬라이드 개수 표시
        slide_count = get_slide_count(pptx_path)
        print(f"PPTX contains {slide_count} slides.")
        print("Use --slide N or --all to analyze.")


if __name__ == '__main__':
    main()
