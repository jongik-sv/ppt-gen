# Document + Content Integration Workflow

문서 양식(표지, 헤더, 풋터)은 유지하면서 본문 영역에 LLM이 디자인한 콘텐츠를 OOXML로 삽입하는 워크플로우.

## Triggers

- "동국시스템즈 양식으로 보고서 만들어줘"
- "회사 양식에 차트 슬라이드 추가해줘"
- "문서 양식 유지하면서 내용 넣어줘"

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 문서 양식 (기본양식.yaml)                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 표지 (Layout 1)      ← 제목, 부제목 텍스트만 교체         │ │
│ │ 간지 (Layout 2)      ← 섹션 번호, 제목만 교체             │ │
│ │ 내지 (Layout 3,4,5)  ← 제목 영역 + content_zone          │ │
│ │   ├─ main_title      : 플레이스홀더 텍스트 교체          │ │
│ │   ├─ action_title    : 플레이스홀더 텍스트 교체          │ │
│ │   └─ content_zone    : OOXML 콘텐츠 삽입                 │ │
│ │ 헤더/풋터            ← 자동 유지                         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ OOXML 삽입
┌─────────────────────────────────────────────────────────────┐
│ LLM 디자인 콘텐츠 (ooxml-generator.py)                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 콘텐츠 템플릿 참조 (llm_guide) → 디자인 결정              │ │
│ │ 데이터 바인딩 (data_slots) → 텍스트/값 채우기            │ │
│ │ OOXML 변환 (ooxml_export) → DrawingML 생성              │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 5-Stage Pipeline

### Stage 1: Setup

전역 설정 수집:

```json
{
  "presentation": {
    "title": "2024년 하반기 실적 보고",
    "topic": "실적 보고",
    "audience": "경영진",
    "document_type": "report"
  },
  "document_template": {
    "group": "dongkuk-systems",
    "template": "기본양식"
  },
  "theme": {
    "id": "dongkuk-systems",
    "colors": {
      "primary": "#002452",
      "secondary": "#C51F2A",
      ...
    }
  }
}
```

### Stage 2: Outline

슬라이드별 콘텐츠 계획:

```json
{
  "slides": [
    {
      "index": 0,
      "purpose": "cover",
      "title": "2024년 하반기 실적 보고",
      "subtitle": "경영기획팀 | 2024.12.15"
    },
    {
      "index": 1,
      "purpose": "section",
      "section_number": "01",
      "section_title": "매출 현황"
    },
    {
      "index": 2,
      "purpose": "chart",
      "title": "분기별 매출 추이",
      "action_title": "3분기 매출 전년 대비 23% 성장, 신사업 부문 견인",
      "content_type": "bar_chart",
      "key_points": ["1분기 1200억", "2분기 1500억", "3분기 1800억"]
    },
    {
      "index": 3,
      "purpose": "grid",
      "title": "주요 추진 과제",
      "action_title": "6대 전략 과제 중심 추진",
      "content_type": "card_grid",
      "element_count": 6
    }
  ]
}
```

### Stage 3: Matching

문서 레이아웃 + 콘텐츠 템플릿 매칭:

```json
{
  "slides": [
    {
      "index": 0,
      "layout_index": 1,
      "layout_category": "cover",
      "content_template": null
    },
    {
      "index": 1,
      "layout_index": 2,
      "layout_category": "section",
      "content_template": null
    },
    {
      "index": 2,
      "layout_index": 4,
      "layout_category": "content_visual",
      "content_template": "deepgreen-chart-bar1",
      "match_score": 0.92
    },
    {
      "index": 3,
      "layout_index": 4,
      "layout_category": "content_visual",
      "content_template": "deepgreen-grid-3col1",
      "match_score": 0.88
    }
  ]
}
```

**레이아웃 선택 규칙** (기본양식.yaml의 selection_guide 참조):

| purpose | layout_index | layout_category |
|---------|--------------|-----------------|
| cover | 1 | cover |
| section, toc | 2 | section |
| text, bullets | 3 | content_text |
| chart, diagram, grid, timeline | 4 | content_visual |
| simple, reference | 5 | content_simple |

### Stage 4: Content Generation

각 슬라이드에 대해 콘텐츠 생성:

#### 4.1 표지/간지 슬라이드 (플레이스홀더만 교체)

```json
{
  "slide_index": 0,
  "placeholder_bindings": {
    "cover_title": "2024년 하반기 실적 보고",
    "cover_subtitle": "경영기획팀 | 2024.12.15"
  }
}
```

#### 4.2 내지 슬라이드 (content_zone에 OOXML 삽입)

```json
{
  "slide_index": 2,
  "placeholder_bindings": {
    "main_title": "분기별 매출 추이",
    "action_title": "3분기 매출 전년 대비 23% 성장, 신사업 부문 견인"
  },
  "content_zone_data": {
    "template": "deepgreen-chart-bar1",
    "data": {
      "chart_data": {
        "categories": ["1분기", "2분기", "3분기"],
        "series": [
          {"name": "매출", "values": [1200, 1500, 1800], "color": "primary"}
        ]
      }
    }
  }
}
```

```json
{
  "slide_index": 3,
  "placeholder_bindings": {
    "main_title": "주요 추진 과제",
    "action_title": "6대 전략 과제 중심 추진"
  },
  "content_zone_data": {
    "template": "deepgreen-grid-3col1",
    "data": {
      "cards": [
        {"number": "1", "title": "디지털 전환", "description": "클라우드 마이그레이션 완료"},
        {"number": "2", "title": "ESG 경영", "description": "탄소 배출량 20% 감축"},
        {"number": "3", "title": "신사업 확대", "description": "친환경 철강 라인 증설"},
        {"number": "4", "title": "인재 확보", "description": "핵심 인력 50명 채용"},
        {"number": "5", "title": "품질 혁신", "description": "불량률 0.1% 이하 달성"},
        {"number": "6", "title": "고객 만족", "description": "NPS 80점 이상 달성"}
      ]
    }
  }
}
```

### Stage 5: PPTX Generation

#### 5.1 문서 양식 PPTX 복사

```bash
# 원본 양식 PPTX를 작업 디렉토리로 복사
cp "원본양식.pptx" "output/working.pptx"
```

#### 5.2 슬라이드 구성

```python
# 필요한 레이아웃의 슬라이드만 선택하여 재구성
# rearrange.py 사용
python scripts/rearrange.py working.pptx layout_indices.json
```

#### 5.3 플레이스홀더 텍스트 교체

```bash
# inventory.py로 플레이스홀더 위치 추출
python scripts/inventory.py working.pptx > inventory.json

# replace.py로 텍스트 교체
python scripts/replace.py working.pptx replacements.json output.pptx
```

**replacements.json 형식:**

```json
{
  "slide-0": {
    "shape-title": {
      "paragraphs": [
        {"text": "2024년 하반기 실적 보고", "level": 0}
      ]
    }
  }
}
```

#### 5.4 content_zone에 OOXML 삽입

```bash
# OOXML 생성
python scripts/ooxml-generator.py \
  templates/contents/templates/grid/deepgreen-grid-3col1.yaml \
  templates/documents/dongkuk-systems/기본양식.yaml \
  slide_3_data.json \
  slide_3_content.xml

# PPTX 언팩
python ooxml/scripts/unpack.py output.pptx unpacked/

# 슬라이드 XML에 콘텐츠 삽입
# slide3.xml의 <p:spTree>에 생성된 콘텐츠 추가

# PPTX 재팩
python ooxml/scripts/pack.py unpacked/ final.pptx
```

## Content Template Selection

### llm_guide 활용

콘텐츠 템플릿의 `llm_guide` 섹션을 참조하여 적절한 템플릿 선택:

```yaml
# templates/contents/templates/grid/deepgreen-grid-3col1.yaml

llm_guide:
  description: |
    6개의 카드로 구성된 3열 그리드 레이아웃.

  best_for:
    - 단계별 프로세스 설명 (6단계)
    - 기능/특징 나열

  avoid_for:
    - 5개 이하의 항목 (빈 카드 발생)
    - 7개 이상의 항목 (공간 부족)

  element_count:
    fixed: 6

  data_slots:
    - slot_id: cards
      type: array
      count: 6
      item_schema:
        - field: number
        - field: title
        - field: description
```

### 선택 알고리즘

```python
def select_content_template(purpose, element_count, data_type):
    """콘텐츠 유형에 맞는 템플릿 선택"""

    if purpose == "chart":
        if data_type == "bar":
            return "deepgreen-chart-bar1"
        elif data_type == "line":
            return "deepgreen-chart-line1"

    elif purpose == "grid":
        if element_count == 6:
            return "deepgreen-grid-3col1"
        elif element_count == 4:
            return "deepgreen-grid-icon1"

    elif purpose == "timeline":
        return "deepgreen-timeline1"

    elif purpose == "comparison":
        return "deepgreen-comparison-image1"

    return None  # LLM이 직접 디자인
```

## Theme Color Token Resolution

문서 양식의 테마 색상을 콘텐츠에 적용:

```python
# templates/documents/dongkuk-systems/config.yaml
theme:
  colors:
    primary: '#002452'
    secondary: '#C51F2A'
    accent: '#A1BFB4'
    dark: '#153325'

# 콘텐츠 템플릿의 style_tokens
style_tokens:
  primary_bg: primary    # → '#002452'
  accent_bg: accent      # → '#A1BFB4'
```

## Output Structure

```
output/{session-id}/
├── session.json
├── stage-1-setup.json
├── stage-2-outline.json
├── stage-3-matching.json
├── stage-4-content.json
├── stage-5-generation.json
├── slides/
│   ├── slide-002-data.json      # content_zone 데이터
│   ├── slide-002-content.xml    # 생성된 OOXML
│   └── slide-003-data.json
├── unpacked/                     # OOXML 작업 디렉토리
└── output.pptx
```

## Validation

### 1. 플레이스홀더 텍스트 검증

```bash
# 텍스트 오버플로우 검사
python scripts/inventory.py output.pptx --issues-only
```

### 2. 시각적 검증

```bash
# 썸네일 생성
python scripts/thumbnail.py output.pptx thumbnails/ --cols 4
```

### 3. OOXML 유효성 검사

```bash
# XML 스키마 검증
python ooxml/scripts/validate.py output.pptx
```

## Error Handling

| 에러 | 원인 | 해결 |
|------|------|------|
| `content_zone not found` | Layout 3,5는 content_zone 없음 | Layout 4 사용 |
| `element_count mismatch` | 데이터 개수와 템플릿 불일치 | 템플릿 변경 또는 데이터 조정 |
| `text overflow` | 텍스트가 플레이스홀더 초과 | constraints 확인 후 텍스트 축약 |
