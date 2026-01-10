# Content Template Extractor

슬라이드 이미지를 분석하여 재사용 가능한 YAML 콘텐츠 템플릿을 생성하는 프롬프트입니다.
GPT-4, Gemini, Claude 등 다양한 LLM에서 사용할 수 있습니다.

## 역할

당신은 슬라이드 이미지를 분석하여 재사용 가능한 YAML 콘텐츠 템플릿을 생성하는 전문가입니다.
이미지에서 레이아웃 구조, 도형, 텍스트 배치, 색상, 아이콘 등을 추출하여 표준화된 YAML 형식으로 변환합니다.

## Input/Output

### Input
- PNG/JPG 이미지 파일 (슬라이드 스크린샷 또는 인포그래픽)
- 선택적: 원본 출처 URL, 슬라이드 번호

### Output
1. **YAML 템플릿 파일**: `templates/contents/templates/{category}/{id}.yaml`
2. **썸네일 PNG**: `templates/contents/thumbnails/{category}/{id}.png`
3. **레지스트리 업데이트**: `templates/contents/registry.yaml`에 항목 추가

---

## YAML 스키마 참조

> **스키마 문서**: `.claude/skills/ppt-gen/references/content-schema.md`

YAML 템플릿 작성 시 위 스키마 문서를 참조하세요. 주요 섹션:
- `content_template`: 기본 메타데이터
- `design_meta`: 디자인 품질/의도 분석
- `canvas`: 캔버스 정규화 기준
- `shapes[]`: 도형 배열 스키마
- `svg` 타입: 복잡 다이어그램용 SVG 필드
- `icons[]`: 아이콘 배열 스키마
- 시맨틱 색상 토큰

---

## Design Intent 카테고리 (40개)

### 분류 체계

| 대분류 | 세부 카테고리 |
|--------|---------------|
| **Cover** | cover-centered, cover-banner, cover-split, cover-fullimage |
| **TOC** | toc-list, toc-grid, toc-visual |
| **Section** | section-title, section-number, section-image |
| **Closing** | closing-thankyou, closing-qna, closing-contact |
| **Comparison** | comparison-2col, comparison-table, pros-cons |
| **Matrix** | matrix-2x2, matrix-swot, matrix-3x3 |
| **Timeline** | timeline-horizontal, timeline-vertical, timeline-milestone |
| **Roadmap** | roadmap-horizontal, roadmap-phases, roadmap-gantt |
| **Process** | process-linear, process-circle, process-honeycomb, process-pyramid |
| **Cycle** | cycle-circular, cycle-loop, cycle-4arrow |
| **Funnel** | funnel-vertical, funnel-horizontal |
| **Stats** | stats-cards, stats-chart, stats-donut, stats-dotgrid |
| **Dashboard** | dashboard-kpi, dashboard-overview, dashboard-metrics |
| **Table** | table-simple, table-comparison, table-pricing |
| **Grid** | grid-2col, grid-3col, grid-4col, grid-icon |
| **Feature** | feature-list, feature-icons, feature-benefits |
| **Content** | content-image-text, content-quote, content-team, content-profile |
| **Hierarchy** | hierarchy-org, hierarchy-tree, hierarchy-mindmap |
| **Agenda** | agenda-numbered, agenda-visual |
| **Map** | map-world, map-region, map-location |
| **Flow** | flow-circular, flow-linear, flow-branching |
| **Diagram** | diagram-venn, diagram-pyramid, diagram-hexagon |
| **Infographic** | infographic-race, infographic-comparison |

### 자동 분류 생성

기존 분류에 없는 패턴 발견 시 `{대분류}-{특징}` 형식으로 생성:
- 예: `process-5step`, `cycle-6segment`, `grid-hexagon`

---

## Zone Detection 규칙

### 슬라이드 영역 구조

```
┌─────────────────────────────────────────┐
│  TITLE ZONE (0-20%)                     │  ← 제외
│  - placeholder_type: TITLE, CENTER_TITLE │
│  - 메인 타이틀, 서브타이틀                 │
├─────────────────────────────────────────┤
│                                         │
│  CONTENT ZONE (20-92%)                  │  ← 추출 대상
│  - 실제 콘텐츠 영역                       │
│  - shapes[], icons[] 추출               │
│                                         │
├─────────────────────────────────────────┤
│  FOOTER ZONE (92-100%)                  │  ← 제외
│  - 페이지 번호, 저작권 표시               │
└─────────────────────────────────────────┘
```

### 영역 감지 기준

| 영역 | 감지 조건 | Fallback |
|------|----------|----------|
| Title | placeholder_type in [TITLE, CENTER_TITLE, SUBTITLE] | 상단 0-20% |
| Title | name contains 'title', '제목', '타이틀' | |
| Title | y < 25% AND height < 15% | |
| Footer | name contains 'footer', 'page', '페이지', '푸터' | 하단 92-100% |
| Footer | y > 90% | |
| Content | 타이틀 하단 ~ 푸터 상단 | 20-92% |

### 좌표 변환

콘텐츠 영역을 100%로 정규화:

```python
# Content Zone 경계
content_top = 0.20 * canvas_height    # 20%
content_bottom = 0.92 * canvas_height # 92%
content_height = content_bottom - content_top

# 도형 좌표 → Content Zone % 변환
shape_y_percent = (shape_y - content_top) / content_height * 100
```

---

## 도형 추출 규칙

### geometry 추출

```yaml
geometry:
  x: 25%                           # 콘텐츠 영역 기준 %
  y: 10%
  cx: 50%                          # 너비
  cy: 80%                          # 높이
  original_aspect_ratio: 0.625     # 필수: width_px / height_px
```

### style 추출

```yaml
style:
  fill:
    type: solid                    # solid | gradient | none
    color: primary                 # 시맨틱 토큰 우선
    # 또는 HEX: "#1E5128"
    opacity: 1.0

  stroke:
    color: dark_text               # 테두리 색상
    width: 2                       # 두께 (pt)

  shadow:
    enabled: true
    blur: 4
    offset_x: 2
    offset_y: 3
    opacity: 0.15

  rounded_corners: 8               # 모서리 둥글기 (pt)
```

### text 추출

```yaml
text:
  has_text: true
  content: "텍스트 내용"
  placeholder_type: BODY           # TITLE | BODY | SUBTITLE
  alignment: center                # left | center | right
  font_size_ratio: 0.028           # 필수: font_size / canvas_height
  original_font_size_pt: 30.24     # 필수: 원본 폰트 크기
  font_weight: bold                # normal | bold
  font_color: light                # 시맨틱 토큰
```

### icon 추출

```yaml
# 독립 아이콘 (icons[] 배열)
icons:
  - id: "icon-0"
    icon_name: "fa-chart-bar"
    position: {x: 100, y: 300}
    size: 32                       # 필수: size 또는 size_ratio
    color: primary

# 인라인 아이콘 (shapes 내)
- icon:
    name: "chart-bar"
    color: primary
    size: 48                       # 필수
```

---

## SVG 추출 조건

### 복잡 도형 판단 기준

다음 조건에 해당하면 `type: svg` 사용:

| 조건 | 예시 |
|------|------|
| 방사형 세그먼트 (3개+) | cycle-6segment, radial chart |
| 벌집형 레이아웃 | honeycomb process |
| 곡선 화살표/커넥터 | curved arrow cycle |
| 비정형 다각형 | custom polygons |
| 연속된 곡선 경로 | flow diagrams |
| 겹치는 타원/원 | Venn diagrams |

### SVG 생성 가이드

1. **전체 슬라이드 SVG**: 복잡한 다이어그램은 `svg_inline`에 전체 SVG 작성
2. **기준점 설정**: 다이어그램 중심을 명시적으로 설정
3. **Path 명령어**: M(이동), L(직선), C(베지어 곡선), Q(2차 곡선), Z(닫기)
4. **디자인 토큰**: fill, stroke에 시맨틱 색상 사용

### svg_inline 예시

```yaml
svg_inline: |
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">
    <defs>
      <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#7B68EE"/>
        <stop offset="100%" stop-color="#9370DB"/>
      </linearGradient>
      <filter id="shadow">
        <feDropShadow dx="2" dy="3" stdDeviation="4" flood-opacity="0.15"/>
      </filter>
    </defs>

    <!-- Background -->
    <rect width="960" height="540" fill="#F8F9FA"/>

    <!-- Header Bar -->
    <rect x="0" y="0" width="960" height="60" fill="url(#headerGrad)"/>

    <!-- Circular Arrow -->
    <g filter="url(#shadow)">
      <path d="M 340,230 Q 340,150 480,150 Q 620,150 620,230"
            stroke="#7B8FD4" stroke-width="22" fill="none"/>
      <polygon points="608,215 635,245 605,250" fill="#7B8FD4"/>
    </g>

    <!-- Center Label -->
    <text x="480" y="300" text-anchor="middle" font-size="26" font-weight="bold">
      Next Level AI
    </text>
  </svg>
```

---

## 프롬프트 역추론

### expected_prompt 생성 규칙

추출된 shapes 구조를 분석하여 사용자가 요청할 법한 프롬프트를 역추론:

```yaml
expected_prompt: |
  {슬라이드 유형} 슬라이드를 만들어줘.
  - {요소1}: {위치/스타일/용도}
  - {요소2}: {위치/스타일/용도}
  - {전체 레이아웃 특징}
```

### 요소별 변환 규칙

| 도형 타입 | 프롬프트 표현 |
|----------|--------------|
| `rounded-rectangle` (상단) | "상단에 라운드 형태의 라벨/배지" |
| `textbox` (TITLE) | "중앙에 큰 제목 텍스트" |
| `textbox` (BODY) | "본문 설명 텍스트" |
| `group` (N열) | "N개의 카드/열로 구성된 그리드" |
| `icon` | "아이콘과 함께 표시" |
| `line` | "구분선" |
| `picture` | "이미지/사진 영역" |
| `oval` (원형) | "원형 도형/단계 표시" |
| `arrow` | "화살표로 연결/흐름 표현" |
| `svg` (cycle) | "순환 다이어그램/사이클" |
| `svg` (venn) | "벤 다이어그램/겹치는 영역" |

### prompt_keywords 추출

```yaml
prompt_keywords:
  - "{category에서 파생}"      # comparison → "비교"
  - "{design_intent에서 파생}" # grid-4col → "4열", "그리드"
  - "{shapes.type에서 파생}"   # icon → "아이콘"
  - "{레이아웃 분석}"          # 대칭 → "대칭"
  # 5-7개 권장
```

---

## 완전한 워크플로우 (5단계)

### Phase 1: 이미지 분석

1. **이미지 읽기**: 슬라이드 구조, 색상, 레이아웃 파악
2. **design_intent 결정**: 40개 카테고리 중 가장 적합한 것 선택
3. **번호 충돌 확인**: 기존 템플릿 확인하여 다음 번호 결정

```bash
# 기존 템플릿 확인
ls templates/contents/templates/{category}/
```

### Phase 2: YAML 추출 및 파일 생성

1. **Zone Detection**: Title/Content/Footer 영역 분리
2. **shapes[] 추출**: 콘텐츠 영역 내 도형 추출
3. **svg_inline 생성**: 복잡 도형은 SVG로 변환
4. **expected_prompt 역추론**: 프롬프트 생성
5. **YAML 파일 저장**:

```bash
# 저장 경로
templates/contents/templates/{category}/{design_intent}{N}.yaml

# 예시
templates/contents/templates/cycle/cycle-4arrow1.yaml
templates/contents/templates/comparison/comparison-2col1.yaml
```

### Phase 3: 썸네일 생성

```bash
# 방법 1: 원본 이미지 복사 (이미지 입력인 경우)
cp {input}.png templates/contents/thumbnails/{category}/{id}.png

# 방법 2: SVG 렌더링 (Playwright 필요)
cd .claude/skills/ppt-gen
node scripts/html2pptx.js --render-svg {yaml_path} --output {png_path}

# 방법 3: PPTX에서 추출
python scripts/thumbnail.py {input}.pptx output/ --slides {N} --single
mv output/slide-{N}.png templates/contents/thumbnails/{category}/{id}.png
```

### Phase 4: 레지스트리 업데이트

`templates/contents/registry.yaml`에 새 항목 추가:

```yaml
templates:
  # ... 기존 항목들

  - id: {design_intent}{N}
    name: "{한글 이름}"
    file: templates/{category}/{design_intent}{N}.yaml
    thumbnail: thumbnails/{category}/{design_intent}{N}.png
    category: {category}
    design_intent: {design_intent}
    description: "{설명}"
    use_for: ["용도1", "용도2"]
    expected_prompt: |
      {역추론 프롬프트}
    prompt_keywords: ["{키워드1}", "{키워드2}"]
```

### Phase 5: 검증

```bash
# 1. YAML 파일 존재 확인
test -f templates/contents/templates/{category}/{id}.yaml && echo "YAML OK"

# 2. 썸네일 존재 확인
test -f templates/contents/thumbnails/{category}/{id}.png && echo "Thumbnail OK"

# 3. YAML 문법 검증
python -c "import yaml; yaml.safe_load(open('{path}'))"

# 4. 레지스트리 업데이트 확인
grep "{id}" templates/contents/registry.yaml && echo "Registry OK"
```

---

## 스크립트 CLI 레퍼런스

### 썸네일 생성 (PPTX → PNG)

```bash
cd .claude/skills/ppt-gen
python scripts/thumbnail.py {input}.pptx {output_dir}/ --slides {N} --single

# 의존성: LibreOffice, Poppler
```

### 웹 이미지 크롤링 (보호된 사이트)

```bash
cd .claude/skills/ppt-gen/scripts

# 미리보기 (다운로드 없이)
python asset-manager.py crawl "{URL}" --prefix {prefix} --preview

# 다운로드
python asset-manager.py crawl "{URL}" \
    --prefix {prefix} \
    --tags "reference,template" \
    --max-images 50 \
    --min-size 300

# 의존성: playwright (pip install playwright && playwright install chromium)
```

### SVG → PNG 렌더링

```bash
cd .claude/skills/ppt-gen
node scripts/html2pptx.js --render-svg {yaml_path} --output {png_path}

# 의존성: playwright (npm install playwright)
```

---

## 출력 예시

### 예시 1: 비교 슬라이드 (comparison-2col)

```yaml
content_template:
  id: comparison-2col1
  name: "비교 (A vs B) - 기본"
  version: "3.0"
  schema_version: "3.0-svg"

design_meta:
  quality_score: 8.5
  design_intent: comparison-2col
  visual_balance: symmetric
  information_density: medium

canvas:
  reference_width: 960
  reference_height: 540
  aspect_ratio: "16:9"

background:
  type: solid
  color: "#FFFFFF"

shapes:
  - id: "left-panel"
    name: "왼쪽 패널"
    type: rectangle
    z_index: 0
    geometry:
      x: 2%
      y: 0%
      cx: 47%
      cy: 100%
      original_aspect_ratio: 0.47
    style:
      fill: {type: solid, color: primary, opacity: 1.0}
      rounded_corners: 8

  - id: "right-panel"
    name: "오른쪽 패널"
    type: rectangle
    z_index: 0
    geometry:
      x: 51%
      y: 0%
      cx: 47%
      cy: 100%
      original_aspect_ratio: 0.47
    style:
      fill: {type: solid, color: secondary, opacity: 1.0}
      rounded_corners: 8

  - id: "left-title"
    name: "왼쪽 제목"
    type: textbox
    z_index: 1
    geometry:
      x: 5%
      y: 10%
      cx: 40%
      cy: 15%
    text:
      has_text: true
      content: "Option A"
      alignment: center
      font_size_ratio: 0.044
      original_font_size_pt: 24
      font_weight: bold
      font_color: light

gaps:
  global: {column_gap: 4%, row_gap: 3%}

thumbnail: thumbnails/comparison/comparison-2col1.png

use_for:
  - "A vs B 비교"
  - "Before/After"
  - "장단점 비교"

keywords: ["비교", "vs", "대비", "양쪽", "2분할"]

expected_prompt: |
  비교 슬라이드를 만들어줘.
  - 좌우 2분할 레이아웃
  - 왼쪽: Option A (파란색 배경)
  - 오른쪽: Option B (녹색 배경)
  - 각 영역에 제목과 설명
  - 대칭 구조

prompt_keywords: ["비교", "vs", "2분할", "좌우", "대비"]
```

### 예시 2: 순환 다이어그램 (cycle-4arrow)

```yaml
content_template:
  id: cycle-4arrow1
  name: "4요소 순환 화살표 다이어그램"
  version: "3.0"
  schema_version: "3.0-svg"

design_meta:
  quality_score: 9.2
  design_intent: cycle-4arrow
  visual_balance: symmetric
  information_density: medium
  render_method: svg

canvas:
  reference_width: 960
  reference_height: 540
  viewBox: "0 0 960 540"

svg_inline: |
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">
    <defs>
      <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#7B68EE"/>
        <stop offset="100%" stop-color="#9370DB"/>
      </linearGradient>
      <filter id="shadow">
        <feDropShadow dx="2" dy="3" stdDeviation="4" flood-opacity="0.15"/>
      </filter>
    </defs>

    <rect width="960" height="540" fill="#F8F9FA"/>
    <rect x="0" y="0" width="960" height="60" fill="url(#headerGrad)"/>

    <text x="20" y="35" font-size="20" font-weight="bold" fill="white">
      Next Level AI : 4 Powers
    </text>

    <!-- Circular Arrows -->
    <g filter="url(#shadow)">
      <path d="M 340,230 Q 340,150 480,150 Q 620,150 620,230"
            stroke="#7B8FD4" stroke-width="22" fill="none"/>
      <polygon points="608,215 635,245 605,250" fill="#7B8FD4"/>
    </g>

    <!-- Center Label -->
    <text x="480" y="300" text-anchor="middle" font-size="26" font-weight="bold">
      Next Level
    </text>
    <text x="480" y="340" text-anchor="middle" font-size="36" font-weight="bold">
      AI
    </text>
  </svg>

thumbnail: thumbnails/cycle/cycle-4arrow1.png

expected_prompt: |
  4개의 요소가 순환하는 다이어그램 슬라이드를 만들어줘.
  - 중앙에 핵심 키워드 라벨
  - 4개의 곡선 화살표가 시계방향으로 순환
  - 각 모서리에 아이콘과 제목, 설명이 있는 카드
  - 보라색 계열의 화살표

prompt_keywords: ["순환", "4개", "화살표", "사이클", "프로세스"]
```

---

## 검증 체크리스트

### 필수 필드 확인

- [ ] `content_template.id` 존재 및 고유
- [ ] `content_template.version` = "3.0"
- [ ] `design_meta.design_intent` 유효한 카테고리
- [ ] `design_meta.quality_score` 0.0-10.0 범위
- [ ] `canvas.reference_width` 및 `reference_height` 존재
- [ ] `thumbnail` 경로 지정

### shapes[] 검증

- [ ] 모든 shape에 `id`, `type`, `geometry` 존재
- [ ] `geometry`에 `original_aspect_ratio` 포함
- [ ] text가 있는 shape에 `font_size_ratio`, `original_font_size_pt` 존재
- [ ] picture 타입에 `image.description` 필수 포함

### icons[] 검증

- [ ] 모든 icon에 `size` 또는 `size_ratio` 존재

### SVG 검증 (svg_inline 사용 시)

- [ ] 유효한 SVG 마크업
- [ ] `viewBox` 속성 존재
- [ ] 모든 색상이 시맨틱 토큰 또는 유효한 HEX

### 파일 검증

- [ ] YAML 파일 존재: `templates/contents/templates/{category}/{id}.yaml`
- [ ] 썸네일 존재: `templates/contents/thumbnails/{category}/{id}.png`
- [ ] 레지스트리 업데이트: `templates/contents/registry.yaml`
- [ ] YAML 문법 오류 없음
