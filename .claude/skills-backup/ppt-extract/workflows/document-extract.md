# Document Template Extraction Workflow

전체 문서의 구조와 테마를 분석하여 문서 템플릿(회사/브랜드)으로 저장합니다.

## Triggers

- "문서 양식 추출해줘"
- "이 PPT를 템플릿으로 등록"
- "회사 양식으로 저장"

## Workflow

### 1. User Input (REQUIRED)

**AskUserQuestion 도구를 사용하여 다음 정보를 수집:**

| 질문 | 설명 | 예시 |
|------|------|------|
| 회사/그룹명 | 템플릿이 속할 회사 또는 브랜드명 | "동국제강", "삼성전자" |
| 폴더 ID | 영문 소문자 폴더명 (자동 제안 가능) | "dongkuk", "samsung" |
| 양식 이름 | 이 특정 양식의 이름 | "기본양식", "제안서", "보고서" |

```
AskUserQuestion:
  questions:
    - header: "회사명"
      question: "이 템플릿이 속할 회사/브랜드명은 무엇인가요?"
      options:
        - label: "{PPT에서 감지된 이름}"
          description: "PPT 테마에서 추출된 이름"
        - label: "직접 입력"
          description: "다른 회사명 사용"

    - header: "폴더 ID"
      question: "템플릿을 저장할 폴더 ID를 선택하세요 (영문 소문자)"
      options:
        - label: "{자동 생성된 ID}"
          description: "templates/documents/{id}/ 에 저장"
        - label: "직접 입력"
          description: "커스텀 폴더명 사용"

    - header: "양식 이름"
      question: "이 양식의 이름은 무엇인가요?"
      options:
        - label: "기본양식"
          description: "범용 기본 템플릿"
        - label: "제안서"
          description: "제안/영업용 템플릿"
        - label: "보고서"
          description: "내부 보고용 템플릿"
```

### 2. Generate Thumbnails

```bash
# ppt-gen의 thumbnail.py 사용
python .claude/skills/ppt-gen/scripts/thumbnail.py input.pptx workspace/template-preview
```

### 3. Analyze Theme, Layouts, and Placeholders

```bash
# PPTX 언팩 (ppt-gen의 ooxml 스크립트 사용)
python .claude/skills/ppt-gen/ooxml/scripts/unpack.py input.pptx workspace/unpacked
```

**분석 항목:**

#### 3.1 테마 분석
- **테마 파일**: `ppt/theme/theme1.xml` → 색상/폰트 추출

#### 3.2 플레이스홀더 추출

**슬라이드 레이아웃 파일**: `ppt/slideLayouts/slideLayout*.xml`

```xml
<!-- 플레이스홀더 예시 -->
<p:sp>
  <p:nvSpPr>
    <p:nvPr>
      <p:ph type="title" idx="0"/>  <!-- type과 idx로 역할 식별 -->
    </p:nvPr>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="457200" y="274638"/>   <!-- 위치 (EMU 단위) -->
      <a:ext cx="8229600" cy="1143000"/> <!-- 크기 (EMU 단위) -->
    </a:xfrm>
  </p:spPr>
</p:sp>
```

**EMU → % 변환:**
```python
# 슬라이드 크기 (기본: 9144000 x 6858000 EMU = 10" x 7.5")
slide_width = 9144000
slide_height = 6858000

x_percent = (x_emu / slide_width) * 100
y_percent = (y_emu / slide_height) * 100
width_percent = (cx_emu / slide_width) * 100
height_percent = (cy_emu / slide_height) * 100
```

#### 3.3 슬라이드 카테고리 분류
각 슬라이드의 플레이스홀더 구성으로 카테고리 추론

### 4. Create Group Folder and YAML

`templates/documents/{그룹}/` 폴더 생성:

**config.yaml** (테마 정보):
```yaml
group:
  id: new-company
  name: New Company

theme:
  colors:
    primary: "#002452"
    secondary: "#C51F2A"
  fonts:
    title: "본고딕 Bold"
    body: "본고딕 Normal"

companies:
  - id: new-company
    name: New Company
```

**{양식}.yaml** (레이아웃 + 플레이스홀더 정보):
```yaml
template:
  id: 제안서1
  name: 제안서 (기본)
  source: input.pptx

layouts:
  - index: 0
    category: cover
    name: 표지
    placeholders:
      - type: title
        role: "메인 제목"
        position: {x: 10%, y: 35%, width: 80%, height: 15%}
      - type: subtitle
        role: "부제목/슬로건"
        position: {x: 10%, y: 52%, width: 80%, height: 8%}
      - type: picture
        role: "배경 이미지"
        position: {x: 0%, y: 0%, width: 100%, height: 100%}
        z_order: -1

  - index: 1
    category: toc
    name: 목차
    placeholders:
      - type: title
        role: "목차 제목"
        position: {x: 5%, y: 8%, width: 90%, height: 10%}
      - type: body
        role: "목차 항목 리스트"
        position: {x: 10%, y: 25%, width: 80%, height: 65%}

  - index: 2
    category: content_bullets
    name: 본문 (불릿)
    placeholders:
      - type: title
        role: "슬라이드 제목"
        position: {x: 5%, y: 5%, width: 90%, height: 12%}
      - type: body
        role: "본문 내용 (불릿 포인트)"
        position: {x: 5%, y: 20%, width: 90%, height: 70%}
```

### Placeholder Types (PPTX 표준)

| type | idx | 역할 |
|------|-----|------|
| `title` | 0 | 슬라이드 제목 |
| `body` | 1 | 본문 텍스트 |
| `subtitle` | - | 부제목 |
| `ctrTitle` | - | 중앙 제목 (표지용) |
| `picture` | - | 이미지 영역 |
| `chart` | - | 차트 영역 |
| `table` | - | 표 영역 |
| `dgm` | - | 다이어그램 (SmartArt) |
| `footer` | 10 | 바닥글 |
| `sldNum` | 12 | 슬라이드 번호 |
| `dt` | 11 | 날짜/시간 |

### 5. Update Registry

`templates/documents/{그룹}/registry.yaml`:

```yaml
templates:
  - id: 제안서1
    name: 제안서 (기본)
    file: 제안서1.yaml
    type: proposal
    description: "표지 + 목차 + 본문(불릿) + 마무리 구성"
```

### 6. User Confirmation

- 생성된 썸네일 표시
- 템플릿 정보 요약 제공

## Auto Layout Classification

| 카테고리 | 감지 조건 |
|----------|----------|
| `cover` | 첫 슬라이드, 큰 제목만 |
| `toc` | 번호+텍스트 반복 패턴 |
| `section` | 제목만, 배경색 있음 |
| `content_bullets` | BODY placeholder + 불릿 |
| `content_free` | 제목만, 넓은 빈 공간 |

## Output Structure

```
templates/documents/{그룹}/
├── config.yaml          # 테마 정보
├── registry.yaml        # 양식 목록
├── assets/              # 에셋 (로고 등)
└── {양식}.yaml          # 각 양식 정의
```
