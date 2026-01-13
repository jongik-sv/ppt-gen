#!/usr/bin/env python3
"""
Stage 5: PPTX 병합기.
개별 슬라이드들을 최종 PPTX로 병합.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import yaml

# lib 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from ooxml.scripts import pack_office_file, unpack_office_file


def merge_html_slides(
    html_files: list,
    output_pptx: str,
    slide_size: str = "16:9",
) -> str:
    """
    HTML 슬라이드들을 PPTX로 변환 및 병합.

    Args:
        html_files: HTML 파일 경로 리스트
        output_pptx: 출력 PPTX 경로
        slide_size: 슬라이드 크기 (16:9, 4:3, 16:10)

    Returns:
        출력 파일 경로
    """
    script_dir = Path(__file__).parent
    html2pptx_js = script_dir / "html2pptx.js"

    # 크기 설정
    size_map = {
        "16:9": {"w": 10, "h": 5.625},
        "4:3": {"w": 10, "h": 7.5},
        "16:10": {"w": 10, "h": 6.25},
    }
    size = size_map.get(slide_size, size_map["16:9"])

    # Node.js 스크립트 생성
    js_code = f"""
const html2pptx = require('{html2pptx_js}');
const PptxGenJS = require('pptxgenjs');

async function main() {{
    const pptx = new PptxGenJS();
    pptx.defineLayout({{ name: 'CUSTOM', width: {size['w']}, height: {size['h']} }});
    pptx.layout = 'CUSTOM';

    const htmlFiles = {html_files};

    for (const htmlFile of htmlFiles) {{
        await html2pptx(htmlFile, pptx);
    }}

    await pptx.writeFile('{output_pptx}');
    console.log('Created:', '{output_pptx}');
}}

main().catch(console.error);
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(js_code)
        temp_js = f.name

    try:
        # NODE_PATH를 설정하여 현재 작업 디렉토리의 node_modules를 찾을 수 있도록 함
        import os
        env = os.environ.copy()
        env["NODE_PATH"] = str(Path.cwd() / "node_modules")
        result = subprocess.run(
            ["node", temp_js],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(f"html2pptx failed: {result.stderr}")
    finally:
        Path(temp_js).unlink(missing_ok=True)

    return output_pptx


def merge_pptx_slides(
    pptx_files: list,
    output_pptx: str,
) -> str:
    """
    여러 PPTX 파일을 하나로 병합.

    Args:
        pptx_files: PPTX 파일 경로 리스트
        output_pptx: 출력 PPTX 경로

    Returns:
        출력 파일 경로
    """
    if not pptx_files:
        raise ValueError("No PPTX files to merge")

    if len(pptx_files) == 1:
        shutil.copy(pptx_files[0], output_pptx)
        return output_pptx

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 첫 번째 파일을 베이스로 사용
        base_dir = temp_path / "base"
        unpack_office_file(pptx_files[0], str(base_dir))

        # 나머지 파일들의 슬라이드 추가
        slide_count = count_slides(base_dir)

        for pptx_file in pptx_files[1:]:
            source_dir = temp_path / f"source_{Path(pptx_file).stem}"
            unpack_office_file(pptx_file, str(source_dir))

            # 슬라이드 복사
            source_slides = source_dir / "ppt" / "slides"
            target_slides = base_dir / "ppt" / "slides"

            for slide_file in sorted(source_slides.glob("slide*.xml")):
                slide_count += 1
                new_name = f"slide{slide_count}.xml"
                shutil.copy(slide_file, target_slides / new_name)

                # 관계 파일도 복사
                rels_file = source_slides / "_rels" / f"{slide_file.name}.rels"
                if rels_file.exists():
                    target_rels = target_slides / "_rels"
                    target_rels.mkdir(exist_ok=True)
                    shutil.copy(rels_file, target_rels / f"{new_name}.rels")

            # presentation.xml 업데이트 필요 (슬라이드 목록)
            update_presentation_xml(base_dir, slide_count)

        # 패킹
        Path(output_pptx).parent.mkdir(parents=True, exist_ok=True)
        pack_office_file(str(base_dir), output_pptx)

    return output_pptx


def count_slides(unpacked_dir: Path) -> int:
    """슬라이드 수 카운트."""
    slides_dir = unpacked_dir / "ppt" / "slides"
    return len(list(slides_dir.glob("slide*.xml")))


def update_presentation_xml(unpacked_dir: Path, total_slides: int) -> None:
    """presentation.xml 슬라이드 목록 업데이트."""
    pres_xml = unpacked_dir / "ppt" / "presentation.xml"
    content = pres_xml.read_text(encoding="utf-8")

    # 슬라이드 리스트 재생성 (간단한 구현)
    # 실제로는 r:id 관계도 업데이트 필요
    # 이 부분은 복잡해서 실제 사용 시 더 정교한 구현 필요

    pres_xml.write_text(content, encoding="utf-8")


def apply_document_style(
    pptx_path: str,
    style_id: str,
    documents_dir: str = "templates/documents",
) -> str:
    """
    문서 양식 적용 (헤더, 푸터, 로고, 슬라이드 마스터).

    Args:
        pptx_path: 대상 PPTX 경로
        style_id: 문서 양식 ID
        documents_dir: 문서 양식 디렉토리

    Returns:
        수정된 PPTX 경로
    """
    style_dir = Path(documents_dir) / style_id
    if not style_dir.exists():
        return pptx_path  # 양식 없으면 그대로 반환

    # 양식 정보 로드
    info_path = style_dir / "info.yaml"
    if not info_path.exists():
        return pptx_path

    with open(info_path, "r", encoding="utf-8") as f:
        style_info = yaml.safe_load(f)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        unpacked_dir = temp_path / "unpacked"

        # PPTX 언팩
        unpack_office_file(pptx_path, str(unpacked_dir))

        # 슬라이드 마스터 적용
        master_pptx = style_dir / "master.pptx"
        if master_pptx.exists():
            apply_slide_master(unpacked_dir, master_pptx)

        # 헤더/푸터 적용
        header_footer = style_info.get("header_footer", {})
        if header_footer:
            apply_header_footer(unpacked_dir, header_footer)

        # 로고 적용
        logo = style_info.get("logo", {})
        if logo:
            apply_logo(unpacked_dir, style_dir, logo)

        # 재패킹
        pack_office_file(str(unpacked_dir), pptx_path)

    return pptx_path


def apply_slide_master(unpacked_dir: Path, master_pptx: Path) -> None:
    """슬라이드 마스터 적용."""
    # 마스터 PPTX에서 slideMasters, slideLayouts, theme 복사
    with tempfile.TemporaryDirectory() as temp:
        master_dir = Path(temp) / "master"
        unpack_office_file(str(master_pptx), str(master_dir))

        # 복사할 폴더들
        for folder in ["slideMasters", "slideLayouts", "theme"]:
            src = master_dir / "ppt" / folder
            dst = unpacked_dir / "ppt" / folder
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)


def apply_header_footer(unpacked_dir: Path, config: dict) -> None:
    """헤더/푸터 적용."""
    # 각 슬라이드에 헤더/푸터 요소 추가
    # 실제 구현은 OOXML 구조에 맞게 작성 필요
    pass


def apply_logo(unpacked_dir: Path, style_dir: Path, config: dict) -> None:
    """로고 적용."""
    logo_file = style_dir / config.get("file", "logo.png")
    if not logo_file.exists():
        return

    # 로고 이미지를 media 폴더에 복사하고 슬라이드에 추가
    # 실제 구현은 OOXML 구조에 맞게 작성 필요
    media_dir = unpacked_dir / "ppt" / "media"
    media_dir.mkdir(exist_ok=True)
    shutil.copy(logo_file, media_dir / "logo.png")


def run_stage5(
    session_path: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Stage 5 실행: 최종 PPTX 생성.

    Args:
        session_path: session.yaml 경로
        output_path: 출력 PPTX 경로 (None이면 자동 생성)

    Returns:
        출력 PPTX 경로
    """
    with open(session_path, "r", encoding="utf-8") as f:
        session = yaml.safe_load(f)

    settings = session.get("settings", {})
    slides = session.get("slides", [])
    quality = settings.get("quality", "medium")

    # 출력 경로 결정
    if not output_path:
        session_dir = Path(session_path).parent
        output_path = str(session_dir / "output" / "presentation.pptx")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if quality == "high":
        # OOXML 슬라이드 병합
        pptx_files = []
        for slide in slides:
            final_attempt = slide.get("final_attempt", 1)
            attempts = slide.get("attempts", [])
            if attempts and final_attempt <= len(attempts):
                pptx_file = attempts[final_attempt - 1].get("file")
                if pptx_file and Path(pptx_file).suffix == ".pptx":
                    pptx_files.append(pptx_file)

        merge_pptx_slides(pptx_files, output_path)
    else:
        # HTML 슬라이드 변환 및 병합
        html_files = []
        for slide in slides:
            final_attempt = slide.get("final_attempt", 1)
            attempts = slide.get("attempts", [])
            if attempts and final_attempt <= len(attempts):
                html_file = attempts[final_attempt - 1].get("file")
                if html_file and Path(html_file).suffix == ".html":
                    html_files.append(html_file)

        slide_size = settings.get("slide_size", "16:9")
        merge_html_slides(html_files, output_path, slide_size)

    # 문서 양식 적용
    document_style = settings.get("document_style")
    if document_style:
        apply_document_style(output_path, document_style)

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PPTX 병합")
    parser.add_argument("session", help="session.yaml 경로")
    parser.add_argument("--output", default=None, help="출력 PPTX 경로")

    args = parser.parse_args()

    output = run_stage5(args.session, args.output)
    print(f"Created: {output}")
