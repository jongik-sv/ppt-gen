# Style Extraction Workflow

이미지에서 디자인 스타일을 추출하여 자동으로 분류하고 저장합니다.

## Triggers

- "이 이미지 스타일 추출해줘"
- "스타일 저장해줘"
- "이 디자인 분석해서 저장해줘"
- 이미지 첨부 + 스타일 관련 요청

## Workflow

### 1. Image Analysis (LLM Vision)

이미지 파일 읽기 (Read tool):

분석 항목:
- **색상 팔레트**: Primary, Secondary, Accent, Background, Text
- **레이아웃 구조**: 열 구성, 헤더/푸터, 카드 등
- **타이포그래피**: 크기 비율, 정렬, 굵기
- **무드/분위기**: 전문적, 활기찬, 고급스러운 등

### 2. Auto Classification

color-palettes.md 참조:

| 감지 색상 | 무드 | ID 접두사 |
|----------|------|----------|
| 네이비/블루 | 전문적/신뢰 | classic-, corp- |
| 그린 | 자연/친환경 | nature-, eco- |
| 레드/오렌지 | 활기/에너지 | vibrant-, bold- |
| 퍼플 | 창의/혁신 | creative-, tech- |
| 블랙/골드 | 고급/프리미엄 | luxury-, premium- |
| 파스텔 | 부드러움/친근 | soft-, warm- |

### 3. Auto Save

**a) 색상/테마 → documents/{그룹}/config.yaml**

```yaml
# templates/documents/{mood}-{timestamp}/config.yaml
group:
  id: classic-20260106
  name: Classic Blue Style
  source: extracted_image
  source_url: "{이미지 출처 URL}"      # 웹 출처 시 기록

theme:
  colors:
    primary: "1E3A5F"      # # 제외
    secondary: "4A90D9"
    accent: "F5A623"
    background: "FFFFFF"
    text: "333333"
  fonts:
    title: Arial
    body: Arial
```

**b) 레이아웃 패턴 → contents/templates/{id}.yaml** (감지된 경우)

```yaml
template:
  id: layout-classic-twocol
  name: 2열 레이아웃 (Classic)
  category: two-column
  source: extracted

structure:
  type: two-column
  ratio: "40:60"
```

**c) 원본 이미지 → assets/images/{id}.png**

이미지 파일 복사 (참조용)

### 4. Registry Update

- `documents/{그룹}/registry.yaml` 생성/업데이트
- `contents/registry.yaml` 업데이트 (레이아웃 감지 시)
- `assets/registry.yaml` 업데이트 (이미지 저장 시)

### 5. Result Report

```
스타일 추출 완료!

추출된 색상:
- Primary: #1E3A5F (네이비)
- Secondary: #4A90D9 (블루)
- Accent: #F5A623 (오렌지)

무드: 전문적/신뢰 (Classic Blue 계열)

저장 위치:
- 테마: templates/documents/classic-20260106/config.yaml
- 레이아웃: templates/contents/templates/layout-classic-twocol.yaml
- 이미지: templates/assets/images/ref-classic-20260106.png
```

## Naming Rules

- 그룹 ID: `{mood}-{YYYYMMDD}` (예: classic-20260106)
- 레이아웃 ID: `layout-{mood}-{pattern}` (예: layout-classic-twocol)
- 이미지 ID: `ref-{mood}-{YYYYMMDD}` (예: ref-classic-20260106)
- 사용자가 이름을 지정하면 해당 이름 사용

## Notes

- 이미지 분석 색상은 **추정값**입니다
- HEX 코드에서 **# 제외**하여 저장 (PowerPoint 호환)
- 기존 그룹과 이름 충돌 시 timestamp로 구분
