---
name: ppt-extract
description: "PPT 템플릿/에셋 추출 서비스. Use when: (1) 슬라이드에서 콘텐츠/오브젝트 추출, (2) PPTX에서 문서 양식/슬라이드 마스터 추출, (3) 이미지에서 테마/스타일 추출, (4) 온라인 슬라이드 크롤링"
user-invocable: true
---

# PPT Template Extraction Service

PPTX, 이미지에서 재사용 가능한 템플릿과 에셋을 추출합니다. PPT 생성 파이프라인(ppt-gen)과 독립적으로 실행됩니다.

## Workflow Selection

| 요청 유형 | 워크플로우 | 가이드 |
|----------|-----------|--------|
| "콘텐츠 추출해줘", "슬라이드 저장" | content-extract | [workflows/content-extract.md](workflows/content-extract.md) |
| "문서 양식 추출해줘", "템플릿 등록" | document-extract | [workflows/document-extract.md](workflows/document-extract.md) |
| "이 이미지 스타일로" | style-extract | [workflows/style-extract.md](workflows/style-extract.md) |
| "이미지를 SVG로", "벡터화" | image-vectorize | 아래 Scripts 섹션 참조 |

## Output Structure

추출 결과물은 `templates/` 폴더에 저장됩니다:

```
C:/project/docs/templates/
├── themes/                  # 테마 정의 (style-extract 출력)
│   └── {theme-id}.yaml
├── contents/                # 콘텐츠 템플릿 (content-extract 출력)
│   ├── templates/{category}/
│   ├── objects/
│   └── registry.yaml
└── documents/               # 문서 템플릿 (document-extract 출력)
    └── {group}/
        ├── config.yaml
        ├── registry.yaml
        └── {양식}.yaml
```

## Dependencies

**Python:**
- python-pptx: PPTX 분석
- pyyaml: YAML 생성
- colorthief: 이미지 색상 추출
- Pillow: 이미지 처리
- defusedxml: XML 파싱
- vtracer: 이미지 벡터화 (Rust 기반, 빠름)

**System:**
- LibreOffice (`soffice`): 썸네일 생성용

## Scripts

| 스크립트 | 용도 |
|---------|------|
| `scripts/content-analyzer.py` | 슬라이드 콘텐츠 OOXML 완전 추출 (NEW) |
| `scripts/template-analyzer.py` | 문서 템플릿 (slideLayouts) 분석 |
| `scripts/style-extractor.py` | 이미지 색상 추출 |
| `scripts/slide-crawler.py` | 온라인 슬라이드 크롤링 |
| `scripts/image-vectorizer.py` | 이미지 → SVG 벡터화 |

### Content Analyzer (콘텐츠 분석기) - v4.0 NEW

슬라이드의 모든 요소(도형, 이미지, 연결선, SmartArt)를 완전히 추출합니다.

**사용법:**
```bash
# 단일 슬라이드 분석
python .claude/skills/ppt-extract/scripts/content-analyzer.py input.pptx --slide 11

# 파일로 저장
python .claude/skills/ppt-extract/scripts/content-analyzer.py input.pptx --slide 11 -o result.yaml

# 모든 슬라이드 요약
python .claude/skills/ppt-extract/scripts/content-analyzer.py input.pptx --all --summary
```

**추출 요소:**
- `p:sp` - 도형 (preset, fill, stroke, effects, text)
- `p:pic` - 이미지/SVG 아이콘
- `p:cxnSp` - 연결선 (dash, arrow)
- `p:grpSp` - 그룹 도형
- `p:graphicFrame` - SmartArt/차트

### Image Vectorizer (이미지 벡터화)

래스터 이미지(PNG, JPG)를 벡터 그래픽(SVG)으로 변환합니다. VTracer 기반으로 빠르고 고품질.

**설치:**
```bash
pip install vtracer
```

**사용법:**
```bash
# 기본 변환 (자동 프리셋)
python .claude/skills/ppt-extract/scripts/image-vectorizer.py icon.png

# 프리셋 지정
python .claude/skills/ppt-extract/scripts/image-vectorizer.py logo.png --preset icon --output logo.svg

# 배치 변환 (디렉토리)
python .claude/skills/ppt-extract/scripts/image-vectorizer.py ./images/ --output ./svgs/

# 프리셋 목록
python .claude/skills/ppt-extract/scripts/image-vectorizer.py --list-presets
```

**프리셋:**
| 프리셋 | 용도 | 특징 |
|-------|------|------|
| `icon` | 아이콘 | 최고 품질, 세밀한 디테일 보존 |
| `logo` | 로고 | 선명한 엣지, 날카로운 코너 |
| `diagram` | 다이어그램 | 직선/곡선 혼합, 부드러운 곡선 |
| `chart` | 차트 | 직각 보존, 다각형 모드 |
| `default` | 기본 | 균형 잡힌 설정 |

**예상 품질:**
- 단색 아이콘: 95-99%
- 플랫 로고: 90-95%
- 다이어그램: 85-95%
- 차트: 85-90%

## Shared Resources (ppt-gen에서 공유)

추출 작업에 필요한 공유 스크립트:
- `ppt-gen/ooxml/scripts/unpack.py`: PPTX 언팩
- `ppt-gen/scripts/thumbnail.py`: 썸네일 생성
- `ppt-gen/scripts/asset-manager.py`: 에셋 관리/크롤링

## References

- [ppt-gen/references/content-schema.md](../ppt-gen/references/content-schema.md): 콘텐츠 템플릿 v4.0 스키마 (공유)
- [references/font-mappings.yaml](references/font-mappings.yaml): 폰트 매핑 정의

---

## 완료 후 정리 (MANDATORY)

**중요**: 추출 작업 완료 시 생성한 임시 파일을 반드시 삭제합니다.

### 삭제 대상

1. **언팩된 PPTX 폴더**:
   - `workspace/unpacked/` 전체 폴더
   - `workspace/template-preview/` 폴더

2. **임시 스크립트** (프로젝트 루트에 생성된 경우):
   - `extract_*.py`
   - `analyze_*.py`
   - `*_temp*.py`

3. **임시 작업 파일**:
   - `workspace/analysis/` 폴더 (분석 결과 YAML)
   - 임시 `.pdf` 파일
   - 크롤링 임시 이미지 (`templates/` 외부)

### 보존 대상 (삭제 금지)

- `templates/` 하위 모든 파일 (추출 결과물)
- `registry.yaml` 파일들
- 사용자가 명시적으로 요청한 출력물

### 정리 명령어

```bash
# 언팩 폴더 삭제
rm -rf workspace/unpacked workspace/template-preview workspace/analysis

# 프로젝트 루트 임시 스크립트 삭제
rm -f extract_*.py analyze_*.py *_temp*.py
```

### 정리 체크리스트

추출 완료 전 다음을 확인:
- [ ] `templates/` 에 결과물 저장됨
- [ ] `registry.yaml` 업데이트됨
- [ ] 썸네일 생성됨 (`thumbnails/`)
- [ ] 임시 폴더 삭제됨 (`workspace/`)
