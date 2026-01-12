# Stage 3: 템플릿 시맨틱 매칭 프롬프트

## 개요

`template_filter.py`가 규칙 기반으로 후보를 필터링한 후:
- **후보 0개**: LLM이 새 HTML 직접 생성 (Stage 4 low 경로)
- **후보 1개**: 바로 사용 (LLM 개입 불필요)
- **후보 다수**: 이 프롬프트로 최적 템플릿 선택

## 입력

```yaml
slide_outline:
  index: 3
  type: content
  outline:
    title: "핵심 서비스 4가지"
    content_type: comparison
    design_intent:
      visual_type: card-grid
      layout: equal-weight
      emphasis: title
      icon_needed: true
      description: |
        4개 서비스를 균등한 카드 형태로 배치.
        WMS, TMS 등 약어가 크게 보이도록 제목 강조.
        각 서비스에 관련 아이콘 배치.
        깔끔하고 전문적인 그리드 레이아웃.
    key_points:
      - "WMS: 창고 관리 시스템"
      - "TMS: 운송 관리 시스템"
      - "OMS: 주문 관리 시스템"
      - "WCS: 창고 제어 시스템"

candidates:
  - id: card-4col-01
    name: 4열 카드 레이아웃
    category: grid
    semantic_description: |
      4열 카드 레이아웃. 상단에 타이틀, 하단에 녹색 카드.
      각 카드는 직사각형 배경에 설명 텍스트.
      아이콘 포함 가능.
    match_keywords: [카드, 그리드, 4열, 박스]

  - id: card-icon-4col-01
    name: 4열 아이콘 카드
    category: grid
    semantic_description: |
      4열 아이콘 카드 레이아웃. 각 카드 상단에 아이콘.
      제목이 크게 표시되고 설명은 작게.
    match_keywords: [카드, 그리드, 4열, 아이콘]

  - id: list-disk-4row-01
    name: 4행 디스크 리스트
    category: list
    semantic_description: |
      4행 리스트. 좌측 원형 아이콘, 우측 텍스트.
    match_keywords: [리스트, 목록, 항목]
```

## 출력

```yaml
template:
  id: card-icon-4col-01
  match_score: 0.95
  match_reason: "design_intent에서 요청한 아이콘 카드 + 제목 강조에 가장 적합"
```

## 매칭 기준

**design_intent를 최우선으로 고려하여 템플릿 선택.**

### 1. design_intent 적합성 (40%) ← 핵심 기준
- **visual_type 일치**: design_intent.visual_type과 템플릿 category 매칭
  - card-grid → grid 카테고리
  - timeline → timeline 카테고리
  - flowchart → process 카테고리
  - list → list 카테고리
  - diagram → diagram 카테고리
  - infographic/metrics-highlight → infographic 카테고리
- **layout 일치**: design_intent.layout과 템플릿 구조 매칭
- **emphasis 일치**: 강조 요소와 템플릿 디자인 특성 매칭
- **icon_needed 일치**: 아이콘 포함 여부
- **description 시맨틱 매칭**: 자유 형식 설명과 템플릿 특성 비교

### 2. 구조 적합성 (30%)
- 항목 수와 레이아웃 구조 일치
- 4개 항목 → 4열 카드 / 2x2 그리드
- 3개 항목 → 3열 또는 3단계 프로세스
- 순차적 내용 → 프로세스/타임라인

### 3. 콘텐츠 유형 (20%)
- content_type과 템플릿 용도 일치
- 병렬 비교 → 그리드/카드
- 순서/단계 → 프로세스/타임라인
- 계층 구조 → 리스트/다이어그램
- 수치 데이터 → 차트/인포그래픽

### 4. 키워드 매칭 (10%)
- outline의 title/key_points와 match_keywords 비교

## 프롬프트 템플릿

```
당신은 프레젠테이션 레이아웃 전문가입니다.

슬라이드 아웃라인:
{slide_outline}

후보 템플릿:
{candidates}

위 아웃라인에 가장 적합한 템플릿을 선택하세요.

**핵심: design_intent를 최우선으로 고려하세요.**

평가 기준:
1. design_intent 적합성 (40%):
   - visual_type과 템플릿 category 일치
   - layout, emphasis, icon_needed 일치
   - description에 서술된 의도와 템플릿 특성 시맨틱 매칭
2. 구조 적합성 (30%): 항목 수와 레이아웃 일치
3. 콘텐츠 유형 (20%): content_type과 템플릿 용도 일치
4. 키워드 매칭 (10%): 관련 키워드 유사성

출력 형식 (YAML):
template:
  id: [선택한 템플릿 ID]
  match_score: [0.0~1.0]
  match_reason: [design_intent 기반 선택 이유 1줄]
```

## 특수 케이스

### 후보 0개 처리
```yaml
template:
  id: null
  action: generate
  reason: "적합한 템플릿 없음. LLM이 HTML 직접 생성"
```

→ Stage 4에서 `quality: low` 경로로 처리

### 차트 데이터가 있는 경우
- `chart` 카테고리 우선
- 데이터 타입(bar, line, pie)과 템플릿 일치 확인

### 이미지가 필요한 경우
- `image` 카테고리 우선
- 이미지 위치(left, right, full) 확인
