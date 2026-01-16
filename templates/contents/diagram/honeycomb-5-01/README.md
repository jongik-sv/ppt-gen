# 허니콤(Honeycomb) 다이어그램 템플릿

**ID**: `honeycomb-5-01`  
**카테고리**: diagram  
**버전**: 2.0

## 개요

5개의 육각형을 허니콤(벌집) 패턴으로 배치한 다이어그램 템플릿입니다. 상단에 2개, 하단에 3개의 육각형이 계층적으로 배치되며, 각 육각형 사이를 연결하는 아이콘을 포함합니다.

**원본**: `ppt-sample/깔끔이-딥그린.pptx` - 슬라이드 11

## 구조

### 배치 (Arrangement)

```
        [좌상단]    [우상단]
    [좌측]  [중앙]  [우측]
```

- 상단: 2개 육각형 (가로 간격 34%)
- 하단: 3개 육각형 (가로 간격 34%)
- 수직 간격: 18%

### 색상 팔레트

| 위치 | 색상코드 | 설명 |
|------|---------|------|
| 상단 좌 | #83A99B | 중간 녹색 |
| 상단 우 | #E8E8E8 | 라이트 그레이 |
| 하단 좌 | #DCF0EF | 연한 청록 |
| 하단 중 | #A1BFB4 | 밝은 녹색 |
| 하단 우 | #578F76 | 진한 녹색 |

### 아이콘

5개의 연결 아이콘이 육각형 사이에 배치됩니다:

1. **좌측** (12%, 59%): 블로그/문서 아이콘
2. **좌상단** (29%, 41%): 도시/조직 아이콘
3. **중앙** (46%, 59%): 악수/협력 아이콘
4. **우상단** (63%, 41%): 모래시계/시간 아이콘
5. **우측** (80%, 59%): 전구/아이디어 아이콘

## 파일 구성

### 1. `template.yaml`
메타데이터, 레이아웃 정의, 색상 팔레트, 데이터 스키마를 포함합니다.

**주요 필드**:
- `layout.pattern`: "honeycomb-5"
- `layout.hexagon_count`: 5
- `schema.properties.items`: 5개 고정

### 2. `template.html`
CSS clip-path를 사용하여 육각형을 구현한 재사용 가능한 HTML 템플릿입니다.

**특징**:
- 반응형 디자인 (모바일/태블릿 지원)
- clip-path로 진정한 육각형 도형 구현
- 실시간 데이터 바인딩 (JavaScript)
- 호버 효과 및 그림자 포함

**데이터 바인딩 함수**:
```javascript
// 데이터 업데이트
updateHoneycomb({
    items: [
        { title: "아이템 1" },
        { title: "아이템 2" },
        // ... 5개
    ]
});

// 데이터 추출
const data = getHoneycombData();
```

### 3. `example.html`
4가지 실제 사용 사례를 보여주는 예제 페이지입니다:

1. **조직 구조**: 회사 조직도 표현
2. **개발 프로세스**: 5단계 개발 플로우
3. **마케팅 채널**: 5가지 마케팅 채널
4. **제품 기능**: 핵심 제품 기능

각 예제는 다른 색상 테마를 사용하여 다양한 적용 방식을 시연합니다.

### 4. `thumbnail.png`
400×225px PNG 썸네일 이미지 (16:9 비율)

## 사용 방법

### HTML 템플릿 사용

```html
<!-- 템플릿 HTML 파일 임포트 -->
<link rel="stylesheet" href="template.html">

<!-- 또는 JavaScript로 동적 로드 -->
<script>
    // 데이터 객체 정의
    const honeycombData = {
        items: [
            { title: "조직문화", icon: "team" },
            { title: "경영진", icon: "leader" },
            { title: "인사팀", icon: "people" },
            { title: "개발팀", icon: "dev" },
            { title: "마케팅팀", icon: "marketing" }
        ]
    };

    // 렌더링
    updateHoneycomb(honeycombData);
</script>
```

### YAML 메타데이터 활용

```yaml
# template.yaml에서 스키마 참조
schema:
  type: "object"
  properties:
    items:
      type: "array"
      min_items: 5
      max_items: 5  # 정확히 5개 필수
      items:
        type: "object"
        properties:
          title:
            type: "string"
            max_length: 20
          icon_name:
            type: "string"
            enum: ["blog", "city", "handshake", "hourglass", "lightbulb"]
```

## 커스터마이징

### 색상 변경

```css
/* CSS에서 색상 직접 수정 */
.hexagon-0 {
    background: linear-gradient(135deg, #NEW_COLOR 0%, #DARKER 100%);
}

/* 또는 CSS 변수 사용 */
:root {
    --color-hex-0: #83A99B;
    --color-hex-1: #E8E8E8;
    /* ... */
}
```

### 폰트 변경

```css
.hexagon {
    font-family: "새로운 폰트", sans-serif;
    font-size: 18px;  /* 조정 가능 */
}
```

### 크기 조정

```css
/* 전체 스케일 조정 */
.container {
    transform: scale(1.2);  /* 120% 확대 */
}

/* 개별 육각형 크기 조정 */
.hexagon-0 {
    width: 22%;  /* 기본: 20% */
    aspect-ratio: 1.2;  /* 기본: 1.16 */
}
```

## 적용 사례

### 조직 구조 다이어그램
```
        [경영진]     [이사회]
    [재무팀] [개발팀] [마케팅팀]
```

### 프로세스 플로우
```
        [기획]      [설계]
    [개발] [테스트] [배포]
```

### 5대 핵심 가치
```
        [혁신]      [신뢰]
    [품질] [서비스] [성과]
```

### 마케팅 믹스 (4P)
```
        [Product]   [Price]
    [Place] [Promotion] [People]
```

## 기술 사양

| 항목 | 값 |
|------|-----|
| 캔버스 크기 | 1920×1080px (16:9) |
| 육각형 수 | 5개 (고정) |
| 육각형 크기 | 20% 너비 × 31.3% 높이 |
| 육각형 비율 | 1.16:1 |
| 최소 안전 마진 | 3-5% |
| 폰트 | 카페24 써라운드 (20pt) |
| 텍스트 색상 | #153325 (다크 그린) |
| 그림자 반경 | 3.7px |
| 그림자 불투명도 | 40% |

## 호환성

- **브라우저**: Chrome, Firefox, Safari, Edge (최신 버전)
- **CSS**: CSS Grid, clip-path 지원 필요
- **JavaScript**: ES6 이상
- **모바일**: iOS Safari, Chrome Android 지원

## 성능 최적화

- 이미지 대신 CSS clip-path 사용
- GPU 가속 (transform, opacity)
- 최소 재페인트 (CSS 전환)
- 반응형 단위 사용 (%)

## 접근성 (Accessibility)

```html
<!-- WAI-ARIA 지원 추천 -->
<div class="hexagon" role="region" aria-label="조직 구조 - 경영진">
    <span class="hexagon-text">경영진</span>
</div>
```

## 라이선스

원본: Deep Green Theme for PowerPoint  
템플릿: 자유로운 사용 및 수정 가능

## 관련 템플릿

- `radial-5-01`: 원형 배치 다이어그램
- `smartart-left-01`: 좌측 정렬 SmartArt
- `circle-3step-01`: 3단계 원형 프로세스

## 업데이트 이력

### v2.0 (2026-01-16)
- 초기 추출 및 릴리스
- template.yaml, template.html, example.html 생성
- 4가지 사용 사례 예제 추가
- 반응형 디자인 구현

---

**마지막 수정**: 2026-01-16  
**작성자**: Claude Code (Anthropic)
