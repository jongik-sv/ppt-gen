# content-create 워크플로우

라이브러리 기반 콘텐츠 템플릿 동적 생성.

## 트리거

- "Chart.js로 막대차트 템플릿 만들어줘"
- "Mermaid 플로우차트 템플릿 추가해줘"
- "파이차트 템플릿 생성해줘"
- "시퀀스 다이어그램 템플릿 필요해"

## 지원 라이브러리

| 라이브러리 | 타입 | 용도 |
|-----------|------|------|
| **Chart.js** | bar, pie, line, doughnut, radar | 데이터 시각화 차트 |
| **Mermaid** | flowchart, sequence, class, state, er | 다이어그램 |
| **ApexCharts** | dashboard, area, radial | 대시보드용 차트 |
| **Lucide** | icon-grid, icon-list | 아이콘 그리드 |

## 실행 방법

### CLI

```bash
# 막대 차트
python ppt_extract.py content-create --library chartjs --type bar --name sales-chart

# 파이 차트
python ppt_extract.py content-create --library chartjs --type pie --name market-share

# 플로우차트
python ppt_extract.py content-create --library mermaid --type flowchart --name process-flow

# 시퀀스 다이어그램
python ppt_extract.py content-create --library mermaid --type sequence --name api-flow

# 라이브러리 목록 확인
python ppt_extract.py content-create --list
```

### 옵션

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--library`, `-l` | ✅ | 라이브러리 (chartjs, mermaid, apexcharts, lucide) |
| `--type`, `-t` | ✅ | 템플릿 타입 |
| `--name`, `-n` | ✅ | 템플릿 이름 (케밥케이스) |
| `--category`, `-c` | ❌ | 카테고리 (기본: 라이브러리 기본값) |
| `--theme` | ❌ | 테마 모드 (light, dark) |
| `--list` | ❌ | 지원 라이브러리 목록 출력 |

## 출력 구조

```
templates/contents/{category}/{name}/
├── template.yaml   # 스키마 + 예시 데이터
├── template.html   # Handlebars 템플릿
└── example.html    # 미리보기용 완전한 HTML
```

### template.yaml 예시

```yaml
id: sales-chart
category: chart
pattern: chartjs-bar
description: Chart.js bar 템플릿
has_ooxml: false
render_method: library

library:
  name: Chart.js
  cdn: https://cdn.jsdelivr.net/npm/chart.js
  type: bar

schema:
  title: string
  labels: [string]
  datasets:
    - label: string
      data: [number]
      backgroundColor: string

example:
  title: 월별 매출 현황
  labels: ['1월', '2월', '3월', '4월', '5월', '6월']
  datasets:
    - label: '2024년'
      data: [120, 150, 180, 140, 200, 190]
      backgroundColor: '#3b82f6'
```

## 렌더링 방식

`render_method: library` → HTML 렌더링 → 스크린샷 → 이미지 삽입

**제약사항:**
- 편집 불가 (이미지로 삽입됨)
- 수정 시 재생성 필요
- 대화형 기능 미지원

## 기존 템플릿과의 차이

| 항목 | content-extract | content-create |
|------|-----------------|----------------|
| 입력 | PPTX 파일 | 라이브러리 선택 |
| 출력 | YAML + HTML + OOXML | YAML + HTML |
| 편집 | 가능 (OOXML) | 불가 (이미지) |
| 용도 | 기존 디자인 재사용 | 동적 콘텐츠 생성 |

## 예제

### Chart.js 막대 차트

```bash
python ppt_extract.py content-create \
  --library chartjs \
  --type bar \
  --name quarterly-sales \
  --category chart \
  --theme light
```

### Mermaid 플로우차트

```bash
python ppt_extract.py content-create \
  --library mermaid \
  --type flowchart \
  --name order-process \
  --category diagram
```

## 참고

- 기존 간트 차트 템플릿: `templates/contents/schedule/gantt-yearly/`
- 라이브러리 CDN은 최신 버전 사용
- 테마 색상은 theme.yaml과 연동 가능
