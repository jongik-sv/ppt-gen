---
name: ppt-gen
description: |
  PPT 생성 스킬. 5단계 파이프라인으로 전문 디자이너 수준의 프레젠테이션 자동 생성.

  트리거:
  - 새 PPT 생성: "PPT 만들어줘", "프레젠테이션 만들어줘", "발표자료 만들어줘"
  - 템플릿 기반: "동국제강 양식으로 PPT 만들어줘"
  - 기존 PPT 수정: "이 PPT 수정해줘", "슬라이드 추가해줘"
  - PPT 분석: "PPT 분석해줘", "구조 알려줘"

  ppt-extract 스킬로 추출된 템플릿(templates/)을 활용하여 PPT 생성.
---

# ppt-gen 스킬

## 워크플로우

| 워크플로우 | 트리거 | 상세 |
|-----------|--------|------|
| `generate` | "PPT 만들어줘" | [workflows/generate.md](workflows/generate.md) |
| `template` | "동국제강 양식으로" | [workflows/template.md](workflows/template.md) |
| `ooxml` | "이 PPT 수정해줘" | [workflows/ooxml.md](workflows/ooxml.md) |
| `analysis` | "PPT 분석해줘" | [workflows/analysis.md](workflows/analysis.md) |

## 5단계 파이프라인 요약

```
Stage 1 [스크립트] → Stage 2 [LLM] → Stage 3 [하이브리드] → Stage 4 [LLM] → Stage 5 [스크립트]
설정 수집           아웃라인 생성     템플릿 매칭          콘텐츠+평가        PPTX 생성
```

| Stage | 방식 | 핵심 |
|-------|------|------|
| 1 | 스크립트 | 문서 종류, 양식, 청중, 품질 등 질문 |
| 2 | LLM | 슬라이드 구성, 제목, 핵심 포인트 |
| 3 | 하이브리드 | 스크립트 필터 → LLM 시맨틱 선택 |
| 4 | LLM | 콘텐츠 생성 → 렌더링 → 평가 루프 (최대 3회) |
| 5 | 스크립트 | HTML→PPTX 또는 OOXML 병합 |

## 품질 옵션

| 품질 | 포맷 | 평가 기준 |
|------|------|----------|
| high | OOXML | 콘텐츠 적합성만 (20점+/25점) |
| medium | HTML | 전체 (85점+/100점) |
| low | 시맨틱 | 전체 (85점+/100점) |

## 세션 관리

`working/{session_id}/session.yaml`에 상태 저장.

스키마: [references/session-schema.md](references/session-schema.md)

## 스크립트

| 스크립트 | Stage | 용도 |
|---------|-------|------|
| `questionnaire.py` | 1 | 대화형 질문 수집 |
| `template_filter.py` | 3 | 규칙 기반 템플릿 필터링 |
| `html_renderer.py` | 4 | Handlebars + 테마 주입 |
| `ooxml_renderer.py` | 4 | OOXML 플레이스홀더 치환 |
| `thumbnail.py` | 4 | 평가용 썸네일 생성 |
| `html2pptx.js` | 5 | HTML→PPTX 변환 |
| `pptx_merger.py` | 5 | 슬라이드 병합 + 양식 적용 |
| `session_manager.py` | 전체 | 세션 CRUD |

## 프롬프트

| 프롬프트 | Stage | 용도 |
|---------|-------|------|
| [stage2-outline.md](prompts/stage2-outline.md) | 2 | 아웃라인 생성 |
| [stage3-matching.md](prompts/stage3-matching.md) | 3 | 시맨틱 템플릿 선택 |
| [stage4-content.md](prompts/stage4-content.md) | 4 | 콘텐츠 데이터 생성 |
| [stage4-evaluation.md](prompts/stage4-evaluation.md) | 4 | 디자인 평가 |

## 템플릿 저장소

```
templates/
├── documents/{group}/{template}/  # 문서 양식
├── themes/{theme_id}/             # 테마
├── contents/{category}/{id}/      # 콘텐츠 템플릿
└── objects/{category}/{id}/       # 오브젝트
```

> 템플릿은 ppt-extract 스킬로 추출/관리

## 핵심 실행 순서 (medium 품질)

```
Stage 1-3: 설정 → 아웃라인 → 템플릿 매칭
    ↓
Stage 4: 슬라이드별로 html_renderer.py 호출 → HTML 파일 생성
         session.yaml에 attempts[].file 경로 저장
    ↓
Stage 5: pptx_merger.py가 HTML 파일들을 PPTX로 변환
```

**⚠️ 중요:** Stage 4에서 HTML 파일을 생성하지 않으면 Stage 5 실패!

## 의존성

- Playwright, python-pptx, PptxGenJS, LibreOffice, Handlebars

## 참조

- [references/design-guidelines.md](references/design-guidelines.md) - 디자인 평가 기준
- [references/session-schema.md](references/session-schema.md) - 세션 YAML 스키마
