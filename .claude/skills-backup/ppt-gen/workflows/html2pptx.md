# HTML to PowerPoint Workflow

템플릿 없이 새 PPT를 생성합니다. HTML을 PowerPoint로 변환합니다.

> **v3.0 Update**: 테마와 컨텐츠가 분리되었습니다. PPT 생성 시 먼저 테마를 선택합니다.

---

## ⚠️ MANDATORY EXECUTION RULES (v5.8)

**이 섹션은 PPT 생성 시 반드시 따라야 하는 실행 규칙입니다. 건너뛰면 안 됩니다.**

### 파이프라인 시작 전 필수 체크리스트

```
□ Step 0: 사전 질문 (MUST NOT SKIP)
  ├─ □ 청중 확인 (경영진/실무자/혼합)
  ├─ □ 발표 시간 확인 (10분/20-30분/1시간+)
  └─ □ 강조점 확인 (기술/일정/팀/균형)

□ Step 1: 테마 선택 (MUST NOT SKIP)
  └─ □ 테마 목록 표시 후 사용자 선택 받기
```

**위 체크리스트를 건너뛰고 바로 슬라이드 생성을 시작하면 안 됩니다.**

### Stage별 필수 호출 규칙

| Stage | 필수 호출 | 저장 필드 |
|-------|----------|----------|
| **Stage 1** | 사전 질문 → 테마 선택 | `setup.presentation`, `setup.theme` |
| **Stage 2** | 아웃라인 작성 | slides[].`title`, `purpose`, `key_points` |
| **Stage 3** | 템플릿 매칭 + **아이콘 결정** | slides[].`template_id`, `match_score`, `icon_decision` |
| **Stage 4** | **아이콘 생성** + HTML 생성 | slides[].`html_file`, `content_bindings`, `assets_generated` |
| **Stage 5** | PPTX 변환 + **디자인 정보 추출** | slides[].`generated`, `design_info`, `evaluation` |

### Stage 3: 아이콘 결정 (MANDATORY)

**템플릿 매칭 후 반드시 아이콘 필요성을 판단합니다.**

```javascript
// 필수 호출
const { analyzeIconNeed } = require('./scripts/icon-decision');
const iconMappings = loadYaml('templates/assets/icon-mappings.yaml');

for (const slide of slides) {
  const iconDecision = analyzeIconNeed(slide, template, iconMappings);
  await session.updateSlide(slide.index, { icon_decision: iconDecision });
}
```

**아이콘 적합 슬라이드 유형**: grid, feature, stats, process, comparison

### Stage 4: 아이콘 생성 및 HTML 삽입 (MANDATORY)

**`icon_decision.needs_icons === true`인 슬라이드는 아이콘을 생성해야 합니다.**

```javascript
// 필수 호출
const { resolveIcons, insertIconsToHtml } = require('./scripts/icon-resolver');

if (slide.icon_decision?.needs_icons) {
  const icons = await resolveIcons(slide, slide.icon_decision, theme, outputDir);
  const updatedHtml = insertIconsToHtml(htmlContent, icons.icons);

  await session.updateSlide(slide.index, {
    assets_generated: { icons: icons.icons, images: [] }
  });
}
```

**아이콘 생성 결과**: `output/{session-id}/icons/*.png`

### Stage 5: 디자인 평가 및 PPTX 변환 (MANDATORY)

**Stage 5는 3단계로 진행됩니다: 평가 → 재시도 루프 → PPTX 변환**

```javascript
// Stage 5: 전체 흐름
const evaluator = require('./scripts/design-evaluator');
const rematcher = require('./scripts/template-rematcher');
const html2pptx = require('./scripts/html2pptx');

const MAX_ATTEMPTS = 3;

for (const slide of slides) {
  let attempt = 1;
  let passed = false;
  const attemptHistory = [];

  while (!passed && attempt <= MAX_ATTEMPTS) {
    // Step 1: HTML 읽기
    const htmlContent = await fs.readFile(slide.html_file, 'utf-8');

    // Step 2: 디자인 평가 (70점 합격 기준)
    const evaluation = await evaluator.evaluate({
      html: htmlContent,
      slide: slide,
      template: await loadTemplate(slide.template_id),
      theme: theme
    });

    attemptHistory.push({
      attempt,
      template_id: slide.template_id,
      score: evaluation.score,
      passed: evaluation.passed,
      issues: evaluation.issues,
      timestamp: new Date().toISOString()
    });

    if (evaluation.passed) {
      passed = true;
      break;
    }

    // Step 3: 불합격 시 재매칭
    if (attempt < MAX_ATTEMPTS) {
      const failedTemplates = attemptHistory.map(h => h.template_id);
      const alternative = rematcher.selectAlternative(slide, failedTemplates, registry);

      if (alternative) {
        slide.template_id = alternative.id;
        // Stage 4로 롤백하여 HTML 재생성
        const newHtml = await renderTemplate(alternative.id, slide.content_bindings, theme);
        await fs.writeFile(slide.html_file, newHtml);
      }
    }

    attempt++;
  }

  // Step 4: 최종 결과 저장
  await session.updateSlide(slide.index, {
    generated: true,
    slide_stage: 5,
    revision: attemptHistory.length - 1,
    design_info: extractDesignInfo(htmlContent, slide),
    evaluation: {
      attempt_number: attempt,
      current_score: attemptHistory[attemptHistory.length - 1].score,
      passed: passed,
      selected_reason: passed ? 'passed' : 'best_of_3'
    },
    attempt_history: attemptHistory
  });
}

// Step 5: PPTX 변환
await html2pptx.convert(outputDir + '/slides', outputDir + '/output.pptx');

// Step 6: stage-5-generation.json 저장 (MANDATORY)
await session.saveStage(5);
```

### 품질 합격 기준 (PASS CRITERIA)

| 항목 | 기준 | 불합격 시 조치 |
|------|------|---------------|
| **슬라이드 평가 점수** | **85점 이상** | Stage 3 롤백 → 템플릿 재매칭 → 재생성 |
| 아이콘 적용 | 필수 슬라이드 100% | icon-resolver 재실행 |
| 콘텐츠 바인딩 | 모든 필드 채워짐 | content_bindings 보완 |

**불합격 슬라이드 처리**:
```
evaluation.score < 85 ?
  → slide_stage = 3 으로 롤백
  → 해당 슬라이드만 Stage 3 → 4 → 5 재진행
  → 재평가 (최대 3회 반복)
```

### 데이터 누적 규칙 (CRITICAL)

**stage-N.json은 반드시 stage-1부터 stage-N까지의 모든 데이터를 포함해야 합니다.**

```
stage-5-generation.json 필수 포함 필드:
├── session (id, title, status, created_at, updated_at)
├── current_stage: 5
├── setup (presentation, theme)
├── slides[] 각 슬라이드:
│   ├── Stage 2: index, title, purpose, key_points
│   ├── Stage 3: template_id, match_score, icon_decision
│   ├── Stage 4: html_file, content_bindings, assets_generated
│   └── Stage 5: generated, design_info, evaluation, slide_stage, revision
└── output (pptx_file, method, generated_at)
```

**검증**: Stage 5 저장 전 모든 슬라이드에 위 필드가 존재하는지 확인

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
├── slides/                 # HTML 파일들
└── output.pptx             # 최종 결과물
```

### 단계별 필수 포함 데이터

| Stage | 파일명 | 필수 포함 데이터 |
|-------|-------|----------------|
| 1 | stage-1-setup.json | `session`, `setup` (theme, presentation) |
| 2 | stage-2-outline.json | 위 + `slides[]` (index, title, purpose, key_points, speaker_notes) |
| 3 | stage-3-matching.json | 위 + slides에 `template_id`, `match_score`, `match_reason`, `layout` 추가 |
| 4 | stage-4-content.json | 위 + slides에 `html_file`, `assets`, `content_bindings` 추가 (v5.3) |
| 5 | stage-5-generation.json | 위 + slides에 `generated`, `design_info`, `slide_stage`, `revision` 추가, `output` 섹션 (v5.3) |

### 올바른 예시 (stage-3-matching.json)

```json
{
  "session": {
    "id": "2026-01-09_100000_a1b2c3d4",
    "title": "프로젝트 수행계획서",
    "status": "in_progress",
    "created_at": "2026-01-09T10:00:00Z",
    "updated_at": "2026-01-09T10:10:00Z"
  },
  "current_stage": 3,
  "setup": {
    "presentation": { "title": "...", "audience": "혼합" },
    "theme": { "id": "deepgreen", "colors": { "primary": "#1E5128" } }
  },
  "slides": [
    {
      "index": 0,
      "title": "표지",
      "purpose": "cover",
      "key_points": ["제목", "날짜"],
      "speaker_notes": "프로젝트 소개",
      "template_id": "deepgreen-cover-centered1",
      "match_score": 0.95,
      "match_reason": "cover 카테고리 정확 매칭"
    }
  ]
}
```

### 잘못된 예시 (현재 문제)

```json
{
  "stage": 3,
  "slides": [
    {
      "index": 0,
      "template_id": "deepgreen-cover-centered1"
    }
  ]
}
```

**문제점**: `session`, `setup` 누락, slides에 `title`, `purpose`, `key_points` 누락

### 단계 전환 시 데이터 병합

각 단계 시작 시:

1. **이전 단계 JSON 로드**: `Read stage-{N-1}-*.json`
2. **데이터 확장**: 각 슬라이드에 새 필드 추가
3. **누적 저장**: 전체 데이터를 `stage-{N}-*.json`에 저장

```python
# 개념적 예시
previous = read_json('stage-2-outline.json')

for slide in previous['slides']:
    slide['template_id'] = matched_template
    slide['match_score'] = score
    slide['match_reason'] = reason

previous['current_stage'] = 3
write_json('stage-3-matching.json', previous)
```

### 세션 재개 지원

중단된 세션 재개 시:

1. 가장 최신 stage-N.json 파일 확인
2. 해당 파일에 모든 이전 데이터가 포함되어 있으므로 즉시 재개 가능
3. 다음 단계부터 진행

---

## CRITICAL: 스크린캡처 방식 금지

**슬라이드 전체를 스크린캡처해서 PPT에 이미지로 삽입하는 것은 절대 금지입니다.**

### 금지 사항

- Playwright/Puppeteer로 HTML 페이지 전체를 스크린샷 캡처
- 슬라이드를 1920x1080 등 Full HD 이미지로 변환
- `stage-5-generation.json`에 `"method": "screenshot"` 사용
- 슬라이드 1장당 이미지 1개로 변환하는 모든 방식

### 필수 사항

- 반드시 `html2pptx.js` 스크립트를 사용하여 HTML 요소를 개별 PPT 오브젝트로 변환
- 텍스트 → 텍스트 상자 (편집 가능)
- 이미지 → 이미지 오브젝트
- 도형 → 도형 오브젝트
- SVG만 예외적으로 PNG 래스터라이즈 허용 (개별 SVG 요소만, 전체 페이지 X)

### 올바른 변환 명령

```bash
node .claude/skills/ppt-gen/scripts/html2pptx.js slides/ output.pptx
```

### 검증 방법

```bash
# PPTX 내 이미지 크기 확인
unzip -l output.pptx | grep media/
file /tmp/extracted/ppt/media/*.png

# 1920x1080 등 슬라이드 크기 이미지가 있으면 잘못된 것
# stage-5-generation.json의 method가 "html2pptx"여야 함
```

---

## Triggers

- "PPT 만들어줘"
- "프레젠테이션 생성해줘"
- "슬라이드 만들어줘"

## Pre-Generation Questions (MANDATORY - 사전 질문)

**PPT 생성 시작 전 반드시 다음 정보를 확인해야 합니다.**

### Step P.1: 사전 질문 (AskUserQuestion 도구 사용)

다음 3가지 질문을 **AskUserQuestion** 도구로 한 번에 물어봅니다:

```json
{
  "questions": [
    {
      "question": "발표 대상(청중)은 누구인가요?",
      "header": "청중",
      "options": [
        {"label": "경영진/스폰서", "description": "고위 의사결정자, 핵심 요약 중심"},
        {"label": "발주기관 담당자", "description": "프로젝트 실무자, 상세 내용 포함"},
        {"label": "내부 팀원", "description": "프로젝트 수행 팀, 실무 중심"},
        {"label": "혼합 (경영진+실무자)", "description": "착수보고 등 공식 발표"}
      ],
      "multiSelect": false
    },
    {
      "question": "발표 시간은 얼마나 되나요?",
      "header": "시간",
      "options": [
        {"label": "10분 내외", "description": "핵심 요약만 (8-10장)"},
        {"label": "20-30분", "description": "주요 내용 상세 (15-20장)"},
        {"label": "1시간 이상", "description": "전체 내용 포함 (25장+)"}
      ],
      "multiSelect": false
    },
    {
      "question": "강조하고 싶은 핵심 포인트가 있나요?",
      "header": "강조점",
      "options": [
        {"label": "기술 아키텍처", "description": "MSA, 클라우드, AI/ML 등"},
        {"label": "프로젝트 일정", "description": "마일스톤, 단계별 계획"},
        {"label": "팀 및 역할", "description": "조직 구성, R&R"},
        {"label": "전체 균형", "description": "모든 섹션 동등하게"}
      ],
      "multiSelect": false
    }
  ]
}
```

### Step P.2: 응답 기반 슬라이드 구성 결정

| 청중 | 시간 | 슬라이드 수 | 상세도 |
|------|------|------------|--------|
| 경영진/스폰서 | 10분 | 8-10장 | 핵심 요약, 비주얼 중심 |
| 경영진/스폰서 | 20-30분 | 12-15장 | 주요 내용 + 요약 |
| 발주기관 담당자 | 20-30분 | 15-20장 | 상세 내용 포함 |
| 혼합 | 20-30분 | 15-20장 | 균형 잡힌 구성 |
| 내부 팀원 | 1시간+ | 25장+ | 전체 상세 내용 |

### Step P.3: 강조점 반영

- **기술 아키텍처**: 아키텍처 다이어그램, 기술 스택 슬라이드 추가
- **프로젝트 일정**: 타임라인, 마일스톤 슬라이드 강조
- **팀 및 역할**: 조직도, R&R 슬라이드 상세화
- **전체 균형**: 모든 섹션 동등 비중

---

## Theme Selection (MANDATORY - 테마 선택)

**PPT 생성 시작 전 반드시 테마를 선택해야 합니다.**

### Step T.1: 테마 목록 표시

사용자에게 다음과 같이 테마 목록을 보여줍니다:

```markdown
## 🎨 테마 선택

사용 가능한 테마 목록입니다:

| # | 테마 | 설명 | 주요 색상 |
|---|------|------|----------|
| 1 | **Deep Green** | 자연스럽고 깔끔한 딥그린 테마 | 🟢 #1E5128 / 🟩 #4E9F3D |
| 2 | **Brand New** | 신선하고 깔끔한 스카이블루 테마 | 🔵 #7BA4BC / 🩷 #F5E1DC |
| 3 | **Default** | 중립적인 기본 블루 테마 | 💙 #2563EB / 🩵 #DBEAFE |

> 원하는 테마 번호를 선택하거나, 직접 색상을 지정할 수 있습니다.
> 예: "1번 테마" 또는 "파란색 계열로"
```

### Step T.2: 사용자 응답 처리

**옵션 A: 번호 선택** (1, 2, 3)
```python
theme_id = ["deepgreen", "brandnew", "default"][user_choice - 1]
theme = load_theme(f"C:/project/docs/templates/themes/{theme_id}.yaml")
```

**옵션 B: 커스텀 색상 지정**
사용자가 직접 색상을 지정하면 임시 테마 생성:
```yaml
theme:
  id: custom
  name: "Custom Theme"

colors:
  primary: "{사용자 지정 색상}"
  secondary: "{자동 계산 - 밝은 버전}"
  accent: "{자동 계산 - 보색}"
  background: "#FFFFFF"
  dark_text: "#1F2937"
  light: "#FFFFFF"
```

### Step T.3: 테마 확인

선택된 테마를 확인합니다:
```markdown
✅ **선택된 테마**: Deep Green
- Primary: #1E5128 (진한 녹색)
- Secondary: #4E9F3D (밝은 녹색)
- Accent: #D8E9A8 (연두색)

이 테마로 진행할까요? (Y/n)
```

### Step T.4: 디자인 토큰 해석

선택된 테마의 색상을 컨텐츠 템플릿에 적용합니다:

```python
def resolve_design_tokens(template: dict, theme: dict) -> dict:
    """디자인 토큰을 테마 색상으로 치환"""
    colors = theme['colors']

    def resolve_value(value):
        if isinstance(value, str) and value in colors:
            return colors[value]
        return value

    def walk_and_resolve(obj):
        if isinstance(obj, dict):
            return {k: walk_and_resolve(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [walk_and_resolve(item) for item in obj]
        else:
            return resolve_value(obj)

    return walk_and_resolve(template)
```

**적용 예시**:
```yaml
# 템플릿 원본 (디자인 토큰)
style:
  fill:
    color: primary    # ← 토큰
  text:
    font_color: light # ← 토큰

# 테마 적용 후 (실제 색상)
style:
  fill:
    color: "#1E5128"  # ← Deep Green primary
  text:
    font_color: "#FFFFFF"  # ← light
```

---

## Design Principles

**CRITICAL**: PPT 생성 전 디자인 분석 필수:

1. **주제 고려**: 프레젠테이션 주제, 톤, 분위기
2. **브랜딩 확인**: 회사/조직 언급 시 브랜드 색상 고려
3. **팔레트 매칭**: 주제에 맞는 색상 선택
4. **접근법 설명**: 코드 작성 전 디자인 선택 설명

### Requirements

- 코드 작성 전 디자인 접근법 설명
- 웹 안전 폰트만 사용: Arial, Helvetica, Times New Roman, Georgia, Courier New, Verdana, Tahoma, Trebuchet MS, Impact
- 명확한 시각적 계층 구조
- 가독성 보장: 충분한 대비, 적절한 텍스트 크기
- 일관성 유지: 패턴, 간격, 시각 언어 반복

### Color Palette Selection

**창의적 색상 선택**:
- 기본값을 넘어 생각하기
- 다양한 각도 고려: 주제, 산업, 분위기, 타겟 오디언스
- 3-5개 색상 구성 (주색 + 보조색 + 강조색)
- 대비 확보: 배경과 텍스트 가독성

**예시 팔레트** (참고용):

| 이름 | 색상 |
|------|------|
| Classic Blue | #1C2833, #2E4053, #AAB7B8, #F4F6F6 |
| Teal & Coral | #5EA8A7, #277884, #FE4447, #FFFFFF |
| Warm Blush | #A49393, #EED6D3, #E8B4B8, #FAF7F2 |
| Black & Gold | #BF9A4A, #000000, #F4F6F6 |
| Forest Green | #191A19, #4E9F3D, #1E5128, #FFFFFF |

## Workflow

### 0. Content Template Search (MANDATORY - DO NOT SKIP)

**중요**: 이 단계를 건너뛰면 안 됩니다. 매칭되는 템플릿이 없는 슬라이드만 직접 디자인합니다.

#### Step 0.1: 슬라이드 목록 작성

콘텐츠를 분석하여 필요한 슬라이드 목록을 먼저 작성합니다:

```markdown
| # | 슬라이드 유형 | 콘텐츠 특성 | 매칭 키워드 |
|---|-------------|------------|-----------|
| 1 | 표지 | 제목, 날짜, 작성자 | cover, 표지 |
| 2 | 목차 | 섹션 리스트 | toc, 목차, 아젠다 |
| 3 | 비교표 | A vs B | comparison, 비교 |
| ... | ... | ... | ... |
```

#### Step 0.2: 분리형 레지스트리 로드 및 매칭 (v4.1)

> **v4.1 Update**: 레지스트리가 카테고리별로 분리되었습니다. 토큰 효율적 검색을 위해 필요한 카테고리만 로드합니다.

**검색 프로세스**:
```
1. 사용자 쿼리에서 카테고리 힌트 추출
2. 카테고리 힌트 있음: registry-{category}.yaml만 로드
3. 카테고리 힌트 없음: registry.yaml(인덱스) → 관련 카테고리 순회
4. 3단계 매칭 알고리즘 실행
```

**카테고리 힌트 추출 예시**:
| 사용자 요청 | 힌트 | 로드 파일 |
|-----------|------|----------|
| "비교 슬라이드" | comparison | registry-comparison.yaml |
| "프로세스 다이어그램" | process | registry-process.yaml |
| "타임라인" | timeline | registry-timeline.yaml |
| "4열 그리드" | grid | registry-grid.yaml |
| "일반 콘텐츠" | (없음) | registry.yaml → 전체 순회 |

**레지스트리 로드**:
```
# 카테고리 힌트가 있는 경우 (효율적)
Read C:/project/docs/templates/contents/registry-comparison.yaml

# 힌트가 없는 경우 (인덱스 먼저)
Read C:/project/docs/templates/contents/registry.yaml
```

---

### 3단계 매칭 알고리즘 (v4.1 검색 메타데이터 활용)

각 템플릿의 검색 메타데이터를 활용하여 3단계로 매칭합니다:

| 단계 | 필드 | 가중치 | 설명 |
|------|------|--------|------|
| **1단계** | `match_keywords` | 60% | 키워드 직접 매칭 (Primary) |
| **2단계** | `expected_prompt` | 30% | 의미적 구조 유사도 (Semantic) |
| **3단계** | `description` | 10% | 설명 텍스트 매칭 (Fallback) |

#### 1단계: match_keywords 매칭 (Primary - 60%)

```python
def match_keywords(query: str, template: dict) -> float:
    """사용자 쿼리 토큰과 match_keywords 배열 비교"""
    query_tokens = tokenize(query)  # ["비교", "장단점", "좌우"]
    keywords = template['match_keywords']  # ["비교", "장단점", "vs", "대조", "좌우", "2열"]

    matched = set(query_tokens) & set(keywords)
    return len(matched) / len(query_tokens)  # 0.0 ~ 1.0
```

**match_keywords 필드 구성** (ppt-extract에서 자동 생성):
- `use_for`: 사용 용도 (3-5개)
- `keywords`: 검색 키워드 (5-10개)
- `prompt_keywords`: 프롬프트 매칭 키워드 (5-10개)
→ 모두 통합하여 `match_keywords` 배열로 저장

#### 2단계: expected_prompt 매칭 (Semantic - 30%)

```python
def match_expected_prompt(query: str, template: dict) -> float:
    """사용자 요청과 expected_prompt의 구조적 유사성 비교"""
    expected = template['expected_prompt']

    # 구조적 요소 추출
    query_elements = extract_structural_elements(query)
    # 예: {"열수": 2, "형태": "비교", "요소": ["불릿", "텍스트"]}

    expected_elements = extract_structural_elements(expected)
    # 예: {"열수": 2, "형태": "비교", "요소": ["불릿", "리스트"]}

    return calculate_structural_similarity(query_elements, expected_elements)
```

**expected_prompt 참조 예시**:
```yaml
# comparison-2col1의 expected_prompt
expected_prompt: |
  2열 불릿 비교 슬라이드를 만들어줘.
  - 좌우 2열로 배치된 비교 레이아웃
  - 각 열에 중제목 + 불릿 포인트 리스트
  - 하단에 요약 또는 결론 텍스트 박스

# 사용자 요청: "장단점을 좌우로 비교하는 슬라이드"
# → 구조 유사: 2열, 비교, 좌우 ✓
```

#### 3단계: 최종 점수 계산

```python
def calculate_match_score(query: str, template: dict) -> float:
    """가중 평균으로 최종 매칭 점수 계산"""
    keyword_score = match_keywords(query, template) * 0.6    # 60%
    prompt_score = match_expected_prompt(query, template) * 0.3  # 30%
    desc_score = fuzzy_match(query, template['description']) * 0.1  # 10%

    return keyword_score + prompt_score + desc_score
```

---

### 매칭 예시 (v4.1)

**사용자 요청**: "장단점을 좌우로 비교하는 슬라이드"

**Step 1: 카테고리 힌트 추출**
- 힌트: "비교" → `comparison`
- 로드: `registry-comparison.yaml`

**Step 2: 매칭 분석**

| 템플릿 ID | match_keywords 매칭 | expected_prompt 유사도 | 최종 점수 |
|----------|-------------------|----------------------|----------|
| comparison-2col1 | ["비교", "장단점", "좌우"] = 1.0 × 0.6 | 구조 일치 = 0.9 × 0.3 | **0.87** ✓ |
| comparison-4col-stats | ["비교"] = 0.33 × 0.6 | 구조 불일치 = 0.2 × 0.3 | 0.26 |

**Step 3: 선택**
→ `comparison-2col1` 선택 (최고 점수 0.87)

---

### 매칭 결과 기록 필드

Stage 3 JSON에 다음 필드를 기록합니다:

```json
{
  "template_id": "comparison-2col1",
  "match_score": 0.87,
  "match_reason": "match_keywords 3/3 일치, expected_prompt 구조 유사",
  "match_details": {
    "keyword_score": 0.6,
    "prompt_score": 0.27,
    "category_hint": "comparison"
  }
}
```

#### Step 0.3: 매칭 결과 테이블 작성 (필수)

**반드시** 매칭 결과를 테이블로 정리합니다 (v4.1 형식):

```markdown
| # | 슬라이드 | 카테고리 | 매칭 템플릿 | 점수 | 매칭 근거 |
|---|---------|---------|-----------|------|----------|
| 1 | 표지 | - | cover-centered1 | 0.95 | category 힌트 |
| 2 | 목차 | - | toc-simple1 | 0.90 | category 힌트 |
| 3 | 섹션 구분 | - | section-number1 | 0.88 | category 힌트 |
| 4 | 기대효과 (30%, 99%) | stats | stats-donut-2col | 0.85 | match_keywords: 퍼센트, 통계 |
| 5 | 3가지 전략 | grid | grid-3col1 | 0.82 | match_keywords: 3열, 그리드 |
| 6 | 프로세스 | process | process-linear1 | 0.88 | match_keywords: 프로세스, 단계 |
| 7 | 일정 | timeline | timeline-horizontal | 0.91 | match_keywords: 타임라인, 일정 |
| 8 | 비교표 | comparison | ❌ 없음 | - | 직접 디자인 필요 |
```

**매칭 근거 표기법**:
- `category 힌트`: cover, toc, section, closing 등 명확한 카테고리
- `match_keywords: [키워드들]`: 1단계 키워드 매칭으로 선택
- `expected_prompt 유사`: 2단계 의미적 유사도로 선택
- `❌ 없음`: 모든 템플릿 점수 0.5 미만, 직접 디자인 필요

#### Step 0.4: 템플릿 YAML 기반 HTML 생성 (v6.0 - Option C 하이브리드)

**Stage 4에서 템플릿 YAML의 완전성에 따라 렌더링 방식을 선택합니다.**

> **상세 설계 문서**: `.claude/skills/ppt-gen/docs/yaml-rendering-design.md`

##### 0.4.1 shapes 완전성 체크

템플릿 YAML을 로드한 후 shapes 배열의 완전성을 판단합니다:

| 조건 | 판정 | 렌더링 방식 |
|------|------|------------|
| shapes 있음 + `{{placeholder}}` 형식 | ✅ 완전 | 스크립트 `renderFromYaml()` |
| shapes 있음 + 하드코딩 텍스트 | ⚠️ 불완전 | LLM이 geometry 참고하여 직접 디자인 |
| shapes 없음 | ❌ 없음 | LLM이 design_intent 기반 직접 디자인 |
| 차트/복잡한 다이어그램 | 🎨 커스텀 | LLM 직접 디자인 |

**완전성 판단 예시**:
```yaml
# ✅ 완전한 shapes (스크립트 렌더링)
shapes:
- geometry: { x: 10%, y: 20%, cx: 30%, cy: 15% }
  text:
    placeholders:
    - text: '{{title}}'      # placeholder 형식 ✓
    - text: '{{subtitle}}'   # placeholder 형식 ✓

# ⚠️ 불완전한 shapes (LLM 직접 디자인, geometry 참고)
shapes:
- geometry: { x: 10%, y: 20%, cx: 30%, cy: 15% }
  text: "하드코딩된 샘플 텍스트"  # placeholder 없음 ✗
```

##### 0.4.2 렌더링 워크플로우

```
template YAML 로드
       │
       ▼
┌──────────────────┐
│ shapes 완전성    │
│ 체크             │
└──────┬───────────┘
       │
   ┌───┴───────────────┐
   │                   │
   ▼                   ▼
┌────────┐         ┌────────┐
│ 완전   │         │ 불완전 │
└───┬────┘         └───┬────┘
    │                  │
    ▼                  ▼
┌────────────────┐ ┌────────────────┐
│ renderFromYaml │ │ LLM 직접 디자인 │
│ (스크립트)     │ │ (geometry 참고) │
└────────────────┘ └────────────────┘
```

##### 0.4.3 스크립트 렌더링 (shapes 완전 시)

```javascript
const { renderTemplate, loadTemplate } = require('./scripts/html-templates');

// shapes가 완전한 경우
const template = await loadTemplate(templateId);
if (isShapesComplete(template)) {
  const html = await renderTemplate(templateId, data, theme);
  // ...
}
```

##### 0.4.4 LLM 직접 디자인 (shapes 불완전 시)

shapes가 불완전하거나 없는 경우, LLM이 직접 HTML을 작성합니다.

**geometry 참고 규칙** (720pt × 405pt 캔버스):
```
left   = x%  × 7.2   (pt)
top    = y%  × 4.05  (pt)
width  = cx% × 7.2   (pt)
height = cy% × 4.05  (pt)
```

**LLM 디자인 시 준수사항**:
1. 템플릿 YAML의 geometry가 있으면 대략적인 위치/크기 참고
2. `design_intent` 필드의 스타일 의도 반영
3. 테마 색상 토큰 적용 (primary, secondary, accent 등)
4. 캔버스 크기 720pt × 405pt 준수

**예시** (불완전한 shapes를 참고한 LLM 디자인):
```yaml
# 템플릿 YAML (불완전)
shapes:
- geometry: { x: 10%, y: 20%, cx: 80%, cy: 60% }
  text: "샘플 텍스트"
```

```html
<!-- LLM이 geometry 참고하여 생성한 HTML -->
<div style="position: absolute; left: 72pt; top: 81pt; width: 576pt; height: 243pt;">
  <p>실제 콘텐츠</p>
</div>
```

##### 0.4.5 Stage 4 데이터 저장

```javascript
for (const slide of slides) {
  const template = await loadTemplate(slide.template_id);
  let html;
  let renderMethod;

  if (isShapesComplete(template)) {
    // 스크립트 렌더링
    html = await renderTemplate(slide.template_id, data, theme);
    renderMethod = 'yaml_script';
  } else {
    // LLM 직접 디자인 (geometry 참고)
    html = await generateHtmlWithLLM(slide, template, theme);
    renderMethod = 'llm_design';
  }

  // HTML 파일 저장
  const htmlPath = `slides/slide-${String(slide.index + 1).padStart(3, '0')}.html`;
  await fs.writeFile(path.join(outputDir, htmlPath), html);

  // Stage 4 데이터 저장
  await session.updateSlide(slide.index, {
    html_file: htmlPath,
    content_bindings: data,
    render_method: renderMethod,  // 렌더링 방식 기록
    assets_generated: { icons: [], images: [] }
  });
}

// stage-4-content.json 저장 (MANDATORY)
await session.saveStage(4);
```

**렌더링 우선순위** (Option C 하이브리드):
1. shapes 완전 → `renderFromYaml()` 스크립트 호출
2. shapes 불완전 → LLM이 geometry 참고하여 직접 디자인
3. shapes 없음 → LLM이 design_intent 기반 직접 디자인

**매칭된 템플릿이 있는 경우**:

1. `templates/contents/templates/{category}/{id}.yaml` 자동 로드
2. `shapes[]` 구조에서 **shape_source 타입 확인** (v3.1)
3. shape_source 타입별 처리 (아래 참조)
4. % 단위를 pt로 자동 변환 (720pt x 405pt 기준)
5. HTML 자동 생성

---

#### Step 0.4.1: Shape Source 기반 렌더링 (v3.1 NEW)

템플릿의 각 shape는 **shape_source** 필드에 따라 다르게 처리됩니다:

**Shape Source 타입별 처리**:

| shape_source | 처리 방식 | 설명 |
|--------------|----------|------|
| `ooxml` | OOXML fragment 직접 사용 | 좌표/색상만 치환 후 slide.xml에 삽입 |
| `svg` | SVG → OOXML 변환 | `<a:custGeom>` path로 변환 |
| `reference` | 참조 대상 로드 | Object 파일에서 OOXML 복사 |
| `html` | html2pptx.js 변환 | 개별 HTML 요소를 PPT 오브젝트로 변환 (스크린샷 금지) |
| `description` | LLM 생성 또는 HTML 변환 | 자연어 설명 기반 생성 |

**1. OOXML 타입 처리** (`shape_source: ooxml`):

```python
def render_ooxml_shape(shape, theme, target_canvas):
    """OOXML fragment를 직접 재사용"""
    xml = shape['ooxml']['fragment']

    # 1. 좌표 스케일링 (EMU 단위)
    original_emu = shape['ooxml']['emu']
    scale_x = target_canvas['width_emu'] / 12192000  # 원본 16:9 기준
    scale_y = target_canvas['height_emu'] / 6858000

    xml = scale_emu_coordinates(xml, original_emu, scale_x, scale_y)

    # 2. 테마 색상 치환
    if theme.get('apply_colors') and shape.get('style'):
        original_colors = shape['ooxml'].get('colors', {})
        for color_type, original_hex in original_colors.items():
            if original_hex and shape['style'].get('fill', {}).get('color'):
                token = shape['style']['fill']['color']
                new_hex = theme['colors'].get(token, original_hex)
                xml = xml.replace(original_hex.replace('#', ''), new_hex.replace('#', ''))

    return xml

# slide.xml에 직접 삽입
def insert_shape_to_slide(slide_xml, shape_xml):
    """<p:spTree>에 shape 추가"""
    sp_tree = slide_xml.find('.//p:spTree', NS)
    shape_element = etree.fromstring(shape_xml)
    sp_tree.append(shape_element)
```

**2. Reference 타입 처리** (`shape_source: reference`):

```python
def render_reference_shape(shape, theme, target_canvas):
    """Object 파일에서 참조 로드"""
    ref = shape['reference']

    # Object 파일 로드
    object_path = f"templates/contents/{ref['object']}"
    object_yaml = load_yaml(object_path)

    # 컴포넌트들의 OOXML 수집
    result_xml = []
    for component in object_yaml['object']['components']:
        if component.get('shape_source') == 'ooxml':
            xml = component['ooxml']['fragment']

            # 오버라이드 적용 (있는 경우)
            if ref.get('override'):
                xml = apply_overrides(xml, ref['override'], component['id'])

            result_xml.append(xml)

    return result_xml
```

**3. Description 타입 처리** (`shape_source: description`):

```python
def render_description_shape(shape, theme, target_canvas):
    """자연어 설명을 HTML로 변환"""
    desc = shape['description']['text']
    hints = shape['description'].get('hints', {})

    # geometry와 hints를 기반으로 HTML 생성
    geometry = shape['geometry']
    style = shape.get('style', {})

    html = f"""
    <div style="
        position: absolute;
        left: {geometry['x']};
        top: {geometry['y']};
        width: {geometry['cx']};
        height: {geometry['cy']};
        background: {resolve_color(style.get('fill', {}).get('color'), theme)};
        border-radius: {style.get('rounded_corners', 0)}pt;
    ">
        <!-- 설명 기반 콘텐츠 -->
    </div>
    """

    return html
```

**렌더링 흐름도**:

```
템플릿 로드
  │
  ▼
┌─────────────────────────────────────┐
│ shape_source 타입 확인               │
└─────────────────────────────────────┘
  │
  ├── ooxml ──────► OOXML fragment 직접 사용
  │                  ├── 좌표 스케일링
  │                  └── 색상 토큰 치환
  │
  ├── reference ──► Object 파일 로드
  │                  ├── 컴포넌트 OOXML 수집
  │                  └── 오버라이드 적용
  │
  ├── svg ────────► SVG → OOXML 변환
  │                  └── <a:custGeom> 생성
  │
  ├── html ───────► html2pptx.js 처리
  │                  └── 개별 요소를 PPT 오브젝트로 변환 (스크린샷 금지)
  │
  └── description ► HTML/CSS 생성
                     └── html2pptx 처리
```

---

**기존 방식 (shape_source가 없는 경우)**:

shape_source 필드가 없는 레거시 템플릿은 기존 방식대로 처리합니다:

1. **이미지 필드** 확인: `type: picture`인 경우 `image.description` 읽기
2. **배경** 확인: `background.type: image`인 경우 `background.image.description` 읽기
3. geometry와 style을 HTML/CSS로 변환

**이미지 설명 활용** (picture 타입):

템플릿의 이미지 설명을 참고하여 적절한 이미지를 선택하거나 생성합니다.

```yaml
# 템플릿 YAML
shapes:
  - id: "hero-image"
    type: picture
    geometry: {x: 50%, y: 0%, cx: 50%, cy: 100%}
    image:
      description: "도시 야경 사진, 고층 빌딩과 조명이 반짝이는 모습"
      purpose: hero
      fit: cover
```

→ HTML 생성 시 이미지 설명에 맞는 이미지를 배치하거나, 설명을 참고하여 유사한 분위기의 이미지 검색/생성

**배경 이미지 활용**:

```yaml
# 템플릿 YAML
background:
  type: image
  image:
    description: "어두운 그라데이션 배경, 미세한 기하학적 패턴"
    fit: cover
    opacity: 0.3
```

→ HTML에서 배경 스타일링 시 설명에 맞는 이미지 또는 유사한 효과 적용

**geometry 변환 공식** (16:9 기준):
- x(pt) = x(%) × 7.2
- y(pt) = y(%) × 4.05
- width(pt) = cx(%) × 7.2
- height(pt) = cy(%) × 4.05

**예시** - deepgreen-cover1.yaml shapes → HTML:

```yaml
# YAML
- id: "label-box"
  geometry: { x: 25%, y: 12%, cx: 50%, cy: 8% }
  style: { fill: { color: primary }, rounded_corners: 25 }
```

```html
<!-- HTML 변환 -->
<div style="position: absolute; left: 180pt; top: 49pt; width: 360pt; height: 32pt;
            background: #1E5128; border-radius: 25pt;">
  <p>라벨 텍스트</p>
</div>
```

#### Step 0.5: 매칭 없는 슬라이드만 직접 디자인

**매칭 결과 테이블에서 ❌ 표시된 슬라이드만** Step 1 (Design Principles)로 진행합니다.

**금지**: 매칭 가능한 템플릿이 있는데 직접 디자인하는 것

---

### 0.6 Asset Recommendation (아이콘/이미지 추천)

템플릿 매칭 후, 슬라이드에 필요한 아이콘과 이미지를 자동 추천합니다.

#### Step 0.6.1: 에셋 필요 파악

매칭된 템플릿의 shapes에서 `type: icon` 또는 `type: picture` 플레이스홀더 확인:

```markdown
| # | Slide | Template | Asset Placeholders |
|---|-------|----------|-------------------|
| 4 | 4대 핵심기능 | grid-4col-icon1 | 4x icon |
| 5 | 제품 소개 | image-text1 | 1x picture |
```

#### Step 0.6.2: 아이콘 선택 (우선순위)

**1단계: react-icons 검색**

콘텐츠 키워드로 `templates/assets/icon-mappings.yaml` 매칭:

```yaml
# icon-mappings.yaml 참조
보안 → fa/FaShieldAlt
속도 → fa/FaBolt
데이터 → fa/FaDatabase
AI → fa/FaBrain
```

**2단계: SVG 직접 생성 (대안)**

react-icons에서 적합한 아이콘을 찾지 못한 경우 간단한 SVG 생성.

**아이콘 래스터라이즈** (테마 색상 적용):

```bash
node scripts/rasterize-icon.js fa/FaShieldAlt "#1E5128" 256 shield.png
node scripts/rasterize-icon.js fa/FaBolt "#1E5128" 256 bolt.png
```

#### Step 0.6.3: 이미지 선택

**1단계: registry.yaml 검색**

기존 에셋에서 태그/키워드 매칭:

```bash
# asset-manager.py 검색
python scripts/asset-manager.py search --tag "AI" --tag "technology"
```

**2단계: 웹 크롤링 (필요 시)**

```bash
python scripts/asset-manager.py crawl "https://example.com/images" --tag "hero"
```

**3단계: 이미지 생성 프롬프트 출력**

매칭되는 이미지가 없으면 외부 서비스용 프롬프트 생성:

```bash
node scripts/image-prompt-generator.js --subject "AI 기술 네트워크" --purpose hero --industry tech
```

출력:
```
Prompt: cinematic wide shot of AI technology network, professional photography,
        dramatic lighting, high contrast, futuristic, digital, blue and purple tones,
        8k resolution, highly detailed

Negative Prompt: text, watermark, logo, low quality, blurry, cartoon, anime
Aspect Ratio: 16:9 (1920x1080)
```

> **Note**: 프롬프트만 생성됨. 이미지 생성은 DALL-E, Midjourney 등 외부 서비스에서 수동 진행.
> (MCP 통한 이미지 생성 모델 연동 미구현)

#### Step 0.6.4: 에셋 추천 테이블 출력 (필수)

**반드시** 에셋 추천 결과를 테이블로 정리:

```markdown
| # | Slide | Type | Keyword | Asset | Source |
|---|-------|------|---------|-------|--------|
| 4-1 | 핵심기능 | icon | 보안 | FaShieldAlt | react-icons |
| 4-2 | 핵심기능 | icon | 속도 | FaBolt | react-icons |
| 4-3 | 핵심기능 | icon | 데이터 | FaDatabase | react-icons |
| 4-4 | 핵심기능 | icon | 자동화 | FaCogs | react-icons |
| 5 | 제품소개 | picture | - | ❌ 프롬프트 생성 | image-prompt |
```

#### Step 0.6.5: HTML에 에셋 삽입

**아이콘 삽입**:
```html
<div class="icon-container">
  <img src="file:///C:/project/docs/workspace/icons/shield.png"
       style="width: 40pt; height: 40pt;">
</div>
```

**이미지 삽입**:
```html
<div class="image-area">
  <img src="file:///C:/project/docs/templates/assets/images/hero-ai.png"
       style="width: 100%; height: 100%; object-fit: cover;">
</div>
```

---

### 1. MANDATORY - Read Full Guide

**반드시** 상세 가이드 전체를 읽으세요:

```
Read .claude/skills/ppt-gen/html2pptx.md (전체 파일)
```

이 가이드에는 다음이 포함됩니다:
- HTML 슬라이드 생성 규칙
- html2pptx.js 라이브러리 사용법
- PptxGenJS API (차트, 테이블, 이미지)
- 색상 규칙 (# 제외)

### 2. Create HTML Slides

각 슬라이드별 HTML 파일 생성:
- 16:9: `width: 720pt; height: 405pt`
- 텍스트는 반드시 `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>` 태그 내
- `class="placeholder"`: 차트/테이블 영역
- 그라디언트/아이콘은 PNG로 먼저 래스터라이즈

### 2.5 Content Bindings 기록 (v5.3 NEW)

**HTML 생성 시 사용된 콘텐츠 구조를 `content_bindings`에 기록합니다.**

이 단계는 슬라이드 재사용, 템플릿 학습, 수정 루프에 필수입니다.

#### Step 4.5.1: content_bindings 구조

```json
{
  "index": 3,
  "title": "프로젝트 기본 정보",
  "purpose": "stats",
  "template_id": "basic-stats-cards",
  "html_file": "slides/slide-004-info.html",
  "content_bindings": {
    "title": "프로젝트 기본 정보",
    "subtitle": null,
    "items": [
      { "number": "01", "title": "발주기관", "description": "(주)글로벌물류" },
      { "number": "02", "title": "수행사", "description": "(주)테크솔루션" },
      { "number": "03", "title": "계약금액", "description": "15억원" },
      { "number": "04", "title": "계약기간", "description": "12개월" }
    ],
    "footer": {
      "page_number": "4",
      "project_name": "스마트 물류관리 시스템"
    }
  }
}
```

#### Step 4.5.2: 콘텐츠 타입별 바인딩

| 슬라이드 유형 | content_bindings 구조 |
|--------------|----------------------|
| **cover** | `title`, `subtitle`, `date`, `company` |
| **toc** | `title`, `items[{number, title}]` |
| **section** | `title`, `section_number`, `key_points[]` |
| **stats** | `title`, `items[{number, title, description, value}]` |
| **grid** | `title`, `items[{title, description, icon, features[]}]` |
| **comparison** | `title`, `columns[{header, items[]}]` |
| **timeline** | `title`, `items[{period, title, description}]` |
| **process** | `title`, `steps[{number, title, description}]` |
| **table** | `title`, `table{headers[], rows[][]}` |
| **hierarchy** | `title`, `root{title, children[{title, children[]}]}` |
| **closing** | `title`, `contact{name, title, email}` |

#### Step 4.5.3: content_bindings 생성 시점

```
HTML 생성 시
  │
  ├── 원본 콘텐츠 분석 (key_points, 소스 문서)
  │
  ├── HTML 요소 생성
  │
  └── content_bindings 동시 기록  ← 이 시점!
      │
      └── stage-4-content.json에 저장
```

**중요**: HTML에 렌더링된 모든 텍스트/데이터가 content_bindings에 구조화되어야 합니다.

---

### 3. Convert to PowerPoint

```javascript
const pptxgen = require('pptxgenjs');
const html2pptx = require('./html2pptx');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_16x9';

const { slide, placeholders } = await html2pptx('slide1.html', pptx);

// 차트 추가 (placeholder 영역에)
if (placeholders.length > 0) {
    slide.addChart(pptx.charts.BAR, chartData, placeholders[0]);
}

await pptx.writeFile('output.pptx');
```

### 4. Visual Validation

```bash
python scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4
```

썸네일 이미지 검토:
- **텍스트 잘림**: 헤더, 도형, 슬라이드 가장자리에 의한 잘림
- **텍스트 겹침**: 다른 텍스트나 도형과 겹침
- **위치 문제**: 슬라이드 경계나 다른 요소와 너무 가까움
- **대비 문제**: 배경과 텍스트 대비 부족

문제 발견 시 HTML 수정 후 재생성.

---

### 4.5 Design Info 추출 (v5.3 NEW)

**PPTX 변환 완료 후, 슬라이드별 디자인 정보를 `design_info`에 기록합니다.**

이 정보는 템플릿 학습, 디자인 재사용, 문서화에 활용됩니다.

#### Step 5.3.1: design_info 구조

```json
{
  "index": 8,
  "title": "핵심 추진 전략",
  "design_info": {
    "layout": {
      "type": "grid",
      "grid": { "columns": 3, "rows": 1, "column_weights": [1, 1, 1] },
      "direction": "horizontal"
    },
    "zones": [
      {
        "id": "title-zone",
        "role": "slide_title",
        "geometry": { "x": 36, "y": 20, "cx": 648, "cy": 40 },
        "placeholder_type": "TITLE"
      },
      {
        "id": "content-zone",
        "role": "main_content",
        "geometry": { "x": 36, "y": 80, "cx": 648, "cy": 280 },
        "placeholder_type": "BODY",
        "element_type": "card-grid",
        "element_count": 3
      },
      {
        "id": "footer-zone",
        "role": "footer",
        "geometry": { "x": 36, "y": 380, "cx": 648, "cy": 20 }
      }
    ],
    "shapes_summary": {
      "total_count": 12,
      "by_type": { "rectangle": 6, "text_box": 4, "circle": 2 },
      "patterns": [
        { "type": "numbered_card", "count": 3, "elements": ["number_circle", "title_text", "description_text", "features_list"] }
      ]
    },
    "color_tokens": {
      "primary": "#002452",
      "secondary": "#C51F2A",
      "accent": "#4B6580",
      "background": "#FFFFFF",
      "dark_text": "#262626",
      "light": "#FFFFFF"
    },
    "typography": {
      "slide_title": { "font_size_pt": 24, "font_weight": "bold", "font_color": "#002452" },
      "card_title": { "font_size_pt": 14, "font_weight": "bold", "font_color": "#262626" },
      "body": { "font_size_pt": 11, "font_weight": "normal", "font_color": "#262626", "line_height": 1.4 }
    },
    "spacing": {
      "slide_margin": { "top": 20, "right": 36, "bottom": 25, "left": 36 },
      "section_gap": 24,
      "item_gap": 16,
      "card_padding": 12
    },
    "constraints": {
      "max_items": 4,
      "min_items": 2,
      "title_max_chars": 30,
      "description_max_lines": 3
    },
    "visual_properties": {
      "balance": "symmetric",
      "hierarchy": 3,
      "emphasis_style": "numbered"
    }
  }
}
```

#### Step 5.3.2: design_info 추출 대상

| 필드 | 추출 대상 | 설명 |
|------|----------|------|
| **layout** | HTML 구조 | grid/radial/sequential/freeform/split |
| **zones** | HTML 영역 | 각 콘텐츠 영역의 역할과 위치 |
| **shapes_summary** | HTML 요소 | 도형 개수, 타입별 분류, 패턴 |
| **color_tokens** | CSS 색상 | 사용된 색상 토큰 매핑 |
| **typography** | CSS 폰트 | 타이포그래피 정보 |
| **spacing** | CSS 간격 | 마진, 패딩, 갭 |
| **constraints** | 콘텐츠 | 최대/최소 아이템, 문자 수 제한 |
| **visual_properties** | 전체 | 균형, 계층, 강조 스타일 |

#### Step 5.3.3: 수정 루프 지원 (v5.3 NEW)

개별 슬라이드만 수정하는 경우를 지원합니다:

```json
{
  "index": 5,
  "slide_stage": 5,      // 현재 스테이지 (2~5)
  "revision": 0,         // 수정 횟수 (0 = 최초 생성)
  "revision_history": [] // 선택적: 수정 이력
}
```

**수정 루프 시나리오**:

```
전체 생성 완료 (모든 slides[].slide_stage = 5)
        │
        ▼
5번 슬라이드 수정 요청: "템플릿 바꿔줘"
        │
        ▼
slides[5].slide_stage = 3 (Matching 단계로 롤백)
slides[5].revision = 1
        │
        ▼
5번만 Stage 3 → 4 → 5 진행
        │
        ▼
slides[5].slide_stage = 5
slides[5].revision_history = [
  { "revision": 0, "template_id": "old-template", "timestamp": "...", "reason": "초기 생성" },
  { "revision": 1, "template_id": "new-template", "timestamp": "...", "reason": "사용자 요청" }
]
```

#### Step 5.3.4: design_info 생성 시점

```
PPTX 변환 완료 (html2pptx.js)
        │
        ├── 각 슬라이드 HTML 분석
        │   ├── DOM 구조 → layout 추출
        │   ├── CSS → typography, spacing, colors 추출
        │   └── 요소 수 → shapes_summary 추출
        │
        └── design_info 기록
            │
            └── stage-5-generation.json에 저장
```

**중요**: design_info는 PPTX 변환 성공 후에만 기록됩니다 (`generated: true` 슬라이드만).

### 5. HTML 작성 규칙 (CRITICAL)

**html2pptx.js에서 지원되지 않는 태그가 있습니다. 반드시 대체 방법을 사용하세요.**

#### 5.1 지원되지 않는 태그

| 태그 | 상태 | 대체 방법 |
|------|------|----------|
| `<table>`, `<tr>`, `<td>`, `<th>` | ❌ 미지원 | `<div>` + display: flex |
| `<span>` (텍스트 포함) | ❌ 변환 안 됨 | `<p>` 또는 `<div><p>` |

**표 레이아웃 예시**:
```html
<!-- ❌ 잘못된 방법 (변환 안 됨) -->
<table>
  <tr><th>구분</th><th>내용</th></tr>
  <tr><td>PM</td><td>관리</td></tr>
</table>

<!-- ✅ 올바른 방법 -->
<div class="table-row header">
  <div class="cell"><p>구분</p></div>
  <div class="cell"><p>내용</p></div>
</div>
<div class="table-row">
  <div class="cell"><p>PM</p></div>
  <div class="cell"><p>관리</p></div>
</div>

<style>
.table-row { display: flex; }
.table-row.header { background: #002452; }
.table-row.header .cell p { color: white; }
.cell { flex: 1; padding: 10pt 8pt; }
</style>
```

#### 5.2 지원되는 태그

| 태그 | 용도 |
|------|------|
| `<div>` | 배경, 테두리, 그림자 (shape) |
| `<p>`, `<h1>`-`<h6>` | 텍스트 |
| `<ul>`, `<ol>`, `<li>` | 리스트 |
| `<img>` | 이미지 |
| `<svg>` | 벡터 (PNG로 래스터라이즈) |

---

### 6. HTML 검증 및 수정 (필수)

HTML 슬라이드 생성 후 **반드시** 다음 검증을 수행하고 문제 발견 시 수정합니다.

#### 6.1 검증 체크리스트

모든 슬라이드에 대해 다음을 확인:

| 검증 항목 | 기준 | 수정 방법 |
|----------|------|----------|
| **색상 대비** | 어두운 배경 + 밝은 텍스트 또는 그 반대 | rgba 투명 배경 → 불투명 solid 색상 |
| **오버플로우** | 720pt × 405pt 내 | 폰트 크기 축소, 마진 조정 |
| **CSS 클래스** | 정의 ↔ 사용 일치 | 누락 클래스 추가 |
| **태그 규칙** | 텍스트는 `<p>`, `<h1-6>` 내에만 | wrapper 태그 추가 |
| **콘텐츠 누락** | 원본 데이터와 비교 | 누락된 콘텐츠 추가 |

#### 6.2 색상 대비 검사 규칙

**문제 패턴 감지**:
```css
/* 문제: 투명 배경에 밝은 텍스트 */
.element { background: rgba(183,208,212,0.1); }
.element span { color: white; }

/* 수정: solid 어두운 배경으로 변경 */
.element { background: #002452; }
```

**테마 색상 활용** (동국시스템즈 기준):
- 어두운 배경: `#002452`, `#4B6580`, `#C51F2A`
- 밝은 텍스트: `white`, `#FFFFFF`
- 밝은 배경: `#FFFFFF`, `#F8F9FA`
- 어두운 텍스트: `#262626`, `#002452`

**검사 명령어**:
```bash
# 투명 배경 찾기 (rgba 알파값 0.0~0.2)
grep -n "rgba.*0\.[0-2])" slides/*.html

# 밝은 텍스트 찾기
grep -n "color:\s*white\|color:\s*#fff" slides/*.html
```

#### 6.3 검증/수정 루프 (최대 3회)

```
HTML 생성 완료
    ↓
[1] 모든 HTML 파일 읽기
    ↓
[2] 각 슬라이드 검증:
    - rgba 배경 + white/light 텍스트 조합 찾기
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

**CRITICAL**: PPTX 변환 전 반드시 이 검증 단계를 수행해야 합니다.

---

### 6.5 디자인 평가 루프 (v5.7 NEW)

**기술 검증 통과 후, LLM이 디자인 품질을 평가하고 불합격 시 재매칭합니다.**

#### 6.5.1 평가 기준 (100점 만점)

| 카테고리 | 배점 | 평가 항목 |
|---------|-----|----------|
| **레이아웃** | 25점 | 정렬 일관성(10), 여백 균형(8), 시각적 균형(7) |
| **타이포그래피** | 20점 | 가독성(10), 계층 구조(5), 줄간격/자간(5) |
| **색상** | 20점 | 대비(10), 조화(5), 강조 적절성(5) |
| **콘텐츠 적합성** | 25점 | 템플릿 매칭(15), 정보량(10) |
| **시각 요소** | 10점 | 아이콘/이미지(5), 장식 요소(5) |

#### 6.5.2 합격/불합격 기준

| 점수 | 결과 |
|-----|------|
| **70점 이상** | 합격 → Stage 5 진행 |
| **70점 미만** | 불합격 → 재매칭 |

#### 6.5.3 자동 불합격 (Critical Failures)

점수와 관계없이 불합격:
- `overflow`: 텍스트/요소가 720x405pt 초과
- `contrast_failure`: 대비 4.5:1 미만 (WCAG AA 미달)
- `element_count_mismatch`: 템플릿과 콘텐츠 수 차이 2개 이상
- `content_missing`: title, key_points 미표시

#### 6.5.4 평가 루프 흐름

```
기술 검증 통과 (6.3)
    │
    ▼
디자인 평가 (attempt = 1)
    │
    ├─ 합격 (≥70) ─────────────────► Stage 5: PPTX 변환
    │
    └─ 불합격 (<70 또는 Critical)
           │
           ▼
       attempt < 3?
           │
           ├─ Yes → 재매칭 (실패 템플릿 제외)
           │            │
           │            └───► HTML 재생성 → 기술 검증 → 디자인 평가 (attempt++)
           │
           └─ No → 최고 점수 디자인 선택 (best_of_3)
                       │
                       ▼
                   Stage 5: PPTX 변환
```

#### 6.5.5 평가 모듈 사용

```javascript
const evaluator = require('./scripts/design-evaluator');
const rematcher = require('./scripts/template-rematcher');

// 단일 슬라이드 평가
const result = await evaluator.evaluate({
  html: htmlContent,
  slide: slideData,
  template: templateInfo,
  theme: themeColors
});

// 불합격 시 재매칭
if (!result.passed) {
  const failedTemplates = [slideData.template_id];
  const alternative = rematcher.selectAlternative(slideData, failedTemplates, registry);

  if (alternative) {
    // 새 템플릿으로 HTML 재생성
    slideData.template_id = alternative.id;
    // ... HTML 재생성 로직
  }
}
```

#### 6.5.6 세션 저장

```javascript
const session = await SessionManager.resume(sessionId);

// 평가 결과 저장
await session.saveEvaluation(slideIndex, evaluation);

// 재매칭 위한 리셋
await session.resetForRematching(slideIndex);

// 3회 실패 시 최고 점수 선택
await session.finalizeBestOf3(slideIndex, bestAttempt);
```

#### 6.5.7 슬라이드별 평가 데이터

```json
{
  "slides[i]": {
    "evaluation": {
      "attempt_number": 2,
      "current_score": 78,
      "passed": true,
      "selected_reason": "passed",
      "details": {
        "layout": { "score": 22, "max": 25, "issues": [] },
        "typography": { "score": 18, "max": 20, "issues": [] },
        "color": { "score": 17, "max": 20, "issues": [] },
        "content_fit": { "score": 15, "max": 25, "issues": [] },
        "visual": { "score": 6, "max": 10, "issues": [] }
      },
      "critical_failures": null
    },
    "attempt_history": [
      {
        "attempt": 1,
        "template_id": "deepgreen-feature-cards1",
        "score": 52,
        "passed": false,
        "critical_failures": ["element_count_mismatch"],
        "issues": ["4개 카드 템플릿에 6개 콘텐츠"],
        "timestamp": "2026-01-09T14:30:00Z"
      }
    ]
  }
}
```

#### 6.5.8 selected_reason 값

| 값 | 설명 |
|----|------|
| `passed` | 70점 이상 합격 |
| `best_of_3` | 3회 실패 후 최고 점수 선택 |

**CRITICAL**: 평가 루프를 건너뛰지 마세요. 모든 슬라이드는 반드시 평가를 거쳐야 합니다.

---

## Layout Tips

차트/테이블 포함 슬라이드:
- **2열 레이아웃 (권장)**: 전체 너비 헤더 + 아래 2열 (텍스트 | 차트)
- **전체 슬라이드 레이아웃**: 차트/테이블이 슬라이드 전체 차지
- **절대 세로 스택 금지**: 텍스트 아래 차트/테이블 배치 금지

## Visual Design Options

### Geometric Patterns
- 대각선 섹션 구분선
- 비대칭 열 너비 (30/70, 40/60)
- 90도/270도 회전 텍스트 헤더
- 원형/육각형 이미지 프레임

### Border Treatments
- 한쪽 면만 두꺼운 테두리 (10-20pt)
- 코너 브라켓
- 헤더 밑줄 강조 (3-5pt)

### Typography
- 극단적 크기 대비 (72pt 헤드라인 vs 11pt 본문)
- 대문자 헤더 + 넓은 자간
- Courier New: 데이터/기술 콘텐츠

## Dependencies

이미 설치된 라이브러리:
- pptxgenjs, playwright, sharp
- react-icons, react, react-dom
