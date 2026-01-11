# document-extract 워크플로우

문서 양식(슬라이드 마스터, 로고, 레이아웃) 추출.

## 트리거

- "이 PPT를 양식으로 등록해줘"
- "동국제강 양식 등록해줘"

## 입력

- PPTX 파일

## 출력

- `templates/documents/{group}/{template}/`
  - `template.yaml` - 메타데이터
  - `ooxml/` - 슬라이드 마스터, 레이아웃, 테마
  - `assets/` - 로고, 이미지

## 프로세스

### 1. 파일 분석

```bash
# 슬라이드 구조 파싱
python scripts/slide-crawler.py input.pptx --all --output working/parsed.json
```

### 2. 레이아웃 분류 (LLM)

LLM이 슬라이드를 분류:
- **표지** (cover): 타이틀만 있는 첫 슬라이드
- **목차** (toc): 목록/인덱스 형태
- **섹션** (section): 구분 슬라이드
- **내지** (body): 콘텐츠 슬라이드

내지 유형 분류:
- 제목만
- 제목+액션타이틀
- 2단 레이아웃
- 이미지+텍스트

### 3. OOXML 추출

각 레이아웃 타입별로 대표 1개씩 추출:

```
ppt/
├── slideMaster1.xml      → ooxml/slideMaster1.xml
├── slideLayouts/
│   ├── slideLayout1.xml  → ooxml/slideLayout1.xml (표지)
│   ├── slideLayout2.xml  → ooxml/slideLayout2.xml (목차)
│   └── ...
└── theme/theme1.xml      → ooxml/theme1.xml
```

### 4. 에셋 추출

```
ppt/media/
├── image1.png (로고)     → assets/media/logo.png
├── image2.jpg (배경)     → assets/media/background.jpg
└── ...
```

### 5. 콘텐츠 영역 계산

각 레이아웃의 `content_zone` 계산:

```yaml
layouts:
  - index: 3
    name: "내지 (제목+액션타이틀)"
    content_zone:
      position: { x: 3%, y: 24%, width: 94%, height: 72% }
```

### 6. 메타데이터 생성

```yaml
# template.yaml
document:
  id: "dongkuk-standard"
  name: "동국그룹 기본양식"
  group: "동국그룹"
  source_file: "원본.pptx"
  extracted_at: "2026-01-10"

layouts:
  - index: 0
    name: "표지"
    type: cover
    ooxml_file: "ooxml/slideLayout1.xml"
    placeholders:
      - id: "title"
        type: ctrTitle
        position: { x: 5%, y: 35%, width: 90%, height: 15% }

master:
  ooxml_file: "ooxml/slideMaster1.xml"
  common_elements:
    - id: "logo"
      file: "assets/media/logo.png"
      position: { x: 90%, y: 2%, width: 8%, height: 6% }

theme:
  ooxml_file: "ooxml/theme1.xml"
```

### 7. 썸네일 생성

```bash
python scripts/thumbnail.py input.pptx --all --output-dir templates/documents/{group}/{id}/thumbnails/ --size document
```

## 업데이트 정책

같은 `source_file`로 재등록 시:
1. 기존 콘텐츠 삭제 확인 프롬프트
2. 새로 추출/등록

```bash
# --force: 확인 없이 덮어쓰기
# --new: 기존 유지, 새 ID로 등록
```

## 삭제 정책

```
"동국시스템즈 양식을 지워줘"
    │
    ▼
삭제 대상:
├── documents/dongkuk/dongkuk-systems/  # 문서 양식
├── contents/*/dongkuk-systems-*        # 연관 콘텐츠
└── thumbnails/... (연관 항목)
```

옵션:
- `--cascade`: 연관 콘텐츠 모두 삭제
- `--keep-contents`: 문서 양식만 삭제
- `--dry-run`: 삭제 대상만 표시
