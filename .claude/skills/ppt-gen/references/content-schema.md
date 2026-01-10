# Content Template Schema v4.0

콘텐츠 템플릿의 YAML 스키마 정의서입니다. 슬라이드 레이아웃을 재사용 가능한 형태로 저장합니다.

> **버전 히스토리**
> - v4.0: 콘텐츠-오브젝트 분리, 동적 오브젝트 선택 시스템
> - v3.1: SVG 복잡 도형 지원
> - **v2.1: shape_source 선택적 추출, OOXML 보존, extraction_mode** (NEW)
> - v2.0: 이미지 설명 필수화, expected_prompt 추가

---

# Part 1: v4.0 스키마 (콘텐츠-오브젝트 분리)

## 1. 핵심 개념

v4.0은 **콘텐츠**(배치)와 **오브젝트**(도형)를 분리하여 재사용성과 유연성을 높입니다.

```
┌─────────────────────────────────────────┐
│ CONTENT (콘텐츠)                         │
│ - 배치, 여백, 구조                       │
│ - "어디에" 배치할 것인가?                │
│ - placeholder 기반                      │
└─────────────────────────────────────────┘
                     │
                     │ 동적 참조
                     ▼
┌─────────────────────────────────────────┐
│ OBJECT (오브젝트)                        │
│ - 실제 도형/이미지 정의                  │
│ - "무엇을" 그릴 것인가?                  │
│ - 4가지 타입: OOXML, SVG, Image, Desc   │
└─────────────────────────────────────────┘
```

## 2. v4.0 콘텐츠 템플릿 구조

```yaml
content_template:
  id: comparison-2col1
  version: "4.0"

  content:
    layout:
      type: grid | radial | sequential | freeform
      columns: 2
      rows: 1

    zones:
      # Zone 배열 (아래 섹션 참조)
      - id: main-diagram
        type: placeholder
        geometry: {x: 10%, y: 20%, cx: 80%, cy: 60%}
        placeholder_type: DIAGRAM
        object_hint: {category: cycle, element_count: 4-6}
        object_default: "objects/cycle/6segment.yaml"

    spacing:
      column_gap: 4%
      row_gap: 3%

  inline_objects:
    - id: accent-line
      type: description
      desc: "가로 구분선, 두께 2px"
```

## 3. Layout 섹션

레이아웃 유형을 정의합니다.

```yaml
layout:
  type: grid | radial | sequential | freeform

  # grid 타입
  columns: 2
  rows: 2
  column_weights: [1, 1]  # 비율
  row_weights: [0.3, 0.7]

  # radial 타입
  center: {x: 50%, y: 50%}
  radius: 35%
  start_angle: 90

  # sequential 타입
  direction: horizontal | vertical
  alignment: center | start | end
```

| 타입 | 설명 | 예시 |
|------|------|------|
| `grid` | 격자 배치 | 2열 비교, 4열 그리드 |
| `radial` | 방사형 배치 | 사이클 다이어그램, 원형 차트 |
| `sequential` | 순차 배치 | 프로세스, 타임라인 |
| `freeform` | 자유 배치 | 비정형 레이아웃 |

## 4. Zones 섹션 (핵심)

각 Zone은 슬라이드의 영역을 정의하고, 동적으로 오브젝트를 선택합니다.

### 4.1 Zone 스키마

```yaml
zones:
  - id: main-diagram
    type: container | placeholder

    # 배치 정보
    geometry:
      x: 10%
      y: 20%
      cx: 80%
      cy: 60%

    # 플레이스홀더 유형 (필수)
    placeholder_type: TITLE | SUBTITLE | BODY | ICON | IMAGE | CHART | DIAGRAM

    # 오브젝트 선택 (3가지 방식 - 모두 선택적)
    # 방식 1: 동적 검색 (LLM이 registry에서 최적 오브젝트 선택)
    object_hint:
      category: [cycle, process]    # 검색할 카테고리
      semantic: "순환 프로세스"       # 의미적 설명
      style: colorful               # 스타일 태그
      element_count: 4-6            # 요소 개수 범위
      complexity: medium            # 복잡도

    # 방식 2: 고정/폴백 (검색 실패 시 또는 고정 사용)
    object_default: "objects/cycle/6segment.yaml"

    # 방식 3: 설명 기반 생성 (간단한 도형)
    object_desc: "둥근 모서리 카드 배경"

    # 스타일 참조 (테마 토큰)
    style_ref: primary-fill | secondary-stroke | surface-bg
```

### 4.2 오브젝트 선택 우선순위

```
1. object_hint 있음?
   ├─ YES → Registry 검색 → 매칭 결과 사용
   └─ 매칭 실패 → 2번으로

2. object_default 있음?
   ├─ YES → 기본 오브젝트 사용
   └─ NO → 3번으로

3. object_desc 있음?
   ├─ YES → LLM이 설명 기반 생성
   └─ NO → 텍스트 플레이스홀더만
```

### 4.3 Zone 예시

```yaml
zones:
  # 예시 1: 단순 컨테이너 (오브젝트 불필요)
  - id: left-panel
    type: container
    geometry: {x: 2%, y: 15%, cx: 46%, cy: 80%}
    style_ref: primary-fill
    object_desc: "둥근 모서리 사각형 배경"

  # 예시 2: 동적 오브젝트 선택 (힌트 기반 검색)
  - id: main-diagram
    type: placeholder
    geometry: {x: 10%, y: 20%, cx: 80%, cy: 60%}
    placeholder_type: DIAGRAM
    object_hint:
      category: [cycle, process]
      semantic: "순환 프로세스"
      element_count: 4-6
      style: colorful
    object_default: "objects/cycle/6segment-colorful.yaml"

  # 예시 3: 고정 오브젝트 (특정 도형 필수)
  - id: logo-area
    type: placeholder
    geometry: {x: 85%, y: 5%, cx: 10%, cy: 10%}
    placeholder_type: IMAGE
    object_default: "objects/images/company-logo.yaml"

  # 예시 4: 텍스트 영역 (오브젝트 불필요)
  - id: title
    type: placeholder
    geometry: {x: 10%, y: 5%, cx: 70%, cy: 10%}
    placeholder_type: TITLE
```

## 5. Object Hint 스키마

LLM이 오브젝트 Registry를 검색할 때 사용하는 조건입니다.

```yaml
object_hint:
  # 검색 카테고리 (배열 또는 단일)
  category: [cycle, process, flow]

  # 의미적 설명 (자연어)
  semantic: "6단계 순환 프로세스 다이어그램"

  # 스타일 태그
  style: [colorful, segmented]

  # 요소 개수 (단일, 범위, 배열)
  element_count: 4-6    # 범위
  # element_count: 4    # 단일
  # element_count: [4, 5, 6]  # 배열

  # 복잡도
  complexity: [medium, high]  # low | medium | high
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `category` | string/array | 검색할 오브젝트 카테고리 |
| `semantic` | string | 의미적 설명 (LLM 매칭용) |
| `style` | string/array | 스타일 태그 |
| `element_count` | string/number/array | 요소 개수 조건 |
| `complexity` | string/array | 복잡도 수준 |

## 6. Inline Objects

간단한 도형은 콘텐츠 내에 인라인으로 정의합니다.

```yaml
inline_objects:
  - id: divider-line
    type: description
    desc: "가로 구분선"
    render_hint:
      shape: line
      orientation: horizontal
      thickness: 2px
      color: secondary

  - id: card-bg
    type: description
    desc: "둥근 모서리 카드 배경"
    render_hint:
      shape: rounded-rectangle
      corner_radius: 8px
      fill: surface
      shadow: soft
```

---

# Part 2: Object 스키마

## 7. Object 타입

오브젝트는 4가지 타입으로 분류됩니다.

| 타입 | 설명 | 저장 내용 |
|------|------|----------|
| `ooxml` | PPTX 네이티브 도형 | XML 정의, shape_type, path |
| `svg` | 벡터 그래픽 | SVG inline 또는 파일 경로 |
| `image` | 래스터 이미지 | 파일 경로, 소스 정보 |
| `description` | 간단한 도형 | 텍스트 설명만 |

## 8. Object 파일 구조

```
templates/contents/objects/
├── registry.yaml           # 오브젝트 레지스트리
├── cycle/
│   ├── 6segment-colorful.yaml
│   └── 4arrow.yaml
├── honeycomb/
│   └── process-hex.yaml
├── arrows/
│   └── curved-arrows.yaml
├── icons/
│   └── fa-icons.yaml
└── images/
    └── hero-backgrounds.yaml
```

## 9. Object Registry 스키마

오브젝트 검색을 위한 메타데이터 레지스트리입니다.

```yaml
# objects/registry.yaml
version: "1.0"

objects:
  - id: cycle-6segment-colorful
    file: cycle/6segment-colorful.yaml
    type: ooxml

    # 검색용 메타데이터
    metadata:
      category: cycle
      tags: [colorful, segmented, 6-element, process]
      semantic: "6단계 순환 다이어그램, 컬러풀한 세그먼트"
      element_count: 6
      complexity: high
      style: colorful

  - id: cycle-4arrow
    file: cycle/4arrow.yaml
    type: svg
    metadata:
      category: cycle
      tags: [minimal, arrow, 4-element]
      semantic: "4단계 순환 화살표, 미니멀 스타일"
      element_count: 4
      complexity: medium
      style: minimal

  - id: process-honeycomb
    file: process/honeycomb.yaml
    type: ooxml
    metadata:
      category: process
      tags: [hexagon, connected, flow]
      semantic: "벌집 형태 프로세스 다이어그램"
      element_count: [5, 7]  # 범위
      complexity: high
      style: geometric
```

## 10. Object YAML 예시

### 10.1 OOXML 타입

```yaml
# objects/cycle/6segment-colorful.yaml
object:
  id: 6segment-colorful
  type: ooxml
  version: "1.0"

segments:
  - id: segment-orange
    name: "상단 세그먼트 (주황)"
    type: ooxml
    ooxml:
      shape_type: freeform
      path: "M 0,-35 C 50,-100 100,-130 70,-165 ..."
      fill: "#FF7F50"
      effect: null
    metadata:
      semantic: "순환 다이어그램 상단 조각"
      position_hint: top

  - id: segment-blue
    name: "우상단 세그먼트 (파랑)"
    type: ooxml
    ooxml:
      shape_type: freeform
      path: "M 70,-165 C 120,-180 ..."
      fill: "#6495ED"
```

### 10.2 SVG 타입

```yaml
# objects/cycle/circular-arrows.yaml
object:
  id: circular-arrows
  type: svg
  version: "1.0"

svg:
  viewBox: "0 0 200 200"
  inline: |
    <svg xmlns="http://www.w3.org/2000/svg">
      <path d="M 100,20 A 80,80 0 0,1 180,100"
            fill="none" stroke="currentColor" stroke-width="8"/>
    </svg>

variants:
  - id: 4-segment
    segments: 4
    gap_angle: 8
  - id: 6-segment
    segments: 6
    gap_angle: 5

metadata:
  semantic: "순환 화살표 다이어그램"
  customizable: [segments, gap_angle, colors]
```

### 10.3 Image 타입

```yaml
# objects/images/hero-backgrounds.yaml
object:
  id: hero-backgrounds
  type: image
  version: "1.0"

images:
  - id: city-night
    file: images/city-night.jpg
    description: "도시 야경 사진, 어두운 배경"
    source: unsplash
    license: free
    tags: [dark, urban, tech]

  - id: nature-green
    file: images/nature-green.jpg
    description: "녹색 자연 배경"
    source: unsplash
    tags: [light, nature, eco]
```

### 10.4 Description 타입 (인라인)

```yaml
# 콘텐츠 내 inline_objects로 정의
inline_objects:
  - id: divider-line
    type: description
    desc: "가로 구분선"
    render_hint:
      shape: line
      orientation: horizontal
      thickness: 2px
      color: secondary
```

---

# Part 3: 동적 오브젝트 선택 시스템

## 11. LLM 오브젝트 선택 흐름

```
사용자: "4단계 순환 프로세스 PPT 만들어줘"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. 콘텐츠 분석 & 템플릿 선택                                  │
│    - 콘텐츠: "순환 프로세스" → category: cycle               │
│    - 템플릿: process-visual1 선택                           │
│    - object_hint: {category: cycle, element_count: 4}       │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 오브젝트 Registry 검색                                    │
│                                                             │
│    Query:                                                   │
│    - category IN [cycle, process, flow]                     │
│    - element_count MATCH 4                                  │
│                                                             │
│    결과:                                                     │
│    ┌──────────────────────┬────────────┬──────────┐         │
│    │ 오브젝트             │ 매칭 점수  │ 선택     │         │
│    ├──────────────────────┼────────────┼──────────┤         │
│    │ cycle-4arrow         │ 95%        │ ✓        │         │
│    │ cycle-6segment       │ 60%        │          │         │
│    │ process-honeycomb    │ 40%        │          │         │
│    └──────────────────────┴────────────┴──────────┘         │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PPT 생성                                                 │
│    - 콘텐츠 geometry로 위치 결정                             │
│    - 선택된 오브젝트(cycle-4arrow)로 렌더링                   │
│    - 테마 색상 적용                                          │
└─────────────────────────────────────────────────────────────┘
```

## 12. 유연성 모드

| 모드 | 설명 | 스키마 설정 |
|------|------|------------|
| **고정** | 특정 오브젝트만 사용 | `object_default` only (no hint) |
| **검색** | LLM이 최적 선택 | `object_hint` + `object_default` |
| **자유** | 설명 기반 생성 | `object_desc` only |
| **혼합** | 힌트 + 설명 | `object_hint` + `object_desc` |

## 13. 검색 알고리즘

```python
def select_object(zone, content_context, registry):
    """
    오브젝트 선택 알고리즘

    1. object_hint가 있으면 registry 검색
    2. 매칭 결과가 있으면 최고 점수 오브젝트 반환
    3. 없으면 object_default 반환
    4. default도 없으면 object_desc로 LLM 생성
    """
    if zone.object_hint:
        candidates = registry.search(
            category=zone.object_hint.category,
            element_count=zone.object_hint.element_count,
            style=zone.object_hint.style,
            semantic=zone.object_hint.semantic
        )

        # 콘텐츠 컨텍스트로 점수 계산
        scored = score_candidates(candidates, content_context)

        if scored:
            return scored[0]  # 최고 점수 오브젝트

    if zone.object_default:
        return registry.get(zone.object_default)

    if zone.object_desc:
        return generate_from_description(zone.object_desc)

    return None  # 단순 placeholder
```

---

# Part 3.5: v2.1 스키마 (OOXML 하이브리드)

## 14. 핵심 개념

v2.1은 **선택적 OOXML 보존**을 통해 복잡한 도형의 정확한 재현과 단순한 도형의 유연한 생성을 동시에 지원합니다.

```
┌─────────────────────────────────────────┐
│ Shape Source 선택적 추출                 │
│                                         │
│ 복잡한 도형 → shape_source: ooxml       │
│   (그라데이션, 커스텀 도형, 3D 효과)      │
│   → 원본 OOXML fragment 보존            │
│                                         │
│ 단순한 도형 → shape_source: description │
│   (사각형, 원, 기본 텍스트박스)           │
│   → 자연어 설명으로 저장                 │
└─────────────────────────────────────────┘
```

## 15. extraction_mode (추출 모드)

슬라이드 타입에 따라 추출 범위를 결정합니다.

### 15.1 모드 정의

| 모드 | 설명 | 적용 슬라이드 |
|------|------|--------------|
| `full` | 전체 추출 (제목/푸터 포함) | Cover, TOC, Section, Closing |
| `content_only` | 콘텐츠 Zone만 추출 | 일반 Content 슬라이드 |

### 15.2 스키마

```yaml
content_template:
  id: process-linear1
  design_intent: process
  extraction_mode: content_only  # full | content_only

  # content_only 모드일 때 콘텐츠 영역 경계
  content_zone:
    bounds:
      top: 15%       # 제목 영역 아래부터
      bottom: 92%    # 푸터 영역 위까지
      left: 5%
      right: 95%
```

### 15.3 슬라이드 타입별 모드

```python
FULL_EXTRACTION_TYPES = ['cover', 'toc', 'section', 'closing', 'agenda']

def get_extraction_mode(design_intent):
    """슬라이드 타입에 따른 추출 모드 결정"""
    if design_intent in FULL_EXTRACTION_TYPES:
        return 'full'      # 전체 추출 (제목이 콘텐츠의 일부)
    return 'content_only'  # 콘텐츠 영역만 추출
```

## 16. shape_source (Shape 소스 타입)

각 shape의 정의 방식을 지정합니다.

### 16.1 타입 정의

| shape_source | 설명 | PPT 생성 시 처리 |
|--------------|------|-----------------|
| `ooxml` | 원본 OOXML 보존 | fragment 그대로 사용 (좌표/색상 치환) |
| `svg` | SVG 벡터 경로 | SVG → OOXML 변환 (custGeom) |
| `reference` | 다른 shape/Object 참조 | 참조 대상 복사 + 오버라이드 |
| `html` | HTML/CSS 스니펫 | HTML → 이미지 → PPT 삽입 |
| `description` | 자연어 설명 | LLM이 OOXML 생성 |

### 16.2 복잡도 판단 기준

**OOXML로 추출 (복잡):**
- 그라데이션 채우기 (`<a:gradFill>`)
- 커스텀 도형 (`<a:custGeom>`)
- 3D 효과, 베벨, 반사
- 복잡한 텍스트 서식 (여러 run)
- 그룹화된 도형 (`<p:grpSp>`)
- 패턴/텍스처 채우기

**Description으로 추출 (단순):**
- 단색 채우기 (`<a:solidFill>`)
- 기본 도형 (`<a:prstGeom>`: rect, oval, roundRect)
- 단순 그림자 또는 없음
- 단일 스타일 텍스트
- 단일 도형

```python
def determine_shape_source(shape_xml):
    """Shape 복잡도에 따라 ooxml/description 결정"""

    if has_gradient_fill(shape_xml):        return 'ooxml'
    if has_custom_geometry(shape_xml):      return 'ooxml'
    if has_3d_effects(shape_xml):           return 'ooxml'
    if has_complex_text_formatting(shape_xml): return 'ooxml'
    if has_pattern_fill(shape_xml):         return 'ooxml'
    if is_grouped_shape(shape_xml):         return 'ooxml'

    return 'description'
```

## 17. ooxml 섹션 (shape_source: ooxml)

원본 OOXML을 보존하여 정확한 재현을 보장합니다.

### 17.1 스키마

```yaml
shapes:
  - id: "shape-1"
    name: "배경 상단"
    shape_source: ooxml

    # 기존 필드 (커스터마이징/테마 적용용)
    type: rectangle
    z_index: 1
    geometry:
      x: 0%
      y: 28.4%
      cx: 100%
      cy: 34.8%
    style:
      fill:
        type: solid
        color: accent_light  # 테마 토큰
        opacity: 0.25

    # NEW: 원본 OOXML 보존
    ooxml:
      # 원본 XML fragment (필수)
      fragment: |
        <p:sp>
          <p:nvSpPr>
            <p:cNvPr id="2" name="배경 상단"/>
            <p:cNvSpPr/>
            <p:nvPr/>
          </p:nvSpPr>
          <p:spPr>
            <a:xfrm>
              <a:off x="0" y="3074400"/>
              <a:ext cx="12192000" cy="3762000"/>
            </a:xfrm>
            <a:prstGeom prst="rect">
              <a:avLst/>
            </a:prstGeom>
            <a:solidFill>
              <a:srgbClr val="C5D3CC"><a:alpha val="25000"/></a:srgbClr>
            </a:solidFill>
            <a:ln><a:noFill/></a:ln>
          </p:spPr>
          <p:txBody>
            <a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr/></a:p>
          </p:txBody>
        </p:sp>

      # 원본 EMU 좌표 (스케일링용)
      emu:
        x: 0
        y: 3074400
        cx: 12192000
        cy: 3762000

      # 원본 색상 (테마 치환용)
      colors:
        fill: "#C5D3CC"
        stroke: null
        text: null
```

### 17.2 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `fragment` | string | YES | 원본 OOXML XML 문자열 |
| `emu` | object | YES | 원본 EMU 좌표 {x, y, cx, cy} |
| `colors` | object | No | 원본 색상 (테마 치환 시 사용) |
| `fonts` | object | No | 원본 폰트 정보 |

### 17.3 PPT 생성 시 처리

```python
def render_ooxml_shape(shape, theme, target_canvas):
    xml = shape.ooxml.fragment

    # 1. 좌표 스케일링
    if target_canvas != REFERENCE_CANVAS:
        xml = scale_coordinates(xml, shape.ooxml.emu, target_canvas)

    # 2. 테마 색상 치환 (선택적)
    if theme.apply_colors and shape.ooxml.colors:
        original_color = shape.ooxml.colors.fill
        new_color = theme.get_color(shape.style.fill.color)
        xml = xml.replace(original_color.lstrip('#'), new_color.lstrip('#'))

    return xml
```

## 18. description 섹션 (shape_source: description)

자연어 설명으로 도형을 정의합니다.

### 18.1 스키마

```yaml
shapes:
  - id: "shape-2"
    name: "카드 배경"
    shape_source: description

    # 기존 필드
    type: rectangle
    geometry:
      x: 5%
      y: 10%
      cx: 40%
      cy: 80%

    # 자연어 설명
    description:
      text: |
        둥근 모서리 사각형
        - 모서리 반경: 8px
        - 채우기: surface 색상
        - 그림자: 부드러운 드롭섀도우 (blur: 10px, offset: 0,4px)
        - 투명도: 100%

      # 선택적 힌트 (LLM 가이드용)
      hints:
        shape_type: roundRect
        corner_radius: 8
        has_shadow: true
        fill_token: surface
```

### 18.2 Description으로 처리 가능한 예시

```yaml
# 단순 도형
description:
  text: "사각형, primary 색상, 25% 투명도"

# 이미지
description:
  text: "히어로 배경 이미지, 도시 야경, 어두운 톤, 16:9 비율"

# 차트
description:
  text: |
    막대 차트
    - X축: Q1, Q2, Q3, Q4
    - 매출: 100, 150, 200, 180 (primary 색상)
    - 비용: 80, 90, 120, 100 (secondary 색상)

# 아이콘
description:
  text: "Font Awesome star 아이콘, 32px, primary 색상"
```

## 19. reference 섹션 (shape_source: reference)

다른 shape나 Object를 참조합니다.

### 19.1 스키마

```yaml
shapes:
  - id: "main-diagram"
    shape_source: reference

    reference:
      # 외부 Object 파일 참조
      object: "objects/cycle/6segment-colorful.yaml"

      # 또는 같은 파일 내 shape 참조
      local: "shape-5"

      # 오버라이드 (선택)
      override:
        geometry:
          x: 15%
          y: 20%
          cx: 70%
          cy: 65%
        style:
          fill:
            color: secondary
```

## 20. Object 파일 스키마

재사용 가능한 다이어그램 컴포넌트를 별도 파일로 저장합니다.

### 20.1 디렉토리 구조

```
templates/contents/objects/
├── registry.yaml           # Object 레지스트리
├── cycle/
│   ├── 6segment-colorful.yaml
│   └── 4arrow.yaml
├── process/
│   └── honeycomb.yaml
└── chart/
    └── bar-simple.yaml
```

### 20.2 Object YAML 스키마

```yaml
# objects/cycle/6segment-colorful.yaml
object:
  id: 6segment-colorful
  name: "6세그먼트 컬러풀 사이클"
  type: diagram
  version: "1.0"

  # 바운딩 박스 (원본 슬라이드 내 위치)
  bounding_box:
    x: 20%
    y: 15%
    cx: 60%
    cy: 70%

  # 구성 요소
  components:
    - id: segment-1
      shape_source: ooxml
      ooxml:
        fragment: |
          <p:sp><!-- 세그먼트 1 OOXML --></p:sp>
        emu: {x: 2438400, y: 1028700, cx: 3657600, cy: 2400000}
      relative_position:
        angle: 0
        radius: 35%

    - id: segment-2
      shape_source: ooxml
      ooxml:
        fragment: |
          <p:sp><!-- 세그먼트 2 OOXML --></p:sp>
        emu: {x: 5486400, y: 1028700, cx: 3657600, cy: 2400000}
      relative_position:
        angle: 60
        radius: 35%
    # ... 6개 세그먼트

  # 검색용 메타데이터
  metadata:
    category: cycle
    tags: [colorful, 6-element, radial, process]
    semantic: "6단계 순환 다이어그램, 컬러풀한 세그먼트"
    element_count: 6
    complexity: high
    style: colorful
```

### 20.3 Object Registry 스키마

```yaml
# objects/registry.yaml
version: "1.0"

categories:
  - id: cycle
    name: "순환 다이어그램"
  - id: process
    name: "프로세스 다이어그램"
  - id: chart
    name: "차트"

objects:
  - id: cycle-6segment-colorful
    file: cycle/6segment-colorful.yaml
    type: ooxml
    metadata:
      category: cycle
      tags: [colorful, 6-element]
      element_count: 6
      complexity: high

  - id: cycle-4arrow
    file: cycle/4arrow.yaml
    type: svg
    metadata:
      category: cycle
      tags: [minimal, arrow]
      element_count: 4
      complexity: medium
```

## 21. 추출 워크플로우 (v2.1)

```
PPTX
  │
  ▼
┌─────────────────────────────────────┐
│ Step 1: 슬라이드 타입 분류           │
│ - cover, toc, section, closing      │
│   → extraction_mode: full           │
│ - 나머지                             │
│   → extraction_mode: content_only   │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ Step 2: Zone 필터링                  │
│ - full: 모든 shape 포함             │
│ - content_only: 제목/푸터 제외       │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ Step 3: Shape별 복잡도 판단          │
│ - 복잡 → shape_source: ooxml        │
│ - 단순 → shape_source: description  │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ Step 4: YAML 생성                    │
│ - ooxml: fragment + emu + colors    │
│ - description: 자연어 설명           │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ Step 5: Object 분리 (선택)           │
│ - 재사용 가능한 다이어그램 감지       │
│ - objects/ 폴더에 별도 저장          │
└─────────────────────────────────────┘
```

## 22. v2.1 장점 요약

| 항목 | 기존 (v2.0) | 개선 (v2.1) |
|------|------------|-------------|
| 복잡 도형 보존 | 재구성 필요 | OOXML로 100% 보존 |
| 단순 도형 | 속성 나열 | Description으로 간결화 |
| 생성 속도 | 모두 재생성 | 복잡한 것만 치환 |
| 정확도 | 근사치 | 원본 동일 (복잡 도형) |
| 재사용성 | 템플릿 단위 | Object 단위 컴포넌트 |
| 일관성 | 제목 포함 | 콘텐츠만 분리 (content_only) |
| 용량 | 작음 | 선택적 (복잡한 것만 OOXML) |

---

# Part 4: v2.0 레거시 스키마 (호환성 유지)

## 스키마 개요

```yaml
content_template:     # 기본 메타데이터
design_meta:          # 디자인 품질/의도 분석
canvas:               # 캔버스 정보 (정규화 기준)
background:           # 슬라이드 배경 (NEW v2.2)
shapes:               # 도형 배열 (상세 정보)
icons:                # 아이콘 정보
gaps:                 # 오브젝트 간 여백
spatial_relationships: # 공간 관계 (벡터화)
groups:               # 그룹 정보
thumbnail:            # 썸네일 경로 (필수)
use_for:              # 사용 가이드
keywords:             # 검색 키워드
expected_prompt:      # 역추론 프롬프트 (NEW v2.1)
prompt_keywords:      # 프롬프트 매칭 키워드 (NEW v2.1)
```

---

## 1. content_template (기본 메타데이터)

```yaml
content_template:
  id: comparison1                      # 고유 ID (영문, 숫자, 하이픈)
  name: "비교 (A vs B)"                 # 표시 이름
  version: "2.0"                       # 스키마 버전
  source: original-file.pptx           # 원본 파일명 (PPT 추출 시)
  source_slide_index: 5                # 원본 슬라이드 인덱스 (0-based)
  source_url: null                     # 원본 URL (웹 추출 시, 선택)
  extracted_at: "2026-01-06T14:30:00"  # 추출 시각 (ISO 8601)
```

---

## 2. design_meta (디자인 메타데이터)

LLM이 분석한 디자인 품질과 의도 정보입니다.

```yaml
design_meta:
  quality_score: 9.2              # LLM 평가 점수 (0.0 ~ 10.0)
  design_intent: Comparison       # 주요 분류 (단일)
  design_intents:                 # 복수 분류 (해당되는 모든 의도)
    - Comparison
    - TwoColumn
  visual_balance: symmetric       # symmetric | asymmetric
  information_density: medium     # low | medium | high
```

### 디자인 의도 분류 체계 (40개 카테고리)

| 대분류 | 세부 카테고리 | 설명 |
|--------|---------------|------|
| **Cover** | cover-centered, cover-banner, cover-split, cover-fullimage | 표지 슬라이드 |
| **TOC** | toc-list, toc-grid, toc-visual | 목차 |
| **Section** | section-title, section-number, section-image | 섹션 구분 |
| **Closing** | closing-thankyou, closing-qna, closing-contact | 마무리 |
| **Comparison** | comparison-2col, comparison-table, pros-cons | 비교 |
| **Matrix** | matrix-2x2, matrix-swot, matrix-3x3 | 매트릭스 |
| **Timeline** | timeline-horizontal, timeline-vertical, timeline-milestone | 타임라인 |
| **Roadmap** | roadmap-horizontal, roadmap-phases, roadmap-gantt | 로드맵 |
| **Process** | process-linear, process-circle, process-honeycomb, process-pyramid | 프로세스 |
| **Cycle** | cycle-circular, cycle-loop | 사이클 |
| **Funnel** | funnel-vertical, funnel-horizontal | 퍼널 |
| **Stats** | stats-cards, stats-chart, stats-donut, stats-dotgrid | 통계 |
| **Dashboard** | dashboard-kpi, dashboard-overview, dashboard-metrics | 대시보드 |
| **Table** | table-simple, table-comparison, table-pricing | 표 |
| **Grid** | grid-2col, grid-3col, grid-4col, grid-icon | 그리드 |
| **Feature** | feature-list, feature-icons, feature-benefits | 기능 소개 |
| **Content** | content-image-text, content-quote, content-team, content-profile | 콘텐츠 |
| **Hierarchy** | hierarchy-org, hierarchy-tree, hierarchy-mindmap | 계층 구조 |
| **Agenda** | agenda-numbered, agenda-visual | 아젠다 |
| **Map** | map-world, map-region, map-location | 지도 |

### 자동 분류 생성

기존 분류에 없는 새로운 패턴 발견 시 `{대분류}-{특징}` 형식으로 자동 생성:

```yaml
# 예시
design_intent: process-5step       # 새로 생성된 카테고리
is_new_category: true
category_description: "5단계 프로세스 흐름도"
```

---

## 3. canvas (캔버스 정보)

좌표 정규화의 기준이 되는 캔버스 정보입니다.

```yaml
canvas:
  reference_width: 1980           # 정규화 기준 너비 (px)
  reference_height: 1080          # 정규화 기준 높이 (px)
  original_width_emu: 12192000    # 원본 너비 (EMU)
  original_height_emu: 6858000    # 원본 높이 (EMU)
  aspect_ratio: "16:9"            # 화면 비율
```

---

## 3.1 slide_zones (슬라이드 영역 정의)

콘텐츠 추출 시 **제외할 영역**을 동적으로 감지합니다. 타이틀, 서브타이틀, 푸터 영역은 문서 템플릿에서 결정되므로 콘텐츠 템플릿에서 제외합니다.

### Zone 구조

```
┌─────────────────────────────────────────┐
│  TITLE ZONE                             │  ← 제외 (동적 감지)
│  - 메인 타이틀 (placeholder: TITLE)      │
├─────────────────────────────────────────┤
│  ACTION TITLE ZONE                      │  ← 제외 (동적 감지)
│  - 서브타이틀, Progress Bar              │
├─────────────────────────────────────────┤
│                                         │
│  CONTENT ZONE                           │  ← 추출 대상
│  - 실제 콘텐츠 영역                       │
│                                         │
├─────────────────────────────────────────┤
│  BOTTOM ZONE                            │  ← 제외 (동적 감지)
│  - Footer, 페이지 번호                   │
└─────────────────────────────────────────┘
```

### 동적 감지 기준

| 영역 | 감지 조건 | Fallback |
|------|----------|----------|
| Title | `placeholder_type in [TITLE, CENTER_TITLE]` OR `name contains 'title'` | 0-10% |
| Action Title | `placeholder_type == SUBTITLE` OR `y < 25% with small height` | 10-20% |
| Content | 타이틀 하단 ~ 푸터 상단 (동적 계산) | 20-92% |
| Bottom | `name contains 'footer/page'` OR `y > 90%` | 92-100% |

### 감지 로직

```python
def is_title_shape(shape, slide_height):
    """타이틀/서브타이틀 도형 판별"""
    # 1. placeholder 타입으로 판별 (가장 정확)
    if shape.placeholder_type in ['TITLE', 'CENTER_TITLE', 'SUBTITLE']:
        return True
    # 2. 이름으로 판별
    name_lower = shape.name.lower()
    if any(kw in name_lower for kw in ['title', 'subtitle', '제목', '타이틀']):
        return True
    # 3. 위치로 판별 (상단 25% 이내 + 높이 15% 미만)
    if shape.y < slide_height * 0.25 and shape.cy < slide_height * 0.15:
        return True
    return False

def is_footer_shape(shape, slide_height):
    """푸터/페이지번호 도형 판별"""
    # 1. 이름으로 판별
    name_lower = shape.name.lower()
    if any(kw in name_lower for kw in ['footer', 'page', 'slide', '페이지', '푸터']):
        return True
    # 2. 위치로 판별 (하단 10% 이내)
    if shape.y > slide_height * 0.90:
        return True
    return False

def detect_content_zone(shapes, slide_height=1080):
    """Content Zone 경계 동적 감지"""
    # 타이틀 도형 찾기
    title_shapes = [s for s in shapes if is_title_shape(s, slide_height)]
    if title_shapes:
        title_bottom = max(s.y + s.cy for s in title_shapes)
        content_top = title_bottom + (slide_height * 0.02)  # 2% 여유
    else:
        content_top = slide_height * 0.20  # Fallback 20%

    # 푸터 도형 찾기
    footer_shapes = [s for s in shapes if is_footer_shape(s, slide_height)]
    if footer_shapes:
        footer_top = min(s.y for s in footer_shapes)
        content_bottom = footer_top - (slide_height * 0.02)  # 2% 여유
    else:
        content_bottom = slide_height * 0.92  # Fallback 92%

    return content_top, content_bottom
```

### 수동 오버라이드 (선택)

특정 슬라이드에서 동적 감지 대신 고정값 사용:

```yaml
zone_overrides:
  content_top: 25%      # 동적 감지 무시, 25% 고정
  content_bottom: 90%   # 동적 감지 무시, 90% 고정
```

---

## 4. shapes (도형 배열)

슬라이드의 모든 도형을 상세히 기술합니다.

```yaml
shapes:
  - id: "shape-0"                 # 고유 ID
    name: "Header Bar"            # 이름 (원본에서 추출)
    type: rectangle               # 도형 유형 (아래 참조)
    z_index: 0                    # 레이어 순서 (0 = 최하단)

    geometry:                     # 위치/크기 정보
      # 콘텐츠 영역 기준 % (권장)
      x: 0%                       # 왼쪽 위치
      y: 0%                       # 상단 위치
      cx: 100%                    # 너비
      cy: 15%                     # 높이
      rotation: 0                 # 회전 각도 (도)
      original_aspect_ratio: 6.67 # 원본 비율 (cx_px / cy_px) - 다중 비율 지원용

      # 또는 그리드 기반 (선택적)
      # grid: "col-1-12 row-1-1"  # 12컬럼 기준

    style:                        # 스타일 정보
      fill:
        type: solid               # solid | gradient | none
        color: primary            # 시맨틱 색상
        opacity: 1.0              # 0.0 ~ 1.0
      stroke:
        color: none               # 테두리 색상
        width: 0                  # 테두리 두께 (pt)
      shadow:
        enabled: false
        blur: 4                   # 블러 반경
        offset_x: 2               # X 오프셋
        offset_y: 2               # Y 오프셋
        opacity: 0.3              # 그림자 투명도
      rounded_corners: 0          # 모서리 둥글기 (pt)

    text:                         # 텍스트 정보 (있는 경우)
      has_text: true
      placeholder_type: TITLE     # TITLE | BODY | SUBTITLE | etc.
      alignment: center           # left | center | right
      font_size_ratio: 0.022      # 캔버스 높이 대비 비율
      original_font_size_pt: 24   # 원본 폰트 크기 (pt) - 다중 비율 지원용
      font_weight: bold           # normal | bold
      font_color: light           # 시맨틱 색상
```

### 도형 유형 (type)

| 유형 | 설명 |
|------|------|
| `rectangle` | 사각형 |
| `oval` | 타원/원 |
| `textbox` | 텍스트 상자 |
| `picture` | 이미지 |
| `group` | 그룹 |
| `arrow` | 화살표 |
| `line` | 선 |
| `chevron` | 쉐브론 |
| `callout` | 콜아웃 |
| `connector` | 연결선 |
| `svg` | **SVG 복잡 도형** (NEW v3.1) |

### svg 타입 추가 필드 (NEW v3.1)

복잡한 다이어그램 도형(cycle, honeycomb, curved arrows 등)에 사용합니다.
단순 도형(rectangle, oval)은 기존 geometry만 사용하고, **복잡 도형만** SVG로 추출합니다.

```yaml
shapes:
  - id: "cycle-segment-0"
    name: "사이클 세그먼트 1"
    type: svg                    # SVG 복잡 도형
    z_index: 1
    geometry:
      x: 30%                     # 바운딩 박스 (fallback용)
      y: 0%
      cx: 40%
      cy: 35%

    # SVG 관련 필드 (svg 타입 전용)
    svg:
      # 옵션 A: 단일 path (가장 일반적)
      path: "M 0,-35 C 50,-100 100,-130 70,-165 C 40,-180 -40,-180 -70,-165 Z"

      # 옵션 B: 완전한 인라인 SVG (복잡한 다이어그램)
      inline: |
        <svg viewBox="0 0 200 200">
          <path d="M 0,-35 C 50,-100..." fill="primary"/>
          <circle cx="0" cy="-130" r="24" fill="rgba(255,255,255,0.25)"/>
        </svg>

      # 공통 속성
      viewBox: "0 0 200 200"           # SVG viewBox (선택)
      center: {x: 100, y: 100}         # 상대 좌표 기준점 (선택)
      fill: primary                    # 채우기 색상 (디자인 토큰)
      stroke: {color: dark_text, width: 2}  # 테두리 (선택)

    # 내부 요소 (아이콘, 텍스트 등)
    content:
      icon:
        position: {x: 0, y: -130}      # center 기준 상대 좌표
        name: "fa-user"
        size: 20
        color: white
      label:
        position: {x: 0, y: -95}
        text: "Feature Name"
        font_size: 9
        color: white
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| path | string | **YES*** | SVG path 문자열 (M, C, L, Z 등) |
| inline | string | **YES*** | 완전한 SVG 마크업 (복잡한 경우) |
| viewBox | string | No | SVG viewBox 속성 |
| center | object | No | 상대 좌표 기준점 {x, y} |
| fill | string | No | 채우기 색상 (디자인 토큰 또는 HEX) |
| stroke | object | No | 테두리 {color, width} |
| content | object | No | 내부 아이콘/텍스트 요소 |

\* `path` 또는 `inline` 중 하나 필수

### 복잡 도형 판단 기준

다음 조건에 해당하면 `type: svg`로 추출합니다:

| 조건 | 예시 |
|------|------|
| 방사형 세그먼트 (3개 이상) | cycle-6segment, radial chart |
| 벌집형 레이아웃 | honeycomb process |
| 곡선 화살표/커넥터 | curved arrow cycle |
| 비정형 다각형 | custom polygons |
| `layout.type: radial` | 방사형 레이아웃 |

### picture 타입 추가 필드

이미지 도형에는 설명과 용도를 포함합니다.

```yaml
shapes:
  - id: "image-0"
    name: "Hero Image"
    type: picture
    geometry:
      x: 50%
      y: 0%
      cx: 50%
      cy: 100%

    # 이미지 관련 필드 (picture 타입 전용)
    image:
      source: "path/to/image.jpg"           # 이미지 경로 (선택)
      description: "도시 야경 사진, 고층 빌딩과 조명"  # 이미지 설명 (필수)
      purpose: hero                         # 용도: hero | background | icon | diagram | photo
      alt_text: "서울 도심 야경"              # 접근성용 대체 텍스트 (선택)
      fit: cover                            # 이미지 맞춤: cover | contain | fill | none
      opacity: 1.0                          # 투명도 (0.0~1.0)
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| source | string | No | 이미지 파일 경로 |
| **description** | string | **YES** | 이미지 내용 설명 (LLM이 이해할 수 있는 자연어) |
| purpose | string | No | 용도 분류 (hero, background, icon, diagram, photo) |
| alt_text | string | No | 접근성용 대체 텍스트 |
| fit | string | No | 맞춤 방식 (기본: cover) |
| opacity | number | No | 투명도 (기본: 1.0) |

### image.purpose 분류

| 값 | 설명 | 예시 |
|------|------|------|
| `hero` | 슬라이드 메인 비주얼 | 전면 배경, 큰 이미지 |
| `background` | 배경 이미지 | 흐린 배경, 오버레이 이미지 |
| `icon` | 아이콘성 이미지 | 로고, 심볼 |
| `diagram` | 다이어그램/차트 | 설명 그래픽, 인포그래픽 |
| `photo` | 일반 사진 | 제품 사진, 인물 사진 |

---

## 4.1 background (슬라이드 배경)

슬라이드 전체 배경을 정의합니다. 배경 이미지 사용 시 설명이 필수입니다.

```yaml
background:
  type: image                              # solid | gradient | image

  # type: solid
  color: primary                           # 시맨틱 색상

  # type: gradient
  gradient:
    type: linear                           # linear | radial
    angle: 90                              # 각도 (linear)
    stops:
      - {position: 0%, color: primary}
      - {position: 100%, color: secondary}

  # type: image (배경 이미지)
  image:
    source: "backgrounds/cityscape.jpg"    # 이미지 경로 (선택)
    description: "어두운 도시 야경, 블러 처리된 빌딩 불빛"  # 이미지 설명 (필수)
    fit: cover                             # cover | contain | tile
    opacity: 0.3                           # 투명도 (오버레이용)
    overlay_color: dark_text               # 오버레이 색상 (선택)
    overlay_opacity: 0.5                   # 오버레이 투명도 (선택)
```

### background.image 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| source | string | No | 배경 이미지 파일 경로 |
| **description** | string | **YES** | 배경 이미지 설명 (LLM 생성 시 참조) |
| fit | string | No | 맞춤 방식 (기본: cover) |
| opacity | number | No | 이미지 투명도 (0.0~1.0) |
| overlay_color | string | No | 이미지 위 오버레이 색상 |
| overlay_opacity | number | No | 오버레이 투명도 |

---

## 5. 좌표 시스템

### 콘텐츠 영역 % 기준 (기본)

타이틀과 여백을 제외한 **콘텐츠 영역**을 100%로 간주합니다.

```
┌─────────────────────────────────────────┐
│  margin_top (5%)                        │
│  ┌───────────────────────────────────┐  │
│  │  TITLE AREA (15%)                 │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  │     CONTENT AREA (100% 기준)      │  │
│  │     x: 0-100%, y: 0-100%          │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│  margin_bottom (5%)                     │
└─────────────────────────────────────────┘
     margin_left (3%)    margin_right (3%)
```

### 좌표 변환 공식

```python
# 콘텐츠 영역 정의
content_bounds = {
    "left": 0.03,      # 슬라이드 너비의 3%
    "right": 0.97,     # 슬라이드 너비의 97%
    "top": 0.20,       # 타이틀 영역 아래 (20%)
    "bottom": 0.95     # 하단 여백 위 (95%)
}

# EMU → 콘텐츠 영역 % 변환
content_width = slide_width * 0.94   # (97% - 3%)
content_height = slide_height * 0.75  # (95% - 20%)
content_left = slide_width * 0.03
content_top = slide_height * 0.20

x_percent = (shape_x - content_left) / content_width * 100
y_percent = (shape_y - content_top) / content_height * 100
cx_percent = shape_width / content_width * 100
cy_percent = shape_height / content_height * 100
```

### 12컬럼 그리드 시스템 (대안)

Bootstrap 스타일의 그리드 레이아웃:

```yaml
geometry:
  grid: "col-1-6 row-1-3"   # col-{start}-{span} row-{start}-{span}

# 해석: 1번 컬럼부터 6칸, 1번 행부터 3행
```

| 분할 | 컬럼 설정 |
|------|----------|
| 2분할 | col-6 (50%) |
| 3분할 | col-4 (33.3%) |
| 4분할 | col-3 (25%) |

### 다중 비율 지원 (Multi-Aspect Ratio)

16:9로 추출한 템플릿을 4:3으로 생성할 때 도형과 폰트 비율 왜곡을 방지합니다.

#### 문제점

% 좌표만 사용하면 비율 변환 시 왜곡 발생:

```
원본 (16:9): 원 → cx: 10%, cy: 10%
├── 16:9로 생성: 원 유지 ✓
└── 4:3로 생성: 타원으로 왜곡 ✗ (4:3 높이가 더 높음)
```

#### 해결책: original_aspect_ratio

모든 도형에 **원본 비율**을 함께 저장:

```yaml
geometry:
  x: 25%
  y: 10%
  cx: 8%
  cy: 14.2%                     # 16:9 기준 %
  original_aspect_ratio: 1.0    # 원본 비율 (width_px / height_px)
                                # 원 = 1.0, 정사각형 = 1.0, 가로 직사각형 > 1.0
```

#### 추출 시 계산 로직

```python
# EMU에서 픽셀로 변환
EMU_PER_INCH = 914400
PX_PER_INCH = 96

shape_width_px = shape_cx_emu / EMU_PER_INCH * PX_PER_INCH
shape_height_px = shape_cy_emu / EMU_PER_INCH * PX_PER_INCH

# 원본 비율 계산
original_aspect_ratio = round(shape_width_px / shape_height_px, 3)
```

#### 생성 시 비율 보정 로직

```python
def calculate_geometry(shape, source_ratio, target_ratio):
    """
    source_ratio: 원본 슬라이드 비율 (16:9 = 1.778)
    target_ratio: 타겟 슬라이드 비율 (4:3 = 1.333)
    """
    geo = shape['geometry']
    original_ar = geo.get('original_aspect_ratio')

    if original_ar:
        # 비율 보정 계수
        ratio_factor = target_ratio / source_ratio  # 4:3 / 16:9 = 0.75

        # 방법 1: cy 조정 (cx 유지)
        target_cy = geo['cy'] * ratio_factor

        # 방법 2: original_aspect_ratio로 직접 계산
        # cx 유지하고 cy를 비율에 맞게 재계산
```

### 폰트 크기 보정 (Font Size Preservation)

`font_size_ratio`만 사용하면 높이 변화에 따라 폰트도 축소:

| 비율 | 높이 | font_size_ratio 0.028 | 결과 |
|------|------|----------------------|------|
| 16:9 | 1080px | 1080 × 0.028 | 30.24pt |
| 4:3 | 810px | 810 × 0.028 | 22.68pt (**25% 축소!**) |

#### 해결책: original_font_size_pt

절대 폰트 크기를 함께 저장:

```yaml
text:
  font_size_ratio: 0.028           # 상대값 (기존 호환)
  original_font_size_pt: 30.24     # 절대값 (신규)
```

#### 생성 시 폰트 크기 결정 로직

```python
def calculate_font_size(text_config, target_height, preserve_absolute=True):
    """
    preserve_absolute=True: 절대값 유지 (권장)
    preserve_absolute=False: 비율 기반 스케일링
    """
    original_pt = text_config.get('original_font_size_pt')
    ratio = text_config.get('font_size_ratio')

    if preserve_absolute and original_pt:
        return original_pt  # 절대값 유지
    elif ratio:
        return target_height * ratio  # 비율 기반
```

---

## 6. 시맨틱 색상

테마 독립적인 색상 표현으로 다른 테마에서도 재사용 가능합니다.

| 시맨틱 | Office 테마 색상 | 용도 |
|--------|-----------------|------|
| `primary` | dk2 | 주 강조색 |
| `secondary` | accent1 | 보조 강조색 |
| `accent` | accent1~6 | 포인트 색상 |
| `background` | lt1 | 배경 |
| `dark_text` | dk1 | 어두운 텍스트 |
| `light` | lt1 또는 white | 밝은 요소 |
| `gray` | lt2 | 회색 요소 |

---

## 7. icons (아이콘 정보)

슬라이드의 독립 아이콘을 정의합니다.

### 필수 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| id | string | YES | 고유 ID |
| type | string | YES | font-awesome, material, custom |
| icon_name | string | YES | 아이콘 이름 |
| position | object | YES | x, y 좌표 (px, 1980x1080 기준) |
| size | number | **YES*** | 아이콘 크기 (px) |
| size_ratio | number | **YES*** | 캔버스 높이 대비 비율 (0.0~1.0) |
| color | string | YES | 시맨틱 색상 |

\* `size` 또는 `size_ratio` 중 하나는 반드시 지정해야 합니다.

### 선택 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| opacity | number | 투명도 (0.0~1.0, 기본: 1.0) |

```yaml
icons:
  - id: "icon-0"
    type: font-awesome            # font-awesome | material | custom
    icon_name: "fa-chart-bar"     # 아이콘 이름
    position:
      x: 100                      # px (1980 기준)
      y: 300                      # px (1080 기준)
    size: 32                      # REQUIRED: 아이콘 크기 (px)
    # 또는
    size_ratio: 0.03              # 캔버스 높이 대비 비율 (1080 * 0.03 = 32px)
    color: primary                # 시맨틱 색상
    opacity: 1.0                  # 선택
```

### 크기 가이드라인

| 용도 | size (px) | size_ratio | 예시 |
|------|-----------|------------|------|
| 소형 (텍스트 옆) | 16-24 | 0.015-0.022 | 리스트 아이템 아이콘 |
| 중형 (카드 내) | 32-48 | 0.03-0.044 | 피처 카드 아이콘 |
| 대형 (강조) | 64-96 | 0.06-0.09 | 섹션 아이콘 |
| 초대형 (메인) | 128+ | 0.12+ | 메인 비주얼 아이콘 |

---

## 7.1 인라인 아이콘 (shapes 내)

shapes 배열 내에서 아이콘을 포함하는 경우의 스키마입니다.

```yaml
shapes:
  - id: "icon_card_1"
    type: group
    geometry: {x: "5%", y: "20%", cx: "20%", cy: "70%"}
    children:
      - circle_bg: {color: primary, opacity: 0.15}
      - circle_border: {color: primary, width: 3}
      - icon:
          name: "chart-bar"           # REQUIRED: 아이콘 이름
          color: primary              # REQUIRED: 시맨틱 색상
          size: 48                    # REQUIRED: px 단위
          # 또는
          size_ratio: 0.044           # 캔버스 높이 대비 (1080 * 0.044 = 47.5px)
      - title: "제목을 입력하세요."
      - description: "설명 텍스트"
```

### 인라인 아이콘 필수 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | YES | 아이콘 이름 (접두사 없이) |
| color | string | YES | 시맨틱 색상 |
| size | number | **YES*** | 크기 (px) |
| size_ratio | number | **YES*** | 캔버스 높이 대비 비율 |

\* `size` 또는 `size_ratio` 중 하나 필수

### 예시: 올바른 사용 vs 잘못된 사용

```yaml
# BAD - size 정보 없음 (추출 시 거부됨)
- icon: {name: "chart-bar", color: primary}

# GOOD - size 명시
- icon: {name: "chart-bar", color: primary, size: 48}

# GOOD - size_ratio 명시
- icon: {name: "chart-bar", color: primary, size_ratio: 0.044}

# GOOD - 둘 다 명시 (size 우선 적용)
- icon: {name: "chart-bar", color: primary, size: 48, size_ratio: 0.044}
```

---

## 8. gaps (여백 정보)

오브젝트 간 간격을 정의합니다.

```yaml
gaps:
  # 전역 여백 패턴
  global:
    column_gap: 4%          # 열 간 기본 간격
    row_gap: 3%             # 행 간 기본 간격
    item_gap: 2%            # 아이템 간 간격

  # 개별 여백 (shape 간)
  between_shapes:
    - from: "shape-1"
      to: "shape-2"
      direction: horizontal  # horizontal | vertical
      gap: 4%               # 콘텐츠 영역 대비 %

    - from: "shape-0"
      to: "shape-1"
      direction: vertical
      gap: 2%
```

---

## 9. spatial_relationships (공간 관계)

정렬, 분포 등 도형 간 관계를 벡터화합니다.

```yaml
spatial_relationships:
  # 인접 관계
  - from: "shape-1"
    to: "shape-2"
    relationship: adjacent-horizontal  # 수평 인접
    gap: 4%
    alignment: top          # top | center | bottom

  # 균등 분포
  - shapes: ["shape-1", "shape-2", "shape-3"]
    relationship: distributed-horizontal
    total_gap: 8%           # 총 여백

  # 정렬 관계
  - shapes: ["shape-1", "shape-2"]
    relationship: aligned-top
```

### 관계 유형

| 관계 | 설명 |
|------|------|
| `adjacent-horizontal` | 수평 인접 |
| `adjacent-vertical` | 수직 인접 |
| `aligned-top` | 상단 정렬 |
| `aligned-center` | 중앙 정렬 |
| `aligned-bottom` | 하단 정렬 |
| `aligned-left` | 좌측 정렬 |
| `aligned-right` | 우측 정렬 |
| `distributed-horizontal` | 수평 균등 분포 |
| `distributed-vertical` | 수직 균등 분포 |

---

## 10. groups (그룹 정보)

논리적으로 묶인 도형 그룹을 정의합니다.

```yaml
groups:
  - id: "group-left"
    members: ["shape-1", "shape-2", "shape-4"]
    bounding_box:
      x: 0%
      y: 0%
      cx: 48%
      cy: 100%
    internal_gap: 2%        # 그룹 내부 요소 간 간격
```

---

## 11. thumbnail (썸네일)

**필수 항목**입니다. 콘텐츠 추출 시 반드시 생성됩니다.

```yaml
thumbnail: thumbnails/comparison1.png
```

생성 명령:
```bash
python scripts/thumbnail.py input.pptx output/ --slides 5 --single
```

---

## 12. 사용 가이드

```yaml
use_for:                    # 권장 용도
  - "A vs B 비교"
  - "Before/After"
  - "장단점 비교"

keywords:                   # 검색 키워드
  - "비교"
  - "vs"
  - "대비"
  - "양쪽"
```

---

## 전체 예시

```yaml
content_template:
  id: comparison1
  name: "비교 (A vs B)"
  version: "2.0"
  source: marketing-deck.pptx
  source_slide_index: 5
  extracted_at: "2026-01-06T14:30:00"

design_meta:
  quality_score: 9.2
  design_intent: comparison-2col
  design_intents: [comparison-2col, grid-2col]
  visual_balance: symmetric
  information_density: medium

canvas:
  reference_width: 1980
  reference_height: 1080
  original_width_emu: 12192000
  original_height_emu: 6858000
  aspect_ratio: "16:9"

# 배경 이미지 예시 (선택)
background:
  type: solid
  color: background
  # type: image인 경우
  # image:
  #   source: "backgrounds/abstract-blue.jpg"
  #   description: "추상적인 파란색 그라데이션 배경, 부드러운 곡선 패턴"
  #   fit: cover
  #   opacity: 0.15
  #   overlay_color: dark_text
  #   overlay_opacity: 0.3

shapes:
  - id: "shape-0"
    name: "Left Panel"
    type: rectangle
    z_index: 0
    geometry:
      x: 0%
      y: 0%
      cx: 48%
      cy: 100%
    style:
      fill:
        type: solid
        color: primary
        opacity: 1.0
      stroke:
        color: none
        width: 0
      shadow:
        enabled: false
      rounded_corners: 0
    text:
      has_text: false

  - id: "shape-1"
    name: "Right Panel"
    type: rectangle
    z_index: 0
    geometry:
      x: 52%
      y: 0%
      cx: 48%
      cy: 100%
    style:
      fill:
        type: solid
        color: secondary
        opacity: 1.0
      stroke:
        color: none
        width: 0
      shadow:
        enabled: false
      rounded_corners: 0

gaps:
  global:
    column_gap: 4%
    row_gap: 3%
  between_shapes:
    - from: "shape-0"
      to: "shape-1"
      direction: horizontal
      gap: 4%

spatial_relationships:
  - from: "shape-0"
    to: "shape-1"
    relationship: adjacent-horizontal
    gap: 4%
    alignment: top

groups:
  - id: "comparison-group"
    members: ["shape-0", "shape-1"]
    bounding_box:
      x: 0%
      y: 0%
      cx: 100%
      cy: 100%

thumbnail: thumbnails/comparison1.png

use_for:
  - "A vs B 비교"
  - "Before/After"

keywords:
  - "비교"
  - "vs"

expected_prompt: |
  A vs B 비교 슬라이드를 만들어줘.
  - 좌측에 A 항목 (배경색 구분)
  - 우측에 B 항목
  - 중앙에 구분선
  - 각 항목에 제목과 설명
  - 대칭 레이아웃

prompt_keywords:
  - "비교"
  - "vs"
  - "대비"
  - "Before"
  - "After"
  - "As-Is"
  - "To-Be"
```

---

## 13. expected_prompt (역추론 프롬프트) - NEW v2.1

슬라이드 레이아웃을 생성하는 자연어 프롬프트를 역추론하여 저장합니다.

### 목적

1. **템플릿 매칭**: 사용자 요청과 템플릿을 의미적으로 매칭
2. **역참조**: 템플릿이 어떤 요청에 적합한지 문서화
3. **검색 개선**: 키워드 기반 검색 보완

### 스키마

```yaml
expected_prompt: |                    # YAML 블록 스칼라 (|) 사용
  {슬라이드 유형} 슬라이드를 만들어줘.
  - {요소1 설명}
  - {요소2 설명}
  - ...
  - {레이아웃 특징}
```

### 작성 규칙

1. **첫 줄**: `{슬라이드 유형} 슬라이드를 만들어줘.`
2. **요소 설명**: 상단→하단 순서로 각 구성요소 설명
3. **레이아웃 특징**: 대칭, 그리드, 흐름 등 전체 특성

### 요소별 변환 규칙

| 도형 타입 | 프롬프트 표현 |
|----------|--------------|
| `rounded-rectangle` | "라운드 형태의 박스/라벨" |
| `textbox` (TITLE) | "큰 제목 텍스트" |
| `textbox` (BODY) | "설명 텍스트" |
| `group` (N개) | "N개의 카드/열로 구성" |
| `icon` | "아이콘 표시" |
| `dotgrid` | "도트그리드로 퍼센트 표시" |
| `picture` | "이미지/사진 영역" |
| `oval` | "원형 도형" |
| `arrow` | "화살표로 연결" |

### 예시

```yaml
# deepgreen-grid4col1
expected_prompt: |
  기능 소개 슬라이드를 만들어줘.
  - 4개의 카드를 가로로 균등 배치
  - 각 카드: 상단에 라운드 배경 아이콘
  - 아이콘 아래에 제목 텍스트
  - 제목 아래에 설명 텍스트
  - 균등한 간격의 그리드 레이아웃

# deepgreen-process1
expected_prompt: |
  프로세스 슬라이드를 만들어줘.
  - 4단계 원형 프로세스
  - 각 단계는 원 안에 번호 (01, 02, 03, 04)
  - 원 아래에 제목과 설명
  - 화살표로 단계 연결
  - 가로 흐름 레이아웃
```

---

## 14. prompt_keywords (프롬프트 매칭 키워드) - NEW v2.1

템플릿 매칭에 사용되는 키워드 배열입니다.

### 스키마

```yaml
prompt_keywords:
  - "{키워드1}"
  - "{키워드2}"
  - "{키워드3}"
  # 5-7개 권장
```

### 추출 규칙

| 소스 | 추출 방법 |
|------|----------|
| `category` | cover → "표지", toc → "목차" |
| `design_intent` | grid-4col → "4열", "그리드" |
| `shapes[].type` | icon → "아이콘", dotgrid → "도트" |
| `use_for` | 배열 그대로 포함 |
| 레이아웃 분석 | 대칭 → "대칭", N열 → "N열" |

### 매칭 알고리즘

```python
def match_template(user_prompt, templates):
    """사용자 프롬프트와 템플릿 매칭"""
    scores = []
    user_keywords = extract_keywords(user_prompt)

    for template in templates:
        # 1. prompt_keywords 매칭 (0.0 ~ 1.0)
        keyword_matches = len(set(user_keywords) & set(template['prompt_keywords']))
        keyword_score = keyword_matches / len(template['prompt_keywords'])

        # 2. use_for 매칭 (가중치 1.5)
        use_for_matches = sum(1 for u in template['use_for'] if u in user_prompt)
        use_for_score = use_for_matches * 1.5

        # 3. expected_prompt 유사도 (0.0 ~ 1.0)
        prompt_similarity = compute_similarity(user_prompt, template['expected_prompt'])

        total_score = keyword_score + use_for_score + prompt_similarity
        scores.append((template['id'], total_score))

    return sorted(scores, key=lambda x: -x[1])
```

### 예시

```yaml
# deepgreen-cover1
prompt_keywords:
  - "표지"
  - "타이틀"
  - "발표자"
  - "프로젝트"
  - "중앙정렬"
  - "라벨"

# deepgreen-stats1
prompt_keywords:
  - "통계"
  - "퍼센트"
  - "KPI"
  - "지표"
  - "도트"
  - "비율"
```
