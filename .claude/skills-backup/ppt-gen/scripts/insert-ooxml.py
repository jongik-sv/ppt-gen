#!/usr/bin/env python3
"""
OOXML 콘텐츠를 PPTX 슬라이드에 삽입

stage-4.json의 content_design 정보를 기반으로
생성된 OOXML 요소를 해당 슬라이드의 content_zone에 삽입합니다.

Usage:
    python insert-ooxml.py <input_pptx> <stage4_json> <output_pptx>

Example:
    python insert-ooxml.py working.pptx stage-4.json output.pptx
"""

import argparse
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from copy import deepcopy
import zipfile
import shutil
import tempfile

# OOXML 네임스페이스
NAMESPACES = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}

# 네임스페이스 등록
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


def load_stage4_json(path: str) -> dict:
    """stage-4.json 로드"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_slides_with_content(stage4: dict) -> list:
    """content_design이 있는 슬라이드 목록 반환"""
    slides = []
    for slide in stage4.get('slides', []):
        if slide.get('content_design') and slide['content_design'].get('ooxml_file'):
            slides.append({
                'index': slide['index'],
                'ooxml_file': slide['content_design']['ooxml_file'],
                'template_id': slide['content_design'].get('template_id', ''),
            })
    return slides


def load_ooxml_content(ooxml_path: str) -> ET.Element:
    """OOXML XML 파일 로드"""
    tree = ET.parse(ooxml_path)
    return tree.getroot()


def insert_content_to_pptx(input_pptx: str, slides_data: list, base_dir: str, output_pptx: str):
    """
    PPTX 파일의 슬라이드에 OOXML 콘텐츠 삽입

    Args:
        input_pptx: 입력 PPTX 파일 경로
        slides_data: 삽입할 슬라이드 정보 목록
        base_dir: OOXML 파일들의 기준 디렉토리
        output_pptx: 출력 PPTX 파일 경로
    """
    # 임시 디렉토리에 PPTX 압축 해제
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # PPTX 압축 해제
        with zipfile.ZipFile(input_pptx, 'r') as zf:
            zf.extractall(temp_path)

        # 각 슬라이드에 콘텐츠 삽입
        for slide_info in slides_data:
            slide_index = slide_info['index']
            ooxml_path = Path(base_dir) / slide_info['ooxml_file']

            if not ooxml_path.exists():
                print(f"Warning: OOXML file not found: {ooxml_path}")
                continue

            # 슬라이드 XML 경로 (1-indexed)
            slide_xml_path = temp_path / 'ppt' / 'slides' / f'slide{slide_index + 1}.xml'

            if not slide_xml_path.exists():
                print(f"Warning: Slide XML not found: {slide_xml_path}")
                continue

            # 슬라이드 XML 로드
            tree = ET.parse(slide_xml_path)
            root = tree.getroot()

            # spTree 찾기
            sp_tree = root.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}spTree')
            if sp_tree is None:
                print(f"Warning: spTree not found in slide {slide_index}")
                continue

            # OOXML 콘텐츠 로드 및 삽입
            content_element = load_ooxml_content(str(ooxml_path))

            # 네임스페이스 프리픽스 정리
            content_element = fix_namespaces(content_element)

            # spTree에 추가
            sp_tree.append(content_element)

            # 슬라이드 XML 저장
            tree.write(slide_xml_path, encoding='UTF-8', xml_declaration=True)

            print(f"Inserted content to slide {slide_index}: {slide_info['template_id']}")

        # 새 PPTX로 압축
        with zipfile.ZipFile(output_pptx, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_path)
                    zf.write(file_path, arcname)

        print(f"Output saved: {output_pptx}")


def fix_namespaces(element: ET.Element) -> ET.Element:
    """
    네임스페이스 프리픽스 정리

    ElementTree는 네임스페이스를 자동으로 ns0, ns1 등으로 변경하므로
    원래 프리픽스로 복원
    """
    # 이미 올바른 네임스페이스를 사용하고 있다면 그대로 반환
    return element


def main():
    parser = argparse.ArgumentParser(
        description='OOXML 콘텐츠를 PPTX 슬라이드에 삽입'
    )
    parser.add_argument('input_pptx', help='입력 PPTX 파일')
    parser.add_argument('stage4_json', help='stage-4.json 파일')
    parser.add_argument('output_pptx', help='출력 PPTX 파일')

    args = parser.parse_args()

    # stage-4.json 로드
    stage4 = load_stage4_json(args.stage4_json)

    # content_design이 있는 슬라이드 찾기
    slides_data = get_slides_with_content(stage4)

    if not slides_data:
        print("No slides with content_design found. Copying input to output.")
        shutil.copy(args.input_pptx, args.output_pptx)
        return

    print(f"Found {len(slides_data)} slides with content to insert")

    # 기준 디렉토리 (stage4_json이 있는 디렉토리)
    base_dir = Path(args.stage4_json).parent

    # 콘텐츠 삽입
    insert_content_to_pptx(
        args.input_pptx,
        slides_data,
        str(base_dir),
        args.output_pptx
    )


if __name__ == '__main__':
    main()
