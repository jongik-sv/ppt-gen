# content-extract 워크플로우

슬라이드 콘텐츠 디자인 추출 (YAML + HTML + OOXML 3가지 포맷).

## 트리거

- "이 슬라이드 저장해줘"
- "이 디자인 저장해줘"

## 입력

- PPTX 파일 + 슬라이드 번호
- 또는 이미지 파일 (HTML만 생성)

## 출력

- `templates/contents/{category}/{template_id}/`
  - `template.yaml` - 슬롯 정의, 시맨틱 설명, **출처 정보 필수**
  - `template.html` - Handlebars 템플릿 (**콘텐츠 영역만**)
  - `template.ooxml/` - 원본 XML (**필수**)
  - `example.html` - 샘플 데이터 적용 미리보기 (**필수**)
- `templates/thumbnails/contents/{category}/{template_id}.png` - 썸네일

---

## ⚠️ 중요: 헤더/푸터 제외 규칙

### 영역 구분

```
┌──────────────────────────────────────┐
│ HEADER ZONE (상단 ~22%)               │  ← ❌ 추출 제외 (문서 양식에서 관리)
│   - 슬라이드 제목 (page_title)        │
│   - 부제목/액션 타이틀 (page_subtitle) │
│   - 액센트 도형 (직사각형 2개 등)      │
├──────────────────────────────────────┤
│                                      │
│        CONTENT ZONE (22% ~ 90%)      │  ← ✅ 추출 대상
│                                      │
├──────────────────────────────────────┤
│ FOOTER ZONE (하단 ~8%)                │  ← ❌ 추출 제외 (문서 양식에서 관리)
│   - 저작권 텍스트                     │
│   - 페이지 번호                       │
└──────────────────────────────────────┘
```

### 추출 제외 항목 (일반 내지)

| 항목 | 예시 | 이유 |
|------|------|------|
| **헤더 제목** | "제목을 입력해 주세요." | 문서 양식에서 관리 |
| **헤더 부제목** | "간략한 설명을 적어주세요." | 문서 양식에서 관리 |
| **헤더 액센트** | 좌상단 직사각형 2개 | 문서 양식에서 관리 |
| **저작권** | "© YEONDU-UNNIE POWERPOINT..." | 문서 양식에서 관리 |
| **원본 로고** | 회사 로고, 워터마크 | 문서 양식에서 관리 |

### 예외: 전체 슬라이드가 콘텐츠인 카테고리

| 카테고리 | 이유 | 추출 범위 |
|----------|------|----------|
| `cover` | 표지 전용 슬라이드 | **전체** (헤더 포함) |
| `toc` | 목차 전용 슬라이드 | **전체** (헤더 포함) |
| `divider` | 섹션 구분 전용 슬라이드 | **전체** (헤더 포함) |
| `closing` | 마무리 전용 슬라이드 | **전체** (헤더 포함) |

---

## ⚠️ 콘텐츠 크기 표준 (필수)

모든 콘텐츠 템플릿은 `layout.dimensions` 필드를 **필수**로 포함해야 합니다.

### 크기 정의

| 추출 범위 | 플래그 | 크기 | 적용 카테고리 |
|----------|--------|------|--------------|
| **콘텐츠 영역만** | `content_only: true` | 1920 × 734px | diagram, grid, list, chart, process, timeline, infographic, image |
| **전체 슬라이드** | `full_slide: true` | 1920 × 1080px | cover, toc, divider, closing |

### template.yaml 필수 형식

```yaml
layout:
  type: {카테고리}
  structure: {구조명}
  content_only: true       # 또는 full_slide: true
  dimensions:              # ⚠️ 필수
    width: 1920px
    height: 734px          # content_only일 때 (또는 1080px for full_slide)
```

### template.html CSS 규칙

```css
/* 콘텐츠 영역만 (content_only: true) */
.content {
  width: 1920px;
  height: 734px;  /* 1080px * 0.68 = 734px */
}

/* 전체 슬라이드 (full_slide: true) */
.slide {
  width: 1920px;
  height: 1080px;
}
```

---

## 프로세스

### 1. 슬라이드 파싱

```bash
python scripts/slide-crawler.py input.pptx --slide 3 --content-only --output working/parsed.json
```

### 2. 콘텐츠 분석 (헤더/푸터 제외)

```bash
python scripts/content-analyzer.py working/parsed.json --output working/analysis.json
```

**분석 시 제외할 도형:**
- Y좌표 < 22% (상단 헤더)
- Y좌표 > 90% (하단 푸터)
- 저작권 텍스트 포함 도형
- "제목을 입력", "간략한 설명" 등 헤더 플레이스홀더

분석 결과:
- 텍스트 그룹 후보 (리스트, 그리드 패턴)
- 플레이스홀더 후보
- 레이아웃 패턴 (grid, list, single)

### 3. LLM 플레이스홀더 판단

LLM에게 전달:

```bash
python scripts/content-analyzer.py working/parsed.json --prompt
```

LLM 응답 형식:

```json
{
  "placeholders": [
    { "id": "items", "type": "array", "shapes": ["shape-1", "shape-2", "shape-3"],
      "item_schema": { "icon": "image", "title": "string", "description": "string" }
    }
  ],
  "category": "grid",
  "semantic_description": "3개 아이콘 카드가 균등 배치..."
}
```

**주의:** page_title, page_subtitle 등 헤더 관련 플레이스홀더는 **포함하지 않음**

---

## ⚠️ 중요: 아이콘/이미지 플레이스홀더 규칙

### 아이콘이 있던 자리 처리

원본 PPT에서 아이콘/이미지가 있던 위치는 **반드시 플레이스홀더로 변환**:

```yaml
# template.yaml
placeholders:
  - name: items
    type: array
    item_schema:
      - name: icon           # 아이콘 플레이스홀더 필수
        type: image
        required: false      # 선택적 (없을 수 있음)
        default: null
      - name: title
        type: text
```

```html
<!-- template.html -->
<div class="card">
  {{#if this.icon}}
  <img class="icon" src="{{this.icon}}" alt="" />
  {{else}}
  <div class="icon-placeholder"></div>  <!-- 빈 플레이스홀더 -->
  {{/if}}
  <h3>{{this.title}}</h3>
</div>
```

### 아이콘 플레이스홀더 유형

| 원본 요소 | 플레이스홀더 타입 | 설명 |
|----------|------------------|------|
| SVG 아이콘 | `image` | 벡터 아이콘 |
| PNG/JPG 아이콘 | `image` | 래스터 아이콘 |
| 빈 원형/도형 (아이콘 컨테이너) | `image` | 아이콘이 들어갈 자리 |
| SmartArt 내부 그래픽 | `image` | SmartArt 아이콘 |
| 그룹 내 이미지 | `image` | 그룹화된 아이콘 |

### 아이콘 추출 규칙

1. **원본 아이콘이 있는 경우**:
   - `templates/contents/{id}/assets/` 폴더에 저장
   - 플레이스홀더의 `default` 값으로 경로 지정

2. **원본 아이콘이 없는 경우 (빈 컨테이너)**:
   - 플레이스홀더만 정의, `default: null`

3. **반복 패턴의 아이콘**:
   - 배열 item_schema에 `icon` 필드 추가
   - 각 항목마다 개별 아이콘 지정 가능

```yaml
# 예시: 아이콘이 있는 3개 카드
placeholders:
  - name: cards
    type: array
    min: 2
    max: 4
    item_schema:
      - name: icon
        type: image
        required: false
        description: "카드 상단 아이콘"
      - name: title
        type: text
        required: true
      - name: description
        type: text
        required: false
    sample:
      - { icon: "assets/icon-1.svg", title: "제목 1", description: "설명 1" }
      - { icon: "assets/icon-2.svg", title: "제목 2", description: "설명 2" }
      - { icon: null, title: "제목 3", description: "설명 3" }  # 아이콘 없음
```

---

### 4. 패턴 분석 및 통합 확인

```bash
python scripts/template-analyzer.py working/analysis.json --source "dongkuk" --compare templates/contents/ --output working/pattern.json
```

같은 출처에서 유사한 패턴이면 **가변 템플릿(variants)** 으로 통합.

### 5. 3가지 포맷 생성

LLM이 직접 생성:

#### template.yaml (헤더 플레이스홀더 없음)

```yaml
id: grid-cards-01
name: 그리드 아이콘 카드
category: grid
pattern: grid-icon-cards
description: 2~6개 아이콘 카드 그리드 (콘텐츠 영역만)

source:
  file: "깔끔이 딥그린.pptx"
  slide: 5
  extracted_at: "2026-01-11"

quality: high
theme: deep-green

layout:
  type: grid
  structure: icon-cards
  content_only: true  # 콘텐츠 영역만 (헤더 제외)
  dimensions:         # ⚠️ 필수: 콘텐츠 크기 명시
    width: 1920px
    height: 734px     # 콘텐츠 영역 (1080 * 0.68)

# ⚠️ 헤더 플레이스홀더 없음 (page_title, page_subtitle 없음)
placeholders:
  - name: items
    type: array
    min: 2
    max: 6
    item_schema:
      - { name: icon, type: image }
      - { name: title, type: text }
      - { name: description, type: text }

semantic_description: |
  2~4개 동일 크기 카드가 가로 균등 배치된 그리드 레이아웃.

  **캔버스:**
  - 콘텐츠 영역: 1920 × 734px
  - 배경: {{theme.background.light}} (밝은 배경)

  **레이아웃 구조 (CSS Grid):**
  - 그리드: 4열, gap 40px
  - 카드 너비: 각 22% (약 422px)
  - 좌우 마진: 3% (약 58px)

  **카드 스타일:**
  - 크기: 422 × 520px
  - 배경: {{theme.gradient.primary}} (녹색 계열)
  - border-radius: 16px
  - box-shadow: 0 4px 12px rgba(0,0,0,0.08)

  **카드 내부 구성:**
  1. **상단 아이콘 영역 (25%):**
     - 배경: {{theme.muted.light}} (연한 색)
     - 아이콘 크기: 64 × 64px
  2. **중앙 타이틀 (15%):**
     - 폰트: {{theme.fonts.heading}}, 20px, bold
     - 색상: {{theme.colors.secondary}}
  3. **하단 설명 (50%):**
     - 폰트: {{theme.fonts.body}}, 14px
     - 색상: white
     - line-height: 1.6
  4. **번호 뱃지 (하단 중앙):**
     - 원형, 48px
     - 배경: white
     - 텍스트: {{theme.colors.primary}}, bold

  **디자인 토큰 매핑:**
  - 카드 배경: gradient-3 → gradient-6 (좌→우 그라데이션)
  - 텍스트 강조: muted-1
  - 구분선: muted-5

match_keywords: [그리드, 카드, 아이콘, 서비스, 4열]
```

---

## ⚠️ semantic_description 작성 가이드 (필수)

`semantic_description`은 **HTML/CSS로 재현 가능한 수준**으로 상세하게 작성해야 합니다.

### 필수 포함 항목

| 섹션 | 필수 정보 | 예시 |
|------|----------|------|
| **캔버스** | 크기, 배경색 | `1920 × 734px`, `{{theme.background.light}}` |
| **레이아웃** | 구조, 방향, 간격 | `CSS Grid 4열`, `Flexbox Row`, `gap: 40px` |
| **각 요소 크기** | 너비, 높이 (px 또는 %) | `카드: 422 × 520px` |
| **스타일 속성** | border-radius, shadow | `border-radius: 16px` |
| **색상 (토큰)** | 디자인 토큰 참조 | `{{theme.gradient.primary}}` |
| **타이포그래피** | 폰트, 크기, 굵기 | `{{theme.fonts.heading}}, 20px, bold` |

### 색상 작성 규칙 (디자인 토큰 필수)

**❌ 하드코딩 금지:**
```yaml
# 잘못된 예시
색상: #22523B
배경: #153325
```

**✅ 디자인 토큰 사용:**
```yaml
# 올바른 예시
색상: {{theme.colors.primary}}
배경: {{theme.gradient.dark}}
강조: {{theme.muted.aqua}}
```

### 사용 가능한 디자인 토큰

```yaml
# 주요 색상
{{theme.colors.primary}}      # 메인 색상
{{theme.colors.secondary}}    # 보조 색상
{{theme.colors.accent}}       # 강조 색상

# 그라데이션 (6단계, 진함→밝음)
{{theme.gradient.dark}}       # gradient-1
{{theme.gradient.deep}}       # gradient-2
{{theme.gradient.primary}}    # gradient-3
{{theme.gradient.accent}}     # gradient-4
{{theme.gradient.medium}}     # gradient-5
{{theme.gradient.light}}      # gradient-6

# 보조색 (7단계, 진함→밝음)
{{theme.muted.dark}}          # muted-1
{{theme.muted.green}}         # muted-2
{{theme.muted.sage}}          # muted-3
{{theme.muted.mint}}          # muted-4
{{theme.muted.aqua}}          # muted-5
{{theme.muted.pale}}          # muted-6
{{theme.muted.light}}         # muted-7

# 배경
{{theme.background.dark}}
{{theme.background.light}}
{{theme.background.neutral}}

# 폰트
{{theme.fonts.display}}       # 큰 제목
{{theme.fonts.heading}}       # 헤딩
{{theme.fonts.body}}          # 본문
{{theme.fonts.accent}}        # 강조
```

### 상세 예시 (매트릭스 다이어그램)

```yaml
semantic_description: |
  2x2 매트릭스 다이어그램과 설명 텍스트가 좌우로 배치된 전략 슬라이드.

  **캔버스:**
  - 콘텐츠 영역: 1920 × 734px
  - 배경: white

  **레이아웃 구조 (Flexbox Row):**

  1. **좌측 매트릭스 섹션 (45%):**
     - 2x2 Grid (gap: 15px)
     - 박스 크기: 180 × 180px, border-radius: 24px
     - 박스 색상 (좌상→우하):
       * 좌상: {{theme.muted.dark}} - 흰색 텍스트
       * 우상: {{theme.muted.green}} - 흰색 텍스트
       * 좌하: {{theme.muted.aqua}} - {{theme.colors.secondary}} 텍스트
       * 우하: {{theme.muted.light}} - {{theme.colors.secondary}} 텍스트
     - **십자 화살표 오버레이:**
       * 축: 3px, {{theme.colors.secondary}}
       * 화살표 머리: CSS border로 구현
       * 중앙 원: 12px, {{theme.colors.secondary}}

  2. **중앙 구분선:**
     - 너비: 2px, 높이: 60%
     - 색상: {{theme.colors.accent}}, opacity: 0.6
     - 마진: 60px

  3. **우측 콘텐츠 섹션 (45%):**
     - **메인 타이틀:**
       * 폰트: {{theme.fonts.display}}, 32px, bold
       * 색상: {{theme.colors.secondary}}
     - **콘텐츠 블록 (2개):**
       * 아이콘: FontAwesome, 22px, {{theme.colors.accent}}
       * 블록 타이틀: {{theme.fonts.heading}}, 20px, bold
       * 본문: {{theme.fonts.body}}, 15px, line-height: 1.8
       * 키워드 강조: {{theme.colors.accent}}, font-weight: 500
```

---

## ⚠️ 테마 교체 가능한 디자인 시스템 (필수)

콘텐츠 템플릿은 **다른 테마로 교체 가능**하도록 설계해야 합니다.

### 핵심 원칙

1. **하드코딩 금지**: 색상, 폰트를 직접 코드에 쓰지 않음
2. **CSS 변수 사용**: 모든 스타일 값을 CSS 변수로 참조
3. **Handlebars 바인딩**: 테마 값은 `{{theme.xxx}}`로 주입

### 테마 교체 흐름

```
테마 파일 (theme.yaml)     템플릿 (template.html)      최종 출력
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ colors:         │       │ :root {         │       │ :root {         │
│   primary: "#22 │  ───► │   --primary:    │  ───► │   --primary:    │
│               ..." │    │     {{theme... }}│       │     #22523B;    │
└─────────────────┘       └─────────────────┘       └─────────────────┘
     deep-green                 템플릿                   렌더링 결과
```

---

#### template.html (콘텐츠 영역만, 734px 높이)

**⚠️ 모든 색상/폰트는 CSS 변수로 정의하고, Handlebars로 테마 값을 주입**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1920, height=734">
  <title>{{template_name}}</title>
  <style>
    /* ========================================
       테마 변수 정의 (Handlebars 바인딩)
       ⚠️ 색상/폰트를 직접 쓰지 말고 변수 사용
       ======================================== */
    :root {
      /* 주요 색상 */
      --color-primary: {{theme.colors.primary}};
      --color-secondary: {{theme.colors.secondary}};
      --color-accent: {{theme.colors.accent}};

      /* 그라데이션 팔레트 (6단계) */
      --gradient-1: {{theme.gradient.dark}};
      --gradient-2: {{theme.gradient.deep}};
      --gradient-3: {{theme.gradient.primary}};
      --gradient-4: {{theme.gradient.accent}};
      --gradient-5: {{theme.gradient.medium}};
      --gradient-6: {{theme.gradient.light}};

      /* 보조색 팔레트 (7단계) */
      --muted-1: {{theme.muted.dark}};
      --muted-2: {{theme.muted.green}};
      --muted-3: {{theme.muted.sage}};
      --muted-4: {{theme.muted.mint}};
      --muted-5: {{theme.muted.aqua}};
      --muted-6: {{theme.muted.pale}};
      --muted-7: {{theme.muted.light}};

      /* 배경 */
      --bg-dark: {{theme.background.dark}};
      --bg-light: {{theme.background.light}};
      --bg-neutral: {{theme.background.neutral}};

      /* 폰트 */
      --font-display: {{theme.fonts.display}};
      --font-heading: {{theme.fonts.heading}};
      --font-body: {{theme.fonts.body}};
      --font-accent: {{theme.fonts.accent}};

      /* 스타일 */
      --radius: 16px;
      --shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    /* 콘텐츠 영역 (1920 × 734px) */
    .content {
      width: 1920px;
      height: 734px;
      background: var(--bg-light);
      font-family: var(--font-body), 'Noto Sans KR', sans-serif;
      position: relative;
    }

    /* ========================================
       ⚠️ 모든 스타일에서 CSS 변수 사용
       색상: var(--color-primary), var(--gradient-3)
       폰트: var(--font-heading)
       ======================================== */
    .card-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 40px;
      padding: 60px;
    }

    .card {
      background: var(--gradient-3);  /* ✅ CSS 변수 사용 */
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 32px;
      color: white;
    }

    .card h3 {
      font-family: var(--font-heading);  /* ✅ 폰트 변수 */
      font-size: 20px;
      font-weight: bold;
      color: white;
      margin-bottom: 16px;
    }

    .card p {
      font-size: 14px;
      line-height: 1.6;
    }

    .card .number {
      width: 48px;
      height: 48px;
      background: white;
      color: var(--color-primary);  /* ✅ 테마 색상 */
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
    }

    /* 카드별 색상 그라데이션 (좌→우 진함→밝음) */
    .card:nth-child(1) { background: var(--gradient-3); }
    .card:nth-child(2) { background: var(--gradient-4); }
    .card:nth-child(3) { background: var(--gradient-5); }
    .card:nth-child(4) { background: var(--gradient-6); }
  </style>
</head>
<body>
  <!-- ⚠️ 헤더 없음 (문서 양식에서 관리) -->
  <div class="content">
    <div class="card-grid">
      {{#each items}}
      <div class="card">
        {{#if this.icon}}
        <img class="icon" src="{{this.icon}}" alt="" />
        {{/if}}
        <h3>{{this.title}}</h3>
        <p>{{this.description}}</p>
        <div class="number">{{this.number}}</div>
      </div>
      {{/each}}
    </div>
  </div>
</body>
</html>
```

### CSS 작성 규칙 체크리스트

| 항목 | ❌ 금지 | ✅ 올바른 방법 |
|------|--------|---------------|
| 색상 | `color: #22523B;` | `color: var(--color-primary);` |
| 배경 | `background: #153325;` | `background: var(--gradient-1);` |
| 폰트 | `font-family: 'Noto Sans';` | `font-family: var(--font-body);` |
| 그림자 | 인라인 rgba 값 | `box-shadow: var(--shadow);` |

### 테마 교체 테스트

템플릿이 테마 독립적으로 작동하는지 확인:

```bash
# deep-green 테마로 렌더링
ppt-gen render template.html --theme deep-green --output preview-green.html

# 다른 테마로 렌더링 (테마 교체 테스트)
ppt-gen render template.html --theme corporate-blue --output preview-blue.html
```

두 결과물이 각 테마의 색상/폰트를 올바르게 반영해야 합니다.

---

#### template.ooxml

원본 XML에서 **콘텐츠 영역의 도형만** 추출:
- 헤더 영역(Y < 22%) 도형 제외
- 푸터 영역(Y > 90%) 도형 제외

```xml
<!-- 콘텐츠 영역 도형만 포함 -->
<p:sp>
  <p:txBody>
    <a:p><a:r><a:t>__SLOT_items[0].title__</a:t></a:r></a:p>
  </p:txBody>
</p:sp>
```

### 6. OOXML 추출 (필수, 콘텐츠 영역만)

```bash
python scripts/ooxml_extractor.py input.pptx --slide 3 --content-only --output templates/contents/grid/grid-cards-01/template.ooxml
```

### 7. example.html 생성 (필수)

template.html의 Handlebars 변수를 sample 데이터로 치환.
**원본 PPT의 플레이스홀더 텍스트를 그대로 사용.**

### 8. 썸네일 생성 (원본 PPTX에서)

```bash
python scripts/thumbnail.py input.pptx --slide 5 --size theme --output templates/thumbnails/contents/grid/grid-cards-01.png
```

> ⚠️ 썸네일은 **원본 PPTX 슬라이드**에서 직접 캡처.
> example.html이 아닌 원본 이미지를 사용해야 비교/검증 가능.

### 9. 레지스트리 업데이트

`templates/contents/grid/registry.yaml`에 항목 추가.

---

## 오브젝트 자동 추출

분석 중 복잡한 도형 감지 시 자동으로 `objects/`에 분리 저장:

감지 조건:
- 도형 그룹 5개 이상
- 비선형 배치 (원형, 방사형)
- 커넥터 포함
- 차트/다이어그램

```
content-extract 실행
    │
    ├── 일반 레이아웃 → contents/{category}/
    │
    └── 복잡한 도형 감지 → objects/{category}/
```

---

## 추출 모드

| 모드 | 추출 범위 | 용도 | 카테고리 |
|------|----------|------|----------|
| `full` | 전체 슬라이드 | 표지, 목차, 구분선, 클로징 | cover, toc, divider, closing |
| `content_only` | 콘텐츠 영역만 (헤더/푸터 제외) | **일반 내지** | 그 외 모든 카테고리 |

**기본값: `content_only`**

---

## 좌표 시스템

모든 위치/크기는 **vmin 기준**으로 저장:

```yaml
geometry:
  x: "10vmin"
  y: "10vmin"
  cx: "20vmin"
  cy: "20vmin"
  emu: { x: 914400, y: 914400, cx: 1828800, cy: 1828800 }
```

vmin = min(slide_width, slide_height)

슬라이드 비율이 변경되어도 원형은 원형, 정사각형은 정사각형 유지.

---

## 추출 완료 체크리스트

각 슬라이드 추출 시 아래 항목을 모두 확인:

- [ ] **template.yaml** 생성 완료
  - [ ] `source.file`: 원본 파일명
  - [ ] `source.slide`: 슬라이드 번호 (1-based)
  - [ ] `source.extracted_at`: 추출 일시
  - [ ] `quality: high`
  - [ ] `layout.content_only: true` (일반 내지인 경우)
  - [ ] ❌ **page_title, page_subtitle 플레이스홀더 없음** (일반 내지)
- [ ] **template.html** 생성 완료
  - [ ] 콘텐츠 영역만 (1920x734px)
  - [ ] ❌ **헤더 영역 없음** (일반 내지)
- [ ] **template.ooxml/** 추출 완료 (필수)
  - [ ] slide.xml (콘텐츠 영역 도형만)
  - [ ] _rels/slide.xml.rels
  - [ ] media/ (이미지 있는 경우)
- [ ] **example.html** 생성 완료
  - [ ] 원본 플레이스홀더 텍스트 그대로 사용
- [ ] **썸네일** 생성 완료 (원본 PPTX에서 캡처)
  - [ ] `templates/thumbnails/contents/{category}/{id}.png`
  - [ ] 320x180px 크기

**⚠️ 누락 시 추출 실패로 간주**

> 썸네일은 원본 PPTX 슬라이드에서 직접 캡처해야 함.
> example.html 캡처가 아닌 **원본 이미지**를 사용해야 비교/검증 가능.
