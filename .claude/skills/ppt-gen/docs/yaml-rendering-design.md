# YAML 기반 HTML 렌더링 시스템 설계

## 개요

템플릿 YAML의 shapes 배열을 HTML로 변환하는 시스템 설계.
**현재 채택: Option C (하이브리드)**

---

## Option A: Stage 4 전용 렌더링 스크립트

### 아키텍처

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│ stage-4.json    │ ──▶ │ stage4-render.js │ ──▶ │ slides/*.html│
│ (template_id +  │     │ (Node.js 실행)   │     │ (YAML 기반) │
│  bindings)      │     └──────────────────┘     └─────────────┘
└─────────────────┘
```

### 스크립트 역할

1. `stage-4-content.json` 읽기
2. 각 슬라이드의 `template_id`로 YAML 로드
3. `renderFromYaml(template, content_bindings, theme)` 호출
4. HTML 파일 저장

### 장점

- 템플릿 geometry 100% 정확 반영
- LLM은 content_bindings만 생성하면 됨
- 일관된 디자인 품질 보장

### 단점

- 스크립트 실행 단계 추가
- 템플릿 YAML의 shapes/placeholders가 완전해야 함
- 유연성 부족 (커스텀 디자인 어려움)

### 전제 조건

- 모든 템플릿 YAML에 완전한 shapes 배열 필요
- placeholders가 `{{variable}}` 형식으로 표준화되어야 함

### 사용법

```bash
node .claude/skills/ppt-gen/scripts/stage4-render.js <session-dir>
```

---

## Option B: LLM 수동 YAML→HTML 변환 규칙

### 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ template.yaml│ ──▶ │ LLM 변환    │ ──▶ │ slide.html  │
│ (shapes)    │     │ (수동 계산) │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 변환 규칙

**캔버스 크기**: 720pt × 405pt (16:9)

**수식**:
```
left   = x%  × 7.2   (pt)
top    = y%  × 4.05  (pt)
width  = cx% × 7.2   (pt)
height = cy% × 4.05  (pt)
```

**예시**:
```yaml
# YAML shapes
- geometry: { x: 10%, y: 20%, cx: 30%, cy: 15% }
```

```html
<!-- HTML/CSS 변환 -->
<div style="position: absolute; left: 72pt; top: 81pt; width: 216pt; height: 60.75pt;">
```

### LLM 작업 흐름

1. template YAML 파일 읽기
2. shapes 배열 분석
3. 각 shape의 geometry를 pt로 변환
4. style (fill, stroke) 적용
5. text.placeholders를 content_bindings로 치환
6. HTML 파일 생성

### 장점

- 추가 스크립트 불필요
- 유연한 커스터마이징 가능
- 복잡한 레이아웃 수동 조정 가능

### 단점

- LLM 변환 오류 가능성
- 매번 YAML 읽기 필요
- 복잡한 shapes (svg, ooxml) 처리 어려움
- 시간 소요 증가

### 변환 체크리스트

- [ ] geometry 값을 pt로 변환
- [ ] fill.color를 background CSS로 변환
- [ ] stroke를 border CSS로 변환
- [ ] text.placeholders를 data로 치환
- [ ] 폰트 크기/색상 적용

---

## Option C: 하이브리드 접근 (현재 채택)

### 아키텍처

```
┌─────────────┐
│ template.yaml│
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ 판단 로직        │
│ shapes 완전한가? │
└──────┬───────────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌──────┐ ┌──────┐
│ Yes  │ │ No   │
└──┬───┘ └──┬───┘
   │        │
   ▼        ▼
┌────────┐ ┌────────┐
│스크립트│ │LLM 직접│
│렌더링  │ │디자인  │
└────────┘ └────────┘
```

### 판단 기준

| 조건 | 처리 방법 |
|------|----------|
| shapes 배열 있음 + placeholders 완전 | 스크립트 `renderFromYaml()` |
| shapes 있지만 불완전 (하드코딩 텍스트) | LLM이 geometry 참고하여 직접 디자인 |
| shapes 없음 | LLM이 design_intent 기반 직접 디자인 |
| 커스텀 디자인 필요 (차트, 복잡한 다이어그램) | LLM 직접 디자인 |

### shapes 완전성 체크

```yaml
# 완전한 shapes 예시
shapes:
- geometry: { x: 10%, y: 20%, cx: 30%, cy: 15% }
  text:
    placeholders:
    - text: '{{title}}'      # ✅ placeholder 형식
    - text: '{{subtitle}}'   # ✅ placeholder 형식

# 불완전한 shapes 예시
shapes:
- geometry: { x: 10%, y: 20%, cx: 30%, cy: 15% }
  text: "하드코딩된 샘플 텍스트"  # ❌ placeholder 없음
```

### 장점

- 유연성: 케이스에 따라 최적의 방법 선택
- 현실적: 불완전한 템플릿도 처리 가능
- 점진적 개선: 템플릿 정비하면서 스크립트 비율 증가 가능

### 단점

- 일관성 다소 부족
- 판단 로직 필요
- 두 방법 모두 유지보수 필요

### Stage 4 워크플로우

```
1. template YAML 로드
2. shapes 완전성 체크
3-a. 완전하면 → renderFromYaml() 또는 스크립트 호출
3-b. 불완전하면 → LLM이 geometry 참고하여 HTML 직접 작성
4. HTML 파일 저장
```

### LLM 직접 디자인 시 규칙

1. **geometry 참고**: YAML의 geometry가 있으면 대략적인 위치/크기 참고
2. **design_intent 참고**: 템플릿의 의도된 디자인 스타일 유지
3. **테마 색상 적용**: theme의 색상 토큰 사용
4. **캔버스 크기 준수**: 720pt × 405pt

---

## content_bindings 스키마

각 템플릿 YAML의 `text.placeholders`에 맞춰 데이터 구조화:

```yaml
# template YAML placeholders
- text: '{{title}}'
- text: '{{subtitle}}'
- text: '{{item_1}}'
```

```json
// stage-4-content.json
{
  "content_bindings": {
    "title": "프로젝트 개요",
    "subtitle": "스마트 물류 시스템",
    "item_1": "첫 번째 항목"
  }
}
```

---

## 테마 색상 토큰

| 토큰 | 용도 | deepgreen-clean 값 |
|------|------|-------------------|
| primary | 주요 색상 | #153325 |
| secondary | 보조 색상 | #22523B |
| accent | 강조 색상 | #479374 |
| background | 배경 | #FFFFFF |
| surface | 표면/카드 | #A1BFB4 |
| dark_text | 본문 텍스트 | #153325 |
| light | 밝은 텍스트 | #FFFFFF |
| gray | 보조 텍스트 | #859C80 |

---

## 옵션 전환 가이드

### Option C → Option A 전환 조건

- 모든 템플릿 YAML의 shapes가 표준화됨
- placeholders가 `{{variable}}` 형식으로 통일됨
- `renderFromYaml()` 함수가 모든 shape 타입 처리 가능

### Option C → Option B 전환 조건

- 스크립트 실행 환경 제한
- 모든 슬라이드가 커스텀 디자인 필요
- 템플릿 시스템 폐기 결정

---

## 버전 히스토리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0 | 2026-01-09 | 초기 설계 (A, B, C 옵션 정의) |
| 1.1 | 2026-01-09 | Option C 채택 결정 |
