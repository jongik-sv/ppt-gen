#!/usr/bin/env python3
"""
Stage 3: 템플릿 필터링 스크립트.
규칙 기반으로 후보 템플릿을 필터링.
"""

import sys
from pathlib import Path
from typing import Optional

import yaml


def load_templates(templates_dir: str = "templates/contents") -> list:
    """모든 콘텐츠 템플릿 로드."""
    templates = []
    base_path = Path(templates_dir)

    if not base_path.exists():
        return []

    for template_yaml in base_path.rglob("template.yaml"):
        try:
            with open(template_yaml, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            data["_path"] = str(template_yaml.parent)
            templates.append(data)
        except Exception:
            continue

    return templates


def filter_by_category(templates: list, category: str) -> list:
    """카테고리로 필터링."""
    return [t for t in templates if t.get("category") == category]


def filter_by_quality(templates: list, quality: str) -> list:
    """품질 호환성 필터링."""
    # high 품질은 high 템플릿만
    # medium/low는 모든 품질 사용 가능
    if quality == "high":
        return [t for t in templates if t.get("quality") == "high"]
    return templates


def filter_by_theme(templates: list, theme: Optional[str]) -> list:
    """테마 필터링 (선택적)."""
    if not theme:
        return templates
    # 테마 일치 우선, 없으면 전체
    matched = [t for t in templates if t.get("theme") == theme]
    return matched if matched else templates


def filter_by_item_count(templates: list, item_count: int) -> list:
    """항목 수로 필터링 (variants 확인)."""
    result = []
    for t in templates:
        # placeholders에서 array 타입 찾기
        for ph in t.get("placeholders", []):
            if ph.get("type") == "array":
                min_items = ph.get("min", ph.get("min_items", 1))
                max_items = ph.get("max", ph.get("max_items", 99))
                if min_items <= item_count <= max_items:
                    result.append(t)
                    break
        else:
            # array 타입 없으면 포함
            result.append(t)
    return result


def filter_by_slide_type(templates: list, slide_type: str) -> list:
    """슬라이드 타입으로 필터링."""
    type_to_category = {
        "cover": ["cover"],
        "toc": ["toc"],
        "section": ["divider", "section"],
        "content": ["grid", "list", "process", "timeline", "diagram", "infographic"],
        "chart": ["chart"],
        "closing": ["cover", "closing"],
    }
    categories = type_to_category.get(slide_type, [])
    if not categories:
        return templates
    return [t for t in templates if t.get("category") in categories]


def filter_by_content_type(templates: list, content_type: Optional[str]) -> list:
    """콘텐츠 타입으로 카테고리 필터링.

    content_type은 Stage 2에서 LLM이 분류한 콘텐츠 유형.
    해당 유형에 적합한 카테고리로 후보를 제한.
    """
    if not content_type:
        return templates

    type_to_categories = {
        "comparison": ["grid", "diagram"],      # 병렬 비교, 독립 항목
        "sequence": ["process"],                 # 순서, 단계, 흐름
        "timeline": ["timeline", "process"],     # 시간순 일정
        "hierarchy": ["list", "diagram"],        # 계층, 구조, 목록
        "metrics": ["infographic", "chart"],     # 수치, KPI, 퍼센트
    }

    categories = type_to_categories.get(content_type)
    if not categories:
        return templates  # 매핑 없으면 전체 반환

    filtered = [t for t in templates if t.get("category") in categories]
    # 매칭되는 후보가 없으면 원본 반환 (fallback)
    return filtered if filtered else templates


def filter_templates(
    slide_outline: dict,
    quality: str,
    theme: Optional[str] = None,
    templates_dir: str = "templates/contents",
) -> list:
    """
    슬라이드 아웃라인에 맞는 템플릿 후보 필터링.

    Returns:
        list: 후보 템플릿 목록 (0개, 1개, 또는 다수)
    """
    templates = load_templates(templates_dir)

    if not templates:
        return []

    # 1. 품질 필터링
    templates = filter_by_quality(templates, quality)

    # 2. 슬라이드 타입 필터링
    slide_type = slide_outline.get("type", "content")
    templates = filter_by_slide_type(templates, slide_type)

    # 3. 콘텐츠 타입 필터링 (신규: Stage 2에서 분류한 content_type 사용)
    outline = slide_outline.get("outline", {})
    content_type = outline.get("content_type")
    if content_type:
        templates = filter_by_content_type(templates, content_type)

    # 4. 테마 필터링 (우선순위)
    templates = filter_by_theme(templates, theme)

    # 5. 항목 수 필터링 (key_points 기반)
    key_points = outline.get("key_points", [])
    if key_points:
        templates = filter_by_item_count(templates, len(key_points))

    return templates


def get_template_summary(template: dict) -> dict:
    """LLM 전달용 템플릿 요약."""
    return {
        "id": template.get("id"),
        "name": template.get("name"),
        "category": template.get("category"),
        "description": template.get("description"),
        "semantic_description": template.get("semantic_description"),
        "match_keywords": template.get("match_keywords", []),
        "quality": template.get("quality"),
        "_path": template.get("_path"),
    }


def run_filter(
    slide_outline: dict,
    quality: str,
    theme: Optional[str] = None,
    templates_dir: str = "templates/contents",
) -> dict:
    """
    필터링 실행 및 결과 반환.

    Returns:
        dict: {
            "count": int,
            "action": "use" | "select" | "generate",
            "candidates": list
        }
    """
    candidates = filter_templates(slide_outline, quality, theme, templates_dir)
    summaries = [get_template_summary(t) for t in candidates]

    count = len(summaries)
    if count == 0:
        action = "generate"  # LLM이 새 HTML 생성
    elif count == 1:
        action = "use"  # 바로 사용
    else:
        action = "select"  # LLM이 시맨틱 선택

    return {
        "count": count,
        "action": action,
        "candidates": summaries,
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="템플릿 필터링")
    parser.add_argument("--outline", required=True, help="슬라이드 아웃라인 JSON")
    parser.add_argument("--quality", default="medium", help="품질 옵션")
    parser.add_argument("--theme", default=None, help="테마 ID")
    parser.add_argument("--templates-dir", default="templates/contents")

    args = parser.parse_args()

    outline = json.loads(args.outline)
    result = run_filter(outline, args.quality, args.theme, args.templates_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
