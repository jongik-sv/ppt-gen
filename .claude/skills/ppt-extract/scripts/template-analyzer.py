#!/usr/bin/env python3
"""
PPTX Template Analyzer (슬라이드 마스터/레이아웃 추출)

PPTX 파일의 슬라이드 레이아웃(마스터)을 분석하여 템플릿 파일들을 생성합니다.
- slideLayouts에서 실제 레이아웃 정의 추출
- 미디어 에셋(로고, 이미지) 추출
- OOXML 스니펫 저장

Usage:
    python template-analyzer.py input.pptx 제안서1 --group dongkuk --name "제안서 (기본)"

Output:
    - templates/documents/{group}/config.yaml (테마 정보)
    - templates/documents/{group}/{template-id}.yaml (양식 파일)
    - templates/documents/{group}/registry.yaml (템플릿 목록)
    - templates/documents/{group}/assets/default/ (이미지 에셋)
    - templates/documents/{group}/ooxml/ (레이아웃 XML)
"""

import argparse
import zipfile
import xml.etree.ElementTree as ET
import xml.dom.minidom
from pathlib import Path
from datetime import datetime
import re
import sys
import yaml
import shutil

# 폰트 매니저 임포트 (같은 디렉토리)
try:
    from font_manager import FontManager
    FONT_MANAGER_AVAILABLE = True
except ImportError:
    FONT_MANAGER_AVAILABLE = False

# 공유 모듈 import
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent.parent / 'shared'))
from xml_utils import (
    extract_layout_ooxml,
    extract_layout_rels,
    extract_slide_master_ooxml,
    extract_slide_master_rels,
    extract_theme_ooxml,
    NAMESPACES,
)

# 관계 타입
REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'


def extract_theme(pptx_path: str) -> dict:
    """theme1.xml에서 색상, 폰트 추출"""
    theme = {
        'name': '',
        'colors': {},
        'fonts': {}
    }

    with zipfile.ZipFile(pptx_path, 'r') as zf:
        theme_files = [f for f in zf.namelist() if 'ppt/theme/theme' in f and f.endswith('.xml')]
        if not theme_files:
            return theme

        theme_file = sorted(theme_files)[0]  # theme1.xml 우선
        with zf.open(theme_file) as f:
            tree = ET.parse(f)
            root = tree.getroot()

            # 테마 이름
            theme_elem = root.find('.//a:theme', NAMESPACES)
            if theme_elem is not None:
                theme['name'] = theme_elem.get('name', '')

            # 색상 스키마
            clr_scheme = root.find('.//a:clrScheme', NAMESPACES)
            if clr_scheme is not None:
                color_mapping = {
                    'dk1': 'dark_text',
                    'lt1': 'light_bg',
                    'dk2': 'primary',
                    'lt2': 'gray',
                    'accent1': 'accent1',
                    'accent2': 'accent2',
                    'accent3': 'accent3',
                    'accent4': 'secondary',
                    'accent5': 'accent5',
                    'accent6': 'accent6',
                }

                for color_name, field_name in color_mapping.items():
                    color_elem = clr_scheme.find(f'a:{color_name}', NAMESPACES)
                    if color_elem is not None:
                        srgb = color_elem.find('.//a:srgbClr', NAMESPACES)
                        if srgb is not None:
                            theme['colors'][field_name] = f"#{srgb.get('val', '')}"
                        else:
                            sys_clr = color_elem.find('.//a:sysClr', NAMESPACES)
                            if sys_clr is not None:
                                theme['colors'][field_name] = f"#{sys_clr.get('lastClr', '')}"

            # 폰트 스키마
            font_scheme = root.find('.//a:fontScheme', NAMESPACES)
            if font_scheme is not None:
                major_font = font_scheme.find('.//a:majorFont/a:latin', NAMESPACES)
                if major_font is not None:
                    theme['fonts']['title'] = major_font.get('typeface', '')

                minor_font = font_scheme.find('.//a:minorFont/a:latin', NAMESPACES)
                if minor_font is not None:
                    theme['fonts']['body'] = minor_font.get('typeface', '')

    return theme


def get_layout_count(pptx_path: str) -> int:
    """slideLayouts 폴더에서 레이아웃 개수 반환"""
    with zipfile.ZipFile(pptx_path, 'r') as zf:
        layout_files = [f for f in zf.namelist()
                       if re.match(r'ppt/slideLayouts/slideLayout\d+\.xml$', f)]
        return len(layout_files)


def analyze_slide_layout(pptx_path: str, layout_num: int) -> dict:
    """개별 슬라이드 레이아웃 분석 (slideLayouts에서)"""
    layout_info = {
        'index': layout_num,
        'name': '',
        'placeholders': [],
        'has_title': False,
        'has_body': False,
        'shape_count': 0,
        'image_refs': [],
    }

    with zipfile.ZipFile(pptx_path, 'r') as zf:
        layout_file = f'ppt/slideLayouts/slideLayout{layout_num}.xml'
        if layout_file not in zf.namelist():
            return layout_info

        with zf.open(layout_file) as f:
            tree = ET.parse(f)
            root = tree.getroot()

            # 레이아웃 이름 추출 (cSld/@name)
            cSld = root.find('.//p:cSld', NAMESPACES)
            if cSld is not None:
                layout_info['name'] = cSld.get('name', f'Layout {layout_num}')

            # 슬라이드 크기 (기본값: 10" x 7.5" in EMU)
            # 실제 크기는 presentation.xml에서 가져와야 하지만 기본값 사용
            slide_width_emu = 9144000
            slide_height_emu = 6858000

            # 플레이스홀더 분석
            shapes = root.findall('.//p:sp', NAMESPACES)
            layout_info['shape_count'] = len(shapes)

            for shape in shapes:
                ph = shape.find('.//p:ph', NAMESPACES)
                if ph is not None:
                    ph_type = ph.get('type', 'body')
                    ph_idx = ph.get('idx', '')

                    placeholder = {
                        'type': ph_type,
                    }
                    if ph_idx:
                        placeholder['idx'] = int(ph_idx) if ph_idx.isdigit() else ph_idx

                    # 위치/크기 추출 (xfrm)
                    xfrm = shape.find('.//p:spPr/a:xfrm', NAMESPACES)
                    if xfrm is not None:
                        off = xfrm.find('a:off', NAMESPACES)
                        ext = xfrm.find('a:ext', NAMESPACES)
                        if off is not None and ext is not None:
                            x_emu = int(off.get('x', 0))
                            y_emu = int(off.get('y', 0))
                            cx_emu = int(ext.get('cx', 0))
                            cy_emu = int(ext.get('cy', 0))

                            placeholder['position'] = {
                                'x': round(x_emu / slide_width_emu * 100, 1),
                                'y': round(y_emu / slide_height_emu * 100, 1),
                                'width': round(cx_emu / slide_width_emu * 100, 1),
                                'height': round(cy_emu / slide_height_emu * 100, 1),
                            }

                    # 역할 자동 설정
                    role_map = {
                        'title': '슬라이드 제목',
                        'ctrTitle': '중앙 제목',
                        'subTitle': '부제목',
                        'body': '본문 텍스트',
                        'pic': '이미지',
                        'chart': '차트',
                        'tbl': '표',
                        'dgm': '다이어그램',
                        'sldNum': '슬라이드 번호',
                        'ftr': '바닥글',
                        'dt': '날짜',
                    }
                    placeholder['role'] = role_map.get(ph_type, ph_type)

                    layout_info['placeholders'].append(placeholder)

                    if ph_type in ['title', 'ctrTitle']:
                        layout_info['has_title'] = True
                    elif ph_type == 'body':
                        layout_info['has_body'] = True

            # 이미지 참조 추출 (blip)
            blips = root.findall('.//a:blip', NAMESPACES)
            for blip in blips:
                embed = blip.get(f'{{{NAMESPACES["r"]}}}embed')
                if embed:
                    layout_info['image_refs'].append(embed)

    return layout_info


def resolve_media_references(pptx_path: str, layout_num: int) -> list:
    """레이아웃의 이미지 참조를 실제 미디어 파일로 해석"""
    media_refs = []

    with zipfile.ZipFile(pptx_path, 'r') as zf:
        rels_file = f'ppt/slideLayouts/_rels/slideLayout{layout_num}.xml.rels'
        if rels_file not in zf.namelist():
            return media_refs

        with zf.open(rels_file) as f:
            tree = ET.parse(f)
            root = tree.getroot()

            for rel in root.findall(f'.//{{{REL_NS}}}Relationship'):
                rel_type = rel.get('Type', '')
                target = rel.get('Target', '')
                rel_id = rel.get('Id', '')

                if 'image' in rel_type and target and target != 'NULL':
                    # 상대 경로 변환: ../media/image2.png -> ppt/media/image2.png
                    if target.startswith('../'):
                        actual_path = 'ppt/' + target[3:]
                    else:
                        actual_path = target

                    media_refs.append({
                        'rId': rel_id,
                        'target': actual_path,
                        'filename': Path(actual_path).name,
                    })

    return media_refs


def extract_media_assets(pptx_path: str, output_dir: Path) -> dict:
    """ppt/media/에서 이미지 파일 추출하여 assets/default/에 저장"""
    assets = {}
    assets_dir = output_dir / 'assets' / 'default'
    assets_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(pptx_path, 'r') as zf:
        media_files = [f for f in zf.namelist() if f.startswith('ppt/media/')]

        for media_file in media_files:
            filename = Path(media_file).name
            dest_path = assets_dir / filename

            # 파일 추출
            with zf.open(media_file) as src:
                with open(dest_path, 'wb') as dst:
                    dst.write(src.read())

            # 파일 정보 수집
            info = zf.getinfo(media_file)
            ext = Path(filename).suffix.lower().lstrip('.')

            # 용도 추측
            usage = 'unknown'
            if ext == 'emf':
                usage = 'logo'
            elif info.file_size > 100000:
                usage = 'background'
            else:
                usage = 'icon'

            assets[filename] = {
                'file': f'assets/default/{filename}',
                'type': ext,
                'size_bytes': info.file_size,
                'usage': usage,
                'original_path': media_file,
            }

    return assets


def classify_by_layout_name(layout_name: str, layout_info: dict) -> str:
    """레이아웃 이름으로 카테고리 분류"""
    name_lower = layout_name.lower()

    # 한글/영문 패턴 매칭
    if any(kw in layout_name for kw in ['표지', 'cover', 'White_Big', 'title slide']):
        return 'cover'
    if any(kw in layout_name for kw in ['간지', 'section', 'divider']):
        return 'section'
    if any(kw in layout_name for kw in ['목차', 'toc', 'contents', 'index']):
        return 'toc'
    if 'action title' in name_lower:
        if any(kw in layout_name for kw in ['Body삭제', 'Body 삭제', '자유']):
            return 'content_free'
        return 'content_bullets'
    if '내지' in layout_name:
        if layout_info.get('has_body'):
            return 'content_bullets'
        return 'content_wide'

    # 플레이스홀더 기반 폴백
    if layout_info.get('has_title') and not layout_info.get('has_body'):
        return 'content_free'
    if layout_info.get('has_body'):
        return 'content_bullets'

    return 'content_wide'


def get_use_for(category: str) -> str:
    """카테고리별 use_for 설명"""
    use_for_map = {
        'cover': '문서 제목, 발표 표지, 작성자 정보',
        'toc': '목차, Contents, 챕터 구성, 페이지 안내',
        'section': '섹션 구분, 챕터 시작',
        'content_bullets': '설명, 개요, 리스트 나열, 본문 슬라이드',
        'content_free': '차트, 표, 다이어그램, 이미지, 자유 레이아웃',
        'content_wide': '긴 텍스트, 단순 정보, Action Title 불필요한 콘텐츠',
    }
    return use_for_map.get(category, '일반 콘텐츠')


def get_keywords(category: str) -> list:
    """카테고리별 키워드"""
    keywords_map = {
        'cover': ['표지', '제목', '타이틀', '커버', '시작'],
        'toc': ['목차', 'Contents', '인덱스', '구성'],
        'section': ['섹션', '챕터', '구분', '간지'],
        'content_bullets': ['설명', '개요', '리스트', '본문', '내용', '불릿'],
        'content_free': ['차트', '표', '그래프', '다이어그램', '이미지', '시각화'],
        'content_wide': ['텍스트', '정보', '단순', '설명문', '긴글'],
    }
    return keywords_map.get(category, ['콘텐츠'])


def analyze_all_layouts(pptx_path: str) -> list:
    """모든 슬라이드 레이아웃 분석 (slideLayouts에서)"""
    layouts = []
    layout_count = get_layout_count(pptx_path)

    for i in range(1, layout_count + 1):  # slideLayout은 1부터 시작
        layout_info = analyze_slide_layout(pptx_path, i)
        category = classify_by_layout_name(layout_info['name'], layout_info)

        # 이미지 참조 해석
        media_refs = resolve_media_references(pptx_path, i)

        layout = {
            'index': i,
            'name': layout_info['name'],
            'category': category,
            'use_for': get_use_for(category),
            'keywords': get_keywords(category),
            'placeholders': layout_info['placeholders'],
            'images': media_refs,
            'ooxml_ref': f'ooxml/slideLayout{i}.xml',
        }

        layouts.append(layout)

    return layouts


def get_slide_size(pptx_path: str) -> dict:
    """슬라이드 크기 추출"""
    size = {'width_emu': 9144000, 'height_emu': 6858000}

    with zipfile.ZipFile(pptx_path, 'r') as zf:
        pres_file = 'ppt/presentation.xml'
        if pres_file in zf.namelist():
            with zf.open(pres_file) as f:
                tree = ET.parse(f)
                root = tree.getroot()

                sld_sz = root.find('.//p:sldSz', NAMESPACES)
                if sld_sz is not None:
                    size['width_emu'] = int(sld_sz.get('cx', 9144000))
                    size['height_emu'] = int(sld_sz.get('cy', 6858000))

    return size


def calculate_aspect_ratio(width: int, height: int) -> str:
    """종횡비 계산"""
    ratio = width / height
    if abs(ratio - 16/9) < 0.01:
        return '16:9'
    elif abs(ratio - 4/3) < 0.01:
        return '4:3'
    elif abs(ratio - 16/10) < 0.01:
        return '16:10'
    else:
        return f'{width}:{height}'


def ensure_group_folder(base_dir: Path, group_id: str) -> Path:
    """그룹 폴더 구조 생성"""
    group_dir = base_dir / group_id
    assets_dir = group_dir / 'assets' / 'default'
    ooxml_dir = group_dir / 'ooxml'

    group_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    ooxml_dir.mkdir(parents=True, exist_ok=True)

    return group_dir


def load_or_create_config(group_dir: Path, group_id: str, theme: dict) -> dict:
    """config.yaml 로드 또는 생성"""
    config_path = group_dir / 'config.yaml'

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    config = {
        'group': {
            'id': group_id,
            'name': group_id,
        },
        'theme': {
            'name': theme.get('name', ''),
            'colors': theme.get('colors', {}),
            'fonts': theme.get('fonts', {}),
        },
        'companies': [
            {'id': 'default', 'name': f'{group_id} (기본)'}
        ]
    }

    yaml_str = f"""# {group_id} 그룹 설정
# 자동 생성: {datetime.now().strftime('%Y-%m-%d')}

"""
    yaml_str += yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False)

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(yaml_str)

    print(f"  config.yaml 생성: {config_path}")
    return config


def update_registry(group_dir: Path, template_id: str, name: str,
                    template_type: str, description: str) -> None:
    """registry.yaml 업데이트"""
    registry_path = group_dir / 'registry.yaml'

    if registry_path.exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f) or {}
    else:
        registry = {'templates': []}

    templates = registry.get('templates', [])
    existing_ids = [t['id'] for t in templates]

    if template_id in existing_ids:
        for t in templates:
            if t['id'] == template_id:
                t['name'] = name
                t['type'] = template_type
                t['description'] = description
                t['updated'] = datetime.now().strftime('%Y-%m-%d')
        print(f"  registry.yaml 업데이트: {template_id}")
    else:
        templates.append({
            'id': template_id,
            'name': name,
            'file': f'{template_id}.yaml',
            'type': template_type,
            'description': description,
            'created': datetime.now().strftime('%Y-%m-%d'),
        })
        print(f"  registry.yaml 추가: {template_id}")

    registry['templates'] = templates

    yaml_str = f"""# 문서 템플릿 레지스트리
# 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d')}

"""
    yaml_str += yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False)

    with open(registry_path, 'w', encoding='utf-8') as f:
        f.write(yaml_str)


def generate_document_yaml(template_id: str, name: str, source: str,
                           layouts: list, slide_size: dict, assets: dict) -> str:
    """문서 템플릿 YAML 생성 (새 스키마)"""
    aspect_ratio = calculate_aspect_ratio(slide_size['width_emu'], slide_size['height_emu'])

    # 에셋 목록 생성
    assets_list = []
    for filename, info in assets.items():
        assets_list.append({
            'id': Path(filename).stem,
            'file': info['file'],
            'type': info['type'],
            'size_bytes': info['size_bytes'],
            'usage': info['usage'],
        })

    # 레이아웃 목록 정리
    layouts_out = []
    for layout in layouts:
        layout_entry = {
            'index': layout['index'],
            'name': layout['name'],
            'category': layout['category'],
            'use_for': layout['use_for'],
            'keywords': layout['keywords'],
            'placeholders': layout['placeholders'],
        }
        if layout.get('images'):
            layout_entry['images'] = [
                {'rId': img['rId'], 'file': f"assets/default/{img['filename']}"}
                for img in layout['images']
            ]
        layout_entry['ooxml_ref'] = layout['ooxml_ref']
        layouts_out.append(layout_entry)

    data = {
        'document': {
            'id': template_id,
            'name': name,
            'source': source,
            'aspect_ratio': aspect_ratio,
            'slide_size': slide_size,
        },
        'assets': assets_list,
        'layouts': layouts_out,
        'selection_guide': {
            'cover': next((l['index'] for l in layouts if l['category'] == 'cover'), 1),
            'section': next((l['index'] for l in layouts if l['category'] == 'section'), 2),
            'toc': next((l['index'] for l in layouts if l['category'] == 'toc'), 2),
            'bullets': next((l['index'] for l in layouts if l['category'] == 'content_bullets'), 3),
            'chart': next((l['index'] for l in layouts if l['category'] == 'content_free'), 4),
        },
        'best_practices': [
            '슬라이드당 핵심 메시지 1개',
            '연속 3장 이상 동일 레이아웃 금지',
            '불릿은 최대 4개 권장',
        ]
    }

    yaml_str = f"""# {name}
# 자동 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}
# 원본: {source}

"""
    yaml_str += yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return yaml_str


def main():
    parser = argparse.ArgumentParser(
        description='PPTX 슬라이드 마스터/레이아웃 추출기',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python template-analyzer.py proposal.pptx 제안서1 --group dongkuk
  python template-analyzer.py report.pptx 보고서1 --group dongkuk --type report
        """
    )
    parser.add_argument('pptx_path', help='입력 PPTX 파일 경로')
    parser.add_argument('template_id', help='템플릿 ID (예: 제안서1, 보고서1)')
    parser.add_argument('--group', required=True, help='그룹 ID (예: dongkuk)')
    parser.add_argument('--name', help='템플릿 표시 이름', default=None)
    parser.add_argument('--type', dest='template_type', default='general',
                        choices=['proposal', 'report', 'plan', 'general'],
                        help='템플릿 타입 (proposal, report, plan, general)')
    parser.add_argument('--base-dir', default='templates/documents/',
                        help='기본 출력 디렉토리')
    parser.add_argument('--description', help='템플릿 설명', default=None)
    parser.add_argument('--no-font-install', action='store_true',
                        help='누락 폰트 자동 설치 비활성화')

    args = parser.parse_args()

    pptx_path = args.pptx_path
    template_id = args.template_id
    group_id = args.group
    name = args.name or template_id
    template_type = args.template_type
    base_dir = Path(args.base_dir)

    print(f"PPTX 슬라이드 마스터 추출기")
    print(f"=" * 50)
    print(f"입력: {pptx_path}")
    print(f"그룹: {group_id}")
    print(f"템플릿: {template_id}")
    print()

    # 1. 그룹 폴더 생성
    print("[1/6] 그룹 폴더 확인...")
    group_dir = ensure_group_folder(base_dir, group_id)
    print(f"  폴더: {group_dir}")

    # 2. 미디어 에셋 추출
    print("\n[2/6] 미디어 에셋 추출...")
    assets = extract_media_assets(pptx_path, group_dir)
    print(f"  추출: {len(assets)}개 파일")
    for filename, info in assets.items():
        print(f"    {filename}: {info['size_bytes'] / 1024:.2f} KB ({info['usage']})")

    # 3. 테마 분석
    print("\n[3/6] 테마 분석...")
    theme = extract_theme(pptx_path)
    print(f"  테마: {theme.get('name', 'Unknown')}")
    print(f"  색상: {len(theme.get('colors', {}))}개")
    print(f"  폰트: {theme.get('fonts', {})}")

    # 3.1. 폰트 가용성 검사 및 자동 다운로드
    if FONT_MANAGER_AVAILABLE:
        print("\n[3.1/6] 폰트 가용성 검사...")
        mappings_file = Path(__file__).parent.parent / 'references' / 'font-mappings.yaml'
        fm = FontManager(mappings_file if mappings_file.exists() else None)
        auto_install = not args.no_font_install
        theme = fm.process_theme_fonts(theme, auto_install=auto_install)

        # 폰트 상태 출력
        fonts = theme.get('fonts', {})
        for font_type in ['title', 'body']:
            original = fonts.get(font_type, '')
            fallback = fonts.get(f'{font_type}_fallback')
            if fallback:
                print(f"  {font_type}: '{original}' → '{fallback}' (대체 폰트)")
            elif original:
                print(f"  {font_type}: '{original}' ✅")
    else:
        print("  (font_manager 모듈 없음 - 폰트 검사 스킵)")

    # 4. 슬라이드 레이아웃 분석 (slideLayouts에서)
    print("\n[4/6] 슬라이드 레이아웃 분석...")
    layouts = analyze_all_layouts(pptx_path)
    print(f"  레이아웃: {len(layouts)}개")
    for layout in layouts:
        img_count = len(layout.get('images', []))
        print(f"    [{layout['index']}] {layout['name']} → {layout['category']} (이미지: {img_count})")

    slide_size = get_slide_size(pptx_path)
    aspect_ratio = calculate_aspect_ratio(slide_size['width_emu'], slide_size['height_emu'])
    print(f"  종횡비: {aspect_ratio}")

    # 5. OOXML 스니펫 추출 (레이아웃 + 마스터 + 테마 + 관계파일)
    print("\n[5/6] OOXML 스니펫 추출...")
    ooxml_dir = group_dir / 'ooxml'
    rels_dir = ooxml_dir / '_rels'
    rels_dir.mkdir(parents=True, exist_ok=True)

    # 5.1 슬라이드 레이아웃 OOXML + _rels
    for layout in layouts:
        # 레이아웃 XML
        ooxml_content = extract_layout_ooxml(pptx_path, layout['index'])
        ooxml_path = ooxml_dir / f"slideLayout{layout['index']}.xml"
        with open(ooxml_path, 'w', encoding='utf-8') as f:
            f.write(ooxml_content)

        # 레이아웃 관계 파일
        rels_content = extract_layout_rels(pptx_path, layout['index'])
        if rels_content:
            rels_path = rels_dir / f"slideLayout{layout['index']}.xml.rels"
            with open(rels_path, 'w', encoding='utf-8') as f:
                f.write(rels_content)

    print(f"  레이아웃: {len(layouts)}개")

    # 5.2 슬라이드 마스터 OOXML + _rels
    master_content = extract_slide_master_ooxml(pptx_path)
    if master_content:
        master_path = ooxml_dir / 'slideMaster1.xml'
        with open(master_path, 'w', encoding='utf-8') as f:
            f.write(master_content)

        master_rels = extract_slide_master_rels(pptx_path)
        if master_rels:
            master_rels_path = rels_dir / 'slideMaster1.xml.rels'
            with open(master_rels_path, 'w', encoding='utf-8') as f:
                f.write(master_rels)

        print(f"  마스터: slideMaster1.xml")

    # 5.3 테마 OOXML
    theme_content = extract_theme_ooxml(pptx_path)
    if theme_content:
        theme_path = ooxml_dir / 'theme1.xml'
        with open(theme_path, 'w', encoding='utf-8') as f:
            f.write(theme_content)
        print(f"  테마: theme1.xml")

    print(f"  관계파일: {rels_dir}")

    # 6. config.yaml 처리
    print("\n[6/6] YAML 파일 생성...")
    load_or_create_config(group_dir, group_id, theme)

    # 양식.yaml 생성
    yaml_content = generate_document_yaml(
        template_id, name, pptx_path, layouts, slide_size, assets
    )
    template_path = group_dir / f"{template_id}.yaml"
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    print(f"  양식: {template_path}")

    # registry.yaml 업데이트
    description = args.description or f"{name} 문서 템플릿"
    update_registry(group_dir, template_id, name, template_type, description)

    print("\n" + "=" * 50)
    print("완료!")
    print(f"  그룹 폴더: {group_dir}")
    print(f"  템플릿: {template_path}")
    print(f"  에셋: {group_dir / 'assets' / 'default'}")
    print(f"  OOXML:")
    print(f"    - 레이아웃: {ooxml_dir}/slideLayout*.xml")
    print(f"    - 마스터: {ooxml_dir}/slideMaster1.xml")
    print(f"    - 테마: {ooxml_dir}/theme1.xml")
    print(f"    - 관계: {rels_dir}/*.xml.rels")


if __name__ == '__main__':
    main()
