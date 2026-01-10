# PPTX → HTML 재현율 극대화 조사

**작성일**: 2026-01-10

## 1. 핵심 발견

### 1.1 재현율에 영향을 주는 요소

| 요소 | 영향도 | 설명 |
|------|--------|------|
| **위치/크기** | 매우 높음 | EMU 단위 정확한 추출 필수 |
| **폰트** | 높음 | 폰트명, 크기, 굵기, 색상 모두 추출 |
| **색상** | 높음 | 테마 기반 시맨틱 매핑 필요 |
| **복잡한 효과** | 중간 | 3D, 그라디언트, 베벨 등 |
| **그룹화** | 중간 | 상대 위치 보존 필요 |

### 1.2 기존 KI의 v3.1 전략 요약

> **5단계 하이브리드 포맷** (extraction_strategies.md)

| Layer | 포맷 | 용도 |
|-------|------|------|
| 1 | YAML (메타데이터) | ID, 버전, 디자인 의도 |
| 2 | YAML (레이아웃) | %-based 위치, EMU 원본 보존 |
| 3 | YAML (단순 도형) | 사각형, 타원, 텍스트박스 |
| 4 | SVG Path | 곡선, 순환도, 허니콤 |
| 5 | OOXML | 3D, 글로우, 복잡한 그라디언트 |

---

## 2. 재현율 극대화 전략

### 2.1 Shape Source 결정 로직

```
원본 도형
    │
    ├── 단순 도형 (solid fill, preset shape)
    │   └── → description (YAML) : 편집성 ↑
    │
    ├── 복잡한 효과 (gradient, 3D, bevel, custom path)
    │   └── → ooxml (raw XML) : 재현율 100%
    │
    └── 그룹화된 도형
        └── → ooxml : 상대 위치 보존
```

**판단 트리거 (Python)**:
```python
# OOXML 트리거
if '<a:gradFill' in xml: return 'ooxml'  # 그라디언트
if '<a:custGeom>' in xml: return 'ooxml'  # 커스텀 도형
if '<a:sp3d' in xml: return 'ooxml'       # 3D 효과
if '<a:scene3d' in xml: return 'ooxml'    # 3D 장면
if '<a:bevel' in xml: return 'ooxml'      # 베벨
if 'grpSp' in xml: return 'ooxml'         # 그룹

return 'description'  # 기본: 자연어 설명
```

### 2.2 정확한 위치/크기 추출

```python
# python-pptx로 추출
shape.left   # EMU (English Metric Units)
shape.top    # EMU
shape.width  # EMU
shape.height # EMU

# %-based 변환 (960x540 또는 1920x1080 기준)
x_pct = (shape.left / slide_width) * 100
y_pct = (shape.top / slide_height) * 100
```

> **중요**: EMU 원본값과 % 변환값 모두 저장 → 비율 변환 시 정확도 유지

### 2.3 폰트 속성 완전 추출

```python
for paragraph in shape.text_frame.paragraphs:
    for run in paragraph.runs:
        font_data = {
            'name': run.font.name,
            'size_pt': run.font.size.pt if run.font.size else None,
            'bold': run.font.bold,
            'italic': run.font.italic,
            'color': str(run.font.color.rgb) if run.font.color.rgb else None
        }
```

### 2.4 테마 색상 시맨틱 매핑

| Theme ID | 시맨틱 토큰 | 용도 |
|----------|-------------|------|
| `dk1` | `dark_text` | 어두운 텍스트 |
| `lt1` | `light_bg` | 밝은 배경 |
| `dk2` | `primary` | 주요 색상 |
| `lt2` | `gray` | 회색 |
| `accent1~6` | `accent1~6` | 강조색 |

> 원시 RGB 대신 **시맨틱 토큰**을 저장하면 테마 변경 시에도 일관성 유지

---

## 3. 콘텐츠 영역 추출 (content_only 모드)

### 3.1 동적 영역 감지

```
┌────────────────────────────────────┐
│ TITLE ZONE (상단 ~22%)              │ ← 추출 제외
├────────────────────────────────────┤
│                                    │
│        CONTENT ZONE                │ ← 추출 대상
│        (22% ~ 90%)                 │
│                                    │
├────────────────────────────────────┤
│ FOOTER ZONE (하단 ~8%)              │ ← 추출 제외
└────────────────────────────────────┘
```

**감지 로직**:
1. Title: `placeholder_type`가 TITLE/CENTER_TITLE/SUBTITLE
2. Footer: `placeholder_type`가 FOOTER/SLIDE_NUMBER
3. Content: Title 하단 + 2% ~ Footer 상단 - 2%

### 3.2 도형 필터링

```python
# 중심점 기반 필터링
centroid_y = shape.top + (shape.height / 2)
if content_top <= centroid_y <= content_bottom:
    # 콘텐츠 영역 내 → 추출
```

---

## 4. 웹 조사 결과: PPTX → HTML 고충실도 변환

### 4.1 주요 도전과제

| 도전과제 | 해결책 |
|----------|--------|
| **폰트 불일치** | 웹 폰트 임베딩 또는 fallback 정의 |
| **텍스트 → 이미지 변환** | 텍스트를 HTML로 유지 (접근성/SEO) |
| **복잡한 애니메이션 손실** | 기본 애니메이션만 지원 |
| **레이아웃 왜곡** | 절대 위치 + 비율 기반 혼합 |

### 4.2 권장 도구/라이브러리

| 도구 | 특징 |
|------|------|
| **Aspose.Slides** | .NET/Java, 높은 충실도, 폰트 보존 |
| **iSpring** | PPT 플러그인, 애니메이션/트랜지션 보존 |
| **HTML5Point** | PowerPoint → HTML5, SmartArt 지원 |
| **python-pptx** | Python, 구조 파싱 (렌더링 미지원) |

### 4.3 Best Practices

1. **변환 전 단순화**: 복잡한 애니메이션/효과 최소화
2. **SmartArt → 이미지**: MS Office Graphic Objects는 이미지로 변환
3. **숨긴 슬라이드 제거**: 변환 오류 방지
4. **폰트 확인**: 웹 안전 폰트 사용 또는 CSS @font-face
5. **반응형 출력**: 고정 크기 대신 비율 기반 레이아웃

---

## 5. 권장 추출 아키텍처

### 5.1 하이브리드 방식 (방식 2+4 개선)

```
원본 PPTX 슬라이드
        │
        ▼
┌─────────────────────────────────────────────┐
│ 1. 구조 파싱 (python-pptx)                   │
│    - 도형 목록, Z-order, 그룹 관계            │
└─────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│ 2. 영역 감지                                 │
│    - Title Zone, Content Zone, Footer Zone   │
└─────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│ 3. 도형별 복잡도 판단                         │
│    ┌─────────────┬─────────────┬──────────┐ │
│    │ 단순 (YAML) │ 중간 (SVG)  │ 복잡     │ │
│    │             │             │ (OOXML)  │ │
│    └─────────────┴─────────────┴──────────┘ │
└─────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│ 4. HTML+CSS 템플릿 생성                      │
│    - Handlebars 플레이스홀더                 │
│    - CSS 변수로 테마 매핑                     │
│    - 복잡 도형은 이미지/SVG 참조              │
└─────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│ 5. 메타데이터 + 시맨틱 설명 (YAML)           │
│    - slots, layout, semantic_description    │
│    - EMU 원본값 보존                         │
└─────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│ 6. 썸네일 생성 + 검증                        │
│    - 원본과 비교 (SSIM, 육안 검토)           │
└─────────────────────────────────────────────┘
```

### 5.2 재현율 극대화를 위한 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **1. EMU 보존** | 원본 EMU 값을 별도 저장하여 1:1 재현 가능 |
| **2. 복잡도 기반 분기** | 단순→설명, 복잡→원본 XML 보존 |
| **3. 테마 시맨틱화** | RGB 대신 토큰 사용으로 테마 독립성 확보 |
| **4. 그룹 구조 보존** | 그룹화된 도형은 OOXML로 통째로 저장 |
| **5. 검증 루프** | 생성된 HTML 썸네일 vs 원본 비교 |

---

## 6. 결론

### 6.1 재현율 100%를 위한 핵심

> **"복잡한 것은 원본 그대로, 단순한 것은 편집 가능하게"**

1. **OOXML 조건부 보존**: 그라디언트, 3D, 커스텀 도형 → raw XML
2. **EMU 이중 저장**: % 변환값 + EMU 원본값 모두 저장
3. **테마 시맨틱 매핑**: RGB → 토큰 (primary, accent 등)
4. **검증 파이프라인**: 생성 후 시각적 비교

### 6.2 기존 방식 2+4 개선 포인트

| 기존 | 개선 |
|------|------|
| HTML+CSS만 저장 | + OOXML 조각 조건부 저장 |
| % 기반 위치 | + EMU 원본값 병행 저장 |
| RGB 색상 | → 시맨틱 토큰 매핑 |
| 수동 검증 | → 자동 SSIM 비교 |

---

## 참고 자료

- Visual Content Engineering KI (extraction_strategies.md, optimal_extraction_format.md)
- v3.1 Reference Implementation (v3_1_reference_implementation.md)
- Aspose.Slides, iSpring, HTML5Point 문서
