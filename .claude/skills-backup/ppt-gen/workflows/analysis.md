# PPT Analysis Workflow

PPT 파일의 내용을 읽고 분석합니다.

## Triggers

- "PPT 분석해줘"
- "슬라이드 내용 확인해줘"
- "프레젠테이션 읽어줘"

## Text Extraction

텍스트 내용만 필요한 경우:

```bash
python -m markitdown path-to-file.pptx
```

## Raw XML Access

다음 기능에는 Raw XML 접근이 필요합니다:
- 댓글, 발표자 노트
- 슬라이드 레이아웃, 애니메이션
- 디자인 요소, 복잡한 서식

### Unpacking

```bash
python ooxml/scripts/unpack.py <office_file> <output_dir>
```

### Key File Structures

| 경로 | 설명 |
|------|------|
| `ppt/presentation.xml` | 메인 메타데이터, 슬라이드 참조 |
| `ppt/slides/slide{N}.xml` | 개별 슬라이드 내용 |
| `ppt/notesSlides/notesSlide{N}.xml` | 발표자 노트 |
| `ppt/comments/modernComment_*.xml` | 댓글 |
| `ppt/slideLayouts/` | 레이아웃 템플릿 |
| `ppt/slideMasters/` | 마스터 슬라이드 |
| `ppt/theme/` | 테마, 스타일 정보 |
| `ppt/media/` | 이미지, 미디어 파일 |

## Typography and Color Extraction

**디자인 참조용 분석 시**:

1. **테마 파일 읽기**: `ppt/theme/theme1.xml`
   - `<a:clrScheme>`: 색상 스키마
   - `<a:fontScheme>`: 폰트 스키마

2. **슬라이드 콘텐츠 샘플링**: `ppt/slides/slide1.xml`
   - `<a:rPr>`: 실제 폰트 사용
   - 색상 적용 상태

3. **패턴 검색**:
   ```bash
   grep -r "<a:solidFill>" ppt/
   grep -r "<a:srgbClr" ppt/
   ```
