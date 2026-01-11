# ppt-extract P1 구현 계획

> 4가지 항목: content-create, LLM 통합, object_extractor 완성, 스킬 연결 검증

---

## 1. content-create (라이브러리 기반 콘텐츠 생성)

### 목적
추출할 원본 없이 Chart.js, Mermaid 등 라이브러리로 콘텐츠 템플릿 동적 생성

### 기존 템플릿 분석 (gantt-yearly)
```yaml
render_method: library  # 스크린샷 → 이미지 삽입
has_ooxml: false        # 편집 불가
schema: { ... }         # 데이터 스키마
example: { ... }        # 예시 데이터
```

### 구현 사항

#### 1.1 CLI 서브커맨드 추가
**파일**: `ppt_extract.py`
```python
# content-create 서브커맨드
create_parser = subparsers.add_parser('content-create', ...)
create_parser.add_argument('--type', choices=['chart', 'diagram', 'gantt', 'icon'])
create_parser.add_argument('--library', choices=['chartjs', 'mermaid', 'apexcharts', 'lucide'])
create_parser.add_argument('--name', required=True)
create_parser.add_argument('--category', default='body')
```

#### 1.2 콘텐츠 생성기 스크립트
**파일**: `scripts/content_creator.py`

```python
class ContentCreator:
    """라이브러리 기반 콘텐츠 템플릿 생성."""

    LIBRARY_TEMPLATES = {
        'chartjs': {
            'bar': 'templates/chartjs-bar.html',
            'pie': 'templates/chartjs-pie.html',
            'line': 'templates/chartjs-line.html',
        },
        'mermaid': {
            'flowchart': 'templates/mermaid-flow.html',
            'sequence': 'templates/mermaid-sequence.html',
        },
        'apexcharts': {
            'dashboard': 'templates/apex-dashboard.html',
        }
    }

    def create(self, library: str, template_type: str, name: str):
        # 1. 기본 템플릿 로드
        # 2. schema + example 생성
        # 3. template.yaml, template.html 저장
        # 4. registry 업데이트
```

#### 1.3 워크플로우 문서
**파일**: `workflows/content-create.md`

```markdown
# content-create 워크플로우

## 트리거
- "Chart.js로 막대차트 템플릿 만들어줘"
- "Mermaid 플로우차트 템플릿 추가해줘"

## 실행
python ppt_extract.py content-create --library chartjs --type bar --name sales-chart

## 출력
templates/contents/{category}/{name}/
├── template.yaml   # schema + example
├── template.html   # Handlebars + CDN
└── thumbnail.png   # 미리보기 (선택)
```

#### 1.4 라이브러리 템플릿 기본 파일
**위치**: `.claude/skills/ppt-extract/templates/`

| 라이브러리 | 타입 | 파일 |
|-----------|------|------|
| Chart.js | bar, pie, line | chartjs-{type}.html |
| Mermaid | flowchart, sequence | mermaid-{type}.html |
| ApexCharts | dashboard | apex-dashboard.html |
| Lucide | icons | lucide-icons.html |

---

## 2. LLM 통합

### 현재 상태
- `_classify_slots_llm()`: `input()` 기반 수동 입력
- `classify_layouts_with_llm()`: `input()` 기반 수동 입력

### 목표
Claude CLI 호출로 자동 분류

### 구현 사항

#### 2.1 LLM 인터페이스 모듈
**파일**: `shared/llm_interface.py`

```python
import subprocess
import json

class ClaudeLLM:
    """Claude CLI 호출 인터페이스."""

    def classify_slots(self, shapes_info: List[Dict]) -> Dict:
        """도형 정보로 슬롯 분류 요청."""
        prompt = self._build_slot_prompt(shapes_info)
        result = self._call_claude(prompt)
        return json.loads(result)

    def classify_layouts(self, layouts_info: List[Dict]) -> Dict:
        """레이아웃 정보로 분류 요청."""
        prompt = self._build_layout_prompt(layouts_info)
        result = self._call_claude(prompt)
        return json.loads(result)

    def _call_claude(self, prompt: str) -> str:
        """Claude CLI 호출."""
        # 옵션 1: subprocess로 claude 호출
        # 옵션 2: Anthropic API 직접 호출 (API 키 필요)
        pass
```

#### 2.2 content_extractor.py 수정
```python
def _classify_slots_llm(self, shapes: List[ShapeInfo]) -> List[SlotInfo]:
    if self.use_llm:
        from shared.llm_interface import ClaudeLLM
        llm = ClaudeLLM()
        shapes_info = [self._shape_to_dict(s) for s in shapes]
        result = llm.classify_slots(shapes_info)
        return self._parse_slot_json(result, shapes)

    # 폴백: 규칙 기반
    return self._classify_slots_auto(shapes)
```

#### 2.3 CLI 옵션 추가
```python
content_parser.add_argument('--llm', action='store_true', help='LLM 기반 분류 사용')
```

### 주의사항
- API 키 관리: 환경변수 `ANTHROPIC_API_KEY`
- 폴백: LLM 실패 시 규칙 기반 자동 분류
- 비용 고려: 필요 시에만 LLM 호출

---

## 3. object_extractor 완성

### 현재 상태
- `object_detector.py` ✅ 완전 구현 (5가지 감지 조건)
- `object_extractor.py` ⚠️ 기본 구조만 있음
- content_extractor와 통합: ⚠️ 호출은 있으나 테스트 미완

### 구현 사항

#### 3.1 추출 로직 검증
```python
def extract(self, pptx_path, slide_index, candidate, object_id=None):
    # 1. 오브젝트 이미지 캡처 ← 검증 필요
    object_png = self._capture_object_image(...)

    # 2. 텍스트 오버레이 추출 ← 검증 필요
    text_overlays = self._extract_text_overlays(...)

    # 3. 메타데이터 생성 ← 구현됨
    # 4. 썸네일 생성 ← 구현됨
```

#### 3.2 테스트 케이스
- [ ] 5개 이상 도형 그룹 추출
- [ ] 원형/방사형 배치 추출
- [ ] 커넥터 포함 플로우차트 추출
- [ ] 차트 오브젝트 추출

#### 3.3 출력 검증
```
templates/objects/{category}/{object_id}/
├── object.png      # 크롭된 이미지
├── metadata.yaml   # 메타데이터 + text_overlays
└── thumbnail.png   # 320x180
```

---

## 4. 전체 스킬 연결 검증

### 검증 항목

| 워크플로우 | CLI 명령 | 상태 |
|-----------|----------|------|
| document-extract | `ppt_extract.py document-extract input.pptx --group test` | ✅ 구현됨 |
| document-update | `ppt_extract.py document-update new.pptx --id test-doc` | ✅ 구현됨 |
| document-delete | `ppt_extract.py document-delete test-doc` | ✅ 구현됨 |
| style-extract | `ppt_extract.py style-extract image.png --name new-theme` | ✅ 구현됨 |
| content-extract | `ppt_extract.py content-extract input.pptx --slides 3,5` | ✅ 구현됨 |
| content-create | `ppt_extract.py content-create --library chartjs --type bar` | ❌ 미구현 |
| registry-rebuild | `ppt_extract.py registry-rebuild` | ✅ 구현됨 |

### 연결 테스트 순서
1. **document-extract** → templates/documents/ 생성 확인
2. **content-extract** → templates/contents/ 생성 확인 + object 자동 추출
3. **style-extract** → templates/themes/ 생성 확인
4. **registry-rebuild** → 모든 registry.yaml 업데이트 확인
5. **document-update** → 기존 문서 덮어쓰기 확인
6. **document-delete** → 문서 + 연관 콘텐츠 삭제 확인

### SKILL.md 링크 확인
```markdown
## 워크플로우 상세
- [document-extract.md](workflows/document-extract.md) ✅
- [document-update.md](workflows/document-update.md) ✅
- [document-delete.md](workflows/document-delete.md) ✅
- [style-extract.md](workflows/style-extract.md) ✅
- [content-extract.md](workflows/content-extract.md) ✅
- [content-create.md](workflows/content-create.md) ❌ 추가 필요
```

---

## 구현 순서

### Phase 1: content-create 기반 작업
1. `content_creator.py` 스크립트 생성
2. CLI 서브커맨드 추가
3. 기본 라이브러리 템플릿 (Chart.js bar/pie/line)
4. `workflows/content-create.md` 작성

### Phase 2: LLM 통합
1. `shared/llm_interface.py` 모듈 생성
2. content_extractor.py 수정
3. document_extractor.py 수정
4. CLI --llm 옵션 추가

### Phase 3: object_extractor 검증
1. 테스트 PPTX로 추출 테스트
2. 문제점 수정
3. content_extractor 통합 확인

### Phase 4: 스킬 연결 검증
1. 각 워크플로우 E2E 테스트
2. SKILL.md 업데이트
3. registry 무결성 확인

---

## 예상 파일 변경

### 신규 파일
- `scripts/content_creator.py`
- `shared/llm_interface.py`
- `workflows/content-create.md`
- `templates/chartjs-bar.html`
- `templates/chartjs-pie.html`
- `templates/chartjs-line.html`
- `templates/mermaid-flow.html`
- `templates/mermaid-sequence.html`

### 수정 파일
- `ppt_extract.py` - content-create 서브커맨드 추가
- `scripts/content_extractor.py` - LLM 통합
- `scripts/document_extractor.py` - LLM 통합
- `SKILL.md` - content-create 워크플로우 링크 추가
