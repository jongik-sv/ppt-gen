# Content Template Extraction Workflow

단일 슬라이드 또는 다중 슬라이드의 레이아웃 패턴을 추출하여 재사용 가능한 콘텐츠 템플릿으로 저장합니다.

> **버전 히스토리**
> - **v4.0 (NEW)**: content-analyzer.py 스크립트 추가 - 완전한 OOXML 추출
> - v3.1: shape_source 선택적 추출, OOXML 보존, extraction_mode, Object 분리
> - v3.0: 템플릿 스킬 분리, 프로젝트 루트 저장
>
> 컨텐츠는 테마 독립적이며, 디자인 토큰 기반으로 작성됩니다.

## Triggers

- "콘텐츠 추출해줘"
- "이 슬라이드 저장해줘"
- "레이아웃 추출해줘"
- "이 슬라이드 패턴 저장"
- "템플릿 저장해줘"

## Pre-requisites

1. 원본 PPTX 파일 확인
2. 추출 대상 슬라이드 인덱스 확인 (1-based for script, 0-based for manual)
3. 카테고리 결정 후 해당 폴더 내 기존 파일 확인 (번호 충돌 방지)

---

## Quick Start: content-analyzer.py (v4.0 NEW)

**권장 방식**: 스크립트로 OOXML 완전 추출 후 YAML 템플릿 생성

### 기본 사용법

```bash
# 단일 슬라이드 분석 (1-based index)
python .claude/skills/ppt-extract/scripts/content-analyzer.py input.pptx --slide 11

# 결과를 파일로 저장
python .claude/skills/ppt-extract/scripts/content-analyzer.py input.pptx --slide 11 --output result.yaml

# 모든 슬라이드 요약
python .claude/skills/ppt-extract/scripts/content-analyzer.py input.pptx --all --summary

# 모든 슬라이드 상세 분석
python .claude/skills/ppt-extract/scripts/content-analyzer.py input.pptx --all --output all-slides.yaml
```

### 추출 정보

스크립트가 추출하는 요소:

| 요소 | OOXML 태그 | 추출 정보 |
|------|------------|-----------|
| 일반 도형 | `p:sp` | preset, fill, stroke, effects, text |
| 이미지/아이콘 | `p:pic` | embed_rId, SVG 참조, descr |
| 연결선 | `p:cxnSp` | stroke, dash, head/tail arrow |
| 그룹 | `p:grpSp` | children (재귀) |
| SmartArt/차트 | `p:graphicFrame` | diagram_refs, chart_rId |

### 출력 예시

```yaml
slide_num: 11
elements:
- type: shape
  id: '2'
  name: 육각형 1
  geometry:
    x_emu: 690345
    y_emu: 3417546
    x_pct: 5.66
    y_pct: 49.83
    cx_pct: 20.41
    cy_pct: 31.27
  preset: hexagon
  fill:
    type: solid
    color: '#DCF0EF'
  effects:
  - type: outerShadow
    blur: '50800'
    dist: '38100'

- type: picture
  name: 그래픽 9
  descr: 블로그 단색으로 채워진
  is_svg: true
  svg_target:
    target: ../media/image11.svg

summary:
  total_elements: 20
  shapes: 15
  pictures: 5
  connectors: 0
  groups: 0
  graphic_frames: 0
```

### 워크플로우 통합

1. **스크립트로 분석**: `content-analyzer.py --slide N`
2. **결과 확인**: shapes, pictures, connectors 수 확인
3. **YAML 템플릿 작성**: 스크립트 출력을 기반으로 `zones:` 구조 작성
4. **ooxml_shapes 복사**: 스크립트 출력의 geometry, fill, stroke 정보 활용

---

## 경로 구조 (v3.0)

```
C:/project/docs/templates/              # 프로젝트 루트 (스킬에서 분리)
├── themes/                             # 테마 정의
│   ├── deepgreen.yaml
│   ├── brandnew.yaml
│   └── default.yaml
├── contents/
│   ├── templates/{category}/           # 카테고리별 YAML
│   │   ├── cover/
│   │   ├── toc/
│   │   ├── section/
│   │   └── ...
│   ├── thumbnails/{category}/          # 카테고리별 썸네일
│   │   ├── cover/
│   │   └── ...
│   └── registry.yaml
```

---

## Workflow

### Phase 1: Analysis (전체 분석)

다중 슬라이드 추출 시 먼저 전체 분석을 수행합니다.

```bash
# PPTX 언팩 (ppt-gen의 ooxml 스크립트 사용)
python .claude/skills/ppt-gen/ooxml/scripts/unpack.py input.pptx workspace/unpacked

# 전체 슬라이드 목록 확인
ls workspace/unpacked/ppt/slides/

# 기존 템플릿 확인 (번호 충돌 방지)
ls templates/contents/templates/
```

분석 항목:
- **슬라이드별 design_intent 결정** (40개 카테고리)
- **테마 색상 매핑** (`ppt/theme/theme1.xml`)
- **품질 점수 평가** (0-10)

결과물: `workspace/analysis/{source_name}-analysis.yaml` (전체 분석 결과, 선택적)

---

### Phase 2: Individual Extraction (개별 추출)

**CRITICAL**: 각 슬라이드는 반드시 **개별 YAML 파일**로 저장합니다.

#### Step 2.1: Design Intent 결정

슬라이드 분석 후 40개 카테고리 중 적절한 design_intent 선택:

| 대분류 | 세부 카테고리 |
|--------|---------------|
| Cover | cover-centered, cover-banner, cover-split, cover-fullimage |
| TOC | toc-list, toc-grid, toc-visual |
| Section | section-title, section-number, section-image |
| Closing | closing-thankyou, closing-qna, closing-contact |
| Comparison | comparison-2col, comparison-table, pros-cons |
| Matrix | matrix-2x2, matrix-swot, matrix-3x3 |
| Timeline | timeline-horizontal, timeline-vertical, timeline-milestone |
| Roadmap | roadmap-horizontal, roadmap-phases, roadmap-gantt |
| Process | process-linear, process-circle, process-honeycomb, process-pyramid |
| Cycle | cycle-circular, cycle-loop |
| Funnel | funnel-vertical, funnel-horizontal |
| Stats | stats-cards, stats-chart, stats-donut, stats-dotgrid |
| Dashboard | dashboard-kpi, dashboard-overview, dashboard-metrics |
| Table | table-simple, table-comparison, table-pricing |
| Grid | grid-2col, grid-3col, grid-4col, grid-icon |
| Feature | feature-list, feature-icons, feature-benefits |
| Content | content-image-text, content-quote, content-team, content-profile |
| Hierarchy | hierarchy-org, hierarchy-tree, hierarchy-mindmap |
| Agenda | agenda-numbered, agenda-visual |
| Map | map-world, map-region, map-location |

**자동 분류 생성**: 기존에 없으면 `{대분류}-{특징}` 형식 (예: process-5step-arrow)

#### Step 2.2: Extraction Mode 결정 (v3.1 NEW)

**슬라이드 타입에 따라 추출 범위를 결정합니다.**

| 슬라이드 타입 | extraction_mode | 추출 범위 | 이유 |
|--------------|-----------------|----------|------|
| Cover (표지) | `full` | 전체 | 제목 자체가 콘텐츠 |
| TOC (목차) | `full` | 전체 | 목차 구조 전체가 콘텐츠 |
| Section (섹션) | `full` | 전체 | 섹션 제목이 주요 콘텐츠 |
| Closing (마무리) | `full` | 전체 | 전체 레이아웃이 콘텐츠 |
| Agenda (안건) | `full` | 전체 | 안건 목록 전체가 콘텐츠 |
| **Content (일반)** | `content_only` | 콘텐츠 Zone만 | 제목은 마스터에서 관리 |

**자동 분류 로직**:

```python
FULL_EXTRACTION_TYPES = ['cover', 'toc', 'section', 'closing', 'agenda']

def get_extraction_mode(design_intent: str) -> str:
    """슬라이드 타입에 따른 추출 모드 결정"""
    category = design_intent.split('-')[0]  # cover-centered → cover

    if category in FULL_EXTRACTION_TYPES:
        return 'full'
    return 'content_only'
```

**YAML 출력 예시**:

```yaml
content_template:
  id: process-linear1
  extraction_mode: content_only  # full | content_only

  # content_only 모드에서는 content_zone 명시
  content_zone:
    bounds: {top: 15%, bottom: 92%, left: 5%, right: 95%}
```

#### Step 2.2.1: 파일명 결정

```
파일명 규칙: {design_intent}{번호}.yaml
저장 경로: templates/contents/templates/{category}/{design_intent}{번호}.yaml

예시:
- cover/cover-centered1.yaml
- cover/cover-photo1.yaml
- process/process-honeycomb1.yaml
- stats/stats-dotgrid1.yaml
```

**번호 충돌 방지 로직 (v3.0)**:
```python
import os
import re
from pathlib import Path

TEMPLATES_ROOT = Path("C:/project/docs/templates/contents/templates")

def get_next_number(design_intent: str, category: str) -> int:
    """카테고리 폴더 내에서 다음 번호를 찾습니다."""
    category_dir = TEMPLATES_ROOT / category
    pattern = re.compile(rf'^{re.escape(design_intent)}(\d+)\.yaml$')
    existing_numbers = []

    if category_dir.exists():
        for filename in os.listdir(category_dir):
            match = pattern.match(filename)
            if match:
                existing_numbers.append(int(match.group(1)))

    return max(existing_numbers, default=0) + 1

# 사용 예시
next_num = get_next_number("process-honeycomb", "process")
filename = f"process-honeycomb{next_num}.yaml"  # process-honeycomb1.yaml
filepath = TEMPLATES_ROOT / "process" / filename
```

#### Step 2.3: Zone 경계 동적 감지

**CRITICAL**: 콘텐츠 추출 전 타이틀/푸터 영역을 동적으로 감지하여 제외합니다.

**슬라이드 Zone 구조**:

```
┌─────────────────────────────────────────┐
│  TITLE ZONE                             │  ← 제외
│  - placeholder_type: TITLE/CENTER_TITLE │
├─────────────────────────────────────────┤
│  ACTION TITLE ZONE                      │  ← 제외
│  - placeholder_type: SUBTITLE           │
│  - Progress Bar, 서브타이틀             │
├─────────────────────────────────────────┤
│                                         │
│  CONTENT ZONE                           │  ← 추출 대상
│  - 실제 콘텐츠 영역                       │
│                                         │
├─────────────────────────────────────────┤
│  BOTTOM ZONE                            │  ← 제외
│  - Footer, 페이지 번호                   │
└─────────────────────────────────────────┘
```

**감지 함수**:

```python
def is_title_shape(shape, slide_height):
    """타이틀/서브타이틀 도형 판별"""
    if shape.placeholder_type in ['TITLE', 'CENTER_TITLE', 'SUBTITLE']:
        return True
    name_lower = shape.name.lower()
    if any(kw in name_lower for kw in ['title', 'subtitle', '제목', '타이틀']):
        return True
    # 위치 기반: 상단 25% 이내 + 높이 15% 미만
    if shape.y < slide_height * 0.25 and shape.cy < slide_height * 0.15:
        return True
    return False

def is_footer_shape(shape, slide_height):
    """푸터/페이지번호 도형 판별"""
    name_lower = shape.name.lower()
    if any(kw in name_lower for kw in ['footer', 'page', 'slide', '페이지', '푸터']):
        return True
    # 위치 기반: 하단 10% 이내
    if shape.y > slide_height * 0.90:
        return True
    return False

def detect_content_zone(shapes, slide_height=1080):
    """Content Zone 경계 동적 감지"""
    # 타이틀 도형들의 하단 경계
    title_shapes = [s for s in shapes if is_title_shape(s, slide_height)]
    if title_shapes:
        title_bottom = max(s.y + s.cy for s in title_shapes)
        content_top = title_bottom + (slide_height * 0.02)  # 2% 여유
    else:
        content_top = slide_height * 0.20  # Fallback: 20%

    # 푸터 도형들의 상단 경계
    footer_shapes = [s for s in shapes if is_footer_shape(s, slide_height)]
    if footer_shapes:
        footer_top = min(s.y for s in footer_shapes)
        content_bottom = footer_top - (slide_height * 0.02)  # 2% 여유
    else:
        content_bottom = slide_height * 0.92  # Fallback: 92%

    return content_top, content_bottom
```

**Fallback 경계값** (감지 실패 시):

| Zone | 시작 | 끝 | 비고 |
|------|------|-----|------|
| Title + Action | 0% | 20% | 상단 제외 |
| Content | 20% | 92% | 추출 대상 |
| Bottom | 92% | 100% | 하단 제외 |

#### Step 2.4: 도형 정보 추출 (Zone 필터링 적용)

**CRITICAL**: 동적 감지된 Content Zone 내의 도형만 추출

```python
# 1. 모든 도형 로드
all_shapes = load_shapes_from_xml(slide_xml)

# 2. Zone 경계 감지
content_top, content_bottom = detect_content_zone(all_shapes, slide_height=1080)
print(f"Content Zone: {content_top/1080*100:.1f}% ~ {content_bottom/1080*100:.1f}%")

# 3. 콘텐츠 영역 내 도형만 필터링 (중심점 기준)
shapes_to_extract = []
excluded_shapes = []

for shape in all_shapes:
    shape_center_y = shape.y + (shape.cy / 2)

    if content_top <= shape_center_y <= content_bottom:
        shapes_to_extract.append(shape)
    else:
        excluded_shapes.append(shape)
        zone = "title" if shape_center_y < content_top else "bottom"
        print(f"Excluded: {shape.name} (y={shape.y/1080*100:.1f}%, zone={zone})")
```

**추출 속성** (콘텐츠 영역 % 기준):

- **geometry**: x, y, cx, cy (%), **original_aspect_ratio** (필수)
- **style**: fill, stroke, shadow, rounded_corners
- **text**: placeholder_type, alignment, **font_size_ratio**, **original_font_size_pt** (필수)
- **z_index**: 레이어 순서
- **type**: rectangle, oval, textbox, picture, group, arrow, line
- **image**: (picture 타입 전용) source, **description** (필수), purpose, fit, opacity

**원본 비율 필수 (다중 비율 지원용)**:

```python
# EMU → 원본 비율 계산
EMU_PER_INCH = 914400
PX_PER_INCH = 96

shape_width_px = shape_cx_emu / EMU_PER_INCH * PX_PER_INCH
shape_height_px = shape_cy_emu / EMU_PER_INCH * PX_PER_INCH

# 모든 도형에 원본 비율 기록
geometry['original_aspect_ratio'] = round(shape_width_px / shape_height_px, 3)
```

**원본 폰트 크기 필수**:

```python
# XML에서 폰트 크기 추출 (hundred-point 단위)
font_size_pt = font_size_hundredths / 100

# 모든 텍스트에 원본 크기 기록
text['original_font_size_pt'] = font_size_pt
text['font_size_ratio'] = font_size_pt / canvas_height_px  # 비율도 함께
```

**아이콘 크기 필수**: 아이콘이 포함된 경우 반드시 `size` 또는 `size_ratio` 기록

```yaml
# GOOD
- icon: {name: "chart-bar", color: primary, size: 48}
- icon: {name: "chart-bar", color: primary, size_ratio: 0.044}

# BAD (size 누락)
- icon: {name: "chart-bar", color: primary}
```

#### Step 2.4.1: Shape Source 결정 (v3.1 NEW - OOXML 하이브리드)

**원칙**: 복잡한 도형은 **원본 OOXML 보존**, 단순한 도형은 **자연어 설명**으로 추출합니다.

**Shape Source 타입 (5가지)**:

| shape_source | 설명 | PPT 생성 시 처리 |
|--------------|------|-----------------|
| `ooxml` | 원본 OOXML 보존 | fragment 그대로 사용 (좌표/색상만 치환) |
| `svg` | SVG 벡터 경로 | SVG → OOXML 변환 (custGeom) |
| `reference` | 다른 shape/Object 참조 | 참조 대상의 OOXML 복사 + 오버라이드 |
| `html` | HTML/CSS 스니펫 | HTML → 이미지 → PPT 삽입 |
| `description` | 자연어 설명 | LLM이 설명에 맞게 OOXML 생성 |

**복잡도 판단 기준** (자동 판단):

| 복잡 → `ooxml` | 단순 → `description` |
|----------------|---------------------|
| 그라데이션 채우기 (`<a:gradFill>`) | 단색 채우기 (`<a:solidFill>`) |
| 커스텀 도형 (`<a:custGeom>`) | 기본 도형 (`<a:prstGeom>`) |
| 3D 효과, 베벨, 반사 | 단순 그림자 또는 없음 |
| 복잡한 텍스트 (여러 서식) | 단일 스타일 텍스트 |
| 그룹화된 도형 (`<p:grpSp>`) | 단일 도형 |
| 패턴/텍스처 채우기 | 단색/투명 |
| 방사형 세그먼트 (3개+) | 사각형, 원, 기본 화살표 |

**복잡도 감지 함수**:

```python
def determine_shape_source(shape_xml):
    """Shape 복잡도에 따라 ooxml/description 결정"""

    # OOXML로 추출해야 하는 경우 (복잡)
    if has_gradient_fill(shape_xml):        return 'ooxml'
    if has_custom_geometry(shape_xml):      return 'ooxml'  # <a:custGeom>
    if has_3d_effects(shape_xml):           return 'ooxml'
    if has_complex_text_formatting(shape_xml): return 'ooxml'
    if has_pattern_fill(shape_xml):         return 'ooxml'
    if is_grouped_shape(shape_xml):         return 'ooxml'

    # Description으로 추출 (단순)
    return 'description'

def has_gradient_fill(shape_xml):
    return '<a:gradFill' in shape_xml or '<a:gradFill>' in shape_xml

def has_custom_geometry(shape_xml):
    return '<a:custGeom>' in shape_xml

def has_3d_effects(shape_xml):
    return any(tag in shape_xml for tag in ['<a:sp3d', '<a:scene3d', '<a:bevel'])

def has_complex_text_formatting(shape_xml):
    # 여러 <a:r> (run) 요소가 다른 서식을 가진 경우
    run_count = shape_xml.count('<a:r>')
    return run_count > 3

def has_pattern_fill(shape_xml):
    return '<a:pattFill' in shape_xml or '<a:blipFill' in shape_xml

def is_grouped_shape(shape_xml):
    return shape_xml.strip().startswith('<p:grpSp')
```

**OOXML 추출 시 포함 정보**:

```yaml
shapes:
  - id: "shape-1"
    name: "복잡한 배경 도형"
    shape_source: ooxml    # ← 복잡도 판단 결과

    # 기존 추상화 속성 (테마 적용/커스터마이징용)
    type: custom_shape
    geometry:
      x: 0%
      y: 28.4%
      cx: 100%
      cy: 34.8%
    style:
      fill:
        type: gradient
        color: primary      # 디자인 토큰
      stroke:
        type: none

    # NEW: 원본 OOXML 보존
    ooxml:
      fragment: |
        <p:sp>
          <p:nvSpPr>
            <p:cNvPr id="2" name="배경 도형"/>
            <p:cNvSpPr/>
            <p:nvPr/>
          </p:nvSpPr>
          <p:spPr>
            <a:xfrm>
              <a:off x="0" y="3074400"/>
              <a:ext cx="12192000" cy="3762000"/>
            </a:xfrm>
            <a:custGeom>
              <!-- 복잡한 커스텀 지오메트리 -->
            </a:custGeom>
            <a:gradFill>
              <a:gsLst>
                <a:gs pos="0"><a:srgbClr val="1A5C3E"/></a:gs>
                <a:gs pos="100000"><a:srgbClr val="2D8B5A"/></a:gs>
              </a:gsLst>
            </a:gradFill>
          </p:spPr>
          <p:txBody>...</p:txBody>
        </p:sp>

      # 원본 EMU 좌표 (스케일링 계산용)
      emu:
        x: 0
        y: 3074400
        cx: 12192000
        cy: 3762000

      # 원본 색상 참조 (테마 매핑용)
      colors:
        fill: ["#1A5C3E", "#2D8B5A"]  # 그라데이션 색상들
        stroke: null
        text: "#FFFFFF"
```

**Description 추출 시 자연어 생성**:

```yaml
shapes:
  - id: "shape-2"
    name: "단순 배경"
    shape_source: description

    type: rectangle
    geometry:
      x: 0%
      y: 0%
      cx: 100%
      cy: 100%
    style:
      fill:
        type: solid
        color: surface
        opacity: 0.25

    # NEW: 자연어 설명 (LLM이 OOXML 생성 시 참조)
    description:
      text: "사각형 배경, surface 색상, 25% 투명도"
      hints:
        shape_type: rectangle
        fill_token: surface
        opacity: 0.25
```

**Description 자동 생성 함수**:

```python
SHAPE_NAMES_KO = {
    'rect': '사각형',
    'roundRect': '둥근 사각형',
    'oval': '원형',
    'triangle': '삼각형',
    'arrow': '화살표',
    'line': '직선',
}

def generate_description(shape_xml, style_info):
    """단순 도형에 대한 자연어 설명 생성"""
    desc_parts = []

    # 도형 타입
    shape_type = get_preset_geometry(shape_xml)
    desc_parts.append(SHAPE_NAMES_KO.get(shape_type, shape_type))

    # 채우기
    fill = style_info.get('fill', {})
    if fill.get('type') == 'solid':
        desc_parts.append(f"{fill.get('color')} 색상")
        if fill.get('opacity', 1) < 1:
            desc_parts.append(f"{int(fill.get('opacity') * 100)}% 투명도")

    # 테두리
    if style_info.get('stroke', {}).get('color'):
        desc_parts.append(f"{style_info['stroke']['color']} 테두리")

    # 그림자
    if style_info.get('shadow', {}).get('enabled'):
        desc_parts.append("그림자 효과")

    # 둥근 모서리
    if style_info.get('rounded_corners', 0) > 0:
        desc_parts.append("둥근 모서리")

    return ", ".join(desc_parts)
    # 예: "사각형, primary 색상, 25% 투명도, 둥근 모서리"
```

---

#### Step 2.4.2: 레거시 복잡도 분석 (SVG 추출)

**참고**: SVG 추출은 shape_source: svg로 처리됩니다. 주로 방사형 다이어그램에 사용.

**복잡도 판단 기준**:

| 조건 | 예시 | 추출 방식 |
|------|------|----------|
| 사각형, 원, 텍스트만 | 일반 레이아웃 | `description` |
| 방사형 세그먼트 (3개+) | cycle-6segment, radial chart | `shape_source: svg` |
| 벌집형 레이아웃 | honeycomb process | `shape_source: ooxml` |
| 곡선 화살표/커넥터 | curved arrow cycle | `shape_source: ooxml` |
| 비정형 다각형 | custom polygons | `shape_source: ooxml` |
| `layout.type: radial` | 방사형 배치 | `shape_source: svg` |

**SVG 추출 감지 함수**:

```python
def should_extract_as_svg(shapes, layout=None):
    """SVG 추출 필요 여부 판단"""
    # 1. 레이아웃 타입 체크
    if layout and layout.get('type') == 'radial':
        return True

    # 2. 방사형 배치 감지 (세그먼트 3개 이상)
    segment_count = sum(1 for s in shapes if 'segment' in s.get('name', '').lower())
    if segment_count >= 3:
        return True

    return False
```

**복잡 도형 SVG 추출**:

복잡도가 감지되면 `type: svg`로 추출하고 SVG path를 생성합니다.

```yaml
# Complex 도형 → SVG 추출 결과
shapes:
  - id: "cycle-segment-0"
    name: "사이클 세그먼트 1 (상단)"
    type: svg                           # NEW: SVG 타입
    z_index: 1
    geometry:
      x: 30%                            # 바운딩 박스 (fallback)
      y: 0%
      cx: 40%
      cy: 35%
    svg:                                # NEW: SVG 필드
      path: "M 0,-35 C 50,-100 100,-130 70,-165 C 40,-180 -40,-180 -70,-165 Z"
      viewBox: "0 0 200 200"
      center: {x: 100, y: 100}          # 상대 좌표 기준점
      fill: primary                      # 디자인 토큰
    content:                            # 내부 요소
      icon:
        position: {x: 0, y: -130}       # center 기준 상대 좌표
        name: "fa-user"
        size: 20
        color: white
      label:
        position: {x: 0, y: -95}
        text: "Feature Name"
        font_size: 9
        color: white
```

**SVG Path 생성 가이드**:

1. **기준점 설정**: 다이어그램 중심을 (0, 0) 또는 명시적 center 좌표로 설정
2. **Path 작성**: Bezier 곡선(C), 직선(L), 이동(M), 닫기(Z) 사용
3. **상대 좌표**: 아이콘/텍스트 위치는 center 기준 상대값
4. **디자인 토큰**: fill, stroke에 시맨틱 색상 사용 (primary, secondary 등)

**방사형 세그먼트 Path 예시**:

```yaml
# 6분할 사이클 다이어그램
svg:
  center: {x: 480, y: 280}              # 960x540 캔버스 기준 중심
  segments:
    - id: segment-0
      angle: 0                          # 상단 (12시 방향)
      path: "M 0,-35 C 50,-100 100,-130 70,-165 C 40,-180 -40,-180 -70,-165 Z"
      fill: "#FF7F50"
    - id: segment-1
      angle: 60                         # 우상단 (2시 방향)
      path: "M 30,-20 C 80,-60 140,-60 165,-30 C 185,10 175,60 140,90 Z"
      fill: "#32CD32"
    # ... 4개 더
```

---

#### Step 2.4.3: 이미지 자동 벡터화 (VTracer)

**목적**: 래스터 이미지(PNG, JPG)를 SVG로 변환하여 `shape_source: svg`로 저장

**사용 시점**:
- 아이콘/로고 이미지를 벡터로 변환하고 싶을 때
- 다이어그램 이미지를 편집 가능한 형태로 추출할 때
- 이미지 품질 손실 없이 확대/축소가 필요할 때

**스크립트 사용**:

```bash
# 기본 변환 (자동 프리셋)
python .claude/skills/ppt-extract/scripts/image-vectorizer.py extracted_icon.png --output icon.svg

# 프리셋별 변환
python .claude/skills/ppt-extract/scripts/image-vectorizer.py logo.png --preset logo --output logo.svg
python .claude/skills/ppt-extract/scripts/image-vectorizer.py diagram.png --preset diagram --output diagram.svg

# 배치 변환
python .claude/skills/ppt-extract/scripts/image-vectorizer.py ./media/ --output ./svgs/
```

**프리셋 선택 가이드**:

| 이미지 유형 | 프리셋 | 예상 품질 |
|------------|--------|----------|
| 단색 아이콘 | `icon` | 95-99% |
| 플랫 로고 | `logo` | 90-95% |
| 다이어그램 | `diagram` | 85-95% |
| 차트 | `chart` | 85-90% |
| 기타 | `default` | 80-90% |

**워크플로우 통합**:

```python
# 1. PPTX에서 미디어 추출
media_files = extract_media_from_pptx(pptx_path)

# 2. 벡터화 대상 판단
for media in media_files:
    if should_vectorize(media):  # 아이콘, 로고, 다이어그램인지 판단
        # 3. VTracer로 SVG 변환
        svg_path = vectorize_with_vtracer(media['path'], preset='auto')

        # 4. 템플릿에 shape_source: svg로 저장
        shape['shape_source'] = 'svg'
        shape['svg'] = {
            'file': svg_path,
            'original_image': media['path']  # fallback용 원본 보존
        }
```

**벡터화 대상 판단 함수**:

```python
def should_vectorize(media_file):
    """이미지를 SVG로 변환할지 판단"""
    filename = media_file['name'].lower()

    # 아이콘/로고 판단
    if any(kw in filename for kw in ['icon', 'logo', 'symbol', 'badge']):
        return True

    # 크기 기반 판단 (작은 이미지 = 아이콘 가능성)
    if media_file['width'] <= 256 and media_file['height'] <= 256:
        return True

    # 색상 수 기반 (적은 색상 = 벡터화 적합)
    if media_file.get('color_count', 100) <= 32:
        return True

    return False
```

**출력 YAML 예시**:

```yaml
shapes:
  - id: "icon-diagram"
    type: svg
    shape_source: svg
    geometry:
      x: 10%
      y: 15%
      cx: 80%
      cy: 70%
    svg:
      file: "svgs/process-diagram.svg"
      original_image: "media/image1.png"  # fallback
      preset_used: "diagram"
      vectorization_quality: 0.92
```

**한계 및 주의사항**:
- 사진/복잡한 이미지는 벡터화 품질이 낮음 → `shape_source: html` 또는 원본 이미지 유지
- 텍스트가 포함된 이미지는 경로로 변환됨 (편집 불가)
- 그라데이션은 계단식으로 근사됨

---

**이미지 설명 필수 (picture 타입)**: 이미지 도형에는 반드시 `description` 포함

```yaml
# GOOD - description 포함
shapes:
  - id: "image-0"
    type: picture
    geometry: {x: 50%, y: 0%, cx: 50%, cy: 100%}
    image:
      source: "images/hero-cityscape.jpg"
      description: "도시 야경 사진, 고층 빌딩들과 조명이 반짝이는 모습"
      purpose: hero
      fit: cover

# BAD - description 누락
shapes:
  - id: "image-0"
    type: picture
    geometry: {x: 50%, y: 0%, cx: 50%, cy: 100%}
    # image 필드 자체가 없거나 description이 없으면 안 됨
```

**이미지 설명 작성 가이드**:
- LLM이 이해할 수 있는 자연어로 작성
- 이미지의 주요 피사체, 색상, 분위기 포함
- 예: "추상적인 파란색 그라데이션 배경, 부드러운 곡선과 빛 효과"
- 예: "비즈니스 미팅 장면, 테이블에 앉은 4명의 직원이 노트북을 보고 있음"

**배경 이미지 설명**: 슬라이드 배경에 이미지가 있는 경우

```yaml
background:
  type: image
  image:
    source: "backgrounds/abstract-dark.jpg"
    description: "어두운 그라데이션 배경, 미세한 기하학적 패턴"
    fit: cover
    opacity: 0.3
    overlay_color: dark_text
    overlay_opacity: 0.5
```

#### Step 2.5: 테마 색상 → 시맨틱 매핑

`ppt/theme/theme1.xml`에서 색상 로드:

| 테마 색상 | 시맨틱 |
|----------|--------|
| dk1 | dark_text |
| lt1 | background |
| dk2 | primary |
| accent1 | secondary |

#### Step 2.6: 프롬프트 역추론 (NEW)

추출된 shapes[] 구조를 분석하여 `expected_prompt`와 `prompt_keywords`를 생성합니다.

**역추론 원칙**:
1. 템플릿의 시각적 구성요소 분석
2. 각 요소의 역할과 목적 파악
3. 사용자가 자연어로 요청할 법한 문장으로 변환

**프롬프트 구조**:
```
[슬라이드 유형] 슬라이드를 만들어줘.
- [요소 1]: [위치/스타일/용도]
- [요소 2]: [위치/스타일/용도]
- ...
- [전체 분위기/레이아웃 특징]
```

**요소별 프롬프트 변환 규칙**:

| 도형 타입 | 프롬프트 표현 |
|----------|--------------|
| `rounded-rectangle` (상단) | "상단에 라운드 형태의 라벨/배지" |
| `textbox` (TITLE) | "중앙에 큰 제목 텍스트" |
| `textbox` (BODY) | "본문 설명 텍스트" |
| `group` (N열) | "N개의 카드/열로 구성된 그리드" |
| `icon` | "아이콘과 함께 표시" |
| `line` | "구분선" |
| `dotgrid` | "도트그리드 형태의 퍼센트 표시" |
| `picture` | "이미지/사진 영역" |
| `oval` (원형) | "원형 도형/단계 표시" |
| `arrow` | "화살표로 연결/흐름 표현" |

**역추론 알고리즘**:

```python
def infer_prompt(shapes, design_intent, category):
    """shapes 구조에서 expected_prompt 역추론"""
    prompt_parts = []
    keywords = set()

    # 1. 슬라이드 유형 문장
    type_desc = get_category_desc(category)
    prompt_parts.append(f"{type_desc} 슬라이드를 만들어줘.")
    keywords.add(category)

    # 2. 그룹 분석 (N열 구조 감지)
    groups = [s for s in shapes if s['type'] == 'group']
    if len(groups) >= 3:
        prompt_parts.append(f"- {len(groups)}개의 항목을 가로로 배치")
        keywords.add(f"{len(groups)}열")
        keywords.add("그리드")

    # 3. 요소별 설명 생성 (y 좌표 순서대로)
    for shape in sorted(shapes, key=lambda s: float(s['geometry']['y'].replace('%',''))):
        desc = shape_to_prompt(shape)
        if desc:
            prompt_parts.append(f"- {desc}")
            keywords.update(extract_keywords(shape))

    # 4. 레이아웃 특징
    if is_symmetric(shapes):
        prompt_parts.append("- 대칭적인 레이아웃")
        keywords.add("대칭")
    if has_icons(shapes):
        keywords.add("아이콘")

    return "\n".join(prompt_parts), list(keywords)

def shape_to_prompt(shape):
    """단일 shape를 프롬프트 문장으로 변환"""
    shape_type = shape['type']
    geometry = shape['geometry']
    y_pos = float(geometry['y'].replace('%',''))

    # 위치 판단
    position = "상단" if y_pos < 30 else ("중앙" if y_pos < 70 else "하단")

    if shape_type == 'rounded-rectangle':
        return f"{position}에 라운드 형태의 박스"
    elif shape_type == 'textbox':
        placeholder = shape.get('text', {}).get('placeholder_type', '')
        if placeholder == 'TITLE':
            return f"{position}에 큰 제목 텍스트"
        elif placeholder == 'BODY':
            return "설명 텍스트"
    elif shape_type == 'icon':
        return "아이콘 표시"
    elif shape_type == 'dotgrid':
        return "도트그리드로 퍼센트 시각화"
    elif shape_type == 'group':
        return None  # 그룹은 상위에서 처리
    elif shape_type == 'oval':
        return f"{position}에 원형 도형"
    elif shape_type == 'arrow':
        return "화살표로 연결"

    return None
```

**prompt_keywords 추출 규칙**:

| 소스 | 추출 키워드 |
|------|-----------|
| category | cover → "표지", toc → "목차", process → "프로세스" |
| design_intent | grid-4col → "4열", "그리드" |
| shapes[].type | icon → "아이콘", dotgrid → "도트", "퍼센트" |
| use_for | 배열 그대로 포함 |
| 레이아웃 분석 | 대칭 → "대칭", 가로배치 → "가로", "그리드" |

**생성 예시**:

```yaml
# deepgreen-grid4col1에서 추론된 프롬프트
expected_prompt: |
  기능 소개 슬라이드를 만들어줘.
  - 4개의 카드를 가로로 균등 배치
  - 각 카드: 상단에 라운드 배경 아이콘
  - 아이콘 아래에 제목 텍스트
  - 제목 아래에 설명 텍스트
  - 균등한 간격의 그리드 레이아웃
prompt_keywords: ["기능", "특징", "서비스", "4열", "아이콘", "그리드", "카드"]
```

---

#### Step 2.7: 개별 YAML 생성

**저장 경로**: `templates/contents/templates/{design_intent}{번호}.yaml`

```yaml
# {design_intent} 콘텐츠 템플릿 v2.0
# 원본: {source_file}:{slide_index}

content_template:
  id: {design_intent}{번호}
  name: "{한글 이름}"
  version: "2.0"
  source: {source_file}
  source_slide_index: {0-based index}
  extracted_at: "{ISO 8601 timestamp}"

design_meta:
  quality_score: {0.0-10.0}
  design_intent: {design_intent}
  design_intents:
    - {primary_intent}
    - {secondary_intent}  # 해당되는 경우
  visual_balance: {symmetric|asymmetric}
  information_density: {low|medium|high}

canvas:
  reference_width: 1980
  reference_height: 1080
  aspect_ratio: "16:9"

shapes:
  - id: "shape-0"
    name: "Shape Name"
    type: rectangle
    z_index: 0
    geometry:
      x: 0%
      y: 0%
      cx: 48%
      cy: 100%
      original_aspect_ratio: 0.48  # REQUIRED: 원본 비율 (width_px / height_px)
    style:
      fill: {type: solid, color: primary, opacity: 1.0}
      stroke: {color: none, width: 0}
      shadow: {enabled: false}
      rounded_corners: 0
    text:
      has_text: true
      placeholder_type: BODY
      alignment: center
      font_size_ratio: 0.028          # REQUIRED
      original_font_size_pt: 30.24    # REQUIRED: 원본 폰트 크기 (pt)
      font_weight: bold
      font_color: light

# 아이콘이 포함된 경우
icons:
  - id: "icon-0"
    type: font-awesome
    icon_name: "fa-chart-bar"
    position: {x: 100, y: 300}
    size: 32                      # REQUIRED: size 또는 size_ratio 필수
    # size_ratio: 0.03            # 또는 캔버스 높이 대비 비율
    color: primary

gaps:
  global: {column_gap: 4%, row_gap: 3%}
  between_shapes: []

spatial_relationships: []

groups: []

thumbnail: thumbnails/{category}/{design_intent}{번호}.png  # REQUIRED

# ============================================
# 검색 메타데이터 (REQUIRED - 절대 누락 금지!)
# ============================================
use_for:                              # REQUIRED: 사용 용도 (3-5개)
  - "용도 1"
  - "용도 2"
  - "용도 3"

keywords:                             # REQUIRED: 검색 키워드 (5-10개)
  - "키워드1"
  - "키워드2"
  - "키워드3"

expected_prompt: |                    # REQUIRED: 사용자 요청 프롬프트 예시
  {슬라이드 유형} 슬라이드를 만들어줘.
  - {요소1 설명}
  - {요소2 설명}
  - {레이아웃 특징}

prompt_keywords:                      # REQUIRED: 프롬프트 매칭 키워드 (5-10개)
  - "프롬프트키워드1"
  - "프롬프트키워드2"
  - "프롬프트키워드3"
```

**검색 메타데이터 필수 항목 (CRITICAL)**:

| 필드 | 설명 | 예시 |
|------|------|------|
| `use_for` | 템플릿 사용 용도 (3-5개) | "프로세스 설명", "단계별 안내" |
| `keywords` | 검색용 키워드 (5-10개) | "프로세스", "단계", "흐름" |
| `expected_prompt` | 사용자가 요청할 법한 프롬프트 | "3단계 프로세스 슬라이드 만들어줘" |
| `prompt_keywords` | 프롬프트 매칭 키워드 (5-10개) | "프로세스", "단계", "순서" |

**⚠️ 이 필드들이 없으면 LLM이 템플릿을 검색할 수 없습니다!**

---

### Phase 2.8: Object 분리 저장 (v3.1 NEW - 선택적)

**목적**: 슬라이드에서 재사용 가능한 다이어그램/컴포넌트를 별도 Object로 분리 저장합니다.

#### Object 분리 대상 감지

| 대상 | 예시 | 분리 여부 |
|------|------|----------|
| 방사형 다이어그램 | 6-segment cycle, radial chart | ✅ 분리 |
| 프로세스 흐름도 | honeycomb, pyramid, funnel | ✅ 분리 |
| 복잡한 아이콘 조합 | icon + badge + label 그룹 | ✅ 분리 |
| 단순 레이아웃 | 텍스트 + 배경만 | ❌ 분리 불필요 |

**Object 분리 감지 함수**:

```python
def should_extract_as_object(shapes, design_intent):
    """재사용 가능한 Object로 분리할지 판단"""

    # 1. 다이어그램 카테고리 체크
    diagram_categories = ['cycle', 'process', 'funnel', 'hierarchy', 'matrix']
    category = design_intent.split('-')[0]
    if category in diagram_categories:
        return True

    # 2. 복잡한 shape 그룹 감지
    grouped_shapes = [s for s in shapes if s.get('type') == 'group']
    if len(grouped_shapes) >= 3:
        return True

    # 3. 반복 패턴 감지 (동일 타입 shape 4개+)
    type_counts = {}
    for s in shapes:
        t = s.get('type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1
    if any(count >= 4 for count in type_counts.values()):
        return True

    return False
```

#### Object 파일 구조

**저장 경로**: `templates/contents/objects/{category}/{object_id}.yaml`

```yaml
# Object 파일 예시: objects/cycle/6segment-colorful.yaml
object:
  id: 6segment-colorful
  name: "6세그먼트 컬러풀 사이클"
  type: diagram
  version: "1.0"
  source: "deep-green-template.pptx:11"
  extracted_at: "2025-01-08T10:30:00Z"

  # 바운딩 박스 (원본 슬라이드 내 위치)
  bounding_box:
    x: 20%
    y: 15%
    cx: 60%
    cy: 70%

  # 구성 요소들
  components:
    - id: segment-1
      shape_source: ooxml
      ooxml:
        fragment: |
          <p:sp><!-- 세그먼트 1 OOXML --></p:sp>
        emu: {x: 2438400, y: 1625600, cx: 2438400, cy: 1905000}
      relative_position: {angle: 0, radius: 35%}
      style:
        fill:
          color: primary

    - id: segment-2
      shape_source: ooxml
      ooxml:
        fragment: |
          <p:sp><!-- 세그먼트 2 OOXML --></p:sp>
        emu: {x: 4114800, y: 2286000, cx: 2438400, cy: 1905000}
      relative_position: {angle: 60, radius: 35%}
      style:
        fill:
          color: secondary

    # ... 6개 세그먼트

  # 검색용 메타데이터
  metadata:
    category: cycle
    tags: [colorful, 6-element, radial, diagram]
    element_count: 6
    complexity: high
    use_for: ["프로세스", "사이클", "순환", "6단계"]
```

#### 템플릿에서 Object 참조

**reference 타입으로 Object 참조**:

```yaml
# 템플릿 파일: templates/cycle/cycle-colorful1.yaml
shapes:
  - id: "main-diagram"
    shape_source: reference
    reference:
      object: "objects/cycle/6segment-colorful.yaml"
      # 오버라이드 (선택)
      override:
        geometry: {x: 15%, y: 20%, cx: 70%, cy: 65%}
        style:
          colors:
            segment-1: accent1
            segment-2: accent2

  - id: "title-text"
    shape_source: description
    description:
      text: "중앙 상단에 제목 텍스트"
```

#### Object Registry

**저장 경로**: `templates/contents/objects/registry.yaml`

```yaml
# Object Registry
objects:
  - id: 6segment-colorful
    name: "6세그먼트 컬러풀 사이클"
    file: cycle/6segment-colorful.yaml
    category: cycle
    tags: [colorful, 6-element, radial]
    complexity: high

  - id: honeycomb-6
    name: "6칸 벌집 프로세스"
    file: process/honeycomb-6.yaml
    category: process
    tags: [honeycomb, hexagon, 6-step]
    complexity: high

  - id: pyramid-5level
    name: "5단계 피라미드"
    file: hierarchy/pyramid-5level.yaml
    category: hierarchy
    tags: [pyramid, 5-level, triangle]
    complexity: medium
```

#### Object 분리 워크플로우

```
슬라이드 추출 중
  │
  ▼
┌─────────────────────────────────────┐
│ Object 분리 대상 감지               │
│ - 다이어그램 카테고리?               │
│ - 복잡한 그룹 3개+?                 │
│ - 반복 패턴 4개+?                   │
└─────────────────────────────────────┘
  │ Yes
  ▼
┌─────────────────────────────────────┐
│ Object 바운딩 박스 계산             │
│ - 구성 shape들의 min/max 좌표       │
│ - 중심점 및 상대 좌표 계산           │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ Object YAML 생성                    │
│ - objects/{category}/{id}.yaml      │
│ - 각 component에 shape_source 적용  │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ 템플릿에 reference 추가              │
│ - shape_source: reference           │
│ - reference.object: "path/to/obj"   │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ Registry 업데이트                    │
│ - objects/registry.yaml             │
└─────────────────────────────────────┘
```

---

### Phase 3: Thumbnail Generation - MANDATORY

**CRITICAL**: 썸네일 없이 추출을 완료할 수 없습니다.

#### 스크립트 경로

```bash
# 스크립트 위치 (ppt-gen 스킬 내)
SCRIPT_DIR=".claude/skills/ppt-gen/scripts"

# PYTHONPATH 설정 (inventory.py 등 의존 모듈 포함)
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
```

#### 개별 슬라이드 썸네일 생성

```bash
# 개별 슬라이드 썸네일 생성 (0-based index)
cd .claude/skills/ppt-gen && python scripts/thumbnail.py {source}.pptx templates/contents/thumbnails/ --slides {N} --single

# 파일명 변경 (slide-N.png → {design_intent}{번호}.png)
mv templates/contents/thumbnails/slide-{N}.png templates/contents/thumbnails/{design_intent}{번호}.png
```

#### 다중 슬라이드 추출 시

```bash
# 여러 슬라이드 한 번에 추출
cd .claude/skills/ppt-gen && python scripts/thumbnail.py {input}.pptx templates/contents/thumbnails/ --slides 1,2,4,5,6 --single

# 각각 파일명 변경
mv templates/contents/thumbnails/slide-1.png templates/contents/thumbnails/cover-banner1.png
mv templates/contents/thumbnails/slide-2.png templates/contents/thumbnails/toc-list1.png
mv templates/contents/thumbnails/slide-4.png templates/contents/thumbnails/stats-chart1.png
# ...
```

#### 필수 시스템 의존성

| 도구 | 용도 | 설치 |
|------|------|------|
| LibreOffice (`soffice`) | PPTX → PDF 변환 | `apt install libreoffice` / `brew install --cask libreoffice` |
| Poppler (`pdftoppm`) | PDF → 이미지 변환 | `apt install poppler-utils` / `brew install poppler` |

#### 출력 확인

```bash
# 썸네일 존재 확인 (필수)
test -f templates/contents/thumbnails/{design_intent}{번호}.png && echo "Thumbnail OK" || echo "ERROR: Thumbnail missing!"
```

#### 오류 처리

썸네일 생성 실패 시:
1. **LibreOffice 미설치**: `soffice: command not found` → LibreOffice 설치 필요
2. **Poppler 미설치**: `pdftoppm: command not found` → Poppler 설치 필요
3. **파일 경로 오류**: PPTX 파일 경로가 절대 경로인지 확인

---

### Phase 4: Registry Update (레지스트리 업데이트) - v4.1 분리형

**v4.1 분리형 registry 구조**:
```
templates/contents/
├── registry.yaml              # 마스터 (인덱스): 카테고리 목록만
├── registry-{category}.yaml   # 카테고리별 템플릿 목록 × 13
```

#### 4.1 카테고리별 registry 업데이트

`templates/contents/registry-{category}.yaml`에 새 템플릿 추가:

```yaml
templates:
  # ... 기존 항목들

  - id: {design_intent}{번호}
    name: {한글 이름}
    file: templates/{category}/{design_intent}{번호}.yaml
    thumbnail: thumbnails/{category}/{design_intent}{번호}.png
    source_slide_index: {N}
    # 검색 메타데이터 (압축 통합)
    description: "{expected_prompt 첫 문장}"
    match_keywords:  # use_for + keywords + prompt_keywords 통합 (중복 제거)
      - {keyword1}
      - {keyword2}
      - {keyword3}
    expected_prompt: |
      {슬라이드 유형} 슬라이드를 만들어줘.
      - {요소1 설명}
      - {요소2 설명}
      - {레이아웃 특징}
```

#### 4.2 마스터 registry 업데이트

`templates/contents/registry.yaml`의 해당 카테고리 count 증가:

```yaml
categories:
  {category}:
    count: {N+1}  # 기존 값 + 1
```

#### 4.3 자동화 (권장)

수동 업데이트 대신 `sync_registry.py` 스크립트 실행:

```bash
python .claude/skills/ppt-gen/scripts/sync_registry.py
```

이 스크립트는 개별 템플릿 YAML에서 메타데이터를 추출하여 분리형 registry를 자동 생성합니다.

**match_keywords 생성 규칙**:
- `prompt_keywords` + `use_for` + `keywords` 통합
- 중복 제거, 순서 유지
- 5-10개 키워드 권장

**expected_prompt 작성 가이드**:
- 사용자가 자연어로 요청할 법한 문장으로 작성
- 슬라이드의 주요 구성요소를 순서대로 설명
- 레이아웃 특징(대칭, 그리드, 흐름 등) 포함

---

### Phase 5: Validation (검증)

추출 완료 전 **필수 검증**:

```bash
# 1. YAML 파일 존재 확인
test -f templates/contents/templates/{design_intent}{번호}.yaml && echo "YAML OK"

# 2. 썸네일 존재 확인
test -f templates/contents/thumbnails/{design_intent}{번호}.png && echo "Thumbnail OK"

# 3. YAML 문법 검증
python -c "import yaml; yaml.safe_load(open('templates/contents/templates/{design_intent}{번호}.yaml'))"

# 4. 레지스트리 업데이트 확인
grep "{design_intent}{번호}" templates/contents/registry.yaml && echo "Registry OK"
```

---

## Output Checklist

**추출 완료 시 다음 항목이 모두 존재해야 합니다:**

- [ ] `templates/contents/templates/{design_intent}{번호}.yaml` - YAML 파일
- [ ] `templates/contents/thumbnails/{design_intent}{번호}.png` - 썸네일 (1980x1080)
- [ ] `templates/contents/registry.yaml` 업데이트됨

---

## Multi-Slide Extraction Example

```
입력: deep-green-template.pptx (슬라이드 14개)

처리:
1. 슬라이드 0 (로고) → skip: true
2. 슬라이드 1 → cover-banner1.yaml + cover-banner1.png
3. 슬라이드 2 → toc-list1.yaml + toc-list1.png
4. 슬라이드 3 → section-number1.yaml + section-number1.png
5. 슬라이드 4 → stats-chart1.yaml + stats-chart1.png
6. 슬라이드 5 → stats-dotgrid1.yaml + stats-dotgrid1.png
7. 슬라이드 6 → feature-icons1.yaml + feature-icons1.png
8. 슬라이드 7 → matrix-2x21.yaml + matrix-2x21.png
9. 슬라이드 8 → process-honeycomb1.yaml + process-honeycomb1.png
10. 슬라이드 9 → process-linear1.yaml + process-linear1.png
11. 슬라이드 10 → process-circle1.yaml + process-circle1.png
12. 슬라이드 11 → cycle-circular1.yaml + cycle-circular1.png
13. 슬라이드 12 → content-image-text1.yaml + content-image-text1.png
14. 슬라이드 13 → table-comparison1.yaml + table-comparison1.png

출력 구조:
├── templates/contents/templates/
│   ├── cover-banner1.yaml
│   ├── toc-list1.yaml
│   ├── section-number1.yaml
│   ├── stats-chart1.yaml
│   ├── stats-dotgrid1.yaml
│   ├── feature-icons1.yaml
│   ├── matrix-2x21.yaml
│   ├── process-honeycomb1.yaml
│   ├── process-linear1.yaml
│   ├── process-circle1.yaml
│   ├── cycle-circular1.yaml
│   ├── content-image-text1.yaml
│   └── table-comparison1.yaml
├── templates/contents/thumbnails/
│   ├── cover-banner1.png
│   ├── toc-list1.png
│   └── ... (13개 썸네일)
└── templates/contents/registry.yaml (13개 항목 추가)
```

---

## Parallel Extraction (병렬 추출)

다중 슬라이드를 병렬로 추출하여 속도를 높입니다.

### 서브에이전트 기반 병렬 처리

**사용 서브에이전트**:
- `content-slide-extractor`: 단일 슬라이드 YAML + 썸네일 추출
- `image-style-extractor`: 이미지 스타일 분석 (색상, 타이포그래피)

### 워크플로우

#### 0단계: 스킬 기준 경로 설정

```bash
# ppt-gen 스킬 기준 경로
SKILL_DIR=".claude/skills/ppt-gen"

# 모든 경로는 스킬 디렉토리 기준
TEMPLATES_DIR="$SKILL_DIR/templates/contents/templates"
THUMBNAILS_DIR="$SKILL_DIR/templates/contents/thumbnails"
SCRIPTS_DIR="$SKILL_DIR/scripts"
```

#### 1단계: 메인 에이전트가 전체 분석

```bash
# 1. PPTX 언팩
python .claude/skills/ppt-gen/ooxml/scripts/unpack.py input.pptx workspace/unpacked

# 2. 각 슬라이드의 design_intent 사전 결정
slide_intents = {
    1: "cover-banner",
    2: "toc-list",
    3: "section-number",
    # ...
}

# 3. 기존 파일 확인하여 번호 할당
filenames = {
    1: "cover-banner1",
    2: "toc-list1",
    3: "section-number1",
    # ...
}
```

#### 2단계: 병렬 서브에이전트 실행

```python
# 13개 슬라이드 병렬 추출 (슬라이드 0 제외)
task_ids = []

for slide_index in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]:
    task_id = Task(
        subagent_type="content-slide-extractor",
        prompt=f"""
pptx_path: deep-green-template.pptx
unpacked_dir: workspace/unpacked
slide_index: {slide_index}
design_intent: {slide_intents[slide_index]}
output_filename: {filenames[slide_index]}
source_aspect_ratio: "16:9"
""",
        run_in_background=True,
        model="haiku"
    )
    task_ids.append(task_id)
```

#### 3단계: 결과 수집 및 검증

```python
# 모든 에이전트 결과 수집
results = []
for task_id in task_ids:
    result = TaskOutput(task_id=task_id, block=True)
    results.append(result)

# 실패한 슬라이드 재시도
failed = [r for r in results if r['status'] == 'error']
if failed:
    # 순차 재처리 또는 에러 보고
    pass

# registry.yaml 일괄 업데이트
update_registry(results)
```

### 병렬 추출 시 주의사항

1. **언팩은 순차적으로**: PPTX 언팩은 먼저 완료 후 병렬 추출 시작
2. **파일명 충돌 방지**: 메인 에이전트가 사전에 모든 파일명 할당
3. **썸네일 생성**: 각 서브에이전트가 개별 썸네일 생성
4. **레지스트리 업데이트**: 병렬 완료 후 메인 에이전트가 일괄 업데이트

### 성능 비교

| 방식 | 14슬라이드 예상 시간 |
|------|---------------------|
| 순차 처리 | ~5분 |
| 병렬 처리 (13 에이전트) | ~30초-1분 |

---

## External Image Extraction (웹 이미지 추출)

네이버 블로그 등 보호된 사이트에서 이미지를 추출할 때 사용합니다.

### Triggers

- "이 블로그에서 이미지 추출해줘"
- "네이버 블로그 이미지 다운로드해줘"
- "웹에서 레퍼런스 이미지 가져와줘"
- WebFetch/브라우저 직접 접근이 차단된 경우

### Prerequisites

```bash
pip install playwright
playwright install chromium
```

### Workflow

#### 1. 직접 접근 시도

먼저 WebFetch 또는 브라우저 자동화 도구로 직접 접근을 시도합니다.

```
WebFetch: https://blog.naver.com/...
→ 실패 시: "Claude Code is unable to fetch from blog.naver.com"
```

#### 2. Playwright Fallback (asset-manager.py)

직접 접근이 차단되면 `asset-manager.py crawl` 명령을 사용합니다.

```bash
# 1. 미리보기 (다운로드 없이 목록 확인)
cd .claude/skills/ppt-gen/scripts
python asset-manager.py crawl "{URL}" --prefix {prefix} --preview

# 2. 다운로드 실행
python asset-manager.py crawl "{URL}" \
    --prefix {prefix} \
    --tags "reference,template" \
    --max-images 50 \
    --min-size 300

# 3. 다운로드된 이미지 확인
ls -la templates/assets/images/{prefix}*.png
```

#### 3. 이미지 분석 및 컨텐츠 추출

다운로드된 이미지를 Read 도구로 읽어 분석합니다.

```python
# Claude의 멀티모달 기능으로 이미지 분석
for image_path in downloaded_images:
    Read(image_path)  # 이미지 시각적 분석
    # → 슬라이드 유형, 레이아웃, 색상, 구성요소 파악
```

#### 4. YAML 템플릿 생성

분석 결과를 기반으로 콘텐츠 템플릿 YAML을 생성합니다.

### Supported Sites (지원 사이트)

| 사이트 | 핸들러 | 특수 처리 |
|--------|--------|----------|
| 네이버 블로그 | NaverBlogHandler | iframe 전환, lazy-load |
| 네이버 카페 | NaverBlogHandler | iframe 전환, lazy-load |
| 네이버 포스트 | NaverBlogHandler | iframe 전환, lazy-load |
| 일반 웹사이트 | GenericHandler | 기본 이미지 추출 |

### Error Handling

```yaml
# 접근 차단 감지
if "unable to fetch" in error or "not allowed" in error:
    # → asset-manager.py crawl 로 전환

# Playwright 미설치
if "playwright 모듈이 필요합니다" in error:
    # → pip install playwright && playwright install chromium

# 이미지 없음
if filtered_count == 0:
    # → min-size 값 낮추기 또는 다른 URL 시도
```

### Output

다운로드된 이미지는 다음 위치에 저장됩니다:
- **이미지**: `templates/assets/images/{prefix}-{NNN}.{ext}`
- **레지스트리**: `templates/assets/registry.yaml`

---

## Reference

상세 스키마: [references/content-schema.md](../references/content-schema.md)
