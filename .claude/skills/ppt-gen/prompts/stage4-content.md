# Stage 4: 콘텐츠 생성 프롬프트

## 개요

템플릿의 플레이스홀더에 맞는 콘텐츠 생성.
품질 옵션에 따라 다른 출력 형식.

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
    key_points:
      - "WMS: 창고 관리"
      - "TMS: 운송 관리"
      - "OMS: 주문 관리"
      - "WCS: 창고 제어"

template:
  id: card-4col-01
  category: grid
  placeholders:
    - name: page_title
      type: text
    - name: cards
      type: array
      item_schema:
        - name: number
        - name: title
        - name: description

quality: medium
```

## 출력

### high (OOXML)
```yaml
content:
  page_title: "핵심 서비스"
  cards:
    - number: "01"
      title: "WMS"
      description: "실시간 재고 추적과 창고 공간 최적화를 통해 물류 효율성을 극대화합니다."
    - number: "02"
      title: "TMS"
      description: "최적 경로 계획과 실시간 배송 추적으로 운송 비용을 절감합니다."
    - number: "03"
      title: "OMS"
      description: "주문부터 배송까지 전 과정을 통합 관리하여 고객 만족도를 높입니다."
    - number: "04"
      title: "WCS"
      description: "자동화 설비와 연동하여 창고 운영을 최적화합니다."
```

### medium/low (HTML)
위와 동일한 형식. html_renderer.py로 렌더링.

## 콘텐츠 생성 규칙

### 텍스트 길이 가이드

| 필드 타입 | 권장 길이 |
|----------|----------|
| title | 2~5단어 |
| subtitle | 5~10단어 |
| description | 15~30단어 |
| key_point | 5~15단어 |

### 톤별 스타일

| 톤 | 특징 |
|----|------|
| formal | 격식체, 전문 용어 사용 |
| casual | 친근한 표현, 쉬운 용어 |
| academic | 객관적, 데이터 중심 |
| data-driven | 수치 강조, 비교 데이터 |

### 항목 수 조정

템플릿의 min/max 범위에 맞게 조정:
- 항목 부족: 관련 내용 추가
- 항목 초과: 핵심만 선별 또는 병합

## 프롬프트 템플릿

```
당신은 프레젠테이션 콘텐츠 작성 전문가입니다.

슬라이드 아웃라인:
{slide_outline}

사용할 템플릿:
{template}

설정:
- 톤: {tone}
- 청중: {audience}

위 템플릿의 placeholders에 맞는 콘텐츠를 생성하세요.

규칙:
1. 각 필드는 권장 길이 준수
2. 톤과 청중에 맞는 표현
3. 아웃라인의 key_points를 반영
4. 항목 수는 템플릿의 min/max 범위 내

출력 형식 (YAML):
content:
  [placeholder_name]: [value]
  ...
```

## 차트 데이터 생성

차트 템플릿의 경우 데이터 구조 생성:

```yaml
content:
  chart_data:
    labels: ["1월", "2월", "3월", "4월"]
    datasets:
      - label: "매출"
        data: [120, 190, 160, 210]
        backgroundColor: "#22523B"
      - label: "비용"
        data: [80, 90, 85, 95]
        backgroundColor: "#479374"
```

## 재시도 가이드

평가에서 불합격 시 피드백 반영:

```
이전 시도 결과:
- 점수: 72/100
- 피드백:
  - 레이아웃: 카드 간 간격 불균일
  - 콘텐츠: 2번 항목 텍스트 2줄 넘침

수정 사항:
1. 2번 항목 description을 20자로 축소
2. 모든 항목 길이 균일하게 조정
```

---

## 템플릿 없이 HTML 직접 생성

**Stage 3에서 적합한 템플릿이 없을 때 (action: generate) 이 경로를 사용.**

design_intent를 해석하여 HTML을 직접 생성합니다.

### 입력 (템플릿 없는 경우)

```yaml
slide_outline:
  index: 5
  type: content
  outline:
    title: "프로젝트 일정"
    content_type: timeline
    design_intent:
      visual_type: timeline
      layout: hierarchical
      emphasis: data
      icon_needed: false
      description: |
        6개월 프로젝트 일정을 타임라인 형태로 표시.
        각 마일스톤에 날짜와 담당자 표시.
        완료/진행중/예정 상태를 색상으로 구분.
    key_points:
      - "1~2월: 현황 분석 및 설계"
      - "3~4월: 시스템 개발"
      - "5월: 테스트 및 검증"
      - "6월: 전사 배포"

template: null
action: generate

quality: medium
theme: deep-green
```

### 생성 프로세스

#### 1. design_intent 분석

| 필드 | 해석 |
|------|------|
| visual_type | 기본 HTML 구조 결정 |
| layout | CSS grid/flex 배치 방식 |
| emphasis | 폰트 크기, 색상 강조 |
| icon_needed | 아이콘 삽입 여부 |
| description | 세부 스타일링 힌트 |

#### 2. visual_type별 HTML 구조

| visual_type | HTML 구조 | CSS 핵심 |
|-------------|----------|----------|
| card-grid | `<div class="grid">` + card divs | `display: grid; gap: 24px;` |
| timeline | `<div class="timeline">` + items | `flex-direction: column; border-left;` |
| flowchart | `<div class="flow">` + step divs | `display: flex; ::after` for arrows |
| list | `<ul class="list">` or `<ol>` | `list-style; padding-left;` |
| diagram | SVG or nested divs | `position: relative;` |
| infographic | data-highlight divs | `font-size: 3em;` for numbers |
| comparison-table | `<table>` or grid | `border-collapse; th/td styling` |
| metrics-highlight | big number + label | `display: flex; align-items: baseline;` |

#### 3. 테마 색상 적용

테마 변수를 사용하여 일관된 스타일 적용:

```css
:root {
  --primary: var(--theme-primary, #22523B);
  --secondary: var(--theme-secondary, #479374);
  --accent: var(--theme-accent, #8BC4A9);
  --text: var(--theme-text, #1a1a1a);
  --background: var(--theme-background, #ffffff);
}
```

#### 4. 기본 슬라이드 컨테이너

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 960px;
      height: 540px;
      font-family: 'Pretendard', sans-serif;
      background: var(--background);
      color: var(--text);
      padding: 48px;
    }
    /* visual_type별 스타일 */
  </style>
</head>
<body>
  <h1 class="page-title">{title}</h1>
  <!-- visual_type에 따른 콘텐츠 -->
</body>
</html>
```

### 출력 (템플릿 없이 생성)

```yaml
generated_html: |
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="UTF-8">
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body {
        width: 960px; height: 540px;
        font-family: 'Pretendard', sans-serif;
        background: #fff; color: #1a1a1a;
        padding: 48px;
      }
      .page-title {
        font-size: 32px; font-weight: 700;
        margin-bottom: 32px; color: #22523B;
      }
      .timeline {
        display: flex; flex-direction: column;
        border-left: 4px solid #22523B;
        padding-left: 24px; gap: 24px;
      }
      .timeline-item {
        position: relative;
      }
      .timeline-item::before {
        content: '';
        position: absolute; left: -32px; top: 4px;
        width: 16px; height: 16px;
        background: #22523B; border-radius: 50%;
      }
      .timeline-item.completed::before { background: #479374; }
      .timeline-item.in-progress::before { background: #F59E0B; }
      .timeline-date {
        font-size: 14px; color: #666;
        margin-bottom: 4px;
      }
      .timeline-title {
        font-size: 18px; font-weight: 600;
      }
    </style>
  </head>
  <body>
    <h1 class="page-title">프로젝트 일정</h1>
    <div class="timeline">
      <div class="timeline-item completed">
        <div class="timeline-date">1~2월</div>
        <div class="timeline-title">현황 분석 및 설계</div>
      </div>
      <div class="timeline-item in-progress">
        <div class="timeline-date">3~4월</div>
        <div class="timeline-title">시스템 개발</div>
      </div>
      <div class="timeline-item">
        <div class="timeline-date">5월</div>
        <div class="timeline-title">테스트 및 검증</div>
      </div>
      <div class="timeline-item">
        <div class="timeline-date">6월</div>
        <div class="timeline-title">전사 배포</div>
      </div>
    </div>
  </body>
  </html>

file: "output/slide-05.html"
```

### 프롬프트 템플릿 (템플릿 없이 생성)

```
당신은 프레젠테이션 HTML 개발 전문가입니다.

슬라이드 아웃라인:
{slide_outline}

템플릿이 없어 HTML을 직접 생성해야 합니다.

**design_intent를 해석하여 HTML을 생성하세요:**

1. visual_type에 따른 기본 구조 선택
2. layout에 맞는 CSS grid/flex 배치
3. emphasis에 따른 강조 스타일링
4. icon_needed가 true면 Lucide 아이콘 삽입
5. description의 의도를 최대한 반영

기술 요구사항:
- 슬라이드 크기: 960x540px
- 폰트: Pretendard (fallback: sans-serif)
- 테마 색상: {theme} 적용
- 여백: 48px (슬라이드 패딩)
- 간격: 8px 기준 그리드 (8, 16, 24, 32, 48)

출력 형식 (YAML):
generated_html: |
  [완전한 HTML 코드]

file: "output/slide-{index:02d}.html"
```

### 아이콘 사용 (icon_needed: true)

Lucide 아이콘 CDN 사용:

```html
<script src="https://unpkg.com/lucide@latest"></script>
<script>lucide.createIcons();</script>

<!-- 사용 예 -->
<i data-lucide="warehouse" class="icon"></i>  <!-- WMS -->
<i data-lucide="truck" class="icon"></i>       <!-- TMS -->
<i data-lucide="package" class="icon"></i>     <!-- OMS -->
<i data-lucide="settings" class="icon"></i>    <!-- WCS -->
```

아이콘 스타일:
```css
.icon {
  width: 32px; height: 32px;
  stroke: var(--primary);
  stroke-width: 2;
}
```
