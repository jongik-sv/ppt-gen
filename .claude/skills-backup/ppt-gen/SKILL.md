---
name: ppt-gen
description: "AI-powered PPT generation service. Use when: (1) Creating presentations from Markdown/JSON content, (2) Using templates to generate branded presentations, (3) Modifying or editing existing presentations, (4) Analyzing PPT structure. For template/style extraction, use ppt-extract skill."
license: Proprietary. LICENSE.txt has complete terms
user-invocable: true
---

# PPT Generation Service

AI 기반 PPT 자동 생성 서비스. 콘텐츠를 입력받아 전문가 수준의 프레젠테이션을 생성합니다.

## Workflow Selection

사용자 요청에 따라 적절한 워크플로우를 선택합니다.

| 요청 유형 | 워크플로우 | 가이드 |
|----------|-----------|--------|
| "PPT 만들어줘" (새 PPT 생성) | html2pptx | [workflows/html2pptx.md](workflows/html2pptx.md) |
| "동국제강 양식으로" (템플릿 사용) | template | [workflows/template.md](workflows/template.md) |
| "이 PPT 수정해줘" | ooxml | [workflows/ooxml.md](workflows/ooxml.md) |
| "PPT 분석해줘" | analysis | [workflows/analysis.md](workflows/analysis.md) |

> **추출 기능**: 콘텐츠/문서/스타일 추출은 **ppt-extract** 스킬을 사용하세요.

## ⚠️ 필수 실행 규칙 (v5.9 - MUST READ)

**PPT 생성 시작 전 반드시 다음 단계를 수행해야 합니다. 건너뛰면 안 됩니다!**

### 사전 질문 체크리스트 (MANDATORY)

```
□ 1. 청중 확인 (AskUserQuestion 도구 사용)
  └─ 경영진/스폰서 | 발주기관 담당자 | 내부 팀원 | 혼합

□ 2. 발표 시간 확인
  └─ 10분 내외 | 20-30분 | 1시간 이상

□ 3. 강조점 확인
  └─ 기술 아키텍처 | 프로젝트 일정 | 팀 및 역할 | 전체 균형

□ 4. 테마 선택
  └─ Deep Green | Brand New | Default | 커스텀
```

**슬라이드 수 결정 기준**:
| 청중 | 시간 | 슬라이드 수 |
|------|------|------------|
| 경영진 | 10분 | 8-10장 |
| 경영진 | 20-30분 | 12-15장 |
| 실무자 | 20-30분 | 15-20장 |
| 혼합 | 20-30분 | 15-20장 |

### Stage별 필수 호출 스크립트 (v5.9)

| Stage | 필수 호출 | 저장 필드 |
|-------|----------|----------|
| 3 | `icon-decision.js` → `analyzeIconNeed()` | `icon_decision` |
| 4 | **`html-templates.js` → `renderTemplate()`** (YAML 우선) | `html_file`, `content_bindings` |
| 4 | `icon-resolver.js` → `resolveIcons()`, `insertIconsToHtml()` | `assets_generated.icons` |
| 5 | `design-evaluator.js` → `evaluate()` (70점 기준, 최대 3회 재시도) | `design_info`, `evaluation`, `attempt_history` |

**v5.9 핵심 변경**: Stage 4에서 `renderTemplate()`은 **템플릿 YAML을 우선 로드**하여 shapes/geometry를 HTML로 변환합니다.

### 품질 합격 기준 (PASS CRITERIA)

| 항목 | 기준 | 불합격 시 조치 |
|------|------|---------------|
| **슬라이드 평가 점수** | **85점 이상** | Stage 3으로 롤백 → 템플릿 재매칭 → 재생성 |
| 아이콘 적용 | 필수 슬라이드 100% | icon-resolver 재실행 |
| 콘텐츠 바인딩 | 모든 필드 채워짐 | content_bindings 보완 |

**불합격 슬라이드 처리 프로세스**:
```
평가 점수 < 85점
    ↓
[1] 문제 원인 분석 (아이콘 미적용, 레이아웃 불균형, 콘텐츠 누락 등)
    ↓
[2] 해당 슬라이드만 Stage 3으로 롤백 (slide_stage = 3)
    ↓
[3] 템플릿 재매칭 또는 콘텐츠 수정
    ↓
[4] Stage 4 → 5 재진행
    ↓
[5] 재평가 (85점 이상 될 때까지 반복, 최대 3회)
```

**상세 가이드**: [workflows/html2pptx.md](workflows/html2pptx.md)의 "MANDATORY EXECUTION RULES" 섹션 참조

---

## 5단계 파이프라인 (v5.9)

PPT 생성은 5단계 파이프라인으로 진행됩니다:

```
1단계(Setup) → 2단계(Outline) → 3단계(Matching) → 4단계(Content) → 5단계(PPTX)
```

| 단계 | 이름 | 설명 | 슬라이드 데이터 |
|------|------|------|----------------|
| 1 | Setup | 사전 질문 + 테마 선택 | `setup.presentation`, `setup.theme` |
| 2 | Outline | 슬라이드별 콘텐츠 | `title`, `purpose`, `key_points` |
| 3 | Matching | 템플릿 매칭 + **아이콘 결정** | `template_id`, `match_score`, `icon_decision` |
| 4 | Content | **YAML 템플릿 렌더링** + 아이콘 생성 | `html_file`, `content_bindings`, `assets_generated` |
| 5 | Generation | **디자인 평가 (70점 기준, 최대 3회)** + PPTX 변환 | `generated`, `design_info`, `evaluation`, `attempt_history` |

**v5.9 핵심 변경**:
- Stage 4: `renderTemplate()`가 **템플릿 YAML을 우선 로드**하여 shapes/geometry를 HTML로 변환
- Stage 5: 디자인 평가 70점 미만 시 **템플릿 재매칭 → HTML 재생성 → 재평가** (최대 3회)

### 슬라이드별 플랫 구조

각 슬라이드에 데이터가 **플랫하게 누적**됩니다 (단계 구분 없음):

```json
{
  "session": { "id": "...", "title": "...", "status": "in_progress" },
  "current_stage": 4,
  "setup": { "presentation": {...}, "theme": {...} },
  "slides": [
    {
      "index": 0,
      "title": "표지",
      "purpose": "cover",
      "key_points": ["제안사", "날짜"],
      "template_id": "cover-centered1",
      "match_score": 0.95,
      "html_file": "slides/slide-001.html",
      "assets": { "icons": ["logo.svg"], "images": [] },
      "text_content": { "headline": "스마트 물류 시스템" }
    }
  ],
  "output": { "pptx_file": "output.pptx" }
}
```

### 생성 방식 (2가지)

| 방식 | 용도 | 슬라이드 필드 |
|------|------|--------------|
| **HTML** | 새 슬라이드 생성 | `html_file`, `assets`, `text_content` |
| **OOXML** | 문서양식 편집 | `ooxml_bindings` (ID별 텍스트/이미지/색상) |

- **SVG**: 바인딩 불가 (path 변환됨) → 정적 아이콘/그래픽으로만 사용

### OOXML 바인딩 예시

```json
{
  "ooxml_bindings": {
    "template": "documents/dongkuk/cover.xml",
    "mappings": [
      { "id": "sp_title", "type": "text", "value": "스마트 물류 시스템" },
      { "id": "sp_logo", "type": "image", "value": "assets/logo.png" },
      { "id": "sp_accent", "type": "color", "value": "#1E5128" }
    ]
  }
}
```

### Session Manager 사용법

```javascript
const SessionManager = require('./scripts/session-manager');

// 새 세션 생성
const session = await SessionManager.create('스마트 물류 제안서');

// 1단계: 전역 설정
await session.completeSetup({
  presentation: { title: '...', audience: '경영진' },
  theme: { id: 'deepgreen', colors: { primary: '#1E5128' } }
});

// 2~4단계: 슬라이드별 데이터 누적 (플랫 병합)
await session.updateSlide(0, { title: '표지', purpose: 'cover' });
await session.updateSlide(0, { template_id: 'cover-centered1' });
await session.updateSlide(0, { html_file: 'slide-001.html' });

// 5단계: 최종 생성
await session.updateSlide(0, { generated: true });
await session.completeGeneration({ pptx_file: 'output.pptx' });

// 세션 재개 (폴더명으로 재개)
const session = await SessionManager.resume('2026-01-09_143025_project-plan');
```

### Stage JSON 저장 규칙 (CRITICAL)

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

**단계별 필수 포함 데이터** (v5.8):

| Stage | 슬라이드에 누적되는 필드 |
|-------|------------------------|
| 2 | `index`, `title`, `purpose`, `key_points`, `speaker_notes` |
| 3 | 위 + `template_id`, `match_score`, `match_reason`, `layout`, **`icon_decision`** |
| 4 | 위 + `html_file`, `content_bindings`, **`assets_generated`** |
| 5 | 위 + `generated`, **`design_info`**, **`evaluation`**, `slide_stage`, `revision` |

**v5.8 추가 필드**:
- `icon_decision`: 아이콘 필요성 판단 결과 (Stage 3)
- `assets_generated`: 생성된 아이콘/이미지 목록 (Stage 4)
- `evaluation`: 디자인 품질 평가 점수 (Stage 5)

### v5.3 새 필드 설명

#### content_bindings (Stage 4)

HTML 생성 시 사용된 콘텐츠를 구조화하여 기록합니다. 재사용, 템플릿 학습, 수정 루프에 필수.

```json
{
  "content_bindings": {
    "title": "핵심 추진 전략",
    "items": [
      { "number": "1", "title": "단계적 전환", "description": "...", "features": ["..."] }
    ],
    "footer": { "page_number": "8", "project_name": "스마트 물류" }
  }
}
```

**콘텐츠 타입별 구조**: cover(`title`, `date`), toc(`items[]`), stats(`items[{value}]`), grid(`items[{icon}]`), table(`table{headers, rows}`) 등

#### design_info (Stage 5)

PPTX 변환 후 슬라이드 디자인 정보를 추출합니다. 템플릿 학습, 재사용에 활용.

```json
{
  "design_info": {
    "layout": { "type": "grid", "grid": { "columns": 3 } },
    "zones": [{ "id": "title-zone", "role": "slide_title", "geometry": {...} }],
    "shapes_summary": { "total_count": 12, "by_type": {...}, "patterns": [...] },
    "color_tokens": { "primary": "#002452", "secondary": "#C51F2A" },
    "typography": { "slide_title": { "font_size_pt": 24, "font_weight": "bold" } },
    "spacing": { "slide_margin": {...}, "section_gap": 24 },
    "constraints": { "max_items": 4, "title_max_chars": 30 },
    "visual_properties": { "balance": "symmetric", "hierarchy": 3 }
  }
}
```

#### slide_stage, revision, revision_history (Stage 5 - 수정 루프)

개별 슬라이드 수정을 지원합니다:

```json
{
  "slide_stage": 5,        // 슬라이드별 현재 스테이지 (2~5)
  "revision": 1,           // 수정 횟수 (0 = 최초)
  "revision_history": [    // 선택적: 이력
    { "revision": 0, "template_id": "old-template", "reason": "초기 생성" },
    { "revision": 1, "template_id": "new-template", "reason": "사용자 요청" }
  ]
}
```

**수정 루프 시나리오**: 5번 슬라이드 수정 요청 → `slide_stage=3`으로 롤백 → 5번만 Stage 3→4→5 재진행

**단계 전환 시 데이터 병합**:

```python
# 개념적 예시 (각 단계 시작 시)
previous = read_json('stage-{N-1}-*.json')

for slide in previous['slides']:
    slide['new_field'] = new_value  # 새 필드 추가 (기존 필드 유지)

previous['current_stage'] = N
write_json('stage-{N}-*.json', previous)
```

**세션 재개**: 가장 최신 stage-N.json을 읽으면 모든 이전 데이터가 포함되어 즉시 재개 가능.

## HTML 검증/수정 (v5.4 추가)

HTML 생성 후 **반드시 검증**하고 문제 발견 시 수정합니다.

### 지원되지 않는 태그 (CRITICAL)

| 태그 | 상태 | 대체 방법 |
|------|------|----------|
| `<table>`, `<tr>`, `<td>`, `<th>` | ❌ 미지원 | `<div>` + display: flex |
| `<span>` (텍스트 포함) | ❌ 변환 안 됨 | `<p>` 또는 `<div><p>` |

**지원되는 태그**: `<div>`, `<p>`, `<h1-6>`, `<ul>`, `<ol>`, `<li>`, `<img>`, `<svg>`

### 검증 체크리스트

| 항목 | 문제 패턴 | 수정 |
|------|----------|------|
| 미지원 태그 | `<table>`, `<span>` 사용 | `<div>` + flexbox로 변환 |
| 색상 대비 | `rgba(...0.1)` 배경 + `white` 텍스트 | solid 어두운 배경으로 변경 |
| 오버플로우 | 요소가 body 영역(720pt×405pt) 초과 | 크기/위치 조정 |
| CSS 불일치 | 정의 없는 클래스 사용 | 클래스 정의 추가 |
| 콘텐츠 누락 | 원본 데이터와 비교 | 누락 콘텐츠 추가 |

### 검증/수정 프로세스

```
HTML 생성 완료
    ↓
[1] 모든 HTML 파일 읽기
    ↓
[2] 각 슬라이드 검증:
    - rgba 투명 배경 + white 텍스트 조합 찾기
    - overflow 확인
    - CSS 클래스 일치 확인
    - 콘텐츠 누락 확인
    ↓
[3] 문제 발견? ─No→ PPTX 변환 진행
    ↓ Yes
[4] 문제 수정 (Edit 도구 사용)
    ↓
[5] 재검증 (최대 3회 반복)
    ↓
수정 불가 → 사용자에게 보고
```

### 색상 대비 수정 예시

```css
/* 문제: 투명 배경에 밝은 텍스트 */
.card { background: rgba(183,208,212,0.1); }
.card-title { color: white; }

/* 수정: solid 어두운 배경으로 변경 */
.card { background: #002452; }
```

**테마 색상 활용**:
- 어두운 배경: `#002452`, `#4B6580`, `#C51F2A`
- 밝은 텍스트: `white`, `#FFFFFF`

**CRITICAL**: PPTX 변환 전 반드시 검증을 수행해야 합니다!

## Overview

A user may ask you to create, edit, or analyze the contents of a .pptx file. A .pptx file is essentially a ZIP archive containing XML files and other resources that you can read or edit. You have different tools and workflows available for different tasks.

## Template Priority Rule (CRITICAL)

**PPT 생성 시 반드시 콘텐츠 템플릿 우선 검색** - 이 단계를 건너뛰면 안 됩니다.

### 필수 프로세스

1. **슬라이드 목록 작성**: 콘텐츠 분석 → 슬라이드 유형/키워드 정리
2. **분리형 registry 검색**: 각 슬라이드별 매칭 템플릿 찾기 (v4.1 분리형)
3. **매칭 결과 테이블 작성**: 어떤 템플릿을 사용할지 명시 (필수 출력물)
4. **템플릿 YAML 로드**: 매칭된 템플릿의 `shapes[]` 구조 참조
5. **HTML 생성**: 템플릿 geometry/style을 HTML로 변환

### Registry 구조 (v4.1 분리형)

```
templates/contents/
├── registry.yaml              # 마스터 (인덱스): 카테고리 목록만
├── registry-chart.yaml        # 차트 카테고리 템플릿
├── registry-comparison.yaml   # 비교 카테고리 템플릿
├── registry-grid.yaml         # 그리드 카테고리 템플릿
└── ... (13개 카테고리)
```

### 템플릿 매칭 알고리즘 (v4.1 검색 메타데이터 활용)

**검색 프로세스**:
```
1. 사용자 쿼리에서 카테고리 힌트 추출 (예: "비교" → comparison)
2. 힌트가 있으면: registry-{category}.yaml만 읽기 (토큰 효율적)
3. 힌트가 없으면: registry.yaml(인덱스) → 각 카테고리 순회
4. 3단계 매칭 알고리즘 실행
```

#### 3단계 매칭 알고리즘

| 단계 | 필드 | 매칭 방식 | 점수 |
|------|------|----------|------|
| **1단계** | `match_keywords` | 키워드 직접 매칭 | 일치 수 / 전체 키워드 수 |
| **2단계** | `expected_prompt` | 의미적 유사도 매칭 | 구조 유사성 비교 |
| **3단계** | `description` | 설명 텍스트 매칭 | 보조 점수 |

**1단계: match_keywords 매칭** (Primary)
```python
def match_keywords(query: str, template: dict) -> float:
    """사용자 쿼리와 match_keywords 배열 비교"""
    query_tokens = tokenize(query)  # ["비교", "2열", "장단점"]
    keywords = template['match_keywords']  # ["비교", "장단점", "vs", "대조", "좌우", "2열"]

    matched = set(query_tokens) & set(keywords)
    return len(matched) / len(query_tokens)  # 0.0 ~ 1.0
```

**2단계: expected_prompt 매칭** (Semantic)
```python
def match_expected_prompt(query: str, template: dict) -> float:
    """사용자 요청과 expected_prompt 구조 비교"""
    expected = template['expected_prompt']

    # 구조적 요소 추출
    query_elements = extract_elements(query)   # {"열": 2, "형태": "비교", "요소": "불릿"}
    expected_elements = extract_elements(expected)

    # 요소 일치도 계산
    return calculate_similarity(query_elements, expected_elements)
```

**3단계: 최종 점수 계산**
```python
def calculate_match_score(query: str, template: dict) -> float:
    """최종 매칭 점수"""
    keyword_score = match_keywords(query, template) * 0.6    # 60%
    prompt_score = match_expected_prompt(query, template) * 0.3  # 30%
    desc_score = match_description(query, template) * 0.1    # 10%

    return keyword_score + prompt_score + desc_score
```

#### 매칭 예시

```markdown
사용자 요청: "장단점을 좌우로 비교하는 슬라이드"

| 템플릿 ID | match_keywords 일치 | expected_prompt 유사도 | 최종 점수 |
|----------|-------------------|----------------------|----------|
| comparison-2col1 | ["비교", "장단점", "좌우"] = 1.0 | 구조 일치 = 0.9 | **0.87** ✓ |
| comparison-4col-stats | ["비교"] = 0.33 | 구조 불일치 = 0.2 | 0.26 |
```

**카테고리별 registry 필드**:
- `description`: 템플릿 설명 (1줄) - 보조 매칭용
- `match_keywords`: 검색 키워드 배열 (use_for + keywords + prompt_keywords 통합) - **Primary**
- `expected_prompt`: 예상 사용자 프롬프트 - **Semantic 매칭용**

**동기화**: 개별 템플릿 YAML이 원본. `sync_registry.py` 스크립트로 자동 생성

### 유연한 템플릿 활용

템플릿은 **2가지 레벨**에서 활용합니다:

**슬라이드 레벨**: 전체 레이아웃 참조
- 슬라이드 전체 구조를 템플릿에서 가져오기
- 예: `deepgreen-cover1` → 표지 슬라이드 전체

**요소 레벨**: 개별 shapes 참조 (더 유연함)
- 템플릿의 특정 shape만 가져와서 조합
- 예: `deepgreen-stats1`의 도트그리드 통계 박스 1개만 가져오기
- 예: `deepgreen-grid4col1`의 아이콘+텍스트 카드 패턴만 가져오기
- 예: `timeline1`의 단계 표시 요소만 가져와서 커스텀 레이아웃에 배치

**조합 전략**:
- 여러 템플릿에서 필요한 shapes 선택
- geometry(위치/크기)는 새 슬라이드에 맞게 조정
- style(색상/폰트)은 일관성 유지

### 직접 디자인 허용 조건

- 분리형 registry를 검색했으나 **매칭되는 템플릿이 없는 경우만**
- 매칭 결과 테이블에 ❌ 표시된 슬라이드만 직접 디자인

### 금지 사항

- 분리형 registry 검색 없이 직접 디자인 시작
- 매칭 가능한 템플릿이 있는데 직접 디자인
- **스크린캡처 방식으로 PPT 생성 절대 금지**: 슬라이드를 1920x1080 이미지로 변환해서 삽입하면 안 됨. 반드시 `html2pptx.js`로 개별 요소 변환

### Shape Source 기반 하이브리드 추출 (v3.1)

콘텐츠 템플릿 추출 시, 도형 복잡도에 따라 **shape_source** 타입이 결정됩니다:

**5가지 Shape Source 타입**:

| shape_source | 설명 | PPT 생성 시 처리 |
|--------------|------|-----------------|
| `ooxml` | 원본 OOXML 보존 | fragment 그대로 사용 (좌표/색상만 치환) |
| `svg` | SVG 벡터 경로 | SVG → OOXML 변환 (custGeom) |
| `reference` | 다른 shape/Object 참조 | 참조 대상의 OOXML 복사 + 오버라이드 |
| `html` | HTML/CSS 스니펫 | html2pptx.js로 개별 요소 변환 (스크린샷 금지) |
| `description` | 자연어 설명 | LLM이 설명에 맞게 OOXML 생성 |

**복잡도에 따른 자동 분류**:

| 복잡 → `ooxml` | 단순 → `description` |
|----------------|---------------------|
| 그라데이션 채우기 | 단색 채우기 |
| 커스텀 도형 (`<a:custGeom>`) | 기본 도형 (`<a:prstGeom>`) |
| 3D 효과, 베벨, 반사 | 단순 그림자 또는 없음 |
| 복잡한 텍스트 (여러 서식) | 단일 스타일 텍스트 |
| 그룹화된 도형 | 단일 도형 |
| 방사형 세그먼트 (3개+) | 사각형, 원, 기본 화살표 |

**Extraction Mode (슬라이드 타입별)**:

| 슬라이드 타입 | extraction_mode | 추출 범위 |
|--------------|-----------------|----------|
| Cover, TOC, Section, Closing | `full` | 전체 슬라이드 |
| Content (일반) | `content_only` | 콘텐츠 Zone만 (제목/푸터 제외) |

**Object 분리 저장**:
- 재사용 가능한 다이어그램은 `templates/contents/objects/`에 별도 저장
- 템플릿에서 `shape_source: reference`로 참조

**참조**:
- **ppt-extract** 스킬의 content-extract 워크플로우 (추출 관련)
- [content-schema.md](references/content-schema.md) v2.1 스키마

이 규칙으로:
- 복잡한 도형 100% 보존 (OOXML)
- 단순 도형은 자연어로 간결화
- 재사용 가능한 Object 컴포넌트
- 일관된 디자인 품질 보장

## 3-Type Template System (v3.0)

> **v3.0 Update**: 템플릿이 스킬에서 분리되어 프로젝트 루트(`C:/project/docs/templates/`)에 저장됩니다.
> 테마와 컨텐츠가 분리되어 독립적으로 관리됩니다.

템플릿은 3가지 타입으로 관리됩니다:

| 타입 | 경로 | 용도 |
|------|------|------|
| 테마 | `C:/project/docs/templates/themes/` | 색상/폰트/스타일 정의 (deepgreen, brandnew, default) |
| 콘텐츠 템플릿 | `C:/project/docs/templates/contents/` | 슬라이드 패턴 (테마 독립적, 디자인 토큰 사용) |
| 문서 템플릿 | `C:/project/docs/templates/documents/` | 그룹/회사별 문서 양식 |
| 공용 에셋 | `C:/project/docs/templates/assets/` | 공용 이미지/아이콘 |

### 테마 선택 (MANDATORY)

**PPT 생성 시작 전 반드시 테마를 선택해야 합니다.**

```markdown
## 🎨 테마 선택

| # | 테마 | 설명 | 주요 색상 |
|---|------|------|----------|
| 1 | **Deep Green** | 자연스럽고 깔끔한 딥그린 | 🟢 #1E5128 / 🟩 #4E9F3D |
| 2 | **Brand New** | 신선한 스카이블루 | 🔵 #7BA4BC / 🩷 #F5E1DC |
| 3 | **Default** | 중립적인 기본 블루 | 💙 #2563EB / 🩵 #DBEAFE |

> 번호 선택 또는 직접 색상 지정 가능
```

### 디자인 토큰 시스템

콘텐츠 템플릿은 실제 색상 대신 디자인 토큰을 사용합니다:

```yaml
# 템플릿 (디자인 토큰)
style:
  fill:
    color: primary      # ← 토큰
  text:
    font_color: light   # ← 토큰

# 테마 적용 후 (실제 색상)
style:
  fill:
    color: "#1E5128"    # ← Deep Green primary
  text:
    font_color: "#FFFFFF"
```

**사용 가능한 디자인 토큰**:
- `primary`: 주요 강조색
- `secondary`: 보조 강조색
- `accent`: 하이라이트
- `background`: 배경색
- `surface`: 카드/패널 배경
- `dark_text`: 본문 텍스트
- `light`: 밝은 텍스트
- `gray`: 음소거 요소

## Dependencies

Required dependencies (should already be installed):

### Node.js
- **pptxgenjs**: Creating presentations via html2pptx
- **playwright**: HTML rendering in html2pptx
- **sharp**: SVG rasterization and image processing
- **react-icons, react, react-dom**: Icons

### Python
- **markitdown**: `pip install "markitdown[pptx]"` (text extraction)
- **python-pptx**: PPTX manipulation
- **defusedxml**: Secure XML parsing

### System
- **LibreOffice** (`soffice`): PPTX → PDF conversion (required for thumbnails)
  - Linux: `apt install libreoffice`
  - macOS: `brew install --cask libreoffice`
- **Poppler** (`pdftoppm`): PDF → Image conversion (required for thumbnails)
  - Linux: `apt install poppler-utils`
  - macOS: `brew install poppler`

## Code Style Guidelines

**IMPORTANT**: When generating code for PPTX operations:
- Write concise code
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements
- **임시 스크립트는 절대로 스킬 폴더 안에 생성 금지** → 프로젝트 루트에 생성

## References

| 문서 | 용도 |
|------|------|
| [html2pptx.md](html2pptx.md) | HTML→PPTX 변환 상세 가이드 |
| [ooxml.md](ooxml.md) | OOXML 편집 상세 가이드 |
| [references/content-schema.md](references/content-schema.md) | 콘텐츠 템플릿 v2.0 스키마 |
| [references/design-intent.md](references/design-intent.md) | 디자인 의도 분류 |
| [references/color-palettes.md](references/color-palettes.md) | 색상 팔레트 레퍼런스 |
| [schemas/pipeline.schema.json](schemas/pipeline.schema.json) | 5단계 파이프라인 JSON 스키마 |

## 미구현 사항 (TODO)

스킬 사용 중 "뭐가 안 돼?" 질문 시 아래 목록 참조:

- [ ] **이미지 생성 모델 연동**: MCP를 통한 DALL-E, Midjourney, Stable Diffusion 연결
  - 현재: 이미지 생성 프롬프트 생성만 지원 (`scripts/image-prompt-generator.js`)
  - 향후: 프롬프트 → 이미지 자동 생성 → PPT 삽입 파이프라인

---

## 완료 후 정리

**중요**: 스킬 작업 완료 시 생성한 임시 파일을 반드시 삭제합니다.

### 삭제 대상

1. **프로젝트 루트 임시 스크립트**:
   - `extract_*.py`
   - `generate_*.py`
   - `*_thumbnail*.py`
   - `create_thumbnail.py`
   - `shapes_data.json`

2. **임시 작업 파일**:
   - 작업용 `.pptx` 파일 (사용자 요청 최종 출력물 제외)
   - 임시 `.pdf` 파일
   - 다운로드한 참조 이미지 (templates/ 외부)

3. **스킬 디렉토리 내 파일** (생성 금지 위반 시):
   - 임시 스크립트가 스킬 폴더에 생성되었다면 즉시 삭제

### 보존 대상 (삭제 금지)

- `templates/` 하위 모든 파일
- `registry*.yaml` 파일들 (마스터 + 카테고리별)
- 사용자가 명시적으로 요청한 최종 출력물
- 기존 스킬 스크립트 (`scripts/` 내 기본 파일)
