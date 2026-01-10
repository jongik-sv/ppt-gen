---
subagent:
  primary: requirements-analyst
  description: 요구사항 분석 및 기본설계 문서 생성
hierarchy-input: true
parallel-processing: true
---

# /wf:start - 워크플로우 시작 (Lite)

> **상태 전환**: `[  ] Todo` → `[dd] 상세설계`
> **적용 category**: `development`, `defect`, `infrastructure`
> **계층 입력**: WP/ACT/Task 단위 (WP/ACT 입력 시 하위 Task 병렬 처리)

## 사용법

```bash
/wf:start [PROJECT/]<WP-ID | ACT-ID | Task-ID>
```

| 예시 | 설명 |
|------|------|
| `/wf:start TSK-01-01` | Task 단위 처리 |
| `/wf:start ACT-01-01` | ACT 내 모든 Todo Task 병렬 |
| `/wf:start WP-01` | WP 내 모든 Todo Task 병렬 |
| `/wf:start orchay/TSK-01-01` | 프로젝트 명시 |

---

## 상태 전환 규칙

| category | 현재 | 다음 | 생성 문서 | 내부 호출 |
|----------|------|------|----------|----------|
| development | `[  ]` | `[dd]` | `010-design.md` | `/wf:design` |
| defect | `[  ]` | `[dd]` | `010-defect-analysis.md` | - |
| infrastructure | `[  ]` | `[dd]` | `010-tech-design.md` | - |

> **참고**: development 카테고리는 내부적으로 `/wf:design` 워크플로우를 호출합니다.

---

## 실행 과정

### 0단계: 사전 검증 ⭐

명령어 실행 전 상태 검증:

```bash
npx tsx .orchay/script/transition.ts {Task-ID} start -p {project} --start
```

| 결과 | 처리 |
|------|------|
| `canTransition: true` | 다음 단계 진행 |
| `canTransition: false` | 에러 출력 후 즉시 종료 |

**에러 출력:**
```
[ERROR] 현재 상태 [{currentStatus}]에서 'start' 명령어를 사용할 수 없습니다.
필요한 상태: [  ]
```

### 1. 계층 입력 처리

| 입력 | 처리 | 필터 |
|------|------|------|
| `TSK-XX-XX` | 단일 Task | `[  ]` |
| `ACT-XX-XX` | ACT 내 모든 Task 병렬 | `[  ]` |
| `WP-XX` | WP 내 모든 Task 병렬 | `[  ]` |

### 2. Task 정보 수집

```markdown
# WBS 예시
- [ ] **TSK-01-01-01**: Project CRUD 구현 `[development]`
  - Project 생성, 수정, 삭제 기능
  - Backend: /api/projects REST API
  - _요구사항: PRD 3.1.4_
```

**추출**: Task ID, Task명, category, PRD 참조, 구현 범위

### 3. PRD/TRD 내용 추출

1. **PRD 읽기**: `.orchay/projects/{project}/prd.md`
   - WBS PRD 참조 섹션 번호로 해당 내용 추출
   - 비즈니스 규칙, 사용자 시나리오, UI 요구사항

2. **TRD 참고**: `.orchay/projects/{project}/trd.md`
   - 기술 요구사항 (상세설계 단계 활용)

### 4. 범위 검증 (Scope Validation)

**범위 기준**: WBS Task 설명에 명시된 항목만

| 검증 | 확인 | 조치 |
|------|------|------|
| 누락 | Task 설명 항목 모두 포함? | 누락 추가 |
| 초과 | Task 설명에 없는 기능 포함? | 초과 제거 |
| 정합성 | PRD 내용과 일치? | PRD 기준 |

```
✅ 범위 내: WBS Task 설명에 직접 언급된 기능
❌ 범위 외: PRD 동일 섹션이지만 Task 설명에 없는 기능
```

### 5. 문서 생성

- Task 폴더: `.orchay/projects/{project}/tasks/{TSK-ID}/`
- 템플릿 참조: `.orchay/templates/010-*.md`

**category별 문서 구조**:

| category | 문서 | 주요 섹션 |
|----------|------|----------|
| development | `010-design.md` | 개요, 시나리오, 기능요구, 비즈니스규칙, 화면요구, 수용기준 |
| defect | `010-defect-analysis.md` | 현상, 재현방법, 원인분석, 수정방안 |
| infrastructure | `010-tech-design.md` | 목적, 현재상태, 목표상태, 구현계획 |

### 6. 상태 전환 (자동)

```bash
# {project}: 입력에서 파싱 (예: deployment/TSK-01-01 → deployment)
# 프로젝트 미명시 시 wf-common-lite.md 규칙에 따라 자동 결정
npx tsx .orchay/script/transition.ts {Task-ID} start -p {project}
```
- 성공: `{ "success": true, "newStatus": "dd" }`

---

## 출력 예시 (병렬 처리)

```
[wf:start] 워크플로우 시작 (병렬 처리)

입력: WP-01
대상 Task: 8개 ([  ] Todo 필터)

📦 병렬 처리:
├── [1/8] TSK-01-01-01 ✅ → [dd]
├── [2/8] TSK-01-01-02 ✅ → [dd]
...

📊 결과: 성공 8, 실패 0, 스킵 7

---
ORCHAY_DONE:{project}/WP-01:start:success
```

---

## 에러 케이스

| 에러 | 메시지 |
|------|--------|
| Task 없음 | `[ERROR] Task를 찾을 수 없습니다` |
| 잘못된 상태 | `[ERROR] Todo 상태가 아닙니다` |
| category 없음 | `[ERROR] Task category가 지정되지 않았습니다` |
| PRD 참조 없음 | `[WARN] PRD 참조를 찾을 수 없습니다` |

---

## 완료 신호

작업의 **모든 출력이 끝난 후 가장 마지막에** 다음 형식으로 출력:

**성공:**
```
ORCHAY_DONE:{project}/{task-id}:start:success
```

**실패:**
```
ORCHAY_DONE:{project}/{task-id}:start:error:{에러 요약}
```

> ⚠️ 이 출력은 orchay 스케줄러가 작업 완료를 감지하는 데 사용됩니다. 반드시 정확한 형식으로 출력하세요.

---

## 공통 모듈 참조

@.claude/includes/wf-common-lite.md
@.claude/includes/wf-conflict-resolution-lite.md
@.claude/includes/wf-auto-commit-lite.md

---

<!--
wf:start lite
Version: 1.1
-->
