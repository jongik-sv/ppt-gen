---
subagent:
  primary: refactoring-expert
  description: 설계 리뷰 지적사항 반영
mcp-servers: [sequential-thinking, context7]
hierarchy-input: true
parallel-processing: true
---

# /wf:apply - 설계 리뷰 반영 (Lite)

> **상태 변경 없음**: 반복 실행 가능
> **적용 category**: development only
> **계층 입력**: WP/ACT/Task 단위 (하위 Task 병렬 처리)

## 핵심 원칙 ⭐

- **맥락 기반 선택적 적용**: 무조건 적용 금지
- **P1-P2 집중 처리**: 필수 사항 우선 반영
- **판단 근거 명시**: 모든 적용/보류 결정에 사유 기록

---

## 사용법

```bash
/wf:apply [PROJECT/]<WP-ID | ACT-ID | Task-ID> [--review N]
```

| 예시 | 설명 |
|------|------|
| `/wf:apply TSK-01-01` | 최신 리뷰 기준 |
| `/wf:apply TSK-01-01 --review 2` | 특정 리뷰 회차 |
| `/wf:apply ACT-01-01` | ACT 내 모든 `[dd]` Task 병렬 |

---

## 실행 과정

### 0단계: 사전 검증 ⭐

명령어 실행 전 상태 검증:

```bash
npx tsx .orchay/script/transition.ts {Task-ID} apply -p {project} --start
```

| 결과 | 처리 |
|------|------|
| `canTransition: true` | 다음 단계 진행 |
| `canTransition: false` | 에러 출력 후 즉시 종료 |

**에러 출력:**
```
[ERROR] 현재 상태 [{currentStatus}]에서 'apply' 액션을 실행할 수 없습니다.
필요한 상태: [dd]
```

### 1. 리뷰 파일 선택

```
탐색 순서:
1. "(적용완료)" 표시 없는 최신 리뷰 문서 (기본)
2. --review 옵션 지정 시 해당 회차
3. "(적용완료)" 파일은 탐색에서 제외
```

### 2. 맥락 기반 적용 가능성 분석 ⭐

**각 이슈에 대해 검토**:

| 검토 항목 | 확인 질문 |
|----------|----------|
| 시스템 적합성 | 현재 아키텍처/기술스택과 호환? |
| Task 범위 적합성 | 해당 Task 요구사항 범위 내? |
| 실현 가능성 | 설계 수준에서 명세 가능? |

### 3. 적용 판단 결정

| 판단 | 조건 | 처리 |
|------|------|------|
| ✅ **적용** | 시스템&Task 적합, 실현 가능 | 그대로 반영 |
| 📝 **조정 적용** | 취지 유효, 현재 시스템에 맞춤 필요 | 수정하여 반영 |
| ⏸️ **보류** | 부적합, 범위 초과, 실현 어려움 | 미반영 (사유 기록) |

### 4. 우선순위별 처리 기준

| 우선순위 | 처리 기준 |
|----------|----------|
| 🔴 P1 | 필수 적용 (조정 가능하나 반드시 해결) |
| 🟠 P2 | 적용 권장 (적합성 체크 통과 시) |
| 🟡 P3 | 선별 적용 (효과 명확한 경우만) |
| ⚪ P4-P5 | 선택적 적용 (향후 고려 가능) |

### 5. 설계 문서 수정

**수정 대상**:
- `010-design.md` (주요 수정 대상)
- `025-traceability-matrix.md` (요구사항 매핑 변경 시)
- `026-test-specification.md` (테스트 관련 이슈 시)

### 6. 적용 완료 표시

- 리뷰 문서 끝에 적용 결과 섹션 추가
- 파일명 변경: `021-...(적용완료).md`

---

## 적용 vs 보류 예시

### ✅ 적용
- P1 보안 이슈 → 인증 강화 (시스템 적합 & 필수)
- P2 아키텍처 → API 일관성 개선 (범위 내 & 구현 가능)

### 📝 조정 적용
- Redis 캐싱 도입 → 인메모리 캐싱으로 조정 (현재 스택에 맞춤)
- GraphQL 전환 → REST API 최적화 (현재 스택 유지)

### ⏸️ 보류
- 마이크로서비스 전환 (범위 초과)
- 새 프레임워크 도입 (TRD 위반)

---

## 성공 기준

### 필수
- ✅ P1 100% 처리
- ✅ P2 80% 이상 처리
- ✅ 모든 이슈에 적용/보류 근거 명시
- ✅ 기본-상세설계 일관성 유지

### 금지
- ❌ 맹목적 전체 적용 (맥락 무시)
- ❌ 판단 근거 누락
- ❌ Task 범위 초과 변경
- ❌ TRD 기술 스택 위반

---

## 출력 예시

```
[wf:apply] 리뷰 반영

Task: TSK-01-01-01
리뷰 문서: 021-design-review-claude-2.md

📊 맥락 분석:
├── 시스템 적합: 5/5
├── Task 범위: 4/5
└── 실현 가능: 4/5

📋 적용 판단:
├── ✅ 적용: 3건
├── 📝 조정 적용: 1건
└── ⏸️ 보류: 1건 (범위 초과)

📄 수정된 문서:
├── 010-design.md
└── 021-...(적용완료).md

---
ORCHAY_DONE:{project}/TSK-01-01-01:apply:success
```

---

## 에러 케이스

| 에러 | 메시지 |
|------|--------|
| 리뷰 파일 없음 | `[ERROR] 설계 리뷰 파일이 없습니다` |
| 이미 적용됨 | `[WARN] 이미 적용 완료된 리뷰입니다` |
| 설계 문서 없음 | `[ERROR] 수정 대상 설계 문서가 없습니다` |
| 미적용 리뷰 없음 | `[WARN] 적용 가능한 리뷰가 없습니다` |

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
ORCHAY_DONE:{project}/{task-id}:apply:success
```

**실패:**
```
ORCHAY_DONE:{project}/{task-id}:apply:error:{에러 요약}
```

> ⚠️ 이 출력은 orchay 스케줄러가 작업 완료를 감지하는 데 사용됩니다. 반드시 정확한 형식으로 출력하세요.

---

## 공통 모듈 참조

@.claude/includes/wf-common-lite.md
@.claude/includes/wf-auto-commit-lite.md

---

<!--
wf:apply lite
Version: 1.1
-->
