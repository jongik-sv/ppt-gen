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
│   ├── template.yaml
│   ├── template.html
│   ├── template.ooxml
│   └── thumbnail.png
└── objects/{category}/{id}/        # 오브젝트 (자동 추출)
```

## 스크립트

| 스크립트 | 용도 |
|---------|------|
| `scripts/slide-crawler.py` | PPTX 슬라이드 파싱, 도형/텍스트 추출 |
| `scripts/style-extractor.py` | 색상 팔레트, 폰트 추출 |
| `scripts/content-analyzer.py` | 콘텐츠 영역 감지, 플레이스홀더 후보 탐지 |
| `scripts/template-analyzer.py` | 패턴 시그니처, 유사 템플릿 통합 |
| `scripts/font-manager.py` | 폰트 대체 매핑 |
| `scripts/image-vectorizer.py` | 이미지에서 색상/스타일 추출 |
| `scripts/thumbnail.py` | 썸네일 생성 |

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
# → template.yaml, template.html, template.ooxml 생성
```

### style-extract

```bash
# 이미지에서 색상 추출
python scripts/image-vectorizer.py reference.png --output themes/new-theme/theme.yaml
```

## 워크플로우 상세

각 워크플로우의 상세 절차:
- [document-extract.md](workflows/document-extract.md) - 문서 양식 추출
- [style-extract.md](workflows/style-extract.md) - 테마 추출
- [content-extract.md](workflows/content-extract.md) - 콘텐츠 추출

## 영역 감지 규칙

```
┌──────────────────────────────────────┐
│ TITLE ZONE (상단 ~22%)                │
├──────────────────────────────────────┤
│        CONTENT ZONE (22% ~ 90%)      │
├──────────────────────────────────────┤
│ FOOTER ZONE (하단 ~8%)                │
└──────────────────────────────────────┘
```

- **Title Zone**: 플레이스홀더 타입(TITLE) 또는 이름에 "title" 포함
- **Footer Zone**: 플레이스홀더 타입(FOOTER, SLIDE_NUMBER) 또는 하단 10%
- **Content Zone**: Title 하단 + 2% ~ Footer 상단 - 2%

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
