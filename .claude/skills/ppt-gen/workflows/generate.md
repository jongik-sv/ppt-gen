# PPT 생성 워크플로우

5단계 파이프라인으로 전문 디자이너 수준의 PPT 생성.

## 전체 흐름

```
Stage 1: 설정 수집 [스크립트]
    ↓
Stage 2: 아웃라인 생성 [LLM]
    ↓
Stage 3: 템플릿 매칭 [하이브리드]
    ↓
Stage 4: 콘텐츠 생성 + 평가 [LLM + 스크립트]
    ↓
Stage 5: 최종 PPTX 생성 [스크립트]
```

## Stage 1: 설정 수집

세션 생성 및 사용자 설정 수집.

```bash
python scripts/questionnaire.py --list-options
```

또는 대화형으로:
1. 문서 종류 (proposal, bizplan, report, lecture)
2. 문서 양식 (등록된 양식 또는 빈 슬라이드)
3. 슬라이드 크기 (16:9, 4:3, 16:10)
4. 청중 (executive, team, customer, investor, public)
5. 발표 시간 (5min, 10min, 20min, 30min+)
6. 톤 (formal, casual, academic, data-driven)
7. 품질 (high, medium, low)
8. 차트 렌더링 (native, library)

**결과**: `session.yaml` 생성

## Stage 2: 아웃라인 생성

사용자 요청을 슬라이드 구조로 변환.

**프롬프트**: `prompts/stage2-outline.md`

**입력**:
- 사용자 요청 (주제, 목적)
- session.yaml settings

**출력**: slides[].outline (design_intent 포함)
```yaml
slides:
  - index: 1
    type: cover
    outline:
      title: "제목"
      subtitle: "부제목"
      speaker_notes: "..."

  - index: 3
    type: content
    outline:
      title: "핵심 서비스 4가지"
      content_type: comparison
      design_intent:                    # ← 필수! 템플릿 매칭의 핵심
        visual_type: card-grid
        layout: equal-weight
        emphasis: title
        icon_needed: true
        description: |
          4개 서비스를 균등한 카드 형태로 배치.
          WMS, TMS 등 약어가 크게 보이도록 제목 강조.
      key_points:
        - "WMS: 창고 관리"
        - "TMS: 운송 관리"
      speaker_notes: "..."
```

**⚠️ Stage 2 완료 체크리스트:**
- [ ] 모든 content/chart 슬라이드에 `design_intent` 작성 완료
- [ ] `design_intent.description`에 시각화 의도 구체적으로 서술
- [ ] `session_manager.add_slide()` 호출하여 session.yaml 저장
- [ ] 슬라이드 status가 "outlined"로 변경 확인

## Stage 3: 템플릿 매칭

각 슬라이드에 최적 템플릿 선택. **design_intent를 최우선으로 고려.**

### 3-1. 규칙 기반 필터링
```bash
python scripts/template_filter.py \
  --outline '{"type": "content", "outline": {"content_type": "comparison", "design_intent": {"visual_type": "card-grid"}, "key_points": ["A", "B", "C", "D"]}}' \
  --quality medium \
  --theme deep-green
```

**결과**:
- 후보 0개 → **LLM이 design_intent 기반으로 HTML 직접 생성**
- 후보 1개 → 바로 사용
- 후보 다수 → LLM 시맨틱 선택 (design_intent 기준)

### 3-2. 시맨틱 선택 (후보 다수)

**프롬프트**: `prompts/stage3-matching.md`

**매칭 기준:**
1. **design_intent 적합성 (40%)** ← 핵심 기준
2. 구조 적합성 (30%)
3. 콘텐츠 유형 (20%)
4. 키워드 매칭 (10%)

**출력**: slides[].template
```yaml
template:
  id: card-icon-4col-01
  match_score: 0.95
  match_reason: "design_intent의 아이콘 카드 + 제목 강조 요청에 가장 적합"
```

**⚠️ Stage 3 완료 체크리스트:**
- [ ] 모든 슬라이드에 template 매칭 완료 (또는 action: generate)
- [ ] match_reason에 design_intent 기반 선택 이유 명시
- [ ] `session_manager.update_slide()` 호출하여 session.yaml 저장
- [ ] 슬라이드 status가 "matched"로 변경 확인

## Stage 4: 콘텐츠 생성 + 평가

**슬라이드별로 반복 실행.** 각 슬라이드마다 콘텐츠 생성 → 렌더링 → 평가 수행.

### 품질별 경로

| 품질 | 렌더링 | 출력 | 평가 기준 |
|------|--------|------|----------|
| high | OOXML | `.pptx` | 콘텐츠 25점 (20점+ 합격) |
| medium | HTML | `.html` + `.png` | 전체 100점 (85점+ 합격) |
| low | 시맨틱 HTML | `.html` + `.png` | 전체 100점 (85점+ 합격) |

### 4-1. 콘텐츠 데이터 생성

**프롬프트**: `prompts/stage4-content.md`

템플릿의 placeholders에 맞는 콘텐츠 데이터 생성:
```yaml
content:
  page_title: "핵심 서비스"
  cards:
    - number: "01"
      title: "WMS"
      description: "창고 관리 시스템..."
```

### 4-2. HTML 렌더링 (medium/low 품질)

**⚠️ 필수 단계 - 건너뛰면 Stage 5 PPTX 생성 실패!**

**슬라이드별 반복 실행:**

```python
for slide in slides:
    # 1. 템플릿 경로 결정
    if slide["type"] in ["cover", "closing"]:
        category = "cover"
    else:
        category = slide["template"]["category"]

    template_id = slide["template"]["id"]
    template_path = f"templates/contents/{category}/{template_id}/template.html"

    # 2. HTML 렌더링 실행
    output_html = f"output/slide-{slide['index']:02d}.html"

    # python .claude/skills/ppt-gen/scripts/html_renderer.py 호출
```

**실행 명령:**
```bash
python .claude/skills/ppt-gen/scripts/html_renderer.py \
  templates/contents/{category}/{template_id}/template.html \
  --content '{콘텐츠 JSON}' \
  --theme deep-green \
  --output output/slide-{index:02d}.html \
  --screenshot
```

**출력 파일 (반드시 생성됨):**
- `output/slide-01.html` - 렌더링된 HTML (Stage 5에서 PPTX 변환용)
- `output/slide-01.png` - 스크린샷 (평가용)

**session.yaml 업데이트 (필수):**
```yaml
attempts:
  - attempt: 1
    content: { cards: [...] }
    file: "output/slide-01.html"       # ← Stage 5에서 사용
    screenshot: "output/slide-01.png"  # ← 평가용
```

**Stage 5 연동:** `pptx_merger.py`가 `attempts[final_attempt-1].file` 경로에서 HTML 파일을 읽어 PPTX로 변환.

### 4-3. OOXML 렌더링 (high 품질)

```bash
python .claude/skills/ppt-gen/scripts/ooxml_renderer.py \
  templates/documents/style/master.pptx \
  --slide 3 \
  --content '{"page_title": "..."}' \
  --output output/slide-03.pptx

# 썸네일 생성 (평가용)
python .claude/skills/pptx/scripts/thumbnail.py output/slide-03.pptx output/slide-03 --cols 1
```

### 4-4. 디자인 평가

**프롬프트**: `prompts/stage4-evaluation.md`

스크린샷 이미지를 첨부하여 LLM 평가 요청.

**평가 루프 (슬라이드별 최대 3회):**
```
attempt 1: 콘텐츠 생성 → 렌더링 → 스크린샷 → 평가
    ↓ 불합격 (< 85점)
attempt 2: 피드백 반영 → 재생성 → 렌더링 → 평가
    ↓ 불합격
attempt 3: 피드백 반영 → 재생성 → 렌더링 → 평가
    ↓
3회 중 최고 점수 attempt 선택 → final_attempt
```

### 4-5. session.yaml 업데이트

```python
# 각 attempt 후
session_manager.add_attempt(session_id, slide_idx, {
    "attempt": attempt_num,
    "content": content_data,
    "file": "output/slide-02.html",
    "screenshot": "output/slide-02.png",
    "evaluation": {
        "scores": {...},
        "total": 87,
        "passed": True,
        "feedback": None
    }
})

# 평가 완료 후
session_manager.set_final_attempt(session_id, slide_idx, best_attempt)
session_manager.update_slide_status(session_id, slide_idx, "completed")
```

**출력**: slides[].attempts, slides[].final_attempt

## Stage 5: 최종 PPTX 생성

```bash
python scripts/pptx_merger.py session.yaml --output output/presentation.pptx
```

### 처리 흐름

1. **HTML 슬라이드** (medium/low):
   - html2pptx.js로 변환
   - 슬라이드 병합

2. **OOXML 슬라이드** (high):
   - PPTX 파일 병합

3. **문서 양식 적용** (선택):
   - 슬라이드 마스터
   - 헤더/푸터
   - 로고

**결과**: `output/presentation.pptx`

## 세션 상태 관리

각 Stage 완료 시 **즉시** session.yaml 업데이트 필수.

### 상태 흐름

```yaml
session:
  status: pending → configured → generating → completed

slides[]:
  status: pending → outlined → matched → generated → evaluating → completed
```

### 단계별 저장 지점

**Stage 1 완료:**
```python
session_manager.create(settings)  # 세션 생성
# session.status = "configured"
```

**Stage 2 완료 (슬라이드별):**
```python
session_manager.add_slide(session_id, {
    "index": idx,
    "type": slide_type,
    "status": "outlined",
    "outline": {
        "title": "...",
        "content_type": "timeline",  # 필수 (type=content/chart일 때)
        "design_intent": {           # 필수 (type=content/chart일 때)
            "visual_type": "timeline",
            "layout": "hierarchical",
            "emphasis": "data",
            "icon_needed": False,
            "description": "6개월 프로젝트 일정을 타임라인 형태로..."
        },
        "key_points": [...]
    }
})
```

**⚠️ design_intent 누락 시 Stage 3 매칭 품질 저하!**

**Stage 3 완료 (슬라이드별):**
```python
session_manager.update_slide(session_id, idx, {
    "status": "matched",
    "template": {
        "id": "card-4col-01",
        "category": "grid",
        "match_score": 0.92,
        "match_reason": "..."
    }
})
```

**Stage 4 시도마다:**
```python
session_manager.add_attempt(session_id, idx, {
    "attempt": attempt_num,
    "content": {...},
    "file": "output/slide-03.html",
    "evaluation": {
        "scores": {...},
        "total": 87,
        "passed": True
    }
})
session_manager.update_slide_status(session_id, idx, "evaluating")
```

**Stage 4 완료 (슬라이드별):**
```python
session_manager.set_final_attempt(session_id, idx, best_attempt_num)
session_manager.update_slide_status(session_id, idx, "completed")
```

**Stage 5 완료:**
```python
session_manager.set_output(session_id, "output/presentation.pptx")
session_manager.update_status(session_id, "completed")
```

### 중요

- 각 단계 완료 후 **즉시 저장** (마지막에 일괄 저장 ❌)
- 중간에 오류 발생 시 session.yaml에서 진행 상태 확인 가능
- 재시작 시 마지막 완료 단계부터 재개 가능

**세션 스키마**: `references/session-schema.md`
**디자인 기준**: `references/design-guidelines.md`
