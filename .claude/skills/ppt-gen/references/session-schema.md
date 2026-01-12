# session.yaml 스키마

## 전체 구조

```yaml
session:
  id: "20260112-101500-abc123"
  created_at: "2026-01-12T10:15:00"
  status: "pending"  # pending → configured → generating → completed

settings:  # Stage 1 결과
  document_type: "proposal"
  document_style: "dongkuk-systems"
  slide_size: "16:9"
  audience: "executive"
  duration: "10min"
  tone: "formal"
  quality: "medium"
  chart_rendering: "native"

slides:  # Stage 2-4 결과
  - index: 1
    type: "cover"
    status: "completed"
    outline: { ... }
    template: { ... }
    attempts: [ ... ]
    final_attempt: 1

output:  # Stage 5 결과
  file: "output/presentation.pptx"
  generated_at: "2026-01-12T10:30:00"
```

## 필드 상세

### session

| 필드 | 타입 | 설명 |
|------|------|------|
| id | string | 세션 ID (YYYYMMDD-HHMMSS-xxxxxx) |
| created_at | string | ISO 8601 생성 시간 |
| status | enum | pending, configured, generating, completed |

### settings (Stage 1)

| 필드 | 타입 | 옵션 |
|------|------|------|
| document_type | string | proposal, bizplan, report, lecture |
| document_style | string | 문서 양식 ID 또는 null |
| slide_size | string | 16:9, 4:3, 16:10 |
| audience | string | executive, team, customer, investor, public |
| duration | string | 5min, 10min, 20min, 30min+ |
| tone | string | formal, casual, academic, data-driven |
| quality | string | high, medium, low |
| chart_rendering | string | native, library |

### slides[] (Stage 2-4)

| 필드 | 타입 | 설명 |
|------|------|------|
| index | int | 슬라이드 번호 (1-based) |
| type | string | cover, toc, section, content, closing |
| status | enum | pending, outlined, matched, generated, evaluating, completed |
| outline | object | Stage 2 아웃라인 |
| template | object | Stage 3 매칭 결과 |
| attempts | array | Stage 4 시도 이력 |
| final_attempt | int | 최종 선택된 시도 번호 |

#### outline

```yaml
outline:
  title: "스마트 물류 시스템 제안"
  subtitle: "효율성 혁신을 위한 솔루션"
  content_type: "comparison"  # 콘텐츠 유형 (type=content/chart일 때 필수)

  # 디자인 의도 (type=content/chart일 때 필수)
  design_intent:
    visual_type: "card-grid"    # 시각화 유형
    layout: "equal-weight"       # 배치 방식
    emphasis: "title"            # 강조 요소
    icon_needed: true            # 아이콘 필요 여부
    description: |               # 자유 형식 설명
      4개 서비스를 균등한 카드 형태로 배치.
      WMS, TMS 등 약어가 크게 보이도록 제목 강조.
      각 서비스에 관련 아이콘 배치.

  key_points:
    - "실시간 재고 관리"
    - "AI 기반 수요 예측"
  speaker_notes: "이 슬라이드에서는..."
```

**content_type 옵션:**

| 값 | 설명 | 매핑 카테고리 |
|------|------|--------------|
| comparison | 병렬 비교, 독립 항목 | grid, diagram |
| sequence | 순서, 단계, 흐름 | process |
| timeline | 시간순 일정 | timeline, process |
| hierarchy | 계층, 구조, 목록 | list, diagram |
| metrics | 수치, KPI, 퍼센트 | infographic, chart |

**design_intent 필드:**

| 필드 | 타입 | 옵션 |
|------|------|------|
| visual_type | enum | card-grid, timeline, flowchart, list, diagram, infographic, comparison-table, metrics-highlight |
| layout | enum | equal-weight, hierarchical, centered, split, circular, radial |
| emphasis | enum | title, number, icon, description, image, data |
| icon_needed | bool | true, false |
| description | string | 자유 형식 시각화 의도 설명 |

Stage 3에서 `design_intent`를 최우선으로, `content_type`을 보조로 사용하여 템플릿 매칭.

#### template

```yaml
template:
  id: "grid-cards-01"
  category: "grid"
  match_score: 0.92
  match_reason: "4개 항목 카드 레이아웃 적합"
```

#### attempts[]

```yaml
attempts:
  - attempt: 1
    content:
      title: "핵심 서비스"
      items:
        - { title: "WMS", description: "창고 관리" }
        - { title: "TMS", description: "운송 관리" }
    file: "output/slide-03-v1.html"
    evaluation:
      scores:
        layout: 22
        typography: 18
        color: 19
        content_fit: 20
        visual: 8
      total: 87
      passed: true
      feedback: null
```

### output (Stage 5)

| 필드 | 타입 | 설명 |
|------|------|------|
| file | string | 최종 PPTX 경로 |
| generated_at | string | ISO 8601 생성 시간 |

## 상태 흐름

```
session.status:
pending → configured → generating → completed

slide.status:
pending → outlined → matched → generated → evaluating → completed
```
