#!/usr/bin/env python3
"""
Stage 1: 설정 수집 스크립트.
사용자에게 PPT 생성에 필요한 설정을 질문하고 session.yaml에 저장.
"""

import sys
from pathlib import Path
from typing import Optional

# session_manager 임포트
sys.path.insert(0, str(Path(__file__).parent))
from session_manager import SessionManager


# 문서 종류
DOCUMENT_TYPES = [
    {"id": "proposal", "name": "제안서", "desc": "고객 설득을 위한 임팩트 중심"},
    {"id": "bizplan", "name": "사업계획서", "desc": "체계적인 전략 수립"},
    {"id": "report", "name": "프로젝트 보고서", "desc": "진행 현황 및 성과 공유"},
    {"id": "lecture", "name": "교육 자료", "desc": "정보 전달 및 학습"},
]

# 청중 대상
AUDIENCES = [
    {"id": "executive", "name": "경영진/임원"},
    {"id": "team", "name": "실무자/팀원"},
    {"id": "customer", "name": "고객/파트너"},
    {"id": "investor", "name": "투자자"},
    {"id": "public", "name": "일반 대중"},
]

# 발표 시간
DURATIONS = [
    {"id": "5min", "name": "5분", "slides": "5~7장"},
    {"id": "10min", "name": "10분", "slides": "8~12장"},
    {"id": "20min", "name": "20분", "slides": "15~20장"},
    {"id": "30min+", "name": "30분 이상", "slides": "20장+"},
]

# 톤 & 스타일
TONES = [
    {"id": "formal", "name": "공식적 (Formal)", "desc": "격식 있는 비즈니스"},
    {"id": "casual", "name": "캐주얼 (Casual)", "desc": "친근한 설명"},
    {"id": "academic", "name": "학술적 (Academic)", "desc": "연구/분석 중심"},
    {"id": "data-driven", "name": "데이터 중심", "desc": "차트/수치 강조"},
]

# 품질 옵션
QUALITY_OPTIONS = [
    {"id": "high", "name": "high", "desc": "원본 100% 재현 (테마 변경 불가)"},
    {"id": "medium", "name": "medium", "desc": "85~95% 재현 + 테마 변경 가능 [권장]"},
    {"id": "low", "name": "low", "desc": "빠른 생성 (품질 다소 낮음)"},
]

# 차트 렌더링
CHART_RENDERING = [
    {"id": "native", "name": "편집 가능 (네이티브)", "desc": "PPT 내장 차트, 생성 후 수정 가능"},
    {"id": "library", "name": "라이브러리 기반 (이미지)", "desc": "정교한 시각화, 편집 불가"},
]

# 슬라이드 크기
SLIDE_SIZES = [
    {"id": "16:9", "name": "16:9 (1920x1080)", "desc": "현대적, 와이드스크린 [권장]"},
    {"id": "4:3", "name": "4:3 (1024x768)", "desc": "레거시, 호환성"},
    {"id": "16:10", "name": "16:10 (1920x1200)", "desc": "Mac 디스플레이"},
]


def get_document_styles(templates_dir: str = "templates") -> list:
    """등록된 문서 양식 목록 조회."""
    import yaml
    registry_path = Path(templates_dir) / "documents" / "registry.yaml"
    if not registry_path.exists():
        return []

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("templates", [])
    except Exception:
        return []


def print_options(title: str, options: list, show_desc: bool = True) -> None:
    """옵션 목록 출력."""
    print(f"\n[시스템] {title}\n")
    for i, opt in enumerate(options, 1):
        if show_desc and "desc" in opt:
            print(f"  {i}. {opt['name']} - {opt['desc']}")
        elif "slides" in opt:
            print(f"  {i}. {opt['name']} ({opt['slides']})")
        else:
            print(f"  {i}. {opt['name']}")


def get_choice(options: list, default: int = 1, allow_custom: bool = False) -> dict:
    """사용자 선택 받기."""
    while True:
        prompt = f"\n> 선택 (기본: {default}): " if default else "\n> 선택: "
        choice = input(prompt).strip()

        if not choice and default:
            return options[default - 1]

        if allow_custom and choice.lower() == "c":
            custom = input("> 직접 입력: ").strip()
            return {"id": "custom", "name": custom}

        try:
            idx = int(choice)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        except ValueError:
            pass

        print(f"  1~{len(options)} 사이의 숫자를 입력하세요.")


def run_questionnaire(working_dir: str = "working", templates_dir: str = "templates") -> str:
    """질문 흐름 실행. 세션 ID 반환."""
    settings = {}

    print("\n" + "=" * 60)
    print("  PPT 생성 설정")
    print("=" * 60)

    # 1. 문서 종류
    print_options("어떤 종류의 문서를 만들까요?", DOCUMENT_TYPES)
    choice = get_choice(DOCUMENT_TYPES, default=1)
    settings["document_type"] = choice["id"]

    # 2. 문서 양식
    styles = get_document_styles(templates_dir)
    if styles:
        style_options = [{"id": s.get("id", s.get("name")), "name": s.get("name", s.get("id"))} for s in styles]
        style_options.append({"id": None, "name": "양식 없음 (빈 슬라이드)"})
        print_options("사용할 문서 양식을 선택해 주세요:", style_options, show_desc=False)
        choice = get_choice(style_options, default=len(style_options))
        settings["document_style"] = choice["id"]
    else:
        print("\n[시스템] 등록된 문서 양식이 없습니다. 빈 슬라이드로 시작합니다.")
        settings["document_style"] = None

    # 3. 슬라이드 크기 (양식 없음 시만)
    if not settings["document_style"]:
        print_options("슬라이드 크기를 선택해 주세요:", SLIDE_SIZES)
        choice = get_choice(SLIDE_SIZES, default=1)
        settings["slide_size"] = choice["id"]
    else:
        settings["slide_size"] = "16:9"  # 양식에서 상속

    # 4. 청중 대상
    print_options("발표 대상은 누구인가요?", AUDIENCES, show_desc=False)
    choice = get_choice(AUDIENCES, default=1)
    settings["audience"] = choice["id"]

    # 5. 발표 시간
    print_options("발표 시간 또는 슬라이드 수를 알려주세요:", DURATIONS)
    choice = get_choice(DURATIONS, default=2)
    settings["duration"] = choice["id"]

    # 6. 톤 & 스타일
    print_options("발표 톤을 선택해 주세요:", TONES)
    choice = get_choice(TONES, default=1)
    settings["tone"] = choice["id"]

    # 7. 품질 옵션
    print_options("생성 품질을 선택해 주세요:", QUALITY_OPTIONS)
    # 양식 있으면 high 권장, 없으면 medium 권장
    default_quality = 1 if settings["document_style"] else 2
    choice = get_choice(QUALITY_OPTIONS, default=default_quality)
    settings["quality"] = choice["id"]

    # 8. 차트 렌더링 (간단히 질문)
    print_options("차트/다이어그램 렌더링 방식:", CHART_RENDERING)
    choice = get_choice(CHART_RENDERING, default=1)
    settings["chart_rendering"] = choice["id"]

    # 세션 생성
    print("\n" + "-" * 60)
    manager = SessionManager(working_dir)
    session_id = manager.create(settings)

    print(f"\n[완료] 세션 생성됨: {session_id}")
    print(f"       설정 파일: {working_dir}/{session_id}/session.yaml")

    return session_id


def collect_settings_dict() -> dict:
    """
    대화형 입력 없이 설정 딕셔너리만 반환.
    Claude가 직접 호출하여 사용자에게 질문할 때 사용.
    """
    return {
        "document_types": DOCUMENT_TYPES,
        "audiences": AUDIENCES,
        "durations": DURATIONS,
        "tones": TONES,
        "quality_options": QUALITY_OPTIONS,
        "chart_rendering": CHART_RENDERING,
        "slide_sizes": SLIDE_SIZES,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PPT 생성 설정 수집")
    parser.add_argument("--working-dir", default="working", help="작업 디렉토리")
    parser.add_argument("--templates-dir", default="templates", help="템플릿 디렉토리")
    parser.add_argument("--list-options", action="store_true", help="옵션 목록만 출력 (JSON)")

    args = parser.parse_args()

    if args.list_options:
        import json
        print(json.dumps(collect_settings_dict(), ensure_ascii=False, indent=2))
    else:
        session_id = run_questionnaire(args.working_dir, args.templates_dir)
        print(session_id)
