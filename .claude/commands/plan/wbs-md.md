---
name: plan:wbs-md
description: "PRD를 이슈 계층 구조로 분할하여 WBS를 생성합니다. 프로젝트 규모에 따라 4단계/3단계 구조 선택. (Markdown 형식)"
category: planning
complexity: complex
wave-enabled: true
performance-profile: complex
auto-flags:
  - --seq
  - --token-efficient
mcp-servers: [sequential]
personas: [architect, analyzer, scribe]
---

# /plan:wbs-md - PRD 기반 WBS 생성 (Markdown)

> **PRD → WBS 자동 변환**: PRD 문서를 분석하여 계층적 WBS를 `wbs.md` 파일로 생성합니다.

## 트리거
- PRD 문서를 이슈 계층 구조로 분할이 필요한 경우
- 체계적인 WBS(Work Breakdown Structure) 생성이 필요한 경우
- Task category별 워크플로우 적용이 필요한 경우

## 사용법
```bash
/plan:wbs [PRD 파일 경로]
/plan:wbs [PRD 파일 경로] --scale [large|medium|small]

# 예시
/plan:wbs .orchay/projects/orchay/prd.md
/plan:wbs .orchay/projects/orchay/prd.md --scale large
```

## 핵심 특징
- **프로젝트 초기화 자동 감지**: 프로젝트 미존재 시 WP-00 자동 추가
- **프로젝트 규모 자동 산정**: 대규모/중간규모 자동 판별
- **규모별 계층 구조**: 4단계(대규모) / 3단계(중간/소규모)
- **Task category별 워크플로우**: development, defect, infrastructure 구분
- **워크플로우 상태 표시**: `[ ]`, `[dd]`, `[ap]`, `[im]`, `[xx]`
- **MECE 원칙**: 상호 배타적 + 전체 포괄 분할
- **일정 자동 계산**: category별 기간 추정 + 의존성 기반 일정 산출
- **PRD/TRD 컨텍스트 주입**: 요구사항, 인수조건, 기술스펙을 Task에 직접 포함
- **자기 완결적 Task**: Task만 보고 개발 착수 가능한 상세 정보 제공

---

## 계층 구조

```
Project (프로젝트) - 6~24개월
├── Work Package #1 (주요 기능 묶음) - 1~3개월
│   ├── Activity #1.1 (세부 활동) - 1~4주          ← 4단계만
│   │   ├── Task #1.1.1 (실제 작업) - 1일~1주
│   │   └── Task #1.1.2
│   └── Activity #1.2
│       └── Task #1.2.1
├── Work Package #2
│   └── Task #2.1 (Activity 생략 가능)             ← 3단계
└── Work Package #3
    └── Task #3.1
```

### 계층 타입

| 레벨 | 명칭 | 설명 | 기간 |
|------|------|------|------|
| Level 1 | **Project** | 전체 프로젝트 | 6~24개월 |
| Level 2 | **Work Package** | 주요 기능 단위의 작업 묶음 | 1~3개월 |
| Level 3 | **Activity** | 세부 활동 단위 (4단계에서만 사용) | 1~4주 |
| Level 4 | **Task** | 실제 수행 작업 단위 | 1일~1주 |

### Task category

| category | 설명 | 워크플로우 |
|----------|------|------------|
| `development` | 신규 기능 개발 | `[ ]` → `[dd]` → `[ap]` → `[im]` → `[xx]` |
| `defect` | 결함 수정 | `[ ]` → `[an]` → `[fx]` → `[vf]` → `[xx]` |
| `infrastructure` | 인프라/기술 작업 | `[ ]` → `[dd]?` → `[im]` → `[xx]` |

### Task domain (기술 영역)

| domain | 설명 | 대표 작업 |
|--------|------|----------|
| `frontend` | 클라이언트 UI/UX | Vue 컴포넌트, 페이지, 스타일링, 상태관리 |
| `backend` | 서버 비즈니스 로직 | API 엔드포인트, 서비스, 미들웨어 |
| `database` | 데이터 계층 | 스키마, 마이그레이션, 쿼리 최적화 |
| `infra` | 인프라/DevOps | 배포, CI/CD, 모니터링, 환경설정 |
| `fullstack` | 전체 스택 | E2E 기능, 통합 작업 |
| `docs` | 문서화 | API 문서, 사용자 가이드, README |
| `test` | 테스트 전용 | 단위/통합/E2E 테스트 작성 |

---

## 프로젝트 규모 산정

### 규모 판별 기준

| 기준 | 대규모 (4단계) | 중간/소규모 (3단계) |
|------|---------------|-------------------|
| **예상 기간** | 12개월+ | 12개월 미만 |
| **팀 규모** | 10명+ | 10명 미만 |
| **기능 영역 수** | 5개+ | 5개 미만 |
| **예상 Task 수** | 50개+ | 50개 미만 |

### 규모별 구조

**4단계 (대규모)**: `Project → WP → ACT → TSK`
```
## WP-01: Work Package Name
### ACT-01-01: Activity Name
#### TSK-01-01-01: Task Name
```

**3단계 (중간/소규모)**: `Project → WP → TSK`
```
## WP-01: Work Package Name
### TSK-01-01: Task Name
```

---

## 워크플로우 상태 기호

### 칸반 컬럼 매핑

| 칸반 컬럼 | 통합 상태 | 의미 |
|-----------|-----------|------|
| Todo | `[ ]` | 대기 |
| Design | `[dd]`, `[an]` | 설계/분석 |
| Approve | `[ap]` | 승인 |
| Implement | `[im]`, `[fx]` | 구현/수정 |
| Verify | `[vf]` | 검증 |
| Done | `[xx]` | 완료 |

### 카테고리별 세부 상태

| 기호 | 의미 | 사용 카테고리 |
|------|------|--------------|
| `[ ]` | Todo (대기) | 공통 |
| `[dd]` | 설계 | development, infrastructure |
| `[an]` | 분석 | defect |
| `[ap]` | 승인 | development |
| `[im]` | 구현 | development, infrastructure |
| `[fx]` | 수정 | defect |
| `[vf]` | 검증/테스트 | defect |
| `[xx]` | 완료 | 공통 |

---

## 자동 실행 플로우

### 0단계: 프로젝트 존재 확인 및 초기화

1. `.orchay/projects/{project}/` 폴더 존재 확인
2. **존재하지 않으면**:
   - WBS에 `WP-00: 프로젝트 초기화` Work Package 자동 추가
   - orchay-init 스킬 실행하여 프로젝트 구조 생성
3. **존재하면**: 기존 프로젝트 메타데이터 로드
4. **project-root 확인**:
   - 사용자에게 개발 폴더 경로 질문 (프로젝트 루트 기준 상대 경로)
   - 예시: `./` (루트), `orchay`, `lib/myapp`
   - orchay 스케줄러가 Worker에 Task 분배 시 해당 폴더에서 명령 실행

### 1단계: PRD 분석 및 프로젝트 규모 산정

1. PRD 파일 읽기 및 구조 분석
2. 프로젝트 규모 산정 (기능 영역 수, 예상 복잡도)
3. 규모 결정: 4단계 / 3단계
4. 사용자에게 규모 확인 (옵션)

### 2단계: PRD 섹션 → Work Package 매핑

| PRD 섹션 | Work Package 매핑 |
|----------|------------------|
| 핵심 기능 (Core Features) | WP-01 ~ WP-0N |
| 플랫폼 기능 (Platform Features) | WP-0N+1 ~ WP-0M |
| 지원 기능 (Support Features) | WP-0M+1 ~ WP-0K |

### 3단계: Work Package → Activity 분해 (4단계만)

- 사용자 관점 기능 단위
- 1~4주 규모 검증
- 독립적 테스트 가능 여부
- MECE 원칙 적용

### 4단계: Activity → Task 분해 및 category 분류

| category | 식별 기준 |
|----------|----------|
| **development** | 신규 기능 구현, 설계 필요 |
| **defect** | 결함 수정, 기존 코드 패치 |
| **infrastructure** | 리팩토링, 인프라, 성능개선 |

**Task 크기 검증**:
- 최소: 4시간
- 권장: 1~3일
- 최대: 1주 (초과 시 분할)

### 4.5단계: PRD/TRD 컨텍스트 주입 (신규)

각 Task에 PRD/TRD 문서에서 관련 정보를 추출하여 주입합니다.

**PRD → Task 매핑 규칙:**

| PRD 섹션 | Task 속성 | 추출 방법 |
|----------|----------|----------|
| 기능 요구사항 (FR-XXX) | prd-ref, requirements | 해당 기능 ID 및 상세 내용 |
| 인수 조건 (AC) | acceptance | 완료 판정 기준 목록 |
| 비기능 요구사항 (NFR) | constraints | 성능, 보안, 규격 제한 |
| 사용자 스토리 | note | 요약 또는 참조 |

**TRD → Task 매핑 규칙:**

| TRD 섹션 | Task 속성 | 추출 방법 |
|----------|----------|----------|
| 기술 스택 | tech-spec | 해당 Task에 사용할 기술 |
| API 설계 | api-spec | 엔드포인트, 스키마, 에러코드 |
| 데이터 모델 | data-model | 관련 엔티티, 필드, 관계 |
| UI/컴포넌트 설계 | ui-spec | 컴포넌트, 레이아웃, 스타일 |
| 성능 요구사항 | constraints | 응답시간, 처리량 제한 |

**상세도 레벨 결정:**

| Task 특성 | 권장 레벨 |
|----------|----------|
| 인프라/설정 작업 | minimal |
| 단순 CRUD | standard |
| 비즈니스 로직 | detailed |
| 핵심 기능/신규 개발 | full |

### 5단계: 일정 계산

**Task 기간 추정 (category별 기본값)**:

| category | 기본 기간 | 범위 |
|----------|----------|------|
| development | 10일 | 5~15일 |
| defect | 3일 | 2~5일 |
| infrastructure | 5일 | 2~10일 |

### 6단계: WBS 문서 생성

**생성 파일**: `.orchay/projects/{project}/wbs.md`

---

## 출력 형식

### wbs.md 파일 형식

```markdown
# WBS - {프로젝트명}

> version: 1.0
> depth: 4
> updated: {날짜}
> project-root: {개발 폴더 경로}

---

## WP-00: 프로젝트 초기화 (자동 생성 - 프로젝트 미존재 시)
- status: planned
- priority: critical
- schedule: {시작일} ~ {시작일}
- progress: 0%
- note: 프로젝트 폴더가 존재하지 않아 자동 추가됨

### TSK-00-01: orchay 프로젝트 구조 초기화
- category: infrastructure
- domain: infra
- status: [ ]
- priority: critical
- assignee: -
- schedule: {시작일} ~ {시작일}
- tags: setup, init
- depends: -
- note: orchay-init 스킬 실행 필요

---

## WP-01: {Work Package명}
- status: planned
- priority: high
- schedule: {시작일} ~ {종료일}
- progress: 0%

### ACT-01-01: {Activity명}
- status: todo
- schedule: {시작일} ~ {종료일}

#### TSK-01-01-01: 이메일/비밀번호 로그인 구현
- category: development
- domain: backend
- status: [ ]
- priority: high
- assignee: -
- schedule: {시작일} ~ {종료일}
- tags: api, auth, jwt
- depends: -

##### PRD 요구사항
- prd-ref: FR-AUTH-001
- requirements:
  - 이메일/비밀번호로 로그인
  - JWT 액세스 토큰 + 리프레시 토큰 발급
  - 로그인 실패 시 구체적 에러 메시지 반환
  - 5회 실패 시 계정 임시 잠금 (15분)
- acceptance:
  - 유효한 자격증명 → 토큰 발급 성공
  - 잘못된 이메일 → "존재하지 않는 계정" 에러
  - 잘못된 비밀번호 → "비밀번호 불일치" 에러
  - 잠긴 계정 → 남은 잠금 시간 표시
- constraints:
  - 비밀번호 최소 8자, 영문+숫자+특수문자
  - 응답시간 < 500ms
- test-criteria:
  - 정상 로그인 성공
  - 이메일 형식 검증 실패
  - 비밀번호 불일치 (1~4회)
  - 계정 잠금 트리거 (5회 실패)

##### 기술 스펙 (TRD)
- tech-spec:
  - Framework: Flutter + Riverpod
  - Auth: Supabase Auth
  - Token: JWT (RS256), Access 15분, Refresh 7일
- api-spec:
  - POST /api/v1/auth/login
  - Request: { email: string, password: string }
  - Response: { accessToken, refreshToken, expiresIn, user }
  - Errors: 401 Unauthorized, 423 Locked
- data-model:
  - User: id, email, passwordHash, failedAttempts, lockedUntil, createdAt

#### TSK-01-01-02: 로그인 화면 UI 구현
- category: development
- domain: frontend
- status: [ ]
- priority: medium
- assignee: -
- schedule: {시작일} ~ {종료일}
- tags: ui, form, validation
- depends: TSK-01-01-01

##### PRD 요구사항
- prd-ref: FR-AUTH-001, UI-AUTH-001
- requirements:
  - 이메일/비밀번호 입력 폼
  - 실시간 유효성 검사 피드백
  - 로딩 상태 표시
  - 에러 메시지 표시
- acceptance:
  - 이메일 형식 오류 시 즉시 피드백
  - 비밀번호 8자 미만 시 경고
  - 로그인 중 버튼 비활성화 + 스피너
  - 서버 에러 시 사용자 친화적 메시지
- constraints:
  - 모바일 최적화 (터치 영역 최소 44px)
  - 접근성: 스크린리더 호환

##### 기술 스펙 (TRD)
- tech-spec:
  - Widget: StatefulWidget + Riverpod
  - Validation: flutter_form_builder
  - State: AsyncValue 패턴
- ui-spec:
  - 컴포넌트: EmailField, PasswordField, SubmitButton
  - 레이아웃: Column, 중앙 정렬, 패딩 24px
  - 테마: 앱 기본 테마 적용

---

## WP-02: {Work Package명}
- status: planned
- priority: medium
- schedule: {시작일} ~ {종료일}
- progress: 0%

### TSK-02-01: {Task명} (3단계 예시 - ACT 생략, minimal 레벨)
- category: infrastructure
- domain: infra
- status: [ ]
- priority: high
- assignee: -
- note: 단순 인프라 작업은 minimal 레벨 사용
```

### ID 패턴

| 레벨 | 마크다운 | ID 패턴 | 예시 |
|------|----------|---------|------|
| WP (초기화) | `## WP-00:` | `WP-00` (예약) | `## WP-00: 프로젝트 초기화` |
| WP | `## WP-XX:` | `WP-{2자리}` | `## WP-01: 플랫폼 기반` |
| ACT (4단계) | `### ACT-XX-XX:` | `ACT-{WP}-{순번}` | `### ACT-01-01: 프로젝트 관리` |
| TSK (4단계) | `#### TSK-XX-XX-XX:` | `TSK-{WP}-{ACT}-{순번}` | `#### TSK-01-01-01: API 구현` |
| TSK (3단계) | `### TSK-XX-XX:` | `TSK-{WP}-{순번}` | `### TSK-02-01: 칸반 구현` |

### Task 속성

→ [wbs-task-spec.md](../../../.orchay/docs/wbs-task-spec.md) 참조

**요약:**
- **기본 속성**: category, domain, status, priority, assignee, schedule, tags, depends, blocked-by, note
- **PRD 연동 속성**: prd-ref, requirements, acceptance, constraints, test-criteria
- **TRD 연동 속성**: tech-spec, api-spec, data-model, ui-spec
- **상세도 레벨**: minimal, standard, detailed, full

---

## 고급 옵션

```bash
# 규모 강제 지정
/plan:wbs --scale large .orchay/projects/orchay/prd.md
/plan:wbs --scale medium .orchay/projects/myapp/prd.md

# 시작일 지정
/plan:wbs --start-date 2026-01-15 .orchay/projects/orchay/prd.md

# 개발 폴더 경로 지정 (project-root)
/plan:wbs --project-root orchay .orchay/projects/orchay/prd.md

# 규모 산정만 실행 (WBS 생성 없이)
/plan:wbs --estimate-only .orchay/projects/orchay/prd.md
```

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--scale [large\|medium]` | 프로젝트 규모 강제 지정 | 자동 산정 |
| `--start-date [YYYY-MM-DD]` | 프로젝트 시작일 지정 | 오늘 날짜 |
| `--project-root [PATH]` | 개발 폴더 경로 (프로젝트 루트 기준) | 사용자 입력 |
| `--estimate-only` | 규모 산정만 실행 | - |

---

## 산출물 위치

| 산출물 | 경로 |
|--------|------|
| WBS 문서 | `.orchay/projects/{project}/wbs.md` |

---

## 다음 단계

1. WBS 검토 및 수정
2. Task 우선순위 결정
3. `/wf:start` → 설계 시작
4. `/wf:approve` → 설계 승인
5. `/wf:build` → TDD 기반 구현
6. `/wf:done` → 작업 완료

---

## 성공 기준

- **요구사항 커버리지**: PRD 모든 기능이 Task로 분해됨
- **적정 규모**: 모든 Task가 1일~1주 범위 내
- **추적성**: 각 Task에 PRD 요구사항 ID (prd-ref) 연결
- **워크플로우 준비**: 모든 Task에 상태 기호 및 category 표시
- **컨텍스트 완전성**: 개발 Task는 requirements, acceptance, tech-spec 필수 포함
- **자기 완결성**: Task만 보고 개발 착수 가능한 수준의 상세도

---

## 참조 문서

- `orchay-prd.md`: 프로젝트 요구사항 문서
- `/wf:start`: 설계 시작 (Todo → Design)
- `/wf:approve`: 설계 승인 (Design → Approve)
- `/wf:build`: TDD 기반 구현 (Approve → Implement)
- `/wf:done`: 작업 완료 (Implement → Done)

<!--
orchay 프로젝트 - Command Documentation
Command: plan:wbs
Category: planning
Version: 2.0
-->
