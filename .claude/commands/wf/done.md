---
subagent:
  primary: requirements-analyst
  description: 완료 검증 및 매뉴얼 문서 생성
hierarchy-input: true
parallel-processing: true
---

# /wf:done - 작업 완료 (Lite)

> **상태 전환**: `[vf] 검증` → `[xx] 완료`
> **적용 category**: `development`, `defect`, `infrastructure`
> **계층 입력**: WP/ACT/Task 단위 (하위 Task 병렬 처리)

## 사용법

```bash
/wf:done [PROJECT/]<WP-ID | ACT-ID | Task-ID>
```

| 예시 | 설명 |
|------|------|
| `/wf:done TSK-01-01` | Task 단위 |
| `/wf:done ACT-01-01` | ACT 내 모든 `[vf]` Task 병렬 |
| `/wf:done WP-01` | WP 내 모든 Task 병렬 |

---

## 상태 전환 규칙

| category | 현재 상태 | 다음 상태 | 생성 문서 |
|----------|----------|----------|----------|
| development | `[vf]` 검증 | `[xx]` 완료 | `080-manual.md` |
| defect | `[vf]` 검증 | `[xx]` 완료 | - |
| infrastructure | `[vf]` 검증 | `[xx]` 완료 | - |

---

## 실행 과정

### 0단계: 사전 검증 ⭐

명령어 실행 전 상태 검증:

```bash
npx tsx .orchay/script/transition.ts {Task-ID} done -p {project} --start
```

| 결과 | 처리 |
|------|------|
| `canTransition: true` | 다음 단계 진행 |
| `canTransition: false` | 에러 출력 후 즉시 종료 |

**에러 출력:**
```
[ERROR] 현재 상태 [{currentStatus}]에서 'done' 명령어를 사용할 수 없습니다.
필요한 상태: [vf]
```

### 1단계: 완료 조건 검증

**development 체크리스트** (4단계 워크플로우):
- [ ] 설계 (`010-design.md`)
- [ ] 추적성 매트릭스 (`025-traceability-matrix.md`)
- [ ] 테스트 명세 (`026-test-specification.md`)
- [ ] 설계리뷰 (`021-design-review-*.md`) (선택)
- [ ] 설계승인 완료 (`[ap]` 상태 거침)
- [ ] 구현 (`030-implementation.md`)
- [ ] 코드리뷰 (`031-code-review-*.md`) (선택)
- [ ] 테스트 통과 (test-result: pass)

**defect 체크리스트**:
- [ ] 결함 분석 (`010-defect-analysis.md`)
- [ ] 구현 (`030-implementation.md`)
- [ ] 코드리뷰 (`031-code-review-*.md`)
- [ ] 테스트 결과 (`070-test-results.md`)

**infrastructure 체크리스트**:
- [ ] 설계 (`010-tech-design.md`, 선택)
- [ ] 구현 (`030-implementation.md`)
- [ ] 코드리뷰 (`031-code-review-*.md`)

### 2단계: 매뉴얼 생성 (development only)

```
080-manual.md 구조:
├── 1. 개요 (기능 소개, 대상 사용자)
├── 2. 시작하기 (사전 요구사항, 접근 방법)
├── 3. 사용 방법 (기본 사용법, 상세 기능)
├── 4. FAQ
├── 5. 문제 해결
└── 6. 참고 자료
```

### 3단계: 품질 메트릭 수집 ⭐

```
📊 품질 메트릭:
├── 설계리뷰 횟수: N회
├── 코드리뷰 횟수: N회
├── 테스트 커버리지: N%
└── 통합테스트 통과율: N%
```

### 4단계: 상태 전환

```bash
# {project}: 입력에서 파싱 (예: deployment/TSK-01-01 → deployment)
# 프로젝트 미명시 시 wf-common-lite.md 규칙에 따라 자동 결정
npx tsx .orchay/script/transition.ts {Task-ID} done -p {project}
```
- 성공: `{ "success": true, "newStatus": "xx" }`

### 5단계: 상위 계층 상태 갱신 ⭐

```
상위 계층 자동 업데이트:
├── ACT 내 모든 Task 완료 시 → ACT 상태 업데이트
└── WP 내 모든 ACT 완료 시 → WP 상태 업데이트
```

---

## 출력 예시

```
[wf:done] 작업 최종 완료

Task: TSK-01-01-01
Task명: Project CRUD 구현
Category: development

워크플로우 완료:
✅ [  ] Todo
✅ [dd] 상세설계
✅ [ap] 승인
✅ [im] 구현
✅ [vf] 검증
✅ [xx] 완료

📊 품질 메트릭:
├── 설계리뷰: 2회
├── 코드리뷰: 1회
├── 테스트 커버리지: 87%
└── 통합테스트 통과율: 100%

📄 생성: 080-manual.md

═══════════════════════════════════
Task TSK-01-01-01 완료
═══════════════════════════════════

---
ORCHAY_DONE:TSK-01-01-01:done:success
```

---

## 완료 보고서 요약 ⭐

```
═══════════════════════════════════════════════════════
              Task 완료 보고서
═══════════════════════════════════════════════════════

Task ID: [Task-ID]
Task명: [Task명]
Category: [category]

───────────────────────────────────────────────────────
                    산출물 목록
───────────────────────────────────────────────────────

| 문서 | 경로 |
|------|------|
| 설계 | 010-design.md |
| 추적성 매트릭스 | 025-traceability-matrix.md |
| 테스트 명세 | 026-test-specification.md |
| 설계리뷰 | 021-design-review-*.md |
| 구현 | 030-implementation.md |
| 코드리뷰 | 031-code-review-*.md |
| 통합테스트 | 070-integration-test.md |
| 매뉴얼 | 080-manual.md |

═══════════════════════════════════════════════════════
```

---

## 에러 케이스

| 에러 | 메시지 |
|------|--------|
| 잘못된 상태 | `[ERROR] 검증 상태가 아닙니다. /wf:verify 실행 필요` |
| 필수 문서 없음 | `[ERROR] 필수 문서가 없습니다: {파일명}` |
| 테스트 미완료 | `[ERROR] 테스트가 완료되지 않았습니다` |

---

## 완료 신호

작업의 **모든 출력이 끝난 후 가장 마지막에** 다음 형식으로 출력:

**성공:**
```
ORCHAY_DONE:{project}/{task-id}:done:success
```

**실패:**
```
ORCHAY_DONE:{project}/{task-id}:done:error:{에러 요약}
```

**예시:**
```
ORCHAY_DONE:orchay/TSK-01-01:done:success
ORCHAY_DONE:orchay/TSK-02-03:done:error:테스트 실패
```

> ⚠️ 이 출력은 orchay 스케줄러가 작업 완료를 감지하는 데 사용됩니다. 반드시 정확한 형식으로 출력하세요.

---

## 공통 모듈 참조

@.claude/includes/wf-common-lite.md
@.claude/includes/wf-auto-commit-lite.md

---

<!--
wf:done lite
Version: 1.1
-->
