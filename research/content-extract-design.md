# 콘텐츠 추출 설계

> ppt2html + OOXML 기반 콘텐츠 템플릿 추출 방안

## 적용 범위

| 추출 유형  | 이번 설계    | 비고           |
| ---------- | ------------ | -------------- |
| **콘텐츠** | ✅ 수정      | 이 문서의 대상 |
| 문서 양식  | ❌ 기존 유지 | OOXML 방식     |
| 테마       | ❌ 기존 유지 | 색상/폰트 정의 |

---

## 결정 사항

| 항목          | 결정                                                         |
| ------------- | ------------------------------------------------------------ |
| ppt2html 배포 | **ppt-gen 내장** (`vendor/ppt2html/`)                        |
| 출력물 범위   | **YAML + HTML** (template.yaml, template.html, example.html) |
| 디자인 분류   | **LLM 자동 분류**                                            |

---

## 추출 방식 분리

| 추출 대상     | 포맷        | 이유                           |
| ------------- | ----------- | ------------------------------ |
| **문서 양식** | OOXML       | 마스터/레이아웃 100% 재현 필요 |
| **콘텐츠**    | HTML + YAML | 분석 용이, 테마 변경 가능      |

---

## 콘텐츠 템플릿 구조

```
templates/contents/{category}/{id}/
├── template.html      # LLM 생성 (변수화)
├── template.yaml      # LLM 생성 (스키마) - 핵심 파일
├── example.html       # LLM 생성 (정리된 샘플)
└── thumbnail.png      # ppt2html 출력
```

---

## template.yaml 상세 스키마

> **핵심 원칙**: YAML 파일만 보고 원본과 동일하게 재현 가능해야 함

### 전체 구조

```yaml
# ============================================
# 메타데이터
# ============================================
meta:
  id: "process-arrow-4step-01"
  name: "4단계 화살표 프로세스"
  version: "1.0"
  created_at: "2025-01-16T14:30:00+09:00"

  # 출처 정보 (추적용)
  source:
    file: "동국시스템즈-회사소개서.pptx"
    slide_number: 12 # 1-based
    slide_title: "사업 추진 절차" # 원본 슬라이드 제목
    extracted_at: "2025-01-16T14:30:00+09:00"
    extracted_by: "content-slide-extractor"

# ============================================
# 용도 및 검색 (ppt-gen 매칭용)
# ============================================
usage:
  # 이 템플릿을 사용해야 하는 상황 (상세하게)
  use_when:
    - "단계별 프로세스나 절차를 설명할 때"
    - "시간 순서대로 진행되는 업무 흐름을 표현할 때"
    - "4개의 연속적인 단계가 있는 내용을 시각화할 때"
    - "각 단계에 제목과 설명이 필요한 경우"
    - "화살표로 진행 방향을 강조하고 싶을 때"

  # 이 템플릿을 사용하면 안 되는 상황
  avoid_when:
    - "단계 수가 4개가 아닌 경우 (3개 이하 또는 5개 이상)"
    - "순환하는 프로세스 (시작과 끝이 연결)"
    - "병렬로 진행되는 작업들"
    - "계층 구조나 조직도"

  # 적합한 문서 유형
  document_types:
    - "사업계획서"
    - "프로젝트 제안서"
    - "업무 매뉴얼"
    - "회사소개서"

  # 검색 키워드 (한글 + 영문)
  keywords:
    - "프로세스"
    - "절차"
    - "단계"
    - "흐름"
    - "화살표"
    - "process"
    - "step"
    - "flow"
    - "arrow"

  # 카테고리 (폴더명과 동일)
  category: "process"

  # 관련 템플릿 (유사하지만 다른 용도)
  related_templates:
    - id: "process-circle-3step-01"
      reason: "3단계일 때 사용"
    - id: "cycle-4step-01"
      reason: "순환 프로세스일 때 사용"

# ============================================
# 캔버스 정보
# ============================================
canvas:
  width: 1920
  height: 1080
  aspect_ratio: "16:9"

  # 콘텐츠 영역 (타이틀/푸터 제외)
  content_zone:
    top: 200 # px (타이틀 영역 아래)
    bottom: 980 # px (푸터 영역 위)
    left: 60
    right: 1860

# ============================================
# 레이아웃 구조 (원본 재현의 핵심)
# ============================================
layout:
  type: "horizontal-flow" # horizontal-flow | vertical-flow | grid | radial | freeform
  direction: "ltr" # ltr | rtl | ttb | btt
  alignment: "center" # start | center | end

  # 그리드 정보 (해당하는 경우)
  grid:
    columns: 4
    rows: 1
    column_gap: 40 # px
    row_gap: 0

  # 전체 콘텐츠 영역
  bounds:
    x: 100
    y: 250
    width: 1720
    height: 500

# ============================================
# 도형 정의 (상세하게 - 원본 재현용)
# ============================================
shapes:
  # === 단계 1 ===
  - id: "step-1-box"
    name: "1단계 박스"
    type: "rounded-rectangle"

    # 위치/크기 (절대값 + 비율 둘 다)
    geometry:
      x: 100 # px
      y: 300 # px
      width: 350 # px
      height: 200 # px
      x_percent: 5.2% # 캔버스 대비
      y_percent: 27.8%
      width_percent: 18.2%
      height_percent: 18.5%
      rotation: 0 # degrees
      corner_radius: 15 # px

    # 스타일 (테마 변수 + 구체적 값)
    style:
      fill:
        type: "solid" # solid | gradient | none | pattern
        color: "primary" # 시맨틱 컬러 (테마 연동)
        color_hex: "#1B5E20" # 추출 시점의 실제 색상 (참고용)
        opacity: 1.0
      stroke:
        color: "none"
        width: 0
      shadow:
        enabled: true
        color: "rgba(0,0,0,0.15)"
        blur: 10
        offset_x: 2
        offset_y: 4

    # 텍스트 (있는 경우)
    text:
      content: "{{step1_title}}" # 플레이스홀더
      sample: "기획" # 예시 데이터

      alignment:
        horizontal: "center"
        vertical: "middle"

      font:
        family: "Pretendard" # 또는 테마 변수
        size: 24 # pt
        size_ratio: 0.022 # 캔버스 높이 대비
        weight: "bold" # normal | bold | 100-900
        color: "on-primary" # 시맨틱 (primary 위의 텍스트)
        color_hex: "#FFFFFF"

      padding:
        top: 20
        bottom: 20
        left: 15
        right: 15

    # Z-순서
    z_index: 1

  # === 화살표 1→2 ===
  - id: "arrow-1-2"
    name: "1→2 화살표"
    type: "arrow"

    geometry:
      x: 450
      y: 390
      width: 50
      height: 20
      rotation: 0

    style:
      stroke:
        color: "primary"
        width: 3
      arrow_head:
        type: "triangle"
        size: 12

    z_index: 2

  # === 단계 2, 3, 4... (동일 패턴) ===
  # ...

# ============================================
# 플레이스홀더 정의 (데이터 바인딩)
# ============================================
placeholders:
  - id: "step1_title"
    label: "1단계 제목"
    type: "text"
    required: true
    max_length: 20
    sample: "기획"
    description: "첫 번째 단계의 제목 (간결하게)"

  - id: "step1_desc"
    label: "1단계 설명"
    type: "text"
    required: false
    max_length: 100
    sample: "요구사항 분석 및 기획안 수립"
    description: "첫 번째 단계의 상세 설명"

  - id: "step2_title"
    label: "2단계 제목"
    type: "text"
    required: true
    max_length: 20
    sample: "설계"

  # ... (나머지 플레이스홀더)

# ============================================
# 테마 바인딩 (색상/폰트 연동)
# ============================================
theme_bindings:
  colors:
    primary: "shapes[*].style.fill.color == 'primary'"
    secondary: "shapes[*].style.fill.color == 'secondary'"
    background: "canvas.background"

  fonts:
    heading: "shapes[*].text.font.family where weight == 'bold'"
    body: "shapes[*].text.font.family where weight == 'normal'"

# ============================================
# 반응형/변형 규칙
# ============================================
variants:
  # 단계 수가 다를 때
  step_count:
    min: 3
    max: 6
    default: 4
    resize_rule: "equal-width" # 도형 너비 균등 분배

  # 텍스트 길이에 따른 조정
  text_overflow:
    strategy: "shrink-font" # shrink-font | truncate | wrap
    min_font_size: 14

# ============================================
# 품질 메타데이터
# ============================================
quality:
  score: 8.5 # 0-10 (디자인 품질)
  completeness: "high" # high | medium | low

  # 추출 품질 체크
  extraction_notes:
    - "그라데이션이 단색으로 변환됨"
    - "폰트가 시스템 폰트로 대체될 수 있음"
```

### 핵심 섹션 설명

| 섹션               | 목적          | ppt-gen 활용           |
| ------------------ | ------------- | ---------------------- |
| `meta.source`      | 출처 추적     | 원본 확인, 디버깅      |
| `usage.use_when`   | 사용 상황     | **콘텐츠 매칭의 핵심** |
| `usage.avoid_when` | 부적합 상황   | 잘못된 선택 방지       |
| `usage.keywords`   | 검색어        | 키워드 기반 검색       |
| `shapes`           | 도형 상세     | 원본 재현              |
| `placeholders`     | 데이터 바인딩 | 콘텐츠 삽입            |
| `theme_bindings`   | 테마 연동     | 색상/폰트 변경         |

---

## 통합 아키텍처

### 워크플로우

```
[ppt-extract 스킬]
    │
    ├─ 입력: PPTX 파일 + 슬라이드 번호(들)
    │
    ├─ [1단계] PPTX 언팩 + ppt2html 실행
    │   ├─ unzip input.pptx -d workspace/unpacked/
    │   └─ node vendor/ppt2html/pptxjs-cli/extract.js input.pptx workspace/html/
    │
    ├─ [2단계] 슬라이드 분석 (LLM 자동 분류)
    │   ├─ 입력: slide.html + slide.xml
    │   └─ 출력: 디자인 의도, 카테고리 결정
    │
    ├─ [3단계] 병렬 추출 (content-slide-extractor × N)
    │   ├─ 입력: unpacked XML + slide.html (참고용)
    │   └─ 출력: template.yaml, template.html, example.html
    │
    ├─ [4단계] 썸네일 이동
    │   └─ workspace/html/slide{N}.png → thumbnails/{category}/{id}.png
    │
    ├─ [5단계] 정리
    │   └─ workspace/ 임시 파일 삭제
    │
    └─ [6단계] Registry 업데이트
```

### 역할 분담

| 컴포넌트                    | 담당             | 비고               |
| --------------------------- | ---------------- | ------------------ |
| **ppt2html (내장)**         | HTML + PNG 생성  | 1단계에서 실행     |
| **LLM**                     | 디자인 분류      | 2단계 자동 분류    |
| **content-slide-extractor** | YAML + HTML 생성 | 3단계 병렬 실행    |
| **orchestrator**            | 전체 조율        | 에이전트 호출 관리 |

---

## ppt2html 내장

### 폴더 구조

```
ppt-gen/
├── vendor/
│   └── ppt2html/                    # 내장 (복사)
│       ├── pptxjs-cli/
│       │   ├── extract.js           # CLI 진입점
│       │   └── package.json
│       └── PPTXjs/                  # 라이브러리
│           ├── js/
│           │   ├── pptxjs.js
│           │   ├── d3.min.js
│           │   └── ...
│           └── css/
```

### 내장 작업

1. `/home/jji/project/ppt2html` → `ppt-gen/vendor/ppt2html/` 복사
2. `.gitignore`에 `vendor/ppt2html/node_modules/` 추가
3. 호출 경로: `node vendor/ppt2html/pptxjs-cli/extract.js`

### 시스템 요구사항

| 의존성      | 필수 | 설치 방법                 |
| ----------- | ---- | ------------------------- |
| Node.js ≥18 | ✅   | 시스템 설치               |
| Puppeteer   | ✅   | npm install (vendor 내부) |
| Chromium    | ✅   | Puppeteer 자동 다운로드   |

### 사용법

```bash
# CLI 호출
node vendor/ppt2html/pptxjs-cli/extract.js <PPTX_PATH> [OUTPUT_DIR] [--debug]

# 예시
node vendor/ppt2html/pptxjs-cli/extract.js ./input.pptx ./temp-output
```

### 출력물

- `{basename}_slide{N}.html` - 개별 슬라이드 HTML
- `{basename}_slide{N}.png` - 개별 슬라이드 PNG
- `{basename}(전체).html` - 전체 프레젠테이션 HTML

---

## 에이전트 설계

### content-extract-orchestrator (신규)

```yaml
name: content-extract-orchestrator
description: 다중 슬라이드 추출 조율
tools: Read, Write, Bash, Glob, Grep, Task
model: opus

입력:
  pptx_path: path/to/file.pptx
  output_dir: templates/contents/
  slides: [1, 3, 5, 7] # 또는 "all"

워크플로우: 1. PPTX 언팩 + ppt2html 실행
  2. 슬라이드별 디자인 의도 분류 (LLM)
  3. content-slide-extractor 병렬 호출
  4. 썸네일 이동
  5. 임시 파일 정리
  6. registry.yaml 업데이트
```

### content-slide-extractor (기존)

```yaml
name: content-slide-extractor
description: 단일 슬라이드 YAML/HTML 생성
tools: Read, Write, Bash, Glob, Grep
model: opus
```

### 데이터 흐름

```yaml
# 오케스트레이터 → 에이전트 (입력)
task_input:
  pptx_path: /path/to/file.pptx
  unpacked_dir: /tmp/workspace/unpacked
  html_dir: /tmp/workspace/html
  slide_index: 5
  design_intent: stats-dotgrid
  category: stats
  output_filename: basic-stats-dotgrid1
  source_aspect_ratio: "16:9"

# 에이전트 → 오케스트레이터 (출력)
task_output:
  status: success
  yaml_path: templates/contents/templates/stats/basic-stats-dotgrid1.yaml
  html_path: templates/contents/templates/stats/basic-stats-dotgrid1/template.html
  example_path: templates/contents/templates/stats/basic-stats-dotgrid1/example.html
  shapes_count: 12
  use_for_count: 5
  keywords_count: 7
```

---

## 병렬 처리 전략

### 병렬화 단계

| 단계                 | 병렬화      | 이유                       |
| -------------------- | ----------- | -------------------------- |
| PPTX 언팩 + ppt2html | ❌          | 단일 작업, 순차 실행       |
| 디자인 분류          | ❌          | 전체 슬라이드 분석 후 결정 |
| 슬라이드 추출        | ✅ **병렬** | 각 슬라이드 완전 독립      |
| 썸네일 이동          | ❌          | 단순 파일 작업             |
| Registry 업데이트    | ❌          | 모든 결과 수집 후          |

### Claude Code Task 도구 활용

```python
# 오케스트레이터 의사코드
slides_to_extract = [0, 2, 4, 6, 8]
design_intents = classify_slides(slides_to_extract)  # LLM 자동 분류

# 병렬 Task 호출
for idx, intent in zip(slides_to_extract, design_intents):
    Task(
        subagent_type="content-slide-extractor",
        prompt=f"""
pptx_path: {pptx_path}
unpacked_dir: {unpacked_dir}
html_dir: {html_dir}
slide_index: {idx}
design_intent: {intent}
category: {category_from_intent(intent)}
output_filename: {generate_filename(idx, intent)}
source_aspect_ratio: "16:9"
""",
        model="opus"
    )
```

---

## 파일별 역할

| 파일          | 생성     | 보관          | 설명                                  |
| ------------- | -------- | ------------- | ------------------------------------- |
| slide.html    | ppt2html | 삭제          | 분석용 임시 파일                      |
| slide.png     | ppt2html | thumbnail.png | 미리보기                              |
| template.html | LLM      | 저장          | `{{title}}`, `{{items}}` 등 변수 포함 |
| template.yaml | LLM      | 저장          | 스키마, 카테고리, 메타데이터          |
| example.html  | LLM      | 저장          | 정리된 샘플 데이터                    |

---

## LLM의 example.html 생성 규칙

| 원본 상태              | LLM 처리                  |
| ---------------------- | ------------------------- |
| 정상 텍스트            | 그대로 사용               |
| 깨진 문자, 더미 텍스트 | 실제와 비슷한 샘플로 교체 |
| 의미 없는 숫자         | 적절한 예시 데이터로 교체 |

---

## 인덱스 관리 (하이브리드 방식)

### 저장 구조

- 썸네일은 각 템플릿 폴더에 저장 (원본 관리)
- `registry.yaml`은 스크립트로 자동 생성
- 추출/삭제 시 registry 자동 업데이트

### registry.yaml 예시

```yaml
contents:
  - id: card-4col-01
    category: grid
    name: 4열 카드 레이아웃
    thumbnail: templates/contents/grid/card-4col-01/thumbnail.png
    tags: [card, grid, 4column]

  - id: process-3step-01
    category: process
    name: 3단계 프로세스
    thumbnail: templates/contents/process/process-3step-01/thumbnail.png
    tags: [process, step, flow]
```

---

## 구현 계획

### Phase 1: ppt2html 내장

1. `vendor/ppt2html/` 폴더 생성
2. `/home/jji/project/ppt2html` 복사
3. `.gitignore` 업데이트
4. 호출 테스트

### Phase 2: 오케스트레이터 에이전트 작성

1. `.claude/agents/content-extract-orchestrator.md` 생성
2. 워크플로우 6단계 구현
3. LLM 자동 분류 로직

### Phase 3: content-slide-extractor 수정

1. HTML 출력 기능 추가 (template.html, example.html)
2. ppt2html HTML 참조 로직 추가

### Phase 4: 통합 테스트

1. 단일 슬라이드 추출 테스트
2. 다중 슬라이드 병렬 추출 테스트
3. 에러 핸들링 검증

---

## 수정 필요 파일

### 신규 생성

| 파일                                             | 설명                    |
| ------------------------------------------------ | ----------------------- |
| `vendor/ppt2html/`                               | ppt2html 프로젝트 복사  |
| `.claude/agents/content-extract-orchestrator.md` | 오케스트레이터 에이전트 |

### 기존 파일 수정

| 파일                                        | 수정 내용                            |
| ------------------------------------------- | ------------------------------------ |
| `.claude/agents/content-slide-extractor.md` | HTML 출력 로직 추가                  |
| `.gitignore`                                | `vendor/ppt2html/node_modules/` 추가 |

---

## 검증 방법

```bash
# 1. ppt2html 내장 테스트
node vendor/ppt2html/pptxjs-cli/extract.js sample.pptx ./output
ls ./output/*.html ./output/*.png

# 2. 단일 슬라이드 추출 테스트
# (content-slide-extractor 에이전트 직접 호출)

# 3. 전체 워크플로우 테스트
# (content-extract-orchestrator 에이전트 호출)

# 4. 결과 확인
ls templates/contents/templates/*/
ls templates/contents/thumbnails/*/
cat templates/contents/registry.yaml
```
