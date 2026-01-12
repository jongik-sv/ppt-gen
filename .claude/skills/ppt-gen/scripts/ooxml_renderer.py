#!/usr/bin/env python3
"""
Stage 4: OOXML 렌더러.
high 품질 옵션용 - 원본 PPTX의 플레이스홀더를 콘텐츠로 치환.
"""

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

# lib 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from ooxml.scripts.pack import pack_office_file
from ooxml.scripts.unpack import unpack_office_file


def load_slide_xml(unpacked_dir: Path, slide_index: int) -> str:
    """슬라이드 XML 로드."""
    slide_path = unpacked_dir / "ppt" / "slides" / f"slide{slide_index}.xml"
    if not slide_path.exists():
        raise FileNotFoundError(f"Slide not found: {slide_path}")
    return slide_path.read_text(encoding="utf-8")


def save_slide_xml(unpacked_dir: Path, slide_index: int, content: str) -> None:
    """슬라이드 XML 저장."""
    slide_path = unpacked_dir / "ppt" / "slides" / f"slide{slide_index}.xml"
    slide_path.write_text(content, encoding="utf-8")


def replace_text_in_xml(xml_content: str, replacements: dict) -> str:
    """
    XML 내 텍스트 플레이스홀더 치환.

    replacements: {
        "{{placeholder}}": "replacement text",
        ...
    }
    """
    result = xml_content
    for placeholder, replacement in replacements.items():
        # XML 특수문자 이스케이프
        escaped_replacement = (
            replacement.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
        result = result.replace(placeholder, escaped_replacement)
    return result


def render_ooxml_slide(
    template_pptx: str,
    slide_index: int,
    content: dict,
    output_pptx: str,
) -> str:
    """
    OOXML 슬라이드 렌더링.

    Args:
        template_pptx: 원본 PPTX 템플릿 경로
        slide_index: 슬라이드 번호 (1-based)
        content: 치환할 콘텐츠
        output_pptx: 출력 PPTX 경로

    Returns:
        출력 파일 경로
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        unpacked_dir = temp_path / "unpacked"

        # 1. PPTX 언팩
        unpack_office_file(template_pptx, str(unpacked_dir))

        # 2. 슬라이드 XML 로드
        xml_content = load_slide_xml(unpacked_dir, slide_index)

        # 3. 플레이스홀더 치환
        replacements = build_replacements(content)
        modified_xml = replace_text_in_xml(xml_content, replacements)

        # 4. 수정된 XML 저장
        save_slide_xml(unpacked_dir, slide_index, modified_xml)

        # 5. PPTX 재패킹
        Path(output_pptx).parent.mkdir(parents=True, exist_ok=True)
        pack_office_file(str(unpacked_dir), output_pptx)

    return output_pptx


def build_replacements(content: dict) -> dict:
    """콘텐츠를 플레이스홀더 치환 맵으로 변환."""
    replacements = {}

    # 단순 필드
    for key, value in content.items():
        if isinstance(value, str):
            replacements[f"{{{{{key}}}}}"] = value
        elif isinstance(value, list):
            # 배열 항목
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    for sub_key, sub_value in item.items():
                        replacements[f"{{{{{key}[{i}].{sub_key}}}}}"] = str(sub_value)
                else:
                    replacements[f"{{{{{key}[{i}]}}}}"] = str(item)

    return replacements


def render_multi_slides(
    template_pptx: str,
    slides_content: list,
    output_pptx: str,
) -> str:
    """
    여러 슬라이드를 순차적으로 렌더링.

    Args:
        template_pptx: 원본 PPTX 템플릿
        slides_content: [
            {"index": 1, "content": {...}},
            {"index": 2, "content": {...}},
            ...
        ]
        output_pptx: 출력 PPTX 경로

    Returns:
        출력 파일 경로
    """
    # 첫 번째 슬라이드 처리
    if not slides_content:
        shutil.copy(template_pptx, output_pptx)
        return output_pptx

    # 임시 파일로 순차 처리
    current_pptx = template_pptx

    with tempfile.TemporaryDirectory() as temp_dir:
        for i, slide_data in enumerate(slides_content):
            slide_index = slide_data.get("index", i + 1)
            content = slide_data.get("content", {})

            if i == len(slides_content) - 1:
                # 마지막 슬라이드는 최종 출력으로
                target_pptx = output_pptx
            else:
                target_pptx = str(Path(temp_dir) / f"temp_{i}.pptx")

            render_ooxml_slide(current_pptx, slide_index, content, target_pptx)
            current_pptx = target_pptx

    return output_pptx


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="OOXML 슬라이드 렌더링")
    parser.add_argument("template", help="원본 PPTX 경로")
    parser.add_argument("--slide", type=int, default=1, help="슬라이드 번호")
    parser.add_argument("--content", required=True, help="콘텐츠 JSON")
    parser.add_argument("--output", required=True, help="출력 PPTX 경로")

    args = parser.parse_args()

    content = json.loads(args.content)
    output = render_ooxml_slide(args.template, args.slide, content, args.output)
    print(f"Rendered: {output}")
