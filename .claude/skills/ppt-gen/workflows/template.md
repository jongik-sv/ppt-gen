# 템플릿 기반 생성 워크플로우

기존 템플릿 PPTX를 기반으로 콘텐츠만 교체.

## 사용 시점

- 기존 회사 템플릿 활용
- 원본 디자인 100% 유지 필요
- `quality: high` 선택 시

## 워크플로우

```
1. 템플릿 분석
    ↓
2. 플레이스홀더 추출
    ↓
3. 콘텐츠 매핑
    ↓
4. 치환 및 생성
```

## Step 1: 템플릿 분석

### 썸네일 생성
```bash
python scripts/thumbnail.py template.pptx thumbnails --cols 5
```

### 텍스트 추출
```bash
python -m markitdown template.pptx > template-content.md
```

### 플레이스홀더 인벤토리
```bash
python lib/shared/inventory.py template.pptx inventory.json
```

## Step 2: 슬라이드 선택

썸네일을 보고 사용할 슬라이드 선택:

```python
template_mapping = [
    0,   # 표지
    3,   # 목차
    5,   # 본문 - 4열 카드
    7,   # 본문 - 차트
    12,  # 마무리
]
```

### 슬라이드 재배열
```bash
python lib/ooxml/scripts/rearrange.py template.pptx working.pptx 0,3,5,7,12
```

## Step 3: 콘텐츠 매핑

inventory.json 기반으로 치환 데이터 생성:

```json
{
  "slide-0": {
    "shape-0": {
      "paragraphs": [
        {"text": "새 제목", "bold": true, "alignment": "CENTER"}
      ]
    },
    "shape-1": {
      "paragraphs": [
        {"text": "부제목"}
      ]
    }
  },
  "slide-1": {
    "shape-0": {
      "paragraphs": [
        {"text": "섹션 1", "bullet": true, "level": 0},
        {"text": "섹션 2", "bullet": true, "level": 0}
      ]
    }
  }
}
```

## Step 4: 치환 실행

```bash
python lib/ooxml/scripts/replace.py working.pptx replacement.json output.pptx
```

## 주의사항

### 플레이스홀더 형식
- `{{placeholder}}` 형식 사용
- 배열: `{{items[0].title}}`
- 중첩: `{{section.header.title}}`

### 텍스트 길이
- 원본 텍스트 길이 참고
- 넘침 방지: 글자 수 제한

### 서식 유지
- 원본 폰트/크기/색상 유지
- `paragraphs`에 서식 속성 명시

## 문서 양식 통합

`templates/documents/` 양식 활용:

```yaml
document_style: dongkuk-systems
```

### 양식 구조
```
templates/documents/dongkuk-systems/
├── info.yaml          # 양식 정보
├── master.pptx        # 슬라이드 마스터
├── logo.png           # 로고
└── content_zones.yaml # 콘텐츠 영역 정의
```

### 콘텐츠 영역
```yaml
content_zones:
  - name: main
    top: 1.5in
    left: 0.5in
    width: 9in
    height: 5in
```

콘텐츠는 정의된 영역 내에서만 렌더링.
