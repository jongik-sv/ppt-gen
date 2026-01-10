# Asset Management Workflow

에셋(이미지/아이콘)을 저장하고 검색합니다.
네이버 블로그 등 보호된 사이트에서도 이미지를 크롤링할 수 있습니다.

## Saving Assets

### Triggers

- "이 아이콘 저장해줘" (SVG 생성 후)
- "다운받은 로고 저장해줘"

### Workflow

1. **Save Asset File**:
   - 아이콘: `templates/assets/icons/{id}.svg`
   - 이미지: `templates/assets/images/{id}.png`

2. **Update Registry** (`templates/assets/registry.yaml`):

```yaml
icons:
  - id: new-icon
    name: 새 아이콘
    file: icons/new-icon.svg
    source: generated    # generated | downloaded | brand
    tags: ["tag1", "tag2"]
    created: 2026-01-06
```

3. **Generate Thumbnail** (optional):
   - `templates/assets/thumbnails/{id}.jpg`

### Source Types

| source | 설명 | 예시 |
|--------|------|------|
| `generated` | Claude가 직접 생성한 SVG/이미지 | 아이콘, 다이어그램 |
| `downloaded` | 웹에서 다운로드 | 배경 이미지, 스톡 사진 |
| `crawled` | 웹페이지에서 크롤링 | 레퍼런스 이미지 |
| `brand` | 브랜드 공식 에셋 (Brandfetch 등) | 회사 로고 |

---

## Crawling Images from Web

### Triggers

- "이 블로그에서 이미지 가져와줘"
- "네이버 블로그 이미지 크롤링해줘"
- "이 페이지의 모든 이미지 저장해줘"

### CLI Usage

```bash
# 단일 이미지 (보호된 사이트)
python asset-manager.py add "https://postfiles.pstatic.net/..." \
    --id naver-img --browser

# 페이지 전체 이미지 크롤링
python asset-manager.py crawl "https://blog.naver.com/PostView.naver?blogId=xxx&logNo=yyy" \
    --prefix design-ref \
    --tags "reference,naver" \
    --max-images 10

# 미리보기 (다운로드 없이 목록만)
python asset-manager.py crawl "https://blog.naver.com/..." \
    --prefix test \
    --preview
```

### Crawl Options

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--prefix` | 에셋 ID 접두사 (필수) | - |
| `--tags` | 태그 (쉼표 구분) | - |
| `--min-size` | 최소 이미지 크기 (픽셀) | 100 |
| `--max-images` | 최대 이미지 개수 | 20 |
| `--preview` | 미리보기만 | false |

### Supported Sites

| 사이트 | 특수 처리 |
|--------|----------|
| 네이버 블로그 | iframe 전환, lazy-load 처리 |
| 네이버 카페 | iframe 전환, lazy-load 처리 |
| 네이버 포스트 | iframe 전환, lazy-load 처리 |
| 일반 웹사이트 | 기본 이미지 추출 |

### Dependencies

크롤링 기능을 사용하려면 Playwright가 필요합니다:

```bash
pip install playwright
playwright install chromium
```

---

## Searching Assets

### Triggers

- "차트 관련 아이콘 찾아줘"
- "저장된 로고 보여줘"

### Workflow

1. **Search Registry** (`templates/assets/registry.yaml`):
   - `tags` 배열에서 키워드 매칭
   - `name` 필드에서 검색
   - `source` 타입으로 필터링

2. **Display Results**:
   - 매칭된 에셋 목록
   - 썸네일 이미지 (있는 경우)
   - 파일 경로

3. **Apply to PPT** (optional):
   - html2pptx 워크플로우에서 에셋 참조
   - 이미지 삽입 시 파일 경로 사용

### Search Examples

```bash
# 태그로 검색
tags: ["chart"] → chart-line.svg, chart-bar.svg

# 소스로 필터링
source: brand → dongkuk-logo.png, company-icon.svg

# 이름으로 검색
name: "화살표" → arrow-right.svg, arrow-down.svg
```

## Asset Directory Structure

```
templates/assets/
├── registry.yaml       # 에셋 레지스트리
├── icons/             # SVG 아이콘
│   ├── chart-line.svg
│   └── arrow-right.svg
├── images/            # 이미지 파일
│   ├── tech-bg.png
│   └── office-photo.jpg
└── thumbnails/        # 썸네일 (자동 생성)
    └── tech-bg.jpg
```

## Company Logos

회사 로고는 documents 폴더에 저장:

```
templates/documents/{그룹}/assets/{계열사}/logo.png
```

예: `templates/documents/dongkuk/assets/dongkuk-steel/logo.png`
