#!/usr/bin/env python3
"""
템플릿 패턴 분석 및 유사 템플릿 통합.

슬라이드 분석 결과를 바탕으로:
1. 패턴 시그니처 생성 (레이아웃 유형, 요소 개수, 스타일)
2. 기존 템플릿과 유사도 비교
3. 통합 가능한 템플릿 식별 (같은 출처 내)
4. 가변 템플릿(variants) 생성

Usage:
    python template-analyzer.py working/analysis.json --source "dongkuk" --output working/pattern.json
    python template-analyzer.py working/analysis.json --compare templates/contents/
"""

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class PatternSignature:
    """패턴 시그니처 (템플릿 비교 기준)"""
    layout_type: str  # grid, list, timeline, comparison, etc.
    element_count: int
    structure: List[str]  # 요소 구조 (icon+title+desc, title+text, etc.)
    visual_features: Dict[str, Any]  # border_radius, shadow, colors
    aspect_ratio: str  # 콘텐츠 영역 가로:세로 비율


@dataclass
class TemplateMatch:
    """템플릿 매칭 결과"""
    template_id: str
    similarity: float  # 0.0 ~ 1.0
    match_reason: List[str]
    can_merge: bool  # 통합 가능 여부
    merge_as_variant: bool  # variant로 통합 가능


@dataclass
class VariantDefinition:
    """가변 템플릿 정의"""
    count: int
    layout: Dict[str, Any]  # columns, gap, etc.


@dataclass
class PatternAnalysis:
    """패턴 분석 결과"""
    slide_index: int
    signature: PatternSignature
    suggested_category: str
    suggested_id: str
    matches: List[TemplateMatch]
    variants: List[VariantDefinition]


# 카테고리 키워드 매핑
CATEGORY_KEYWORDS = {
    'cover': ['표지', 'cover', 'title', '제목'],
    'toc': ['목차', 'toc', 'contents', 'agenda'],
    'section': ['섹션', 'section', '구분', 'divider'],
    'comparison': ['비교', 'compare', 'vs', 'pros', 'cons'],
    'process': ['프로세스', 'process', 'flow', 'step', '단계'],
    'timeline': ['타임라인', 'timeline', '일정', 'schedule', 'roadmap'],
    'grid': ['그리드', 'grid', '카드', 'card', 'icon'],
    'chart': ['차트', 'chart', '그래프', 'graph', 'data'],
    'stats': ['통계', 'stats', '수치', 'number', 'metric'],
    'diagram': ['다이어그램', 'diagram', 'cycle', 'matrix', 'venn'],
    'quote': ['인용', 'quote', '명언'],
    'closing': ['클로징', 'closing', 'thank', 'end'],
}


def load_analysis_data(input_path: Path) -> Dict:
    """분석 데이터 로드"""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_template_registry(templates_path: Path) -> List[Dict]:
    """기존 템플릿 레지스트리 로드"""
    templates = []

    # 각 카테고리 폴더의 registry.yaml 검색
    for category_dir in templates_path.iterdir():
        if not category_dir.is_dir():
            continue

        registry_path = category_dir / 'registry.yaml'
        if registry_path.exists() and HAS_YAML:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'templates' in data:
                    for tpl in data['templates']:
                        tpl['_category'] = category_dir.name
                        templates.append(tpl)

        # 또는 각 템플릿 폴더의 template.yaml
        for template_dir in category_dir.iterdir():
            if not template_dir.is_dir():
                continue
            template_yaml = template_dir / 'template.yaml'
            if template_yaml.exists() and HAS_YAML:
                with open(template_yaml, 'r', encoding='utf-8') as f:
                    tpl = yaml.safe_load(f)
                    if tpl:
                        tpl['_category'] = category_dir.name
                        tpl['_path'] = str(template_dir)
                        templates.append(tpl)

    return templates


def extract_pattern_signature(analysis: Dict) -> PatternSignature:
    """분석 결과에서 패턴 시그니처 추출"""

    layout_type = analysis.get('layout_pattern', 'single')
    element_count = analysis.get('element_count', 1)

    # 구조 분석
    structure = []
    for ph in analysis.get('placeholders', []):
        ph_type = ph.get('suggested_type', 'text')
        style_hints = ph.get('style_hints', {})

        if ph_type == 'array':
            # 배열 항목의 구조 파악
            structure.append('array')
        elif style_hints.get('bold'):
            structure.append('title')
        elif style_hints.get('bullet'):
            structure.append('bullet-list')
        else:
            structure.append('text')

    # 시각적 특성 (placeholder에서 추출)
    visual_features = {
        'has_icons': any('icon' in str(ph).lower() for ph in analysis.get('placeholders', [])),
        'has_bullets': any(ph.get('style_hints', {}).get('bullet') for ph in analysis.get('placeholders', [])),
    }

    # 콘텐츠 영역 비율
    content_zone = analysis.get('content_zone', {})
    zone_height = content_zone.get('bottom', 92) - content_zone.get('top', 22)
    aspect_ratio = 'wide' if zone_height < 60 else ('square' if zone_height < 80 else 'tall')

    return PatternSignature(
        layout_type=layout_type,
        element_count=element_count,
        structure=structure,
        visual_features=visual_features,
        aspect_ratio=aspect_ratio
    )


def calculate_similarity(sig1: PatternSignature, sig2: Dict) -> Tuple[float, List[str]]:
    """두 패턴의 유사도 계산"""
    score = 0.0
    reasons = []

    # 레이아웃 타입 (40%)
    sig2_layout = sig2.get('pattern', '').split('-')[0] if sig2.get('pattern') else ''
    if sig1.layout_type == sig2_layout:
        score += 0.4
        reasons.append(f"레이아웃 일치: {sig1.layout_type}")
    elif sig1.layout_type in sig2.get('tags', []):
        score += 0.2
        reasons.append(f"레이아웃 유사: {sig1.layout_type}")

    # 요소 개수 (30%)
    sig2_count = sig2.get('element_count', '1')
    if isinstance(sig2_count, str) and '-' in sig2_count:
        min_count, max_count = map(int, sig2_count.split('-'))
        if min_count <= sig1.element_count <= max_count:
            score += 0.3
            reasons.append(f"요소 개수 범위 내: {sig1.element_count}")
    elif str(sig1.element_count) == str(sig2_count):
        score += 0.3
        reasons.append(f"요소 개수 일치: {sig1.element_count}")

    # 카드 구조 (20%)
    sig2_visual = sig2.get('visual', {})
    if sig1.visual_features.get('has_icons') == sig2_visual.get('has_icons', False):
        score += 0.1
        reasons.append("아이콘 사용 일치")
    if sig1.visual_features.get('has_bullets') == sig2_visual.get('has_bullets', False):
        score += 0.1
        reasons.append("불릿 사용 일치")

    # 스타일 (10%)
    if sig1.aspect_ratio == sig2_visual.get('aspect', ''):
        score += 0.1
        reasons.append("영역 비율 일치")

    return score, reasons


def suggest_category(signature: PatternSignature, text_samples: List[str] = None) -> str:
    """패턴에 맞는 카테고리 추천"""

    # 레이아웃 타입 기반 추천
    layout_mapping = {
        'grid': 'grid',
        'list': 'comparison',
        'mixed': 'content',
        'single': 'content',
    }

    suggested = layout_mapping.get(signature.layout_type, 'content')

    # 텍스트 샘플로 카테고리 보정
    if text_samples:
        text_lower = ' '.join(text_samples).lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                suggested = category
                break

    return suggested


def generate_template_id(source: str, category: str, pattern: str, existing_ids: Set[str]) -> str:
    """고유한 템플릿 ID 생성"""
    base_id = f"{source}-{pattern}" if source else pattern
    template_id = base_id

    counter = 1
    while template_id in existing_ids:
        template_id = f"{base_id}-{counter:02d}"
        counter += 1

    return template_id


def find_mergeable_templates(
    signature: PatternSignature,
    templates: List[Dict],
    source_document: str
) -> List[TemplateMatch]:
    """통합 가능한 기존 템플릿 찾기"""
    matches = []

    for tpl in templates:
        # 같은 출처만 확인
        if tpl.get('source_document', '') != source_document:
            continue

        similarity, reasons = calculate_similarity(signature, tpl)

        if similarity >= 0.5:
            # 통합 가능 여부 판단
            can_merge = similarity >= 0.8
            merge_as_variant = 0.6 <= similarity < 0.8

            matches.append(TemplateMatch(
                template_id=tpl.get('id', ''),
                similarity=similarity,
                match_reason=reasons,
                can_merge=can_merge,
                merge_as_variant=merge_as_variant
            ))

    # 유사도 높은 순 정렬
    matches.sort(key=lambda m: m.similarity, reverse=True)
    return matches


def generate_variants(element_count: int, layout_type: str) -> List[VariantDefinition]:
    """가변 레이아웃 정의 생성"""
    variants = []

    if layout_type == 'grid':
        # 그리드: 개수에 따른 열/간격 변화
        grid_configs = {
            2: {'columns': 2, 'gap': '8%'},
            3: {'columns': 3, 'gap': '4%'},
            4: {'columns': 4, 'gap': '3%'},
            5: {'columns': 5, 'gap': '2%'},
            6: {'columns': 3, 'gap': '3%', 'rows': 2},
        }

        for count, layout in grid_configs.items():
            variants.append(VariantDefinition(count=count, layout=layout))

    elif layout_type == 'list':
        # 리스트: 개수에 따른 간격 변화
        for count in range(2, 7):
            gap = max(2, 15 - count * 2)  # 개수 많을수록 간격 줄임
            variants.append(VariantDefinition(
                count=count,
                layout={'gap': f'{gap}%', 'direction': 'vertical'}
            ))

    else:
        # 기본: 현재 개수만
        variants.append(VariantDefinition(
            count=element_count,
            layout={'columns': element_count, 'gap': '4%'}
        ))

    return variants


def analyze_pattern(analysis: Dict, source: str, templates: List[Dict]) -> PatternAnalysis:
    """패턴 분석 수행"""

    signature = extract_pattern_signature(analysis)

    # 텍스트 샘플 수집
    text_samples = []
    for ph in analysis.get('placeholders', []):
        if ph.get('text_preview'):
            text_samples.append(ph['text_preview'])

    # 카테고리 추천
    category = suggest_category(signature, text_samples)

    # 기존 템플릿과 비교
    matches = find_mergeable_templates(signature, templates, source)

    # 가변 템플릿 생성
    variants = generate_variants(signature.element_count, signature.layout_type)

    # ID 생성
    existing_ids = {tpl.get('id', '') for tpl in templates}
    template_id = generate_template_id(
        source, category, signature.layout_type, existing_ids
    )

    return PatternAnalysis(
        slide_index=analysis.get('slide_index', 0),
        signature=signature,
        suggested_category=category,
        suggested_id=template_id,
        matches=matches,
        variants=variants
    )


def dataclass_to_dict(obj) -> Any:
    """dataclass를 dict로 변환"""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: dataclass_to_dict(v) for k, v in asdict(obj).items()}
    elif isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}
    else:
        return obj


def main():
    parser = argparse.ArgumentParser(
        description="템플릿 패턴 분석 및 유사 템플릿 통합"
    )
    parser.add_argument("input", help="content-analyzer 출력 JSON 파일")
    parser.add_argument("--source", default="", help="소스 문서 ID (예: dongkuk)")
    parser.add_argument("--compare", help="비교할 템플릿 폴더 (templates/contents/)")
    parser.add_argument("--output", "-o", help="출력 JSON 파일")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: 파일을 찾을 수 없습니다: {args.input}")
        sys.exit(1)

    try:
        data = load_analysis_data(input_path)

        # 기존 템플릿 로드
        templates = []
        if args.compare:
            compare_path = Path(args.compare)
            if compare_path.exists():
                templates = load_template_registry(compare_path)
                print(f"기존 템플릿 {len(templates)}개 로드됨")

        results = []
        for analysis in data.get('analyses', []):
            pattern_analysis = analyze_pattern(analysis, args.source, templates)
            results.append(pattern_analysis)

        # 출력
        output_data = {
            "source_file": data.get('source_file', ''),
            "source_document": args.source,
            "patterns": [dataclass_to_dict(r) for r in results]
        }

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"저장됨: {args.output}")
        else:
            print(json.dumps(output_data, indent=2, ensure_ascii=False))

        # 통계
        merge_candidates = sum(
            1 for r in results
            if any(m.can_merge or m.merge_as_variant for m in r.matches)
        )
        print(f"분석 완료: {len(results)} 패턴, {merge_candidates} 통합 후보")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
