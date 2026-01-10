# PRD: PPT Skills Suite - 부록

> 본문: [PRD_PPT_Skills_Suite.md](./PRD_PPT_Skills_Suite.md)

---

## 부록 A: 세션 스키마 (session.yaml)

### A.1 전체 예시

```yaml
session:
  id: "2026-01-11-abc123"
  created_at: "2026-01-11T01:15:00"
  status: "generating"

# ===== 전체 설정 (Stage 1) =====
settings:
  document_type: "proposal"
  document_style: "dongkuk-systems"
  slide_size: "16:9"
  audience: "executive"
  duration: "10min"
  tone: "formal"
  quality: "medium"

# ===== 슬라이드별 통합 정보 =====
slides:
  - index: 1
    type: "cover"
    outline:
      title: "스마트 물류 혁신 제안"
      subtitle: "2026년 물류 전략"
    template: null
    file: "output/slide-01.html"
    status: "completed"
    
  - index: 3
    type: "content"
    
    # Stage 2: 아웃라인 (고정)
    outline:
      title: "현황 분석"
      key_points:
        - "물류 현황 데이터"
        - "문제점 3가지"
        - "개선 필요성"
      speaker_notes: "현재 물류 시스템의 비효율성 강조"
    
    # Stage 3~4: 시도별 기록
    attempts:
      - attempt: 1
        template:
          matched: "dongkuk-grid-cards-01"
          match_reason: "key_points 3개 → 그리드 카드 적합"
          match_score: 0.87
        content:
          title: "현황 분석"
          items:
            - { icon: "chart", title: "물류 현황", description: "연간 처리량 150만 건" }
            - { icon: "warning", title: "주요 문제점", description: "배송 지연율 12%" }
            - { icon: "target", title: "개선 필요성", description: "목표 지연율 5% 이하" }
        file: "output/slide-03-v1.html"
        evaluation:
          scores: { layout: 20, typography: 16, color: 18, content: 18, visual: 6, total: 78 }
          passed: false
          feedback: "카드 간격 좁음, 폰트 크기 불균형"
          
      - attempt: 2
        template:
          matched: "dongkuk-grid-cards-01"
          reuse_reason: "템플릿 유지, 스타일만 개선"
        content:
          same_as_prev: true
        file: "output/slide-03-v2.html"
        evaluation:
          scores: { total: 82 }
          passed: false
          feedback: "개선됨, 색상 대비 부족"
          
      - attempt: 3
        template:
          matched: "tipgreen-grid-cards-01"
          change_reason: "2회 실패 → 대안 템플릿 선택"
        content:
          same_as_prev: true
        file: "output/slide-03-v3.html"
        evaluation:
          scores: { total: 89 }
          passed: true
          feedback: null
          
    final_attempt: 3
    status: "completed"

# ===== 최종 결과 =====
output:
  file: "output/presentation.pptx"
  generated_at: "2026-01-11T01:30:00"
  slide_count: 10
```

### A.2 최종 파일 결정 로직

```python
def get_final_file(slide):
    """session.yaml의 슬라이드에서 최종 HTML 파일 경로 반환"""
    
    if not slide.get("attempts"):
        # 레이아웃 슬라이드 (cover, toc 등)
        return slide["file"]
    
    final_attempt = slide["final_attempt"]
    
    if final_attempt == 1 and len(slide["attempts"]) == 1:
        # 첫 시도 합격 → 버전 없는 파일명
        return f"output/slide-{slide['index']:02d}.html"
    else:
        # 재시도 → 버전 번호 포함
        return f"output/slide-{slide['index']:02d}-v{final_attempt}.html"

# 전체 슬라이드 목록 생성
def get_all_final_files(session):
    return [get_final_file(s) for s in session["slides"]]
```

---

## 부록 B: 템플릿 파일 예시

### B.1 template.html 구조

> **HTML + CSS 변수 + Handlebars** 방식

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    /* 테마 색상 변수 (생성 시 치환됨) */
    :root {
      --primary: {{theme.primary}};
      --secondary: {{theme.secondary}};
      --accent: {{theme.accent}};
      --background: {{theme.background}};
      --text: {{theme.text}};
      --border-radius: {{theme.style_hints.border_radius}};
    }
    
    /* 컴포넌트 스타일 */
    .slide { 
      width: 1920px; 
      height: 1080px; 
      background: var(--background); 
    }
    .card { 
      background: var(--primary); 
      color: white;
      border-radius: var(--border-radius);
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
  </style>
</head>
<body>
  <div class="slide">
    <h2 class="title">{{title}}</h2>
    <div class="card-grid">
      {{#each items}}
      <div class="card">
        <img src="{{this.icon}}" alt="icon"/>
        <h3>{{this.title}}</h3>
        <p>{{this.description}}</p>
      </div>
      {{/each}}
    </div>
  </div>
</body>
</html>
```

### B.2 template.ooxml 플레이스홀더

> **네이티브 플레이스홀더 + 커스텀 마커 혼합** 방식

**단순 텍스트 (네이티브):**
```xml
<p:sp>
  <p:nvSpPr>
    <p:nvPr><p:ph type="title"/></p:nvPr>
  </p:nvSpPr>
  <p:txBody>
    <a:p><a:r><a:t>제목 플레이스홀더</a:t></a:r></a:p>
  </p:txBody>
</p:sp>
```

**배열 항목 (커스텀 마커):**
```xml
<p:sp>
  <!-- 첫 번째 카드 (템플릿으로 사용, 복제됨) -->
  <p:txBody>
    <a:p><a:r><a:t>__SLOT_items[0].title__</a:t></a:r></a:p>
    <a:p><a:r><a:t>__SLOT_items[0].description__</a:t></a:r></a:p>
  </p:txBody>
</p:sp>
```

### B.3 OOXML 처리 로직

```python
# 1. 단순 플레이스홀더: python-pptx
slide.shapes.title.text = data["title"]

# 2. 배열: 도형 복제 + 마커 치환
template_shape = find_shape_with_marker("__SLOT_items[0]")
for i, item in enumerate(data["items"]):
    if i == 0:
        replace_markers(template_shape, item, index=0)
    else:
        new_shape = clone_shape(template_shape, offset=i)
        replace_markers(new_shape, item, index=i)
```

---

## 부록 C: 레지스트리 스키마 상세

### C.1 콘텐츠 레지스트리 (contents/*/registry.yaml)

```yaml
version: "1.0"
updated_at: "2026-01-10"

templates:
  - id: "tipgreen/timeline-01"
    name: "타임라인"
    
    # === 기본 정보 ===
    category: "process"
    pattern: "timeline-horizontal"
    element_count: "3-5"
    
    # === 출처 정보 ===
    source_document: "tipgreen"
    source_file: "깔끔이_팁그린.pptx"
    slide_index: 7
    extracted_at: "2026-01-10"
    
    # === 시각적 특성 (LLM 매칭용) ===
    visual:
      layout: "horizontal"           # horizontal, vertical, zigzag
      shape: "circle"                # circle, rectangle, diamond, arrow
      connector: "line"              # line, arrow, curve, dotted
      
    # === 색상 정보 ===
    colors:
      primary: "#1E5128"
      accent: "#4E9F3D"
      palette_type: "green"          # blue, green, gray, multi
      
    # === 스타일 특성 ===
    style:
      mood: "modern"                 # modern, classic, minimal, playful
      corners: "rounded"             # rounded, sharp
      shadows: true
      gradients: true
      
    # === 적합 용도 ===
    recommended_for:
      industries: ["tech", "eco", "startup"]
      audiences: ["executive", "client"]
      purposes: ["proposal", "report"]
      
    # === 시맨틱 설명 ===
    semantic_description: |
      수평 배치된 원형 노드를 직선으로 연결한 타임라인.
      녹색 그라디언트와 둥근 모서리로 친환경/기술 느낌.
    
    # === 검색용 태그 ===
    tags: ["timeline", "process", "horizontal", "modern"]
    thumbnail: "tipgreen/timeline-01.png"
```

### C.2 문서 양식 스키마 (documents/*.yaml)

```yaml
document:
  id: "dongkuk-standard"
  name: "동국그룹 기본양식"
  group: "동국그룹"
  source_file: "원본.pptx"
  extracted_at: "2026-01-10"

layouts:
  - index: 0
    name: "표지"
    type: cover
    ooxml_file: "ooxml/slideLayout1.xml"
    thumbnail: "thumbnails/layout-0.png"
    placeholders:
      - id: "title"
        type: ctrTitle
        position: { x: 5%, y: 35%, width: 90%, height: 15% }
      - id: "subtitle"
        type: subTitle
        position: { x: 5%, y: 52%, width: 90%, height: 8% }

  - index: 3
    name: "내지 (제목+액션타이틀)"
    type: body
    variant: "title-action"
    ooxml_file: "ooxml/slideLayout4.xml"
    content_zone:
      position: { x: 3%, y: 24%, width: 94%, height: 72% }

master:
  ooxml_file: "ooxml/slideMaster1.xml"
  common_elements:
    - id: "logo"
      file: "assets/media/logo.png"
      position: { x: 90%, y: 2%, width: 8%, height: 6% }

theme:
  ooxml_file: "ooxml/theme1.xml"
  colors:
    dk2: "#002452"
    accent1: "#C51F2A"
  fonts:
    major: "맑은 고딕"
    minor: "맑은 고딕"
```

### C.3 테마 스키마 (themes/*.yaml)

```yaml
id: deepgreen
name: "딥그린 테마"
colors:
  primary: "#1a5f4a"
  secondary: "#2d7a5e"
  accent: "#4a9d7f"
  background: "#f5f9f7"
  surface: "#ffffff"
  text: "#1a1a1a"
  muted: "#6b7c74"
fonts:
  major: "Pretendard"
  minor: "Pretendard"
style_hints:
  border_radius: "16px"
  shadow: "0 4px 12px rgba(0,0,0,0.08)"
```

---

## 부록 D: 콘텐츠 템플릿 스키마 상세

### D.1 template.yaml 전체 예시

```yaml
# === 기본 정보 ===
id: dongkuk-grid-cards-01
category: grid
pattern: grid-icon-cards           # 레이아웃 유형 (검색/그룹핑용)
element_count: "2-6"
description: "아이콘 카드 그리드 (2~6개)"

# === 문서 양식 연결 ===
document_style: dongkuk            # 연결된 문서 양식 (null이면 범용)
has_ooxml: true                    # OOXML 포함 여부

# === 가변 레이아웃 ===
variants:
  - count: 2
    layout: { columns: 2, gap: 8% }
  - count: 3
    layout: { columns: 3, gap: 4% }
  - count: 4
    layout: { columns: 4, gap: 3% }

# === 슬롯 정의 (Handlebars 바인딩용) ===
slots:
  - name: title
    type: text
    required: true
    example: "핵심 서비스"
  - name: items
    type: array
    min: 2
    max: 6
    item_schema:
      - { name: icon, type: image }
      - { name: title, type: text, max_length: 20 }
      - { name: description, type: text, max_length: 80 }

# === 시맨틱 설명 (LLM 재현용) ===
semantic_description: |
  슬라이드 상단에 왼쪽 정렬된 큰 제목(48px, bold)이 있습니다.
  그 아래 2~6개의 동일한 크기의 카드가 가로로 균등 배치됩니다.
  각 카드는 둥근 모서리(16px)와 그림자가 있는 흰색 배경입니다.

# === 검색 키워드 ===
match_keywords: [그리드, 카드, 아이콘, 서비스, 동국]
```

---

## 부록 E: 폰트 처리 로직

### E.1 폰트 Fallback 매핑

```yaml
font_fallback:
  Pretendard: ["SUIT", "Noto Sans KR", "맑은 고딕", "sans-serif"]
  "Noto Sans KR": ["맑은 고딕", "Apple SD Gothic Neo", "sans-serif"]
  "나눔스퀘어Neo": ["NanumSquare", "맑은 고딕", "sans-serif"]
  default_korean: ["맑은 고딕", "Apple SD Gothic Neo", "sans-serif"]
  default_english: ["Arial", "Helvetica", "sans-serif"]
```

### E.2 삭제/업데이트 처리 로직

```python
# 문서 삭제: source_document 기준
to_delete = [t for t in registry.templates 
             if t.source_document == "tipgreen"]

# 파일 재등록: source_file 기준
to_delete = [t for t in registry.templates 
             if t.source_file == "깔끔이_팁그린.pptx"]
```

---

## 부록 F: 오브젝트 스키마 (objects/*/metadata.yaml)

```yaml
id: cycle-6segment
category: diagram
name: "6단계 순환도"
description: "6개 단계가 순환하는 원형 다이어그램"
text_overlays:
  - id: "center"
    position: { x: 50%, y: 50% }
    text: "핵심 가치"
  - id: "segment1"
    position: { x: 50%, y: 15% }
    text: "1단계"
keywords: [순환, 사이클, 프로세스, 6단계]
```

---

## 부록 G: 영역 감지 코드

### G.1 Title/Footer 판별 (python-pptx)

```python
def is_title_shape(shape, slide_height):
    """타이틀 영역 판별"""
    if shape.is_placeholder:
        if shape.placeholder_format.type in [
            PP_PLACEHOLDER.TITLE, 
            PP_PLACEHOLDER.CENTER_TITLE,
            PP_PLACEHOLDER.SUBTITLE
        ]:
            return True
    if 'title' in shape.name.lower():
        return True
    return False

def is_footer_shape(shape, slide_height):
    """푸터 영역 판별"""
    if shape.is_placeholder:
        if shape.placeholder_format.type in [
            PP_PLACEHOLDER.FOOTER, 
            PP_PLACEHOLDER.SLIDE_NUMBER
        ]:
            return True
    # 위치 기반 (하단 10%)
    if shape.top > slide_height * 0.90:
        return True
    return False

def detect_content_zone(shapes, slide_height):
    """콘텐츠 영역 경계 계산"""
    title_shapes = [s for s in shapes if is_title_shape(s, slide_height)]
    if title_shapes:
        title_bottom = max(s.top + s.height for s in title_shapes)
        content_top = title_bottom + (slide_height * 0.02)
    else:
        content_top = slide_height * 0.20

    footer_shapes = [s for s in shapes if is_footer_shape(s, slide_height)]
    if footer_shapes:
        footer_top = min(s.top for s in footer_shapes)
        content_bottom = footer_top - (slide_height * 0.02)
    else:
        content_bottom = slide_height * 0.92

    return content_top, content_bottom
```

### G.2 콘텐츠 영역 필터링

```python
# content_only 모드에서 도형 필터링
content_top, content_bottom = detect_content_zone(slide.shapes, slide_height)

for shape in slide.shapes:
    centroid_y = shape.top + (shape.height / 2)
    if content_top <= centroid_y <= content_bottom:
        # 콘텐츠 영역 내 도형만 추출
        extract_shape(shape)
```

---

## 부록 H: 플레이스홀더 처리 로직

### H.1 LLM 판단 결과 적용

```python
# LLM 판단 결과를 3가지 포맷 모두에 적용
for ph in llm_result["placeholders"]:
    yaml_slots.append(ph)  # YAML에 슬롯 정의 추가
    html = html.replace(original, f"{{{{{ph.id}}}}}")  # HTML 치환
    ooxml = ooxml.replace(original, f"{{{{{ph.id}}}}}")  # OOXML 치환
```

### H.2 LLM 입출력 예시

**입력 (스크립트가 제공):**
```
텍스트박스 그룹 후보:
1. (x:10%, y:30%, font:24px bold) "WMS 시스템"
2. (x:10%, y:38%, font:16px) "실시간 재고 관리"
3. (x:10%, y:46%, font:16px) "AI 기반 예측"
4. (x:10%, y:54%, font:16px) "자동 발주 시스템"
```

**출력 (LLM 판단):**
```json
{
  "placeholders": [
    { "id": "title", "type": "text", "shapes": [1] },
    { "id": "items", "type": "array", "shapes": [2,3,4],
      "item_schema": { "text": "string" }
    }
  ]
}
```
