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
  - `template.yaml` - 슬롯 정의, 시맨틱 설명
  - `template.html` - Handlebars 템플릿
  - `template.ooxml` - 원본 XML (PPTX에서만)
  - `thumbnail.png` - 미리보기

## 프로세스

### 1. 슬라이드 파싱

```bash
python scripts/slide-crawler.py input.pptx --slide 3 --content-only --output working/parsed.json
```

### 2. 콘텐츠 분석

```bash
python scripts/content-analyzer.py working/parsed.json --output working/analysis.json
```

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
    { "id": "title", "type": "text", "shapes": ["shape-0"] },
    { "id": "items", "type": "array", "shapes": ["shape-1", "shape-2", "shape-3"],
      "item_schema": { "icon": "image", "title": "string", "description": "string" }
    }
  ],
  "category": "grid",
  "semantic_description": "상단에 제목, 하단에 3개 아이콘 카드가 균등 배치..."
}
```

### 4. 패턴 분석 및 통합 확인

```bash
python scripts/template-analyzer.py working/analysis.json --source "dongkuk" --compare templates/contents/ --output working/pattern.json
```

같은 출처에서 유사한 패턴이면 **가변 템플릿(variants)** 으로 통합.

### 5. 3가지 포맷 생성

LLM이 직접 생성:

#### template.yaml

```yaml
id: dongkuk-grid-cards-01
category: grid
pattern: grid-icon-cards
element_count: "2-6"

document_style: dongkuk
has_ooxml: true

variants:
  - count: 3
    layout: { columns: 3, gap: "4%" }
  - count: 4
    layout: { columns: 4, gap: "3%" }

slots:
  - name: title
    type: text
    required: true
  - name: items
    type: array
    min: 2
    max: 6
    item_schema:
      - { name: icon, type: image }
      - { name: title, type: text }
      - { name: description, type: text }

semantic_description: |
  슬라이드 상단에 왼쪽 정렬된 큰 제목(48px, bold).
  하단에 2~6개 동일 크기 카드가 가로 균등 배치.
  각 카드는 둥근 모서리(16px)와 그림자.

match_keywords: [그리드, 카드, 아이콘, 서비스]
```

#### template.html

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    :root {
      --primary: {{theme.primary}};
      --background: {{theme.background}};
    }
    .slide { width: 1920px; height: 1080px; }
    .card {
      background: white;
      border-radius: 16px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
  </style>
</head>
<body>
  <div class="slide">
    <h2>{{title}}</h2>
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

원본 XML에서 텍스트를 Handlebars 마커로 치환:

```xml
<p:sp>
  <p:txBody>
    <a:p><a:r><a:t>{{title}}</a:t></a:r></a:p>
  </p:txBody>
</p:sp>

<!-- 배열 항목 -->
<p:sp>
  <p:txBody>
    <a:p><a:r><a:t>__SLOT_items[0].title__</a:t></a:r></a:p>
  </p:txBody>
</p:sp>
```

### 6. 썸네일 생성

```bash
python scripts/thumbnail.py input.pptx --slide 3 --output templates/contents/grid/dongkuk-grid-cards-01/thumbnail.png
```

### 7. 레지스트리 업데이트

`templates/contents/grid/registry.yaml`에 항목 추가.

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

## 추출 모드

| 모드 | 추출 범위 | 용도 |
|------|----------|------|
| `full` | 전체 슬라이드 | 표지, 목차, 클로징 |
| `content_only` | 콘텐츠 영역만 | 일반 내지 |

기본값: `content_only`

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
