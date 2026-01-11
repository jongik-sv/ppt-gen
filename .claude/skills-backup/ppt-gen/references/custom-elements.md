# Custom Elements Reference

html2pptx.js로 HTML을 PowerPoint로 변환할 때 지원되는 요소 및 스타일 레퍼런스.

---

## 1. 지원 HTML 태그

### 텍스트 요소

| 태그 | 설명 | 예시 |
|------|------|------|
| `p` | 단락 텍스트 | `<p>본문 텍스트</p>` |
| `h1`-`h6` | 제목 (1~6단계) | `<h1>메인 제목</h1>` |

### 리스트 요소

| 태그 | 설명 | 예시 |
|------|------|------|
| `ul` | 순서 없는 목록 | `<ul><li>항목</li></ul>` |
| `ol` | 순서 있는 목록 | `<ol><li>항목</li></ol>` |
| `li` | 목록 항목 | UL/OL 내부에서만 사용 |

### 인라인 포맷팅

| 태그 | 설명 | 예시 |
|------|------|------|
| `b`, `strong` | 굵은 텍스트 | `<b>강조</b>` |
| `i`, `em` | 이탤릭 | `<i>기울임</i>` |
| `u` | 밑줄 | `<u>밑줄</u>` |
| `span` | 인라인 스타일 | `<span style="color:red">빨강</span>` |
| `br` | 줄바꿈 | `텍스트<br>다음줄` |

### 컨테이너 요소

| 태그 | 설명 | 용도 |
|------|------|------|
| `body` | 슬라이드 전체 | 배경색, 크기 정의 |
| `div` | 도형 컨테이너 | 배경, 테두리, 그림자 |

### 미디어 요소

| 태그 | 설명 | 예시 |
|------|------|------|
| `img` | 이미지 | `<img src="image.png" style="width:200px">` |

### 미지원 요소

- `table` - 테이블 (Placeholder로 대체)
- `svg` - SVG 그래픽 (PNG 변환 필요)
- `canvas` - Canvas 요소
- `video`, `audio` - 미디어 요소

---

## 2. 지원 CSS 스타일

### 텍스트 스타일

```css
/* 폰트 */
font-size: 24px;        /* pt로 변환 (px × 0.75) */
font-family: Arial;     /* 첫 번째 폰트만 사용 */
font-weight: bold;      /* 600 이상 = bold */
font-style: italic;

/* 색상 */
color: #333333;         /* 텍스트 색상 */
color: rgb(51,51,51);   /* RGB 형식 지원 */
color: rgba(0,0,0,0.8); /* 투명도 지원 */

/* 정렬 */
text-align: left;       /* left, center, right */
text-transform: uppercase;

/* 간격 */
line-height: 1.5;       /* pt로 변환 */
```

### 도형 스타일 (div)

```css
/* 배경 */
background-color: #F5F5F5;
background-color: rgba(0,0,0,0.1);  /* 투명도 지원 */

/* 테두리 */
border: 2px solid #333;
border-width: 2px;
border-color: #333333;
border-radius: 10px;    /* 둥근 모서리 */

/* 그림자 */
box-shadow: 5px 5px 10px rgba(0,0,0,0.3);
/* 외부 그림자만 지원, inset 제외 */
```

### 간격 스타일

```css
/* 마진 */
margin: 10px;
margin-top: 20px;       /* paraSpaceBefore로 변환 */
margin-bottom: 20px;    /* paraSpaceAfter로 변환 */
margin-left: 30px;      /* 리스트 들여쓰기 */

/* 패딩 */
padding: 20px;
padding-left: 40px;
```

### 특수 스타일

```css
/* 텍스트 회전 */
writing-mode: vertical-rl;  /* 90° 회전 */
writing-mode: vertical-lr;  /* 270° 회전 */
transform: rotate(45deg);   /* 각도 회전 */
```

### 미지원 CSS

- `linear-gradient`, `radial-gradient` (그라데이션)
- `background-image` (body 배경 제외)
- `display`, `position`, `flex`, `grid`
- 텍스트 요소의 `background`, `border`, `box-shadow`
- 인라인 요소의 `margin`

---

## 3. Placeholder 사용법

차트, 표, 다이어그램 등을 삽입할 위치를 예약합니다.

### 기본 사용법

```html
<div id="chart-1" class="placeholder"
     style="position:absolute; left:50px; top:100px; width:400px; height:300px;">
</div>
```

### 필수 조건

- `class="placeholder"` 필수
- `id` 속성 필수 (또는 자동 생성)
- `width`, `height` > 0

### 반환값

```javascript
const { slide, placeholders } = await html2pptx('slide.html', pptx);

// placeholders[0] = { id: "chart-1", x: 0.52, y: 1.04, w: 4.17, h: 3.13 }
// 좌표는 인치 단위
```

### 차트 삽입 예시

```javascript
if (placeholders[0]) {
  const chartData = [
    { name: '1월', values: [100, 200] },
    { name: '2월', values: [150, 180] }
  ];
  slide.addChart(pptx.ChartType.bar, chartData, {
    ...placeholders[0],
    chartColors: ['4472C4', 'ED7D31']
  });
}
```

---

## 4. 제약사항

### 텍스트 요소 제약

```html
<!-- 금지: 텍스트에 배경/테두리 -->
<p style="background-color: yellow;">텍스트</p>  <!-- X -->
<p style="border: 1px solid black;">텍스트</p>   <!-- X -->

<!-- 해결: div로 감싸기 -->
<div style="background-color: yellow; padding: 10px;">
  <p>텍스트</p>
</div>
```

### 수동 불릿 기호 금지

```html
<!-- 금지 -->
<p>• 첫 번째 항목</p>
<p>- 두 번째 항목</p>
<p>* 세 번째 항목</p>

<!-- 올바른 방법 -->
<ul>
  <li>첫 번째 항목</li>
  <li>두 번째 항목</li>
  <li>세 번째 항목</li>
</ul>
```

### 인라인 요소 마진 금지

```html
<!-- 금지 -->
<span style="margin-left: 20px;">텍스트</span>  <!-- X -->

<!-- 해결 -->
<span style="padding-left: 20px;">텍스트</span>
```

### DIV 내 직접 텍스트 금지

```html
<!-- 금지 -->
<div>직접 텍스트</div>  <!-- X -->

<!-- 올바른 방법 -->
<div>
  <p>텍스트</p>
</div>
```

---

## 5. 슬라이드 크기

### body 요소 설정

```html
<body style="width: 720px; height: 405px; background-color: #FFFFFF;">
  <!-- 슬라이드 콘텐츠 -->
</body>
```

### 지원 레이아웃

| 비율 | 크기 (px) | PptxGenJS 레이아웃 |
|------|----------|-------------------|
| 16:9 | 720 × 405 | `LAYOUT_16x9` |
| 4:3 | 720 × 540 | `LAYOUT_4x3` |
| 16:10 | 720 × 450 | `LAYOUT_16x10` |

### 단위 변환

```
px → 인치: px ÷ 96
px → pt: px × 0.75
```

---

## 6. 색상 처리

### HEX 색상

```javascript
// PowerPoint에서 # 제외 필수
color: "FF0000"    // O
color: "#FF0000"   // X (파일 손상 가능)
```

### RGB/RGBA 변환

```css
color: rgb(255, 0, 0);      /* → FF0000 */
color: rgba(255, 0, 0, 0.5); /* → FF0000 + transparency: 50 */
```

### 투명도

```javascript
// transparency: 0 (불투명) ~ 100 (완전 투명)
backgroundColor: "FF0000",
transparency: 30  // 30% 투명
```

---

## 7. 요소별 예시

### 제목 + 본문 슬라이드

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body {
      width: 720px;
      height: 405px;
      margin: 0;
      background-color: #FFFFFF;
    }
    .title {
      position: absolute;
      left: 30px;
      top: 30px;
      font-size: 36px;
      font-weight: bold;
      color: #002452;
    }
    .content {
      position: absolute;
      left: 30px;
      top: 100px;
      font-size: 18px;
      color: #333333;
    }
  </style>
</head>
<body>
  <h1 class="title">슬라이드 제목</h1>
  <div class="content">
    <ul>
      <li>첫 번째 포인트</li>
      <li>두 번째 포인트</li>
      <li>세 번째 포인트</li>
    </ul>
  </div>
</body>
</html>
```

### 2열 레이아웃

```html
<body style="width:720px; height:405px; display:flex;">
  <div style="width:40%; padding:30px;">
    <h2>텍스트 영역</h2>
    <ul>
      <li>항목 1</li>
      <li>항목 2</li>
    </ul>
  </div>
  <div id="chart-area" class="placeholder"
       style="width:55%; height:300px; margin:30px;">
  </div>
</body>
```

### 카드 그리드

```html
<body style="width:720px; height:405px;">
  <div style="position:absolute; left:30px; top:100px;
              width:200px; height:150px;
              background-color:#F5F5F5;
              border-radius:10px;
              padding:20px;">
    <h3 style="font-size:48px; color:#002452;">85%</h3>
    <p style="font-size:14px; color:#666;">완료율</p>
  </div>
  <!-- 추가 카드들... -->
</body>
```

---

## 8. 검증 규칙

### 크기 검증

- body 크기 = PptxGenJS 레이아웃 (0.1인치 허용 오차)
- 모든 콘텐츠가 body 내부에 있어야 함
- overflow 발생 시 에러

### 위치 검증

- fontSize > 12pt 텍스트는 하단에서 0.5인치 이상 거리 필요
- 요소 겹침 주의

### 에러 메시지 예시

```
1. Body dimensions (720x405px) don't match layout LAYOUT_16x9
2. Content overflow detected: scrollWidth=750 > width=720
3. Text element too close to bottom edge (0.3in < 0.5in minimum)
```

---

## 9. 웹 안전 폰트

PowerPoint 호환을 위해 다음 폰트만 사용:

- Arial
- Helvetica
- Times New Roman
- Georgia
- Courier New
- Verdana
- Tahoma
- Trebuchet MS
- Impact
- Comic Sans MS

### 폰트 폴백

```css
font-family: "본고딕", Arial, sans-serif;
/* 첫 번째 폰트만 사용됨 */
```
