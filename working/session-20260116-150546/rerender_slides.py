#!/usr/bin/env python3
"""
모든 슬라이드 재렌더링 스크립트.
수정된 html_renderer.py를 사용하여 콘텐츠를 올바르게 주입.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / ".claude" / "skills" / "ppt-gen" / "scripts"))

import yaml
from html_renderer import render_template

# Template paths mapping
TEMPLATE_PATHS = {
    "cover-deep-green-01": "templates/contents/cover/cover-deep-green-01/template.html",
    "toc-deep-green-01": "templates/contents/toc/toc-deep-green-01/template.html",
    "divider-deep-green-01": "templates/contents/divider/divider-deep-green-01/template.html",
    "card-4col-01": "templates/contents/grid/card-4col-01/template.html",
    "card-4col-numbered-01": "templates/contents/grid/card-4col-numbered-01/template.html",
    "card-4col-teal": "templates/contents/grid/card-4col-teal/template.html",
    "disk-3row-01": "templates/contents/list/disk-3row-01/template.html",
    "honeycomb-5-01": "templates/contents/diagram/honeycomb-5-01/template.html",
    "smartart-left-01": "templates/contents/diagram/smartart-left-01/template.html",
    "radial-5-01": "templates/contents/diagram/radial-5-01/template.html",
    "circle-3step-01": "templates/contents/process/circle-3step-01/template.html",
    "process-6step-01": "templates/contents/grid/process-6step-01/template.html",
    "connector-2row-01": "templates/contents/timeline/connector-2row-01/template.html",
    "percent-dot-01": "templates/contents/infographic/percent-dot-01/template.html",
}


def main():
    session_dir = Path(__file__).parent
    project_root = session_dir.parent.parent

    # Load session.yaml
    with open(session_dir / "session.yaml", "r", encoding="utf-8") as f:
        session = yaml.safe_load(f)

    slides_dir = session_dir / "slides"
    slides_dir.mkdir(exist_ok=True)

    slides = session.get("slides", [])
    success_count = 0
    fail_count = 0

    for slide in slides:
        slide_num = slide["slide_number"]
        template_id = slide["template"]["id"]
        content = slide.get("content", {})
        slide_title = slide.get("title", "untitled")

        # Create filename
        safe_title = slide_title.lower().replace(" ", "_").replace("/", "_")
        filename = f"slide_{slide_num:02d}_{safe_title}.html"
        output_path = slides_dir / filename

        # Get template path
        if template_id not in TEMPLATE_PATHS:
            print(f"[SKIP] Slide {slide_num}: Template '{template_id}' not found in mapping")
            fail_count += 1
            continue

        template_path = project_root / TEMPLATE_PATHS[template_id]
        if not template_path.exists():
            print(f"[SKIP] Slide {slide_num}: Template file not found: {template_path}")
            fail_count += 1
            continue

        # Render
        try:
            rendered = render_template(
                str(template_path),
                content,
                theme_id="deep-green",
                themes_dir=str(project_root / "templates" / "themes"),
                output_path=str(output_path)
            )
            print(f"[OK] Slide {slide_num}: {filename}")
            success_count += 1
        except Exception as e:
            print(f"[ERROR] Slide {slide_num}: {e}")
            fail_count += 1

    print(f"\nCompleted: {success_count} success, {fail_count} failed")


if __name__ == "__main__":
    main()
