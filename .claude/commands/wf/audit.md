---
subagent:
  phases:
    - id: collect
      agent: backend-architect
      description: 구현 파일 수집 및 분석 대상 결정
    - id: quality-audit
      agent: refactoring-expert
      description: 복잡도, 중복, 네이밍, SOLID 검증
      parallel-with: [security-audit, performance-audit]
    - id: security-audit
      agent: security-engineer
      description: 인젝션, 인증, 암호화 취약점 검증
      parallel-with: [quality-audit, performance-audit]
    - id: performance-audit
      agent: performance-engineer
      description: 쿼리 최적화, 메모리, 캐싱 검증
      parallel-with: [quality-audit, security-audit]
    - id: report
      agent: refactoring-expert
      description: 코드 리뷰 결과 통합 및 문서 작성
      depends-on: [quality-audit, security-audit, performance-audit]
mcp-servers: [sequential-thinking, context7]
hierarchy-input: true
parallel-processing: true
---

# /wf:audit - 코드 리뷰 (Lite)

> **상태 변경 없음**: 반복 실행 가능
> **적용 category**: development, infrastructure
> **계층 입력**: WP/ACT/Task 단위 (하위 Task 병렬 처리)

## 사용법

```bash
/wf:audit [PROJECT/]<WP-ID | ACT-ID | Task-ID>
```

| 예시 | 설명 |
|------|------|
| `/wf:audit TSK-01-01` | Task 단위 |
| `/wf:audit ACT-01-01` | ACT 내 모든 `[im]` Task 병렬 |
| `/wf:audit WP-01` | WP 내 모든 Task 병렬 |

---

## 실행 플로우 (Phase 기반)

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: collect (backend-architect)                        │
│ - 구현 파일 수집, 030-implementation.md에서 파일 목록 추출   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Phase 2:        │ │ Phase 3:        │ │ Phase 4:        │
│ quality-audit   │ │ security-audit  │ │ performance-    │
│ (refactoring-   │ │ (security-      │ │ audit           │
│  expert)        │⇄│  engineer)      │⇄│ (performance-   │
│                 │ │                 │ │  engineer)      │
│ SOLID, 중복,   │ │ 인젝션, 인증,  │ │ 쿼리, 메모리,  │
│ 복잡도         │ │ 암호화         │ │ 캐싱           │
└─────────────────┘ └─────────────────┘ └─────────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 5: report (refactoring-expert)                        │
│ - 코드 리뷰 결과 통합 및 031-code-review-{llm}-{n}.md 작성   │
│ [depends-on: quality-audit, security-audit, performance]    │
└─────────────────────────────────────────────────────────────┘
```

---

## 생성 산출물

| 파일 | 내용 |
|------|------|
| `031-code-review-{llm}-{n}.md` | 코드 리뷰 결과 (3개 관점 통합) |

---

## 실행 과정

### 0단계: 사전 검증 ⭐

명령어 실행 전 상태 검증:

```bash
npx tsx .orchay/script/transition.ts {Task-ID} audit -p {project} --start
```

| 결과 | 처리 |
|------|------|
| `canTransition: true` | 다음 단계 진행 |
| `canTransition: false` | 에러 출력 후 즉시 종료 |

**에러 출력:**
```
[ERROR] 현재 상태 [{currentStatus}]에서 'audit' 액션을 실행할 수 없습니다.
필요한 상태: [im]
```

### 1. 구현 파일 수집

- `030-implementation.md`에서 파일 목록 추출
- 소스 코드 로드

### 2. 코드 분석

| 영역 | 검토 항목 |
|------|----------|
| 품질 | 복잡도, 중복, 네이밍, SOLID |
| 보안 | 인젝션, 인증, 암호화 |
| 성능 | 쿼리, 메모리, 캐싱 |
| 설계 | 패턴, 의존성, 아키텍처 |

### 3. 리뷰 결과 작성

- 지적사항 (심각도/우선순위)
- 개선 제안
- 코드 예시

---

## 심각도(Severity) 분류

| 심각도 | 설명 | 예시 |
|--------|------|------|
| **Critical** | 버그, 보안 취약점 | SQL Injection, NPE |
| **Major** | 성능, 아키텍처 이슈 | N+1 쿼리, 순환 의존 |
| **Minor** | 코드 스타일, 가독성 | 네이밍, 매직 넘버 |
| **Info** | 참고 사항 | 최신 패턴 제안 |

---

## 우선순위(Priority) 분류

| 우선순위 | 설명 |
|----------|------|
| **P1** | 즉시 수정 필수 (버그, 보안) |
| **P2** | 통합테스트 전 수정 |
| **P3** | 향후 개선 |

---

## 출력 예시

```
[wf:audit] 코드 리뷰

Task: TSK-01-01-01

📂 구현 파일 분석:
├── 030-implementation.md ✅
├── Backend: 5개 파일
└── Frontend: 3개 파일

🔍 분석 결과:
┌─────────┬─────────┬─────────┬──────┐
│ 영역    │ Critical│ Major   │ Minor│
├─────────┼─────────┼─────────┼──────┤
│ 품질    │ 0       │ 1       │ 2    │
│ 보안    │ 0       │ 0       │ 0    │
│ 성능    │ 0       │ 1       │ 0    │
│ 설계    │ 0       │ 0       │ 1    │
└─────────┴─────────┴─────────┴──────┘

📄 생성: 031-code-review-claude-1.md

---
ORCHAY_DONE:{project}/TSK-01-01-01:audit:success
```

---

## 에러 케이스

| 에러 | 메시지 |
|------|--------|
| 구현 문서 없음 | `[ERROR] 030-implementation.md가 없습니다` |
| 소스 파일 없음 | `[ERROR] 구현된 소스 파일이 없습니다` |

---

## 완료 신호

작업의 **모든 출력이 끝난 후 가장 마지막에** 다음 순서로 실행:

**1. execution 필드 제거:**
```bash
npx tsx .orchay/script/transition.ts {task-id} -p {project} --end
```

**2. 완료 신호 출력:**

**성공:**
```
ORCHAY_DONE:{project}/{task-id}:audit:success
```

**실패:**
```
ORCHAY_DONE:{project}/{task-id}:audit:error:{에러 요약}
```

> ⚠️ 이 출력은 orchay 스케줄러가 작업 완료를 감지하는 데 사용됩니다. 반드시 정확한 형식으로 출력하세요.

---

## 공통 모듈 참조

@.claude/includes/wf-common-lite.md

---

<!--
wf:audit lite
Version: 1.1
-->
