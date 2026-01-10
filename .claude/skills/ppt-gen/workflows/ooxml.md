# OOXML Editing Workflow

기존 PPT 파일을 직접 수정합니다.

## Triggers

- "이 PPT 수정해줘"
- "슬라이드 내용 바꿔줘"
- "텍스트 수정해줘"

## Workflow

### 1. MANDATORY - Read Full Guide

**반드시** [`ooxml.md`](../ooxml.md) 전체를 읽으세요 (~500 lines).

```
Read ooxml.md (전체 파일, 범위 제한 없이)
```

### 2. Unpack Presentation

```bash
python ooxml/scripts/unpack.py <office_file> <output_dir>
```

### 3. Edit XML Files

주로 편집하는 파일:
- `ppt/slides/slide{N}.xml`: 슬라이드 콘텐츠
- 관련 레이아웃/마스터 파일

### 4. Validate (CRITICAL)

**각 편집 후 즉시 검증**:

```bash
python ooxml/scripts/validate.py <dir> --original <file>
```

검증 오류가 있으면 다음 단계로 진행하지 마세요.

### 5. Pack Final Presentation

```bash
python ooxml/scripts/pack.py <input_directory> <office_file>
```

## Available Scripts

| 스크립트 | 용도 |
|----------|------|
| `unpack.py` | PPTX → 폴더 |
| `pack.py` | 폴더 → PPTX |
| `validate.py` | XML 유효성 검사 |

## Tips

- XML 구조를 정확히 이해한 후 편집
- 작은 변경도 반드시 검증
- 백업 파일 유지
