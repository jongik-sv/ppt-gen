# Template-Based Creation Workflow

기존 템플릿을 사용하여 새 PPT를 생성합니다.

---

## Stage JSON 저장 규칙 (MANDATORY)

**PPT 생성 파이프라인은 5단계로 진행되며, 각 단계 완료 시 JSON 파일을 저장합니다.**

### 핵심 원칙: 누적 저장

**각 stage-N.json은 반드시 stage-1부터 stage-N까지의 모든 데이터를 포함해야 합니다.**

```
output/{session-id}/
├── stage-1-setup.json      # session + setup
├── stage-2-outline.json    # session + setup + slides(outline)
├── stage-3-matching.json   # session + setup + slides(outline + matching)
├── stage-4-content.json    # session + setup + slides(outline + matching + content)
├── stage-5-generation.json # session + setup + slides(전체) + output
├── slides/                 # HTML/OOXML 파일들
└── output.pptx             # 최종 결과물
```

### 단계별 필수 포함 데이터

| Stage | 파일명 | 필수 포함 데이터 |
|-------|-------|----------------|
| 1 | stage-1-setup.json | `session`, `setup` (theme, presentation, document_template) |
| 2 | stage-2-outline.json | 위 + `slides[]` (index, title, purpose, key_points, layout_category) |
| 3 | stage-3-matching.json | 위 + slides에 `template_id`, `match_score`, `content_template` 추가 |
| 4 | stage-4-content.json | 위 + slides에 `placeholder_bindings`, `content_design`, `ooxml_file` 추가 |
| 5 | stage-5-generation.json | 위 + slides에 `generated` 추가, `output` 섹션 |

### 올바른 예시 (stage-4-content.json)

```json
{
  "session": {
    "id": "2026-01-09_100000_a1b2c3d4",
    "title": "프로젝트 수행계획서",
    "status": "in_progress"
  },
  "current_stage": 4,
  "setup": {
    "presentation": { "title": "...", "audience": "혼합" },
    "theme": { "id": "deepgreen" },
    "document_template": { "group": "dongkuk-systems", "template": "기본양식" }
  },
  "slides": [
    {
      "index": 3,
      "title": "시스템 구성",
      "purpose": "grid",
      "key_points": ["WMS", "TMS", "OMS"],
      "layout_category": "content_visual",
      "template_id": "deepgreen-grid-3col1",
      "match_score": 0.90,
      "placeholder_bindings": { "main_title": "시스템 구성" },
      "content_design": {
        "template_id": "deepgreen-grid-3col1",
        "data": { "cards": [...] },
        "ooxml_file": "slides/slide-3-content.xml"
      }
    }
  ]
}
```

### 단계 전환 시 데이터 병합

각 단계 시작 시:

1. **이전 단계 JSON 로드**: `Read stage-{N-1}-*.json`
2. **데이터 확장**: 각 슬라이드에 새 필드 추가
3. **누적 저장**: 전체 데이터를 `stage-{N}-*.json`에 저장

### 세션 재개 지원

중단된 세션 재개 시:

1. 가장 최신 stage-N.json 파일 확인
2. 해당 파일에 모든 이전 데이터가 포함되어 있으므로 즉시 재개 가능
3. 다음 단계부터 진행

---

## Triggers

- "동국제강 양식으로"
- "템플릿으로 PPT 만들어줘"
- "회사 양식 사용해줘"

## 3-Type Template System

### 1. Document Templates (documents/)

그룹/회사별 폴더 구조:

```
documents/dongkuk/
├── config.yaml          # 그룹 공통 테마
├── registry.yaml        # 양식 목록
├── assets/              # 계열사별 에셋
│   ├── dongkuk-steel/logo.png
│   └── dongkuk-cm/logo.png
├── 제안서1.yaml
└── 보고서1.yaml
```

### 2. Content Templates (contents/)

슬라이드 패턴:

```
contents/
├── registry.yaml
├── templates/
│   ├── cover1.yaml
│   ├── comparison1.yaml
│   └── timeline1.yaml
└── thumbnails/
```

### 3. Shared Assets (assets/)

공용 이미지/아이콘:

```yaml
# assets/registry.yaml
icons:
  - id: chart-line
    file: icons/chart-line.svg
    tags: ["chart", "data"]
```

## Workflow

### Step 0: Load Template

템플릿/브랜드 요청 시 YAML 먼저 로드:

```
# documents/dongkuk/config.yaml → 테마
# documents/dongkuk/registry.yaml → 양식 목록
```

### Step 1: Extract and Analyze

```bash
# 텍스트 추출
python -m markitdown template.pptx > template-content.md

# 썸네일 그리드 생성
python scripts/thumbnail.py template.pptx
```

### Step 2: Create Inventory

`template-inventory.md` 생성:

```markdown
# Template Inventory Analysis
**Total Slides: [count]**
**슬라이드는 0-indexed (첫 슬라이드 = 0)**

## [Category Name]
- Slide 0: [Layout] - Description
- Slide 1: [Layout] - Description
```

### Step 3: Create Outline

`outline.md` 생성 - 템플릿 매핑 포함:

```python
template_mapping = [
    0,   # Use slide 0 (Title/Cover)
    34,  # Use slide 34 (B1: Title and body)
    50,  # Use slide 50 (E1: Quote)
]
```

**레이아웃 선택 규칙** (기본양식.yaml 기준):

| 슬라이드 목적 | 레이아웃 | 콘텐츠 템플릿 |
|--------------|---------|--------------|
| 표지 | Layout 1 (cover) | 없음 |
| 목차/섹션 | Layout 2 (section) | 없음 |
| 텍스트 불릿 | Layout 3 (content_text) | 없음 |
| **그리드/카드** | **Layout 4 (content_visual)** | **deepgreen-grid-*** |
| **타임라인/프로세스** | **Layout 4 (content_visual)** | **deepgreen-timeline1** |
| **차트/데이터** | **Layout 4 (content_visual)** | **deepgreen-chart-*** |
| **아키텍처/다이어그램** | **Layout 4 (content_visual)** | **deepgreen-grid-icon1** |
| 심플 텍스트 | Layout 5 (content_simple) | 없음 |

**⚠️ 중요**: 시각적 요소(그리드, 차트, 타임라인 등)가 필요한 슬라이드는 반드시 `content_visual` (Layout 4)를 선택하고, 적절한 콘텐츠 템플릿을 매칭해야 합니다.

**추가 규칙**:
- 2열 레이아웃: 정확히 2개 항목일 때만
- 3열 레이아웃: 정확히 3개 항목일 때만
- 이미지+텍스트: 실제 이미지가 있을 때만
- 인용 레이아웃: 실제 인용문(출처 포함)일 때만

### Step 4: Rearrange Slides

```bash
python scripts/rearrange.py template.pptx working.pptx 0,34,34,50,52
```

- 0-indexed
- 같은 인덱스 여러 번 사용 가능 (복제)

### Step 5: Extract Text Inventory

```bash
python scripts/inventory.py working.pptx text-inventory.json
```

JSON 구조:
```json
{
  "slide-0": {
    "shape-0": {
      "placeholder_type": "TITLE",
      "paragraphs": [{ "text": "...", "bold": true }]
    }
  }
}
```

### Step 6: Generate Replacement (텍스트)

`replacement.json` 생성 - 플레이스홀더 텍스트 교체용:

```json
{
  "slide-0": {
    "shape-0": {
      "paragraphs": [
        { "text": "New Title", "bold": true, "alignment": "CENTER" },
        { "text": "Bullet item", "bullet": true, "level": 0 }
      ]
    }
  }
}
```

**규칙**:
- `paragraphs` 없는 shape는 자동으로 텍스트 삭제
- bullet: true일 때 bullet 심볼 (•, -, *) 포함하지 않기
- level은 bullet: true일 때 필수

### Step 6.5: Generate Content Design (콘텐츠 디자인) ⭐ 필수

**⚠️ 이 단계는 `content_visual` 레이아웃 슬라이드가 있을 때 반드시 실행해야 합니다.**

`content_visual` 레이아웃이 매칭된 슬라이드에 대해 콘텐츠 디자인을 생성합니다.

#### 6.5.1 콘텐츠 템플릿 매칭

Stage 3에서 레이아웃이 `content_visual`인 슬라이드에 대해 콘텐츠 템플릿을 매칭:

```yaml
# templates/contents/registry.yaml 검색
- purpose: architecture → grid/deepgreen-grid-3col1
- purpose: pipeline → timeline/deepgreen-timeline1
- purpose: chart → chart/deepgreen-chart-bar1
```

#### 6.5.2 데이터 생성

콘텐츠 템플릿의 `llm_guide.data_slots` 스키마에 맞는 데이터 생성:

```json
{
  "slide_index": 3,
  "template_id": "deepgreen-grid-3col1",
  "data": {
    "cards": [
      {"number": "1", "title": "ppt-extract", "description": "추출 스킬"},
      {"number": "2", "title": "ppt-gen", "description": "생성 스킬"},
      {"number": "3", "title": "ppt-manager", "description": "관리 앱"}
    ]
  }
}
```

#### 6.5.3 OOXML 생성

```bash
python scripts/ooxml-generator.py \
  templates/contents/templates/grid/deepgreen-grid-3col1.yaml \
  templates/documents/dongkuk-systems/기본양식.yaml \
  output/{session}/slides/slide-3-data.json \
  output/{session}/slides/slide-3-content.xml
```

#### 6.5.4 stage-4.json 저장

```json
{
  "session": { "id": "...", "status": "in_progress" },
  "current_stage": 4,
  "slides": [
    {
      "index": 3,
      "layout_category": "content_visual",
      "placeholder_bindings": {
        "main_title": "2개 스킬 + 1 앱 구조",
        "action_title": "추출 + 생성 + 관리 분리"
      },
      "content_design": {
        "template_id": "deepgreen-grid-3col1",
        "data": { "cards": [...] },
        "ooxml_file": "slides/slide-3-content.xml"
      }
    }
  ]
}
```

### Step 7: Apply Replacements (텍스트)

```bash
python scripts/replace.py working.pptx replacement.json output-text.pptx
```

### Step 7.5: Insert OOXML Content (콘텐츠 삽입) ⭐ 필수

**⚠️ Step 6.5에서 OOXML을 생성했다면 반드시 이 단계를 실행해야 합니다.**

`content_design`이 있는 슬라이드에 OOXML 콘텐츠 삽입:

```bash
python scripts/insert-ooxml.py output-text.pptx stage-4.json output.pptx
```

이 스크립트는:
1. stage-4.json에서 `content_design.ooxml_file` 경로 읽기
2. 해당 슬라이드의 `content_zone`에 OOXML 요소 삽입
3. 기존 플레이스홀더와 충돌 방지

---

## 파이프라인 실행 체크리스트

문서 양식 기반 PPT 생성 시 다음 순서대로 실행:

```
✅ Step 0: 문서 양식 YAML 로드 (기본양식.yaml)
✅ Step 1-2: 콘텐츠 분석 및 인벤토리 작성
✅ Step 3: 레이아웃 선택 (content_visual 필요 여부 판단)
✅ Step 4: 슬라이드 재구성 (rearrange.py)
✅ Step 5: 텍스트 인벤토리 추출 (inventory.py)
✅ Step 6: 텍스트 교체 데이터 생성 (replacement.json)
⭐ Step 6.5: content_visual 슬라이드 OOXML 생성 (ooxml-generator.py)
✅ Step 7: 텍스트 교체 적용 (replace.py)
⭐ Step 7.5: OOXML 콘텐츠 삽입 (insert-ooxml.py)
```

**시각적 디자인이 누락되면** Step 6.5, 7.5가 실행되지 않은 것입니다.

## LLM Template Selection Process

1. **문서 템플릿**: 회사/그룹 언급 시
   - config.yaml → 테마 적용
   - registry.yaml → 양식 목록

2. **콘텐츠 템플릿**: 데이터 특성에 맞는 패턴
   - contents/registry.yaml 검색

3. **조합**: 문서 테마 + 양식 + 에셋 + 콘텐츠 패턴

**예시**: "동국제강 제안서" 요청:
- 테마: dongkuk/config.yaml
- 양식: dongkuk/제안서1.yaml
- 로고: dongkuk/assets/dongkuk-steel/logo.png
