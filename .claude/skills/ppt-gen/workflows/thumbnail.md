# Thumbnail Generation Workflow

PPT 슬라이드의 시각적 썸네일 그리드를 생성합니다.

## Prerequisites

### 시스템 의존성

| 도구 | 용도 | 필수 여부 | 설치 |
|------|------|----------|------|
| LibreOffice | PPTX → PDF | PPTX 모드만 | `brew install --cask libreoffice` |
| Poppler | PDF → Image | PPTX 모드만 | `brew install poppler` |
| Pillow | 이미지 처리 | 필수 | `pip install pillow` |

**Note**: `--from-images` 모드 사용 시 LibreOffice/Poppler 불필요

## Usage

```bash
# PPTX 모드 (LibreOffice 필요)
cd .claude/skills/ppt-gen && python scripts/thumbnail.py template.pptx [output_prefix]

# 이미지 기반 모드 (LibreOffice 불필요)
cd .claude/skills/ppt-gen && python scripts/thumbnail.py --from-images images/ output/
```

## Features

- 기본 출력: `thumbnails.jpg`
- 대용량 덱: `thumbnails-1.jpg`, `thumbnails-2.jpg`, ...
- 기본: 5열, 그리드당 최대 30 슬라이드 (5x6)

## Options

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--cols N` | 열 수 조정 (3-6) | `--cols 4` |
| `--slides N` | 특정 슬라이드만 (0-indexed) | `--slides 0,2,5` |
| `--single` | 개별 이미지로 저장 | `--single` |
| `--from-images DIR` | 이미지 폴더에서 썸네일 생성 (LibreOffice 불필요) | `--from-images slides/` |
| `--prefix NAME` | 출력 파일명 접두사 (기본: slide) | `--prefix deepgreen` |

## Grid Limits by Columns

| 열 수 | 그리드당 슬라이드 |
|-------|------------------|
| 3 | 12 |
| 4 | 20 |
| 5 | 30 |
| 6 | 42 |

## Examples

```bash
# 기본 사용 (ppt-gen 디렉토리에서)
cd .claude/skills/ppt-gen && python scripts/thumbnail.py presentation.pptx

# 커스텀 이름, 4열
cd .claude/skills/ppt-gen && python scripts/thumbnail.py template.pptx analysis --cols 4

# 특정 폴더에 저장
cd .claude/skills/ppt-gen && python scripts/thumbnail.py template.pptx workspace/my-grid

# 특정 슬라이드만 (0-indexed)
cd .claude/skills/ppt-gen && python scripts/thumbnail.py input.pptx output/ --slides 0,2,5

# 개별 이미지로 저장 (콘텐츠 추출용)
cd .claude/skills/ppt-gen && python scripts/thumbnail.py input.pptx templates/contents/thumbnails/ --slides 0,2,5 --single

# 이미지 기반 모드 (LibreOffice 불필요)
cd .claude/skills/ppt-gen && python scripts/thumbnail.py --from-images slides/ grid --cols 4

# 이미지에서 개별 썸네일 생성 (커스텀 접두사)
cd .claude/skills/ppt-gen && python scripts/thumbnail.py --from-images slides/ output/ --single --prefix deepgreen
# 결과: deepgreen-0.png, deepgreen-1.png, ...

# 특정 이미지만 썸네일 생성
cd .claude/skills/ppt-gen && python scripts/thumbnail.py --from-images slides/ output/ --slides 0,2,5 --single --prefix mytemplate
```

## Use Cases

- **템플릿 분석**: 슬라이드 레이아웃, 디자인 패턴 파악
- **콘텐츠 리뷰**: 전체 프레젠테이션 시각적 개요
- **네비게이션 참조**: 시각적 외관으로 특정 슬라이드 찾기
- **품질 체크**: 모든 슬라이드 서식 확인
- **콘텐츠 추출**: 특정 슬라이드 썸네일 생성

## Note

슬라이드는 0-indexed입니다 (Slide 0, Slide 1, ...).
