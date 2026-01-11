#!/usr/bin/env python3
"""
폰트 관리 및 대체 매핑.

시스템 폰트 확인 → 다운로드 시도 → 대체 폰트 적용

Usage:
    python font-manager.py check "Pretendard"
    python font-manager.py fallback "Pretendard"
    python font-manager.py list-system
"""

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# 폰트 대체 매핑 (우선순위 순서)
FONT_FALLBACK = {
    # 한글 모던 폰트
    "Pretendard": ["SUIT", "Noto Sans KR", "맑은 고딕", "Apple SD Gothic Neo"],
    "SUIT": ["Pretendard", "Noto Sans KR", "맑은 고딕", "Apple SD Gothic Neo"],
    "Noto Sans KR": ["Pretendard", "SUIT", "맑은 고딕", "Apple SD Gothic Neo"],

    # 한글 전통 폰트
    "나눔스퀘어Neo": ["NanumSquare", "Noto Sans KR", "맑은 고딕"],
    "NanumSquare": ["나눔스퀘어Neo", "Noto Sans KR", "맑은 고딕"],
    "나눔고딕": ["NanumGothic", "Noto Sans KR", "맑은 고딕"],
    "맑은 고딕": ["Malgun Gothic", "Noto Sans KR", "Apple SD Gothic Neo", "sans-serif"],

    # 영문 폰트
    "Arial": ["Helvetica", "Liberation Sans", "DejaVu Sans", "sans-serif"],
    "Helvetica": ["Arial", "Liberation Sans", "DejaVu Sans", "sans-serif"],
    "Times New Roman": ["Liberation Serif", "DejaVu Serif", "serif"],
    "Georgia": ["Times New Roman", "Liberation Serif", "serif"],
    "Courier New": ["Liberation Mono", "DejaVu Sans Mono", "monospace"],

    # 제목 폰트
    "Impact": ["Arial Black", "Helvetica Bold", "sans-serif"],
    "Trebuchet MS": ["Arial", "Helvetica", "sans-serif"],

    # 기본 대체
    "default_korean": ["맑은 고딕", "Apple SD Gothic Neo", "Noto Sans KR", "sans-serif"],
    "default_english": ["Arial", "Helvetica", "Liberation Sans", "sans-serif"],
    "default_mono": ["Courier New", "Liberation Mono", "monospace"],
}

# 폰트 다운로드 URL (웹폰트 CDN)
FONT_CDN = {
    "Pretendard": "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css",
    "SUIT": "https://cdn.jsdelivr.net/gh/sunn-us/SUIT@v1.0.0/fonts/static/SUIT.css",
    "Noto Sans KR": "https://fonts.googleapis.com/css2?family=Noto+Sans+KR",
}


def get_system_font_dirs() -> List[Path]:
    """시스템 폰트 디렉토리 목록"""
    system = platform.system()

    if system == "Darwin":  # macOS
        return [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path.home() / "Library/Fonts",
        ]
    elif system == "Windows":
        return [
            Path("C:/Windows/Fonts"),
            Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
        ]
    else:  # Linux
        return [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
            Path.home() / ".local/share/fonts",
        ]


def find_font_file(font_name: str) -> Optional[Path]:
    """시스템에서 폰트 파일 찾기"""
    font_dirs = get_system_font_dirs()
    extensions = [".ttf", ".otf", ".ttc", ".woff", ".woff2"]

    # 폰트 이름 변형
    name_variants = [
        font_name,
        font_name.lower(),
        font_name.replace(" ", ""),
        font_name.replace(" ", "-"),
        font_name.replace(" ", "_"),
    ]

    for font_dir in font_dirs:
        if not font_dir.exists():
            continue

        for variant in name_variants:
            for ext in extensions:
                # 직접 매칭
                font_path = font_dir / f"{variant}{ext}"
                if font_path.exists():
                    return font_path

                # 재귀 검색
                for path in font_dir.rglob(f"*{variant}*{ext}"):
                    return path

    return None


def is_font_installed(font_name: str) -> bool:
    """폰트 설치 여부 확인"""
    return find_font_file(font_name) is not None


def get_fallback_font(font_name: str) -> Optional[str]:
    """대체 폰트 찾기 (설치된 것 중 첫 번째)"""
    fallbacks = FONT_FALLBACK.get(font_name, FONT_FALLBACK.get("default_korean", []))

    for fallback in fallbacks:
        if fallback in ["sans-serif", "serif", "monospace"]:
            return fallback
        if is_font_installed(fallback):
            return fallback

    return None


def list_system_fonts() -> List[Dict[str, str]]:
    """시스템에 설치된 폰트 목록"""
    fonts = []
    seen = set()

    for font_dir in get_system_font_dirs():
        if not font_dir.exists():
            continue

        for ext in [".ttf", ".otf", ".ttc"]:
            for font_path in font_dir.rglob(f"*{ext}"):
                font_name = font_path.stem
                if font_name not in seen:
                    seen.add(font_name)
                    fonts.append({
                        "name": font_name,
                        "path": str(font_path),
                        "type": ext[1:].upper(),
                    })

    fonts.sort(key=lambda f: f["name"].lower())
    return fonts


def check_font(font_name: str) -> Dict[str, any]:
    """폰트 상태 확인"""
    installed = is_font_installed(font_name)
    font_path = find_font_file(font_name) if installed else None
    fallback = get_fallback_font(font_name) if not installed else None

    return {
        "font_name": font_name,
        "installed": installed,
        "path": str(font_path) if font_path else None,
        "fallback": fallback,
        "cdn_available": font_name in FONT_CDN,
    }


def resolve_font(font_name: str) -> Tuple[str, str]:
    """
    폰트 해결: 설치됨 → 사용, 아니면 대체 폰트 반환

    Returns:
        (resolved_font, status) 튜플
        status: 'installed', 'fallback', 'generic'
    """
    if is_font_installed(font_name):
        return font_name, "installed"

    fallback = get_fallback_font(font_name)
    if fallback:
        if fallback in ["sans-serif", "serif", "monospace"]:
            return fallback, "generic"
        return fallback, "fallback"

    return "sans-serif", "generic"


def save_fallback_mapping(output_path: Path):
    """대체 매핑을 YAML로 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "font_fallback": FONT_FALLBACK,
        "font_cdn": FONT_CDN,
    }

    if HAS_YAML:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    else:
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="폰트 관리 및 대체 매핑"
    )
    subparsers = parser.add_subparsers(dest="command", help="명령")

    # check 명령
    check_parser = subparsers.add_parser("check", help="폰트 설치 확인")
    check_parser.add_argument("font_name", help="확인할 폰트 이름")

    # fallback 명령
    fallback_parser = subparsers.add_parser("fallback", help="대체 폰트 찾기")
    fallback_parser.add_argument("font_name", help="폰트 이름")

    # resolve 명령
    resolve_parser = subparsers.add_parser("resolve", help="폰트 해결 (설치 또는 대체)")
    resolve_parser.add_argument("font_name", help="폰트 이름")

    # list-system 명령
    list_parser = subparsers.add_parser("list-system", help="시스템 폰트 목록")
    list_parser.add_argument("--json", action="store_true", help="JSON 출력")

    # export 명령
    export_parser = subparsers.add_parser("export", help="대체 매핑 내보내기")
    export_parser.add_argument("--output", "-o", default="font-mappings.yaml", help="출력 파일")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "check":
            result = check_font(args.font_name)
            print(json.dumps(result, indent=2, ensure_ascii=False))

            if result["installed"]:
                print(f"\n✓ '{args.font_name}' 설치됨: {result['path']}")
            else:
                print(f"\n✗ '{args.font_name}' 미설치")
                if result["fallback"]:
                    print(f"  대체 폰트: {result['fallback']}")
                if result["cdn_available"]:
                    print(f"  웹폰트 사용 가능: {FONT_CDN[args.font_name]}")

        elif args.command == "fallback":
            fallback = get_fallback_font(args.font_name)
            if fallback:
                print(f"'{args.font_name}' → '{fallback}'")
            else:
                print(f"'{args.font_name}'에 대한 대체 폰트 없음")
                sys.exit(1)

        elif args.command == "resolve":
            resolved, status = resolve_font(args.font_name)
            print(json.dumps({
                "original": args.font_name,
                "resolved": resolved,
                "status": status,
            }, indent=2))

        elif args.command == "list-system":
            fonts = list_system_fonts()
            if args.json:
                print(json.dumps(fonts, indent=2, ensure_ascii=False))
            else:
                print(f"시스템 폰트 {len(fonts)}개:\n")
                for font in fonts[:50]:  # 처음 50개만 표시
                    print(f"  {font['name']} ({font['type']})")
                if len(fonts) > 50:
                    print(f"  ... 외 {len(fonts) - 50}개")

        elif args.command == "export":
            save_fallback_mapping(Path(args.output))
            print(f"저장됨: {args.output}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
