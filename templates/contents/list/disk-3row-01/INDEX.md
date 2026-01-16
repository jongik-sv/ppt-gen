# 3행 디스크 리스트 템플릿 - 파일 인덱스

## 빠른 시작

1. **예제 보기** → `example.html` (브라우저에서 열기)
2. **템플릿 사용** → `template.html` 복사 후 수정
3. **메타데이터 확인** → `template.yaml` (구조, 색상, 폰트)

## 파일 설명

### 1. template.yaml (메타데이터)
**용도**: 템플릿 구조, 색상, 폰트, 간격 정의

**주요 섹션**:
- `content_template`: 기본 정보
- `design_meta`: 디자인 속성
- `canvas`: 캔버스 설정 (1920x1080, 16:9)
- `content_zones`: 헤더/콘텐츠/푸터 영역
- `structure`: 레이아웃 구조 (3행 고정)
- `colors`: 색상 팔레트
- `fonts`: 폰트 정보
- `spacing`: 여백 및 간격
- `placeholders`: 플레이스홀더 데이터
- `metadata`: 사용 사례 및 키워드

**사용 시기**:
- 템플릿 메타데이터 필요할 때
- 색상/폰트 정보 찾을 때
- 설계 규격 확인할 때

---

### 2. template.html (HTML 템플릿)
**용도**: 재사용 가능한 HTML 템플릿 (플레이스홀더 포함)

**주요 구성**:
```html
<div class="slide-container">
  <div class="header">...</div>        <!-- 제목, 부제, 진행률 바 -->
  <div class="content">
    <div class="row">...</div>         <!-- 행 1 -->
    <div class="row">...</div>         <!-- 행 2 -->
    <div class="row">...</div>         <!-- 행 3 -->
  </div>
  <div class="footer">...</div>        <!-- 저작권 -->
</div>
```

**포함 내용**:
- CSS 스타일 완전 포함 (외부 의존 없음)
- JavaScript API (updateContent, updateProgressBar)
- 플레이스홀더 ID (item-1-title, item-1-description 등)
- 메타 태그 및 인코딩 설정

**사용 방법**:
1. 파일 복사
2. ID 기반으로 콘텐츠 업데이트
3. JavaScript API로 동적 바인딩
4. HTML to PPTX 변환 도구로 변환

**수정 포인트**:
```html
<!-- 제목 업데이트 -->
<div class="header-title" id="slideTitle">YOUR_TITLE</div>

<!-- 부제 업데이트 -->
<div class="header-subtitle" id="slideSubtitle">YOUR_SUBTITLE</div>

<!-- 각 행의 제목 (디스크 위) -->
<div class="disk-title" id="item-1-title">YOUR_TITLE</div>

<!-- 각 행의 제목 (우측 박스) -->
<div class="box-title" id="item-1-box-title">YOUR_TITLE</div>

<!-- 각 행의 설명 -->
<div class="box-description" id="item-1-description">YOUR_TEXT</div>
```

---

### 3. example.html (샘플 데이터)
**용도**: 실제 데이터가 포함된 완전한 예제

**포함 데이터**:
- 제목: "프로젝트 구현 방법론"
- 부제: "3단계 접근 방식"
- Row 1: 계획 → 프로젝트 계획 수립
- Row 2: 실행 → 계획에 따른 실행
- Row 3: 검증 → 결과 검증 및 평가

**사용 시기**:
- 템플릿 미리보기
- 디자인 검증
- 색상/레이아웃 확인
- 샘플 콘텐츠 작성 시 참고

**브라우저에서 열기**:
```bash
# Linux/Mac
open example.html

# Windows
start example.html

# 또는 웹 서버
python -m http.server 8000
# http://localhost:8000/example.html
```

---

### 4. thumbnail.png (썸네일)
**용도**: 템플릿 미리보기 이미지

**규격**:
- 크기: 400x225px
- 비율: 16:9
- 포맷: PNG (RGB, 8-bit)
- 크기: 1.7 KB

**사용 처**:
- 템플릿 카탈로그 표시
- UI 썸네일 표시
- 문서 미리보기

---

### 5. EXTRACTION_REPORT.md (기술 보고서)
**용도**: 상세한 기술 분석 및 추출 정보

**포함 내용**:
- 원본 정보 (파일, 슬라이드, 추출 일시)
- 슬라이드 구조 분석 (ASCII 다이어그램)
- 콘텐츠 영역 제외 상세 설명
- 추출된 도형 목록 (위치, 크기, 색상)
- 색상 팔레트 상세
- 폰트 정보 상세
- 레이아웃 매트릭스
- 플레이스홀더 구조
- 기술 사양
- 사용 사례
- 주의사항
- 향후 확장 가능성

**사용 시기**:
- 깊이 있는 이해가 필요할 때
- 정확한 색상 코드 확인할 때
- 레이아웃 규격 찾을 때
- 도형별 정보 추출할 때

---

### 6. README.md (사용자 가이드)
**용도**: 친절한 사용자 가이드 및 커스터마이징 방법

**주요 섹션**:
- 개요
- 빠른 시작 (3 단계)
- 디자인 특징
- 사용 시나리오 (5가지)
- 커스터마이징 가이드
  - 색상 변경
  - 폰트 변경
  - 행 개수 변경
- 호환성
- 성능 최적화
- 문제 해결 (Q&A)
- 라이선스 정보

**사용 시기**:
- 처음 사용할 때
- 커스터마이징 방법 알고 싶을 때
- 문제 해결할 때

---

## 파일 선택 가이드

### 상황별 필요한 파일

| 상황 | 추천 파일 |
|------|---------|
| 미리보기 보기 | example.html |
| 색상 코드 찾기 | template.yaml 또는 EXTRACTION_REPORT.md |
| 템플릿 복사 | template.html |
| 사용 방법 알기 | README.md |
| 기술 상세 분석 | EXTRACTION_REPORT.md |
| 메타데이터 필요 | template.yaml |
| 프리뷰 이미지 | thumbnail.png |

---

## 데이터 흐름

```
template.yaml
    ↓ (메타데이터 참조)
template.html (일반 템플릿)
    ↓ (데이터 입력)
example.html (구체적인 예제)
    ↓ (검증)
HTML to PPTX 변환
    ↓
최종 PowerPoint 슬라이드
```

---

## JavaScript API 참고

### updateContent(data)
```javascript
templateAPI.updateContent({
  title: "문서 제목",
  subtitle: "문서 부제목",
  items: [
    { 
      title: "단계 1", 
      description: "단계 1에 대한 설명..." 
    },
    { 
      title: "단계 2", 
      description: "단계 2에 대한 설명..." 
    },
    { 
      title: "단계 3", 
      description: "단계 3에 대한 설명..." 
    }
  ]
});
```

### updateProgressBar(itemCount)
```javascript
// itemCount: 0-3
templateAPI.updateProgressBar(2);  // 66.7% 표시
```

### getContent()
```javascript
const currentContent = templateAPI.getContent();
// 반환: { title, subtitle, items: [...] }
```

---

## 색상 참조표

| 요소 | Row 1 | Row 2 | Row 3 |
|------|-------|-------|-------|
| 디스크 색상 | #C4D6D0 | #83A99B | #479374 |
| 테두리 색상 | #153325 | #67B7B5 | #A1BFB4 |

---

## 폰트 참조표

| 요소 | 폰트명 | 크기 | 색상 | 기타 |
|------|--------|------|------|------|
| 헤더 제목 | 코트라 볼드체 | 32pt | #22523B | 진함 |
| 헤더 부제 | 나눔바른펜 | 14pt | #22523B | - |
| 디스크 제목 | 카페24 써라운드 | 16pt | #FFFFFF | 중앙 정렬 |
| 설명 텍스트 | 나눔바른펜 | 12pt | #153325 | 행간 150% |

---

## 문제 해결

### 파일이 보이지 않음
→ `templates2/contents/list/disk-3row-01/` 전체 경로 확인

### 색상이 다름
→ template.yaml의 색상 코드 또는 EXTRACTION_REPORT.md 확인

### 폰트가 다름
→ 시스템에 설치된 폰트 확인, 대체 폰트 선택

### HTML이 렌더링되지 않음
→ 최신 브라우저 사용, 콘솔 오류 확인

---

## 추가 리소스

- **공식 버전**: templates/contents/list/disk-3row-01/
- **유사 템플릿**: 
  - process/circle-3step-01/ (원형 아이콘)
  - timeline/connector-2row-01/ (타임라인)

---

**Last Updated**: 2025-01-16  
**Version**: 1.0  
**Quality Score**: 9.5/10
