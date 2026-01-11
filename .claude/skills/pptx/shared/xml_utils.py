"""
공유 XML/OOXML 유틸리티 모듈
ppt-extract, ppt-gen 스킬에서 OOXML 처리에 공통 사용
"""

import zipfile
import xml.dom.minidom
from pathlib import Path
from typing import Optional, Union


def extract_ooxml(
    pptx_path: Union[str, Path],
    internal_path: str,
    pretty_print: bool = True
) -> str:
    """PPTX 내부의 XML 파일 추출

    Args:
        pptx_path: PPTX 파일 경로
        internal_path: PPTX 내부 경로 (예: 'ppt/slideLayouts/slideLayout1.xml')
        pretty_print: True면 들여쓰기 포맷팅 적용

    Returns:
        XML 문자열 (파일이 없으면 빈 문자열)
    """
    with zipfile.ZipFile(pptx_path, 'r') as zf:
        if internal_path not in zf.namelist():
            return ''

        with zf.open(internal_path) as f:
            content = f.read().decode('utf-8')

            if pretty_print:
                try:
                    dom = xml.dom.minidom.parseString(content)
                    return dom.toprettyxml(indent='  ')
                except Exception:
                    return content

            return content


def extract_layout_ooxml(pptx_path: Union[str, Path], layout_num: int) -> str:
    """레이아웃 XML 추출"""
    return extract_ooxml(pptx_path, f'ppt/slideLayouts/slideLayout{layout_num}.xml')


def extract_layout_rels(pptx_path: Union[str, Path], layout_num: int) -> str:
    """레이아웃 관계 파일 추출"""
    return extract_ooxml(pptx_path, f'ppt/slideLayouts/_rels/slideLayout{layout_num}.xml.rels')


def extract_slide_master_ooxml(pptx_path: Union[str, Path], master_num: int = 1) -> str:
    """슬라이드 마스터 XML 추출"""
    return extract_ooxml(pptx_path, f'ppt/slideMasters/slideMaster{master_num}.xml')


def extract_slide_master_rels(pptx_path: Union[str, Path], master_num: int = 1) -> str:
    """슬라이드 마스터 관계 파일 추출"""
    return extract_ooxml(pptx_path, f'ppt/slideMasters/_rels/slideMaster{master_num}.xml.rels')


def extract_theme_ooxml(pptx_path: Union[str, Path], theme_num: int = 1) -> str:
    """테마 XML 추출"""
    return extract_ooxml(pptx_path, f'ppt/theme/theme{theme_num}.xml')


def extract_theme_rels(pptx_path: Union[str, Path], theme_num: int = 1) -> str:
    """테마 관계 파일 추출"""
    return extract_ooxml(pptx_path, f'ppt/theme/_rels/theme{theme_num}.xml.rels')


def extract_slide_ooxml(pptx_path: Union[str, Path], slide_num: int) -> str:
    """슬라이드 XML 추출"""
    return extract_ooxml(pptx_path, f'ppt/slides/slide{slide_num}.xml')


def extract_slide_rels(pptx_path: Union[str, Path], slide_num: int) -> str:
    """슬라이드 관계 파일 추출"""
    return extract_ooxml(pptx_path, f'ppt/slides/_rels/slide{slide_num}.xml.rels')


def list_ooxml_files(pptx_path: Union[str, Path], prefix: str = '') -> list:
    """PPTX 내부 파일 목록 조회

    Args:
        pptx_path: PPTX 파일 경로
        prefix: 필터링할 경로 접두사 (예: 'ppt/slideLayouts/')

    Returns:
        파일 경로 리스트
    """
    with zipfile.ZipFile(pptx_path, 'r') as zf:
        if prefix:
            return [f for f in zf.namelist() if f.startswith(prefix)]
        return zf.namelist()


def get_layout_count(pptx_path: Union[str, Path]) -> int:
    """슬라이드 레이아웃 개수 반환"""
    files = list_ooxml_files(pptx_path, 'ppt/slideLayouts/')
    # slideLayoutN.xml 형식만 카운트 (_rels 제외)
    return len([f for f in files if f.endswith('.xml') and '/_rels/' not in f])


def get_slide_count(pptx_path: Union[str, Path]) -> int:
    """슬라이드 개수 반환"""
    files = list_ooxml_files(pptx_path, 'ppt/slides/')
    return len([f for f in files if f.endswith('.xml') and '/_rels/' not in f])


# OOXML 네임스페이스 상수
NAMESPACES = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
}
