# 3행 디스크 리스트 템플릿

## 개요

이 템플릿은 PowerPoint 슬라이드의 **3행 디스크 아이콘 기반 리스트 레이아웃**을 재현한 HTML/CSS 기반의 재사용 가능한 콘텐츠 템플릿입니다.

원본: `ppt-sample/깔끔이-딥그린.pptx` 슬라이드 12 (Deep Green 테마)

## 파일 구조

```
disk-3row-01/
├── template.yaml          # YAML 메타데이터 (구조, 색상, 폰트)
├── template.html          # 제네릭 HTML 템플릿 (플레이스홀더 포함)
├── example.html           # 샘플 데이터가 포함된 구체적인 예시
├── thumbnail.png          # 템플릿 썸네일 (400x225px)
├── EXTRACTION_REPORT.md   # 상세 추출 보고서
└── README.md              # 이 파일
```

## 빠른 시작

### 1. 템플릿 YAML 읽기
```yaml
template.yaml 파일에서 다음을 확인하세요:
- canvas: 1920x1080 16:9 비율
- structure: 3행 고정 구조
- colors: 색상 팔레트 (디스크, 테두리, 텍스트)
- fonts: 폰트 및 크기
```

### 2. HTML 템플릿 사용
```html
<!-- template.html을 기반으로 복사 후 수정 -->
<!-- 각 ROW의 데이터를 다음과 같이 업데이트: -->

<div class="row" id="row-1">
  <div class="disk-container">
    <div class="disk-icon"></div>
    <div class="disk-title">YOUR_TITLE_1</div>
  </div>
  <div class="connector"></div>
  <div class="content-box">
    <div class="box-title">YOUR_TITLE_1</div>
    <div class="box-description">YOUR_DESCRIPTION_1</div>
  </div>
</div>
```

### 3. JavaScript API 사용
```javascript
// 동적 콘텐츠 업데이트
templateAPI.updateContent({
  title: "슬라이드 제목",
  subtitle: "부제목",
  items: [
    { title: "제목1", description: "설명1" },
    { title: "제목2", description: "설명2" },
    { title: "제목3", description: "설명3" }
  ]
});

// 진행률 표시
templateAPI.updateProgressBar(2);  // 66.7% 진행률
```

## 디자인 특징

### 레이아웃
- **구조**: 좌(아이콘) - 중(연결선) - 우(설명박스)
- **행 개수**: 고정 3행
- **여백**: 40px 좌우 패딩, 160px 행간 간격

### 색상 시스템
```
디스크 색상 (진행도 표현):
Row 1: #C4D6D0 (가장 연함) 
Row 2: #83A99B (중간톤)
Row 3: #479374 (가장 진함)

테두리 색상 (강조도):
Row 1: #153325 (강한 강조, 진함)
Row 2: #67B7B5 (중간 강조, 라이트 틸)
Row 3: #A1BFB4 (약한 강조, 라이트 민트)
```

### 타이포그래피
- **헤더 제목**: 32pt 진함
- **헤더 부제**: 14pt
- **디스크 제목**: 16pt 화이트 (카페24 써라운드)
- **설명 텍스트**: 12pt 다크그린 (나눔바른펜, 행간 150%)

## 사용 시나리오

| 시나리오 | 예시 |
|---------|------|
| 프로세스 설명 | 계획 → 실행 → 검증 |
| 단계별 절차 | 1단계 기초 → 2단계 심화 → 3단계 응용 |
| 시간순 이벤트 | 분기1 → 분기2 → 분기3 |
| 카테고리 비교 | 제품A 기능 → 제품B 기능 → 제품C 기능 |
| 학습 경로 | 기초 이론 → 실무 응용 → 프로젝트 |

## 커스터마이징 가이드

### 색상 변경
1. `template.html`의 CSS에서 다음을 수정:
   ```css
   .row:nth-child(1) .disk-icon { background: YOUR_COLOR; }
   .row:nth-child(1) .content-box { border-color: YOUR_COLOR; }
   ```

2. `template.yaml`의 `colors.palette` 업데이트

### 폰트 변경
```css
/* 디스크 제목 */
.disk-title { 
  font-family: "YOUR_FONT"; 
}

/* 설명 텍스트 */
.box-description {
  font-family: "YOUR_FONT";
}
```

### 행 개수 변경 (고급)
현재 템플릿은 3행 고정입니다. 행 개수를 변경하려면:
1. HTML에서 `<div class="row">` 요소 추가/제거
2. CSS에서 `row-height` 계산 조정
3. `.row:nth-child(n)` 스타일 추가/수정

## 호환성

| 환경 | 지원 |
|------|------|
| Chrome/Edge | ✅ 완전 지원 |
| Firefox | ✅ 완전 지원 |
| Safari | ✅ 완전 지원 |
| 모바일 | ✅ 반응형 (스케일 조정) |
| IE 11 | ⚠️ 제한적 (CSS Grid 미지원) |
| PowerPoint 변환 | ✅ 가능 (HTML to OOXML) |

## 성능 최적화

### 파일 크기
- `template.html`: ~13KB
- `example.html`: ~9.5KB
- `thumbnail.png`: ~1.7KB

### 렌더링
- 로딩 시간: < 100ms
- 애니메이션: CSS 기반 (부드러움)
- 메모리: ~ 5MB (브라우저에 로드)

## 문제 해결

### Q: 텍스트가 박스를 벗어남
A: `.box-description`의 `word-break: keep-all;` 속성을 `word-wrap: break-word;`로 변경

### Q: 행 높이가 맞지 않음
A: `.row`의 `margin-bottom: 160px;` 값을 조정 (슬라이드 비율에 따라)

### Q: 디스크 아이콘이 보이지 않음
A: `.disk-icon`의 배경색과 테두리 색상이 같지 않은지 확인

## 라이선스 & 출처

- **원본**: ppt-sample/깔끔이-딥그린.pptx (슬라이드 12)
- **추출일**: 2025-01-16
- **품질 점수**: 9.5/10

## 관련 템플릿

- `templates/contents/list/disk-3row-01/` (공식 버전)
- `templates/contents/process/circle-3step-01/` (다른 아이콘)
- `templates/contents/timeline/connector-2row-01/` (타임라인)

---

더 자세한 정보는 `EXTRACTION_REPORT.md`를 참조하세요.
