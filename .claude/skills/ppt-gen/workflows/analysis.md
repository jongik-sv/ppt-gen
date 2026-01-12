# PPT 분석 워크플로우

기존 PPTX 파일의 구조, 디자인, 콘텐츠 분석.

## 사용 시점

- 템플릿 추출 전 분석
- 디자인 패턴 파악
- 콘텐츠 구조 이해
- 문서 양식 추출 준비

## 분석 도구

### 텍스트 추출
```bash
python -m markitdown presentation.pptx > content.md
```

### 썸네일 생성
```bash
python scripts/thumbnail.py presentation.pptx thumbnails --cols 5
```

### 플레이스홀더 분석
```bash
python scripts/thumbnail.py presentation.pptx analysis --cols 4 --outline-placeholders
```

빨간 테두리로 텍스트 영역 표시.

### 텍스트 인벤토리
```bash
python lib/shared/inventory.py presentation.pptx inventory.json
```

## 분석 항목

### 1. 구조 분석

**슬라이드 구성**:
- 총 슬라이드 수
- 슬라이드 타입 (표지, 목차, 본문, 섹션, 마무리)
- 레이아웃 패턴

**콘텐츠 영역**:
- 헤더 영역 (높이, 배경색)
- 콘텐츠 영역 (위치, 크기)
- 푸터 영역 (높이, 내용)

### 2. 디자인 분석

**색상 팔레트**:
```bash
# theme1.xml에서 추출
unpacked/ppt/theme/theme1.xml
```

주요 색상:
- Primary (주요 강조)
- Secondary (보조)
- Accent (포인트)
- Background (배경)
- Text (본문)

**폰트**:
- 제목 폰트
- 본문 폰트
- 강조 폰트
- 폰트 크기 체계

**스타일**:
- 모서리 둥글기
- 그림자 효과
- 선 스타일

### 3. 레이아웃 분석

**그리드 시스템**:
- 열 수 (1열, 2열, 3열, 4열)
- 간격 (gap)
- 여백 (padding, margin)

**공통 패턴**:
- 카드 레이아웃
- 리스트 레이아웃
- 프로세스/타임라인
- 차트/다이어그램

### 4. 콘텐츠 분석

**텍스트 밀도**:
- 슬라이드당 평균 단어 수
- 최대/최소 텍스트량
- 글머리 기호 사용

**시각 요소**:
- 이미지 사용
- 아이콘 스타일
- 차트 유형

## 분석 결과 형식

```yaml
analysis:
  metadata:
    total_slides: 15
    slide_size: "16:9"
    source_file: "presentation.pptx"

  structure:
    cover: [0]
    toc: [1]
    sections: [4, 8, 12]
    content: [2, 3, 5, 6, 7, 9, 10, 11, 13]
    closing: [14]

  design:
    colors:
      primary: "#22523B"
      secondary: "#153325"
      accent: "#479374"
      background: "#FFFFFF"
      text: "#333333"
    fonts:
      display: "나눔스퀘어라운드 Bold"
      body: "Noto Sans KR"
    style:
      border_radius: "16px"
      shadow: "0 4px 12px rgba(0,0,0,0.08)"

  layouts:
    - type: grid
      columns: 4
      gap: "2%"
      slides: [2, 5]
    - type: list
      items: 3
      slides: [3, 6]
    - type: process
      steps: 3
      slides: [7, 10]

  content:
    avg_words_per_slide: 45
    max_bullets: 5
    has_charts: true
    has_images: true
```

## ppt-extract 연계

분석 결과를 기반으로 템플릿 추출:

1. **테마 추출**: `ppt-extract/workflows/theme-extract.md`
2. **콘텐츠 추출**: `ppt-extract/workflows/content-extract.md`
3. **문서 양식 추출**: `ppt-extract/workflows/document-extract.md`

분석 → 추출 → 등록 → 재사용
