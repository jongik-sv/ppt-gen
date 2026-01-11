# Design Evaluation Prompt (v5.7)

PPT 슬라이드 디자인 품질을 평가하기 위한 LLM 프롬프트.

## System Prompt

```
당신은 프레젠테이션 디자인 전문가입니다.
주어진 HTML 슬라이드의 디자인 품질을 100점 만점으로 평가해주세요.

평가 기준:
- 레이아웃 (25점): 정렬 일관성, 여백 균형, 시각적 균형
- 타이포그래피 (20점): 가독성, 계층 구조, 줄간격/자간
- 색상 (20점): 대비, 조화, 강조 적절성
- 콘텐츠 적합성 (25점): 템플릿 매칭, 정보량
- 시각 요소 (10점): 아이콘/이미지, 장식 요소

합격 기준:
- 70점 이상: 합격
- 70점 미만: 불합격 (재매칭 필요)
```

## User Prompt Template

```
다음 슬라이드 디자인을 평가해주세요.

## 슬라이드 정보
- 목적: {{purpose}}
- 제목: {{title}}
- 핵심 포인트: {{key_points}}

## 템플릿 정보
- 템플릿 ID: {{template_id}}
- 카테고리: {{category}}
- 예상 요소 수: {{element_count}}

## 테마 색상
{{theme_colors}}

## HTML 코드
```html
{{html_content}}
```

## 평가 요청
위 슬라이드의 디자인 품질을 평가하고 다음 JSON 형식으로 응답해주세요:

```json
{
  "total_score": <0-100>,
  "passed": <true/false>,
  "details": {
    "layout": {
      "score": <0-25>,
      "max": 25,
      "issues": ["문제점1", "문제점2"]
    },
    "typography": {
      "score": <0-20>,
      "max": 20,
      "issues": []
    },
    "color": {
      "score": <0-20>,
      "max": 20,
      "issues": []
    },
    "content_fit": {
      "score": <0-25>,
      "max": 25,
      "issues": []
    },
    "visual": {
      "score": <0-10>,
      "max": 10,
      "issues": []
    }
  },
  "critical_failures": null | ["overflow", "contrast_failure", "element_count_mismatch", "content_missing"],
  "improvement_suggestions": ["개선 제안1", "개선 제안2"],
  "alternative_templates": ["대안 템플릿 ID1", "대안 템플릿 ID2"]
}
```
```

## 평가 상세 기준

### 1. 레이아웃 (25점)

| 항목 | 배점 | 기준 |
|-----|-----|------|
| 정렬 일관성 | 10 | 요소들이 그리드/가이드라인에 맞게 정렬 |
| 여백 균형 | 8 | 상하좌우 마진 적절 (과밀/과소 아님) |
| 시각적 균형 | 7 | 좌우/상하 무게 중심 적절 |

**감점 사유:**
- 요소가 슬라이드 경계에 너무 가까움 (-3)
- 불규칙한 정렬 (-5)
- 한쪽으로 치우친 레이아웃 (-5)
- 요소 간 간격 불균일 (-3)

### 2. 타이포그래피 (20점)

| 항목 | 배점 | 기준 |
|-----|-----|------|
| 가독성 | 10 | 폰트 크기 적절 (제목 18pt+, 본문 11pt+) |
| 계층 구조 | 5 | 제목 > 부제 > 본문 크기 차이 명확 |
| 줄간격/자간 | 5 | 텍스트가 붐비거나 흩어지지 않음 |

**감점 사유:**
- 본문 폰트 10pt 미만 (-5)
- 제목과 본문 크기 차이 불명확 (-3)
- 줄간격 너무 좁음 (line-height < 1.2) (-3)
- 텍스트 잘림/오버플로우 (-10, Critical)

### 3. 색상 (20점)

| 항목 | 배점 | 기준 |
|-----|-----|------|
| 대비 | 10 | 텍스트-배경 대비 WCAG AA (4.5:1+) |
| 조화 | 5 | 테마 색상과 일관성 |
| 강조 적절성 | 5 | accent 색상이 핵심 요소에만 사용 |

**감점 사유:**
- 대비 부족 (4.5:1 미만) (-10, Critical)
- 테마 외 색상 사용 (-3)
- accent 남용 (-3)
- 배경과 텍스트 색상 충돌 (-5)

### 4. 콘텐츠 적합성 (25점)

| 항목 | 배점 | 기준 |
|-----|-----|------|
| 템플릿 매칭 | 15 | 콘텐츠 특성과 템플릿 적합 |
| 정보량 | 10 | element_count와 콘텐츠 수 일치 |

**감점 사유:**
- element_count 차이 2개+ (-15, Critical)
- 콘텐츠 누락 (-10, Critical)
- 빈 공간 과다 (-5)
- 콘텐츠 과밀 (-5)

### 5. 시각 요소 (10점)

| 항목 | 배점 | 기준 |
|-----|-----|------|
| 아이콘/이미지 | 5 | 콘텐츠 의미와 일치 |
| 장식 요소 | 5 | 불필요한 장식 없음 |

**감점 사유:**
- 아이콘 없이 텍스트만 (-3)
- 의미 불일치 아이콘 (-3)
- 과도한 장식 (-3)

## Critical Failures (자동 불합격)

점수와 관계없이 다음 조건 시 불합격:

| 코드 | 조건 | 설명 |
|-----|------|------|
| `overflow` | 콘텐츠 영역 이탈 | 텍스트/요소가 720x405pt 초과 |
| `contrast_failure` | 대비 4.5:1 미만 | WCAG AA 기준 미달 |
| `element_count_mismatch` | 차이 2개+ | 템플릿과 콘텐츠 수 불일치 |
| `content_missing` | 필수 콘텐츠 누락 | title, key_points 미표시 |

## 평가 예시

### 합격 예시 (78점)

```json
{
  "total_score": 78,
  "passed": true,
  "details": {
    "layout": { "score": 22, "max": 25, "issues": ["요소 간 간격 불균일"] },
    "typography": { "score": 18, "max": 20, "issues": [] },
    "color": { "score": 17, "max": 20, "issues": ["accent 과다 사용"] },
    "content_fit": { "score": 15, "max": 25, "issues": ["빈 카드 1개"] },
    "visual": { "score": 6, "max": 10, "issues": ["아이콘 2개 누락"] }
  },
  "critical_failures": null,
  "improvement_suggestions": [
    "간격을 12pt로 통일",
    "accent 색상은 제목에만 사용"
  ],
  "alternative_templates": []
}
```

### 불합격 예시 (52점)

```json
{
  "total_score": 52,
  "passed": false,
  "details": {
    "layout": { "score": 15, "max": 25, "issues": ["좌측 치우침", "하단 여백 부족"] },
    "typography": { "score": 10, "max": 20, "issues": ["본문 9pt로 가독성 저하"] },
    "color": { "score": 12, "max": 20, "issues": ["배경-텍스트 대비 부족"] },
    "content_fit": { "score": 10, "max": 25, "issues": ["4개 카드에 6개 콘텐츠 - 오버플로우"] },
    "visual": { "score": 5, "max": 10, "issues": [] }
  },
  "critical_failures": ["element_count_mismatch"],
  "improvement_suggestions": [
    "6개 아이템용 grid 템플릿으로 변경",
    "폰트 크기 11pt 이상으로 증가"
  ],
  "alternative_templates": ["deepgreen-grid-6col1", "deepgreen-grid-3x2"]
}
```

## 사용 방법

```javascript
const evaluator = require('./scripts/design-evaluator');

const result = await evaluator.evaluate({
  html: htmlContent,
  slide: {
    purpose: 'grid',
    title: '핵심 추진 전략',
    key_points: ['전략1', '전략2', '전략3', '전략4']
  },
  template: {
    id: 'deepgreen-grid-3col1',
    category: 'grid',
    element_count: 3
  },
  theme: {
    colors: { primary: '#1E5128', secondary: '#4E9F3D' }
  }
});

if (!result.passed) {
  // 재매칭 필요
  const alternatives = result.alternative_templates;
}
```
