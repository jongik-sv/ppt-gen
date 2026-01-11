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
  2~6개 동일 크기 카드가 가로 균등 배치.
  각 카드는 둥근 모서리(16px)와 그림자.
  헤더(제목/부제목)는 문서 양식에서 관리.

match_keywords: [그리드, 카드, 아이콘, 서비스]
```

#### template.html (콘텐츠 영역만, 734px 높이)

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    :root {
      --primary: {{theme.primary}};
      --secondary: {{theme.secondary}};
    }
    /* 콘텐츠 영역만 (22% ~ 90%) = 1080 * 0.68 = 734px */
    .content {
      width: 1920px;
      height: 734px;
      background: white;
    }
    .card {
      background: white;
      border-radius: 16px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
  </style>
</head>
<body>
  <!-- ⚠️ 헤더 없음 (문서 양식에서 관리) -->
  <div class="content">
    <div class="card-grid">
      {{#each items}}
      <div class="card">
        <img src="{{this.icon}}" />
        <h3>{{this.title}}</h3>
        <p>{{this.description}}</p>
      </div>
      {{/each}}
    </div>
  </div>
</body>
</html>
```

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
