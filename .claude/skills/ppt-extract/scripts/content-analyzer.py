#!/usr/bin/env python3
"""
콘텐츠 영역 분석 및 플레이스홀더 후보 탐지.

slide-crawler.py의 출력(parsed.json)을 받아서:
1. 콘텐츠 영역 필터링
2. 텍스트 그룹 후보 탐지 (위치/스타일 기반)
3. LLM 판단을 위한 구조화된 데이터 생성

Usage:
    python content-analyzer.py working/parsed.json --output working/analysis.json
"""

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TextGroupCandidate:
    """텍스트 그룹 후보 (LLM이 최종 판단)"""
    id: str
    shapes: List[str]  # shape IDs
    group_type: str  # list, grid, single
    confidence: float  # 0.0 ~ 1.0
    evidence: List[str]  # 그룹화 근거
    sample_texts: List[str]
    common_style: Dict[str, Any]  # 공통 스타일


@dataclass
class PlaceholderCandidate:
    """플레이스홀더 후보"""
    shape_id: str
    suggested_name: str
    suggested_type: str  # text, array, image
    text_preview: str
    geometry: Dict[str, float]
    style_hints: Dict[str, Any]


@dataclass
class ContentAnalysis:
    """콘텐츠 분석 결과"""
    slide_index: int
    content_zone: Dict[str, float]
    text_groups: List[TextGroupCandidate]
    placeholders: List[PlaceholderCandidate]
    layout_pattern: str  # grid, list, mixed, single
    element_count: int


def load_parsed_data(input_path: Path) -> Dict:
    """slide-crawler 출력 로드"""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_content_shapes(slide_data: Dict) -> List[Dict]:
    """콘텐츠 영역의 도형만 필터링"""
    content_zone = slide_data.get('content_zone', {})
    content_top = content_zone.get('top', 22.0)
    content_bottom = content_zone.get('bottom', 92.0)

    content_shapes = []
    for shape in slide_data.get('shapes', []):
        if shape.get('zone') == 'content':
            content_shapes.append(shape)
        else:
            # zone이 없거나 다른 경우 위치로 판단
            geom = shape.get('geometry', {})
            center_y = geom.get('y', 0) + geom.get('cy', 0) / 2
            if content_top <= center_y <= content_bottom:
                content_shapes.append(shape)

    return content_shapes


def get_shape_style_signature(shape: Dict) -> str:
    """도형의 스타일 시그니처 생성 (그룹화 기준)"""
    parts = []

    # 폰트 크기
    for para in shape.get('paragraphs', []):
        for run in para.get('runs', []):
            if run.get('font_size'):
                parts.append(f"fs:{int(run['font_size'])}")
                break
        if parts:
            break

    # 폰트 볼드
    for para in shape.get('paragraphs', []):
        for run in para.get('runs', []):
            if run.get('bold'):
                parts.append("bold")
                break
        if parts and 'bold' in parts:
            break

    # 불릿
    for para in shape.get('paragraphs', []):
        if para.get('bullet'):
            parts.append("bullet")
            break

    # 도형 크기 (대략적)
    geom = shape.get('geometry', {})
    width_class = 'w-sm' if geom.get('cx', 0) < 30 else ('w-md' if geom.get('cx', 0) < 60 else 'w-lg')
    parts.append(width_class)

    return '|'.join(parts) if parts else 'default'


def detect_grid_pattern(shapes: List[Dict]) -> Tuple[bool, Dict]:
    """그리드 패턴 감지"""
    if len(shapes) < 2:
        return False, {}

    # 같은 Y 위치의 도형들 그룹화
    y_groups = {}
    tolerance = 5.0  # vmin

    for shape in shapes:
        y = shape.get('geometry', {}).get('y', 0)
        matched = False
        for key in y_groups:
            if abs(y - key) < tolerance:
                y_groups[key].append(shape)
                matched = True
                break
        if not matched:
            y_groups[y] = [shape]

    # 각 행에 2개 이상의 도형이 있으면 그리드
    grid_rows = [g for g in y_groups.values() if len(g) >= 2]

    if grid_rows:
        # 열 개수 추정
        max_cols = max(len(row) for row in grid_rows)
        return True, {
            'rows': len(grid_rows),
            'columns': max_cols,
            'pattern': f'{len(grid_rows)}x{max_cols}'
        }

    return False, {}


def detect_list_pattern(shapes: List[Dict]) -> Tuple[bool, Dict]:
    """리스트 패턴 감지 (세로 배열)"""
    if len(shapes) < 2:
        return False, {}

    # X 위치가 비슷하고 Y가 순차적인 도형들
    x_tolerance = 10.0  # vmin
    y_threshold = 3.0  # 최소 Y 간격

    # X 위치로 그룹화
    x_groups = {}
    for shape in shapes:
        x = shape.get('geometry', {}).get('x', 0)
        matched = False
        for key in x_groups:
            if abs(x - key) < x_tolerance:
                x_groups[key].append(shape)
                matched = True
                break
        if not matched:
            x_groups[x] = [shape]

    # 가장 큰 그룹 확인
    largest_group = max(x_groups.values(), key=len) if x_groups else []

    if len(largest_group) >= 2:
        # Y 순서 확인
        sorted_by_y = sorted(largest_group, key=lambda s: s.get('geometry', {}).get('y', 0))
        y_diffs = []
        for i in range(1, len(sorted_by_y)):
            y1 = sorted_by_y[i-1].get('geometry', {}).get('y', 0)
            y2 = sorted_by_y[i].get('geometry', {}).get('y', 0)
            y_diffs.append(y2 - y1)

        # 간격이 일정한지 확인
        if y_diffs and all(d > y_threshold for d in y_diffs):
            avg_spacing = sum(y_diffs) / len(y_diffs)
            return True, {
                'count': len(largest_group),
                'spacing': round(avg_spacing, 1),
                'shapes': [s['id'] for s in sorted_by_y]
            }

    return False, {}


def group_similar_shapes(shapes: List[Dict]) -> List[TextGroupCandidate]:
    """스타일이 비슷한 도형들 그룹화"""
    groups = []

    # 스타일별로 도형 분류
    style_groups: Dict[str, List[Dict]] = {}
    for shape in shapes:
        sig = get_shape_style_signature(shape)
        if sig not in style_groups:
            style_groups[sig] = []
        style_groups[sig].append(shape)

    # 그룹 생성
    group_idx = 0
    for sig, group_shapes in style_groups.items():
        if len(group_shapes) < 2:
            continue

        # 위치 패턴 분석
        is_grid, grid_info = detect_grid_pattern(group_shapes)
        is_list, list_info = detect_list_pattern(group_shapes)

        evidence = [f"동일 스타일: {sig}"]

        if is_grid:
            group_type = "grid"
            evidence.append(f"그리드 패턴: {grid_info.get('pattern', '?')}")
            confidence = 0.85
        elif is_list:
            group_type = "list"
            evidence.append(f"리스트 패턴: {list_info.get('count', '?')}개")
            confidence = 0.80
        else:
            group_type = "mixed"
            evidence.append("위치 패턴 불명확")
            confidence = 0.60

        # 샘플 텍스트
        sample_texts = []
        for s in group_shapes[:3]:
            for para in s.get('paragraphs', []):
                if para.get('text'):
                    sample_texts.append(para['text'][:50])
                    break

        # 공통 스타일 추출
        common_style = {}
        if group_shapes:
            first = group_shapes[0]
            for para in first.get('paragraphs', []):
                for run in para.get('runs', []):
                    common_style = {
                        'font_name': run.get('font_name'),
                        'font_size': run.get('font_size'),
                        'bold': run.get('bold')
                    }
                    break
                break

        groups.append(TextGroupCandidate(
            id=f"group-{group_idx}",
            shapes=[s['id'] for s in group_shapes],
            group_type=group_type,
            confidence=confidence,
            evidence=evidence,
            sample_texts=sample_texts,
            common_style=common_style
        ))
        group_idx += 1

    return groups


def generate_placeholder_candidates(shapes: List[Dict], groups: List[TextGroupCandidate]) -> List[PlaceholderCandidate]:
    """플레이스홀더 후보 생성"""
    candidates = []

    # 그룹에 속한 shape ID 수집
    grouped_ids = set()
    for g in groups:
        grouped_ids.update(g.shapes)

    for shape in shapes:
        shape_id = shape['id']

        # 텍스트가 있는 도형만
        text_preview = ""
        for para in shape.get('paragraphs', []):
            if para.get('text'):
                text_preview = para['text'][:100]
                break

        if not text_preview:
            continue

        # 플레이스홀더 이름/타입 추천
        if shape.get('placeholder_type'):
            ph_type = shape['placeholder_type'].lower()
            if 'title' in ph_type:
                suggested_name = "title"
                suggested_type = "text"
            elif 'subtitle' in ph_type:
                suggested_name = "subtitle"
                suggested_type = "text"
            else:
                suggested_name = ph_type
                suggested_type = "text"
        elif shape_id in grouped_ids:
            # 그룹에 속한 경우 → 배열 항목
            suggested_name = "items"
            suggested_type = "array"
        else:
            # 단독 텍스트
            suggested_name = "body"
            suggested_type = "text"

        # 스타일 힌트
        style_hints = {}
        for para in shape.get('paragraphs', []):
            if para.get('bullet'):
                style_hints['bullet'] = True
            if para.get('alignment'):
                style_hints['alignment'] = para['alignment']
            for run in para.get('runs', []):
                if run.get('bold'):
                    style_hints['bold'] = True
                if run.get('font_size'):
                    style_hints['font_size'] = run['font_size']
                break

        candidates.append(PlaceholderCandidate(
            shape_id=shape_id,
            suggested_name=suggested_name,
            suggested_type=suggested_type,
            text_preview=text_preview,
            geometry=shape.get('geometry', {}),
            style_hints=style_hints
        ))

    return candidates


def analyze_layout_pattern(shapes: List[Dict], groups: List[TextGroupCandidate]) -> str:
    """레이아웃 패턴 분류"""
    if len(shapes) <= 1:
        return "single"

    is_grid, _ = detect_grid_pattern(shapes)
    if is_grid:
        return "grid"

    is_list, _ = detect_list_pattern(shapes)
    if is_list:
        return "list"

    if groups:
        return "mixed"

    return "single"


def analyze_slide(slide_data: Dict) -> ContentAnalysis:
    """슬라이드 콘텐츠 분석"""

    # 콘텐츠 영역 필터링
    content_shapes = filter_content_shapes(slide_data)

    # 텍스트 그룹 탐지
    text_groups = group_similar_shapes(content_shapes)

    # 플레이스홀더 후보 생성
    placeholders = generate_placeholder_candidates(content_shapes, text_groups)

    # 레이아웃 패턴 분석
    layout_pattern = analyze_layout_pattern(content_shapes, text_groups)

    return ContentAnalysis(
        slide_index=slide_data.get('index', 0),
        content_zone=slide_data.get('content_zone', {}),
        text_groups=text_groups,
        placeholders=placeholders,
        layout_pattern=layout_pattern,
        element_count=len(content_shapes)
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


def generate_llm_prompt(analysis: ContentAnalysis) -> str:
    """LLM 판단용 프롬프트 생성"""
    prompt = f"""## 슬라이드 {analysis.slide_index} 콘텐츠 분석

### 레이아웃 패턴: {analysis.layout_pattern}
### 요소 개수: {analysis.element_count}

### 텍스트 그룹 후보
"""

    for group in analysis.text_groups:
        prompt += f"""
**{group.id}** ({group.group_type}, 신뢰도: {group.confidence:.0%})
- 도형: {', '.join(group.shapes)}
- 근거: {', '.join(group.evidence)}
- 샘플: {group.sample_texts[:2]}
"""

    prompt += """
### 플레이스홀더 후보
"""

    for ph in analysis.placeholders:
        prompt += f"""
- **{ph.shape_id}**: {ph.suggested_name} ({ph.suggested_type})
  - 텍스트: "{ph.text_preview[:50]}..."
  - 위치: x={ph.geometry.get('x', 0):.1f}%, y={ph.geometry.get('y', 0):.1f}%
"""

    prompt += """
### 판단 요청

위 분석을 바탕으로 다음을 결정해 주세요:

1. 텍스트 그룹이 실제로 리스트/그리드인가요?
2. 각 플레이스홀더의 이름과 타입을 확정해 주세요.
3. 배열 플레이스홀더의 경우 item_schema를 정의해 주세요.

JSON 형식으로 응답해 주세요:
```json
{
  "placeholders": [
    { "id": "title", "type": "text", "shapes": ["shape-0"] },
    { "id": "items", "type": "array", "shapes": ["shape-1", "shape-2", "shape-3"],
      "item_schema": { "title": "string", "description": "string" }
    }
  ]
}
```
"""

    return prompt


def main():
    parser = argparse.ArgumentParser(
        description="콘텐츠 영역 분석 및 플레이스홀더 후보 탐지"
    )
    parser.add_argument("input", help="slide-crawler 출력 JSON 파일")
    parser.add_argument("--output", "-o", help="출력 JSON 파일")
    parser.add_argument("--prompt", action="store_true", help="LLM 프롬프트 출력")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: 파일을 찾을 수 없습니다: {args.input}")
        sys.exit(1)

    try:
        data = load_parsed_data(input_path)

        results = []
        for slide_data in data.get('slides', []):
            analysis = analyze_slide(slide_data)
            results.append(analysis)

            if args.prompt:
                print(generate_llm_prompt(analysis))
                print("\n" + "="*60 + "\n")

        # 출력
        output_data = {
            "source_file": data.get('source_file', ''),
            "analyses": [dataclass_to_dict(r) for r in results]
        }

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"저장됨: {args.output}")
        elif not args.prompt:
            print(json.dumps(output_data, indent=2, ensure_ascii=False))

        # 통계
        total_groups = sum(len(r.text_groups) for r in results)
        total_placeholders = sum(len(r.placeholders) for r in results)
        print(f"분석 완료: {len(results)} 슬라이드, {total_groups} 그룹, {total_placeholders} 플레이스홀더 후보")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
