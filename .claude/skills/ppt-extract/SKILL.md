---
name: ppt-extract
description: |
  PPT 템플릿과 에셋 추출 스킬. PPTX에서 문서 양식, 테마, 콘텐츠 디자인을 추출하여 재사용 가능한 템플릿으로 저장.

  트리거:
  - 문서 양식 추출: "이 PPT를 양식으로 등록해줘", "양식 업데이트해줘", "양식 지워줘"
  - 테마 추출: "이 이미지 스타일로", "색상 팔레트 추출해줘"
  - 콘텐츠 추출: "이 슬라이드 저장해줘", "이 디자인 저장해줘"
  - 콘텐츠 생성: "간트차트 템플릿 만들어줘" (라이브러리 기반)

  ppt-gen 스킬과 함께 사용. 추출된 템플릿은 templates/ 폴더에 저장됨.
---

# ppt-extract 스킬

PPT 생성 파이프라인과 독립적으로 실행되는 추출 스킬.

## 워크플로우

| 워크플로우 | 트리거 | 입력 | 출력 |
|-----------|--------|------|------|
| `document-extract` | "이 PPT를 양식으로 등록해줘" | PPTX | 문서 템플릿 YAML, OOXML, 에셋 |
| `document-update` | "양식 업데이트해줘" | PPTX | 기존 문서 덮어쓰기 |
| `document-delete` | "양식 지워줘" | 문서 ID | 문서 + 연관 콘텐츠 삭제 |
| `style-extract` | "이 이미지 스타일로" | 이미지 | 테마 YAML |
| `content-extract` | "이 슬라이드 저장해줘" | PPTX | YAML + HTML + OOXML |
| `content-create` | "간트차트 템플릿 만들어줘" | 라이브러리/코드 | 직접 생성된 템플릿 |

## 저장 구조

```
templates/
├── documents/{group}/{template}/   # 문서 양식
│   ├── template.yaml
│   ├── ooxml/
│   └── assets/
├── themes/{theme_id}/theme.yaml    # 테마
├── contents/{category}/{id}/       # 콘텐츠
│   ├── template.yaml               # 필수: 메타데이터/플레이스홀더 정의
│   ├── template.html               # 필수: 핸들바 템플릿
│   ├── example.html                # 필수: 샘플 데이터가 적용된 미리보기
│   └── template.ooxml              # 필수: 원본 OOXML (100% 재현용)
├── objects/{category}/{id}/        # 오브젝트 (자동 추출)
│   ├── object.png
│   ├── object.svg                  # 선택
│   └── metadata.yaml
└── thumbnails/                     # 썸네일 (미러 구조)
    ├── documents/{group}/{template}.png
    ├── themes/{theme_id}.png
    ├── contents/{category}/{id}.png
    └── objects/{category}/{id}.png
```

## 콘텐츠 템플릿 필수 파일

| 파일 | 필수 | 설명 |
|------|------|------|
| `template.yaml` | ✅ | 메타데이터, 출처 정보, 플레이스홀더, 스타일 정의 |
| `template.html` | ✅ | 핸들바 문법 사용 (`{{placeholder}}`) |
| `example.html` | ✅ | 샘플 데이터 적용된 브라우저 미리보기용 |
| `template.ooxml` | ✅ | 원본 OOXML (100% 재현용, **필수**) |

## template.yaml 필수 필드

```yaml
# 기본 정보
id: chart-column-01
name: 묶은 세로 막대형 차트
category: chart
description: 3개 계열의 묶은 세로 막대형 차트

# 출처 정보 (필수) - 원본과 비교/검증용
source:
  file: "깔끔이 딥그린.pptx"      # 원본 파일명
  slide: 4                        # 슬라이드 번호 (1-based)
  extracted_at: "2026-01-11"      # 추출 일시

# 품질 설정
quality: high                     # high (OOXML) | medium (HTML) | low (시맨틱)

# 레이아웃 정보
layout:
  type: chart
  structure: clustered-bar

# 플레이스홀더 정의
placeholders:
  - name: labels
    type: array
    sample: ["1월", "2월", "3월", "4월"]
  - name: datasets
    type: array
    # ...

# 테마 색상 (추출된 원본 색상)
theme_colors:
  primary: "#22523B"
  secondary: "#153325"
```

**필수 출처 필드:**
- `source.file`: 원본 PPTX 파일명
- `source.slide`: 슬라이드 번호 (1-based, 원본과 비교용)
- `source.extracted_at`: 추출 일시

## 썸네일 규칙

- **저장 위치**: `templates/thumbnails/contents/{category}/{id}.png`
- **크기**: 320x180px (16:9 비율)
- **생성 방식**: 원본 PPTX 슬라이드에서 직접 캡처 (PowerPoint COM)
- **스크립트**: `scripts/thumbnail.py input.pptx --slide N --output thumbnails/contents/{category}/{id}.png`

> ⚠️ example.html이 아닌 **원본 PPTX**에서 썸네일을 생성해야 함.
> 원본과의 비교/검증을 위해 원본 슬라이드 이미지가 필요.

### example.html 생성 규칙

- `template.html`의 핸들바 변수를 `template.yaml`의 `sample` 값으로 대체
- 브라우저에서 직접 열어 확인 가능해야 함
- 외부 라이브러리 CDN 링크 포함 (Chart.js 등)

## OOXML 추출 규칙 (필수)

### 추출 대상
- 콘텐츠 영역의 모든 도형 (Header/Footer 제외)
- 도형의 원본 XML 구조 그대로 보존

### template.ooxml 구조

```
template.ooxml/
├── slide.xml              # 슬라이드 본문 (도형 정의)
├── _rels/
│   └── slide.xml.rels     # 관계 파일 (이미지, 차트 참조)
└── media/                 # 미디어 파일 (이미지 등)
```

### 추출 방법

```python
from pptx import Presentation
from lxml import etree
import zipfile

def extract_ooxml(pptx_path, slide_num, output_dir):
    """슬라이드의 OOXML 추출"""
    prs = Presentation(pptx_path)
    slide = prs.slides[slide_num - 1]  # 0-based

    # 슬라이드 XML 추출
    slide_part = slide.part
    slide_xml = slide_part.blob

    # 관계 파일 추출
    rels_xml = slide_part._rels.xml

    # 미디어 파일 추출
    for rel in slide_part.rels.values():
        if rel.is_external:
            continue
        target = rel.target_part
        # 이미지, 차트 등 저장
```

### 플레이스홀더 마킹

텍스트 → `__SLOT_필드명__` 형식으로 치환:

```xml
<!-- 원본 -->
<a:t>제목을 입력하세요</a:t>

<!-- 치환 후 -->
<a:t>__SLOT_title__</a:t>
```

배열 항목:
```xml
<a:t>__SLOT_items[0].title__</a:t>
<a:t>__SLOT_items[0].description__</a:t>
```

## 스크립트

| 스크립트 | 용도 |
|---------|------|
| `scripts/document_extractor.py` | 문서 양식 추출기 |
| `scripts/style_extractor.py` | 테마/색상 팔레트 추출기 |
| `scripts/content_extractor.py` | 콘텐츠 템플릿 추출기 |
| `scripts/ooxml_extractor.py` | OOXML 추출기 (필수) |
| `scripts/content_creator.py` | 라이브러리 기반 콘텐츠 생성기 |
| `scripts/object_detector.py` | 복잡한 도형 자동 감지 |
| `scripts/object_extractor.py` | 오브젝트 추출 및 저장 |
| `scripts/pattern_matcher.py` | 유사 패턴 통합 (variants) |
| `scripts/registry_manager.py` | 레지스트리 자동 관리 |
| `scripts/thumbnail.py` | PPTX 썸네일 생성 (PowerPoint COM) |
| `scripts/html_thumbnail.py` | HTML 썸네일 생성 (Playwright) |
| `shared/ooxml_parser.py` | OOXML 파싱 유틸리티 |
| `shared/color_utils.py` | 색상 분석 유틸리티 |
| `shared/llm_interface.py` | Claude API 호출 인터페이스 |

## 실행 예시

### content-extract

```bash
# 1. 슬라이드 파싱
python scripts/slide-crawler.py input.pptx --slide 3 --output working/parsed.json

# 2. 콘텐츠 영역 분석
python scripts/content-analyzer.py working/parsed.json --output working/analysis.json

# 3. LLM 플레이스홀더 판단 (Claude가 직접 수행)
# → 텍스트 그룹핑 확인, 플레이스홀더 이름 부여

# 4. 템플릿 저장 (Claude가 직접 수행)
# → template.yaml (source.slide 필수), template.html 생성

# 5. OOXML 추출 (필수)
python scripts/ooxml_extractor.py input.pptx --slide 3 --output templates/contents/{category}/{id}/template.ooxml

# 6. example.html 생성
# → template.html + sample 데이터

# 7. 썸네일 생성 (원본 PPTX에서)
python scripts/thumbnail.py input.pptx --slide 3 --size theme --output templates/thumbnails/contents/{category}/{id}.png
```

**추출 완료 체크리스트:**
- [ ] template.yaml (source.file, source.slide 포함)
- [ ] template.html
- [ ] template.ooxml/ (필수)
- [ ] example.html
- [ ] thumbnails/contents/{category}/{id}.png (원본 PPTX에서 캡처)

### style-extract

```bash
# 이미지에서 색상 추출
python scripts/image-vectorizer.py reference.png --output themes/new-theme/theme.yaml
```

## 워크플로우 상세

각 워크플로우의 상세 절차:
- [document-extract.md](workflows/document-extract.md) - 문서 양식 추출
- [document-update.md](workflows/document-update.md) - 문서 양식 업데이트
- [document-delete.md](workflows/document-delete.md) - 문서 양식 삭제
- [style-extract.md](workflows/style-extract.md) - 테마 추출
- [content-extract.md](workflows/content-extract.md) - 콘텐츠 추출
- [content-create.md](workflows/content-create.md) - 라이브러리 콘텐츠 생성

## 영역 감지 규칙

```
┌──────────────────────────────────────┐
│ HEADER ZONE (상단 ~22%)               │  ← 문서 양식에서 관리
├──────────────────────────────────────┤
│        CONTENT ZONE (22% ~ 90%)      │  ← 콘텐츠 템플릿
├──────────────────────────────────────┤
│ FOOTER ZONE (하단 ~8%)                │  ← 문서 양식에서 관리
└──────────────────────────────────────┘
```

### 영역별 담당

| 영역 | 담당 | 포함 요소 |
|------|------|----------|
| **Header** | 문서 양식 | 슬라이드 제목, 부제목, 진행률 바 |
| **Content** | 콘텐츠 템플릿 | 본문 레이아웃 패턴 |
| **Footer** | 문서 양식 | 저작권, 페이지 번호, 날짜 |

### 카테고리별 예외

다음 카테고리는 **전체 슬라이드가 콘텐츠**로 취급 (Header/Footer 구분 없음):

| 카테고리 | 이유 |
|----------|------|
| `cover` | 표지 전용 슬라이드 |
| `toc` | 목차 전용 슬라이드 |
| `divider` | 섹션 구분 전용 슬라이드 |
| `closing` | 마무리 전용 슬라이드 |

### 추출 제외 항목

| 제외 항목 | 이유 | 예시 |
|-----------|------|------|
| **원본 저작권** | 콘텐츠와 무관 | "© YEONDU-UNNIE", "Template by XXX" |
| **슬라이드 제목** | 문서 양식에서 관리 | 헤더의 title, subtitle |
| **원본 로고** | 문서 양식에서 관리 | 회사 로고, 워터마크 |

## 오브젝트 자동 추출 조건

content-extract 중 LLM이 아래 조건 감지 시 objects/로 분리 저장:

| 조건 | 예시 |
|------|------|
| 도형 그룹 5개 이상 | 순환도 6단계, 허니콤 7개 |
| 비선형 배치 | 원형, 방사형, 지그재그 |
| 커넥터 포함 | 플로우차트, 프로세스 |
| 수치 데이터 시각화 | 막대, 선, 파이 차트 |

## 패턴 통합 규칙

같은 문서 템플릿 내에서 유사한 슬라이드는 하나의 가변 템플릿으로 통합:

```yaml
# 통합된 템플릿
variants:
  - count: 3
    layout: { columns: 3, gap: "4%" }
  - count: 4
    layout: { columns: 4, gap: "3%" }
```

**통합 기준**: 같은 출처 + 같은 구조 유형 + 같은 카드 구성 + 유사한 스타일

## 폰트 처리

시스템 확인 → 다운로드 시도 → 실패 시 대체 폰트 적용

대체 매핑: [references/font-mappings.yaml](references/font-mappings.yaml)
