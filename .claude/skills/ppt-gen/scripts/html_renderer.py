#!/usr/bin/env python3
"""
Stage 4: HTML 렌더러.
Handlebars 템플릿에 콘텐츠와 테마를 주입하여 최종 HTML 생성.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml


def load_theme(theme_id: str, themes_dir: str = "templates/themes") -> dict:
    """테마 로드."""
    theme_path = Path(themes_dir) / theme_id / "theme.yaml"
    if not theme_path.exists():
        return get_default_theme()

    with open(theme_path, "r", encoding="utf-8") as f:
        theme = yaml.safe_load(f)

    return flatten_theme(theme)


def get_default_theme() -> dict:
    """기본 테마."""
    return {
        "primary": "#22523B",
        "secondary": "#153325",
        "accent": "#479374",
        "gradient.dark": "#153325",
        "gradient.deep": "#183C2B",
        "gradient.primary": "#22523B",
        "gradient.accent": "#479374",
        "gradient.medium": "#578F76",
        "gradient.light": "#67B7B5",
        "muted.dark": "#6F886A",
        "muted.green": "#83A99B",
        "muted.sage": "#859C80",
        "muted.mint": "#8BAFA2",
        "muted.aqua": "#99C7BF",
        "muted.pale": "#A1BFB4",
        "muted.light": "#C4D6D0",
        "background.dark": "#153325",
        "background.light": "#DCF0EF",
        "background.neutral": "#E8E8E8",
    }


def flatten_theme(theme: dict, prefix: str = "") -> dict:
    """중첩된 테마를 플랫하게 변환."""
    result = {}
    colors = theme.get("colors", {})

    def flatten(obj, current_prefix):
        for key, value in obj.items():
            new_key = f"{current_prefix}.{key}" if current_prefix else key
            if isinstance(value, dict):
                flatten(value, new_key)
            else:
                result[new_key] = value

    flatten(colors, "")
    return result


def render_handlebars(template_html: str, context: dict) -> str:
    """
    Handlebars 템플릿 렌더링.
    Node.js의 handlebars 사용.
    """
    # 간단한 Python 기반 Handlebars 대체 구현
    result = template_html

    # 1. 단순 변수 치환 {{var}}
    def replace_var(match):
        path = match.group(1).strip()
        value = get_nested_value(context, path)
        return str(value) if value is not None else ""

    result = re.sub(r"\{\{(?!#|/)([^}]+)\}\}", replace_var, result)

    # 2. each 블록 처리 {{#each items}}...{{/each}}
    def replace_each(match):
        var_name = match.group(1).strip()
        block_content = match.group(2)
        items = get_nested_value(context, var_name)

        if not items or not isinstance(items, list):
            return ""

        rendered = []
        for item in items:
            item_content = block_content
            # this.property 치환
            item_content = re.sub(
                r"\{\{this\.([^}]+)\}\}",
                lambda m: str(item.get(m.group(1).strip(), "")),
                item_content,
            )
            # this 자체 치환
            item_content = re.sub(
                r"\{\{this\}\}",
                lambda m: str(item) if not isinstance(item, dict) else "",
                item_content,
            )
            rendered.append(item_content)
        return "".join(rendered)

    result = re.sub(
        r"\{\{#each\s+([^}]+)\}\}(.*?)\{\{/each\}\}",
        replace_each,
        result,
        flags=re.DOTALL,
    )

    # 3. if 블록 처리 {{#if condition}}...{{/if}}
    def replace_if(match):
        condition = match.group(1).strip()
        block_content = match.group(2)
        value = get_nested_value(context, condition)
        return block_content if value else ""

    result = re.sub(
        r"\{\{#if\s+([^}]+)\}\}(.*?)\{\{/if\}\}",
        replace_if,
        result,
        flags=re.DOTALL,
    )

    return result


def get_nested_value(obj: dict, path: str):
    """점 표기법으로 중첩 값 가져오기."""
    keys = path.split(".")
    value = obj
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


def inject_css_variables(html: str, theme_path: str) -> str:
    """CSS 변수에 테마 값 주입.

    템플릿 HTML에서 비어있는 CSS 변수 값을 테마 파일의 값으로 채웁니다.

    Args:
        html: 렌더링된 HTML 문자열
        theme_path: 테마 YAML 파일 경로

    Returns:
        CSS 변수가 주입된 HTML 문자열
    """
    with open(theme_path, 'r', encoding='utf-8') as f:
        theme = yaml.safe_load(f)

    colors = theme.get('colors', {})
    tokens = colors.get('tokens', {})
    bg = colors.get('background', {})
    muted = colors.get('muted', {})

    # tokens: gradient-1 ~ gradient-6 (이미 CSS 변수명과 일치)
    for var_name, value in tokens.items():
        # --gradient-1: ; → --gradient-1: #153325;
        pattern = rf"(--{var_name}:\s*);?"
        html = re.sub(pattern, f"--{var_name}: {value};", html)

    # background: bg-light, bg-neutral, bg-dark
    for bg_name, value in bg.items():
        pattern = rf"(--bg-{bg_name}:\s*);?"
        html = re.sub(pattern, f"--bg-{bg_name}: {value};", html)

    # muted: muted.dark → --muted-1 등 (순서 매핑)
    muted_order = ['dark', 'green', 'sage', 'mint', 'aqua', 'pale', 'light']
    for i, key in enumerate(muted_order, 1):
        if key in muted:
            pattern = rf"(--muted-{i}:\s*);?"
            html = re.sub(pattern, f"--muted-{i}: {muted[key]};", html)

    # muted 변수가 단독으로 사용되는 경우 (--muted: )
    if 'dark' in muted:
        pattern = r"(--muted:\s*);?"
        html = re.sub(pattern, f"--muted: {muted['dark']};", html)

    return html


def render_template(
    template_path: str,
    content: dict,
    theme_id: Optional[str] = None,
    themes_dir: str = "templates/themes",
    output_path: Optional[str] = None,
) -> str:
    """
    템플릿 렌더링 메인 함수.

    Args:
        template_path: template.html 경로
        content: 콘텐츠 데이터
        theme_id: 테마 ID
        themes_dir: 테마 디렉토리
        output_path: 출력 파일 경로 (None이면 문자열 반환)

    Returns:
        렌더링된 HTML 문자열
    """
    # 템플릿 로드
    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()

    # 테마 로드
    theme = load_theme(theme_id, themes_dir) if theme_id else get_default_theme()

    # 컨텍스트 구성
    context = {
        "theme": theme,
        **content,
    }

    # 렌더링
    rendered = render_handlebars(template_html, context)

    # CSS 변수 주입 (테마가 지정된 경우)
    if theme_id:
        theme_path = Path(themes_dir) / theme_id / "theme.yaml"
        if theme_path.exists():
            rendered = inject_css_variables(rendered, str(theme_path))

    # 출력
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)

    return rendered


def capture_screenshot(
    html_path: str,
    output_path: str,
    width: int = 1920,
    height: int = 734,
) -> bool:
    """
    Playwright로 HTML 스크린샷 캡처.
    """
    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.setViewportSize({{ width: {width}, height: {height} }});
    await page.goto('file://{html_path}');
    await page.waitForLoadState('networkidle');
    await page.screenshot({{ path: '{output_path}', fullPage: false }});
    await browser.close();
}})();
"""
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="HTML 템플릿 렌더링")
    parser.add_argument("template", help="템플릿 HTML 경로")
    parser.add_argument("--content", required=True, help="콘텐츠 JSON")
    parser.add_argument("--theme", default=None, help="테마 ID")
    parser.add_argument("--output", default=None, help="출력 파일")
    parser.add_argument("--screenshot", action="store_true", help="스크린샷 캡처")

    args = parser.parse_args()

    content = json.loads(args.content)
    html = render_template(args.template, content, args.theme, output_path=args.output)

    if args.screenshot and args.output:
        screenshot_path = args.output.replace(".html", ".png")
        capture_screenshot(args.output, screenshot_path)
        print(f"Screenshot: {screenshot_path}")
    elif not args.output:
        print(html)
