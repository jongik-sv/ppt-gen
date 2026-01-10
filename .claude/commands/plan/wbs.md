---
name: plan:wbs
description: "PRD를 분석하여 YAML 형식의 WBS를 생성합니다. project.json 통합, 구조화된 요구사항 지원."
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

# /plan:wbs - PRD 기반 WBS YAML 생성

> **PRD → WBS YAML 자동 변환**: PRD 문서를 분석하여 계층적 WBS를 `wbs.yaml` 파일로 생성합니다.
> project.json과 wbs.md를 통합한 단일 파일로 관리합니다.

## 트리거

- PRD 문서를 YAML 형식의 WBS로 변환이 필요한 경우
- 기존 wbs.md + project.json을 통합 관리하고 싶은 경우
- 파싱 오류 없이 체계적인 WBS 관리가 필요한 경우

## 사용법

```bash
/plan:wbs-yaml [PRD 파일 경로]
/plan:wbs-yaml [PRD 파일 경로] --scale [large|medium|small]

# 예시
/plan:wbs-yaml .orchay/projects/orchay/prd.md
/plan:wbs-yaml .orchay/projects/myapp/prd.md --scale large
```

## 핵심 특징

- **통합 파일**: project.json + wbs.md → 단일 wbs.yaml
- **구조화된 요구사항**: requirements 블록 내 그룹핑 (prdRef, items, acceptance, techSpec 등)
- **동적 depth 지원**: 2단계(WP→TSK), 3단계(WP→TSK), 4단계(WP→ACT→TSK)
- **완료 타임스탬프**: completed 블록으로 상태 전이 기록
- **YAML 스키마 검증**: 파싱 오류 방지

---

## YAML 스키마

### 최상위 구조

```yaml
# wbs.yaml
project:
  id: my-project
  name: "프로젝트 이름"
  description: "프로젝트 설명"
  version: "0.1.0"
  status: active
  createdAt: "2026-01-01"
  updatedAt: "2026-01-01"
  scheduledStart: "2026-01-01" # 선택
  scheduledEnd: "2026-03-01" # 선택

wbs:
  version: "1.0"
  depth: 3 # 2, 3, or 4
  projectRoot: my-project # 선택
  strategy: "개발 전략 메모" # 선택

workPackages:
  - id: WP-01
    title: "Work Package 제목"
    # ...
```

### Task 구조 (그룹핑된 requirements)

```yaml
tasks:
  - id: TSK-01-01
    title: "Task 제목"
    category: development # .orchay/settings/workflows.json의 categories 참조
    domain: backend # backend, frontend, infra, test, fullstack, database
    status: "[  ]" # "[  ]", "[dd]", "[ap]", "[im]", "[vf]", "[xx]"
    priority: high # critical, high, medium, low
    assignee: "-"
    schedule: "2026-01-01 ~ 2026-01-05"
    tags: [api, auth]
    depends: [TSK-01-00]
    blockedBy: null # skipped 등
    testResult: null # none, pass, fail
    note: "메모"

    # 실행 상태 (워크플로우 실행 중일 때만 존재)
    execution:
      command: "build" # 실행 중인 명령어 (start, build, test 등)
      description: "Backend TDD 구현 중" # 현재 수행 중인 작업 설명
      startedAt: "2026-01-02T10:30:00" # 시작 시각 (ISO 8601)
      worker: 1 # Worker pane ID (선택)

    # 요구사항 그룹
    requirements:
      prdRef: "FR-AUTH-001" # PRD 참조
      items: # 요구사항 목록
        - "이메일/비밀번호 로그인 구현"
        - "JWT 토큰 발급"
      acceptance: # 인수 조건
        - "로그인 성공 시 토큰 반환"
        - "실패 시 에러 메시지"
      techSpec: # 기술 스펙
        - "Framework: Next.js"
        - "Auth: JWT RS256"
      apiSpec: # API 스펙
        - "POST /api/auth/login"
        - "Response: { accessToken, refreshToken }"
      dataModel: # 데이터 모델
        - "User: id, email, passwordHash"
      uiSpec: # UI 스펙
        - "LoginForm 컴포넌트"
        - "글래스모피즘 스타일"
      note: "참고사항"

    # 완료 타임스탬프 (자동 기록)
    completed:
      bd: "2026-01-02T10:00:00"
      dd: "2026-01-02T14:00:00"
      im: "2026-01-03T16:00:00"
      xx: "2026-01-03T18:00:00"
```

---

## 계층 구조

### 3단계 구조 (권장)

```yaml
workPackages:
  - id: WP-01
    title: "플랫폼 기반"
    tasks:
      - id: TSK-01-01
        title: "프로젝트 초기화"
```

### 4단계 구조 (대규모 프로젝트)

```yaml
workPackages:
  - id: WP-01
    title: "플랫폼 기반"
    activities:
      - id: ACT-01-01
        title: "프로젝트 설정"
        tasks:
          - id: TSK-01-01-01
            title: "환경 설정"
```

### 규모 판별 기준

| 기준             | 대규모 (4단계) | 중간/소규모 (3단계) |
| ---------------- | -------------- | ------------------- |
| **예상 기간**    | 12개월+        | 12개월 미만         |
| **팀 규모**      | 10명+          | 10명 미만           |
| **기능 영역 수** | 5개+           | 5개 미만            |
| **예상 Task 수** | 50개+          | 50개 미만           |

---

## 상태 코드

### 상태 코드 (workflows.json 기반)

| 상태 코드 | ID            | 한글     | 영문          | Phase     |
| --------- | ------------- | -------- | ------------- | --------- |
| `"[  ]"`  | todo          | 시작 전  | Todo          | todo      |
| `"[dd]"`  | detail-design | 상세설계 | Detail Design | design    |
| `"[ap]"`  | approve       | 승인     | Approve       | design    |
| `"[im]"`  | implement     | 구현     | Implement     | implement |
| `"[vf]"`  | verify        | 검증     | Verify        | implement |
| `"[xx]"`  | done          | 완료     | Done          | done      |

### 워크플로우 (모든 카테고리 동일)

```
[  ] → [dd] → [ap] → [im] → [vf] → [xx]
start  approve  build   verify   done
```

| Transition      | Command   | 설명      |
| --------------- | --------- | --------- |
| `[  ]` → `[dd]` | start     | 설계 시작 |
| `[dd]` → `[ap]` | approve   | 설계 승인 |
| `[ap]` → `[im]` | build/fix | 구현 시작 |
| `[im]` → `[vf]` | verify    | 검증 시작 |
| `[vf]` → `[xx]` | done      | 완료      |

### 실행 모드

| 모드      | 설명                            | 종료 상태 | 의존성      |
| --------- | ------------------------------- | --------- | ----------- |
| `design`  | 설계만 (start → review → apply) | `[dd]`    | 무시        |
| `quick`   | 단순 워크플로우                 | `[xx]`    | 구현 완료만 |
| `develop` | 전체 워크플로우                 | `[im]`    | 구현 완료만 |
| `force`   | 의존성 무시                     | `[xx]`    | 무시        |
| `test`    | 테스트 전용                     | -         | 무시        |

---

## 자동 실행 플로우

### 1단계: 프로젝트 확인

1. `.orchay/projects/{project}/` 폴더 존재 확인
2. 미존재 시 WP-00 (프로젝트 초기화) 자동 추가
3. 기존 project.json 읽어서 project 섹션 생성
4. **projectRoot 확인**: 개발 코드가 저장될 폴더 경로를 사용자에게 질문
   - 예: "프로젝트 코드를 어디에 생성할까요?"
   - 옵션 제시:
     1. `{cwd}/{project}/` (현재 작업 디렉토리 하위, **권장**)
     2. `{cwd}/../{project}/` (상위 디렉토리와 동일 레벨)
     3. 사용자 지정 경로
   - 기본값: `{cwd}/{project}/` (예: `orchay/table-order/`)
   - 선택된 경로를 wbs.yaml의 `wbs.projectRoot`에 기록

### 2단계: PRD 분석

1. PRD 파일 읽기 및 구조 분석
2. 프로젝트 규모 산정 (기능 영역 수, 예상 복잡도)
3. depth 결정 (3단계 / 4단계)

### 3단계: WBS 구조 생성

1. PRD 핵심 기능 → Work Package 매핑
2. Work Package → Activity 분해 (4단계만)
3. Activity/WP → Task 분해

### 4단계: 요구사항 그룹 생성

각 Task에 requirements 블록 생성:

- `prdRef`: PRD 요구사항 ID
- `items`: 요구사항 목록
- `acceptance`: 인수 조건
- `techSpec`: 기술 스펙 (TRD 참조)
- `apiSpec`: API 스펙
- `dataModel`: 데이터 모델
- `uiSpec`: UI 스펙

### 5단계: YAML 파일 생성

- 파일 경로: `.orchay/projects/{project}/wbs.yaml`

---

## 출력 형식 예시

```yaml
# wbs.yaml - orchay 프로젝트
project:
  id: orchay
  name: "orchay - WezTerm Task Scheduler"
  description: "WezTerm 기반 Task 스케줄러"
  version: "0.1.0"
  status: active
  createdAt: "2025-12-28"
  updatedAt: "2025-12-28"

wbs:
  version: "1.0"
  depth: 3
  projectRoot: orchay

workPackages:
  - id: WP-01
    title: "부트스트랩"
    status: planned
    priority: critical
    schedule: "2025-12-28 ~ 2026-01-03"
    tasks:
      - id: TSK-01-01
        title: "프로젝트 초기화"
        category: infrastructure
        domain: infra
        status: "[xx]"
        priority: critical
        schedule: "2025-12-28 ~ 2025-12-28"
        tags: [setup, init]
        depends: []
        requirements:
          prdRef: "TRD 배포구조"
          items:
            - "pyproject.toml 생성"
            - "패키지 구조 생성"
          acceptance:
            - "uv pip install 성공"
            - "python -m orchay 실행 가능"
          techSpec:
            - "Python >=3.10"
            - "Pydantic ^2.0"
```

---

## 고급 옵션

```bash
# 규모 강제 지정
/plan:wbs-yaml --scale large .orchay/projects/myapp/prd.md

# 시작일 지정
/plan:wbs-yaml --start-date 2026-02-01 .orchay/projects/myapp/prd.md

# 개발 폴더 경로 지정
/plan:wbs-yaml --project-root src/myapp .orchay/projects/myapp/prd.md

# 규모 산정만 (WBS 생성 없이)
/plan:wbs-yaml --estimate-only .orchay/projects/myapp/prd.md
```

| 옵션              | 설명                         | 기본값      |
| ----------------- | ---------------------------- | ----------- |
| `--scale`         | 프로젝트 규모 (large/medium) | 자동 산정   |
| `--start-date`    | 시작일 (YYYY-MM-DD)          | 오늘        |
| `--project-root`  | 개발 폴더 경로               | 사용자 입력 |
| `--estimate-only` | 규모 산정만                  | -           |

---

## 마이그레이션 (기존 wbs.md → wbs.yaml)

기존 마크다운 WBS를 YAML로 변환:

```bash
# 변환 스크립트 (Python)
python -m orchay.utils.migrate_wbs .orchay/projects/myapp/

# 결과
# - wbs.yaml 생성
# - wbs.md.bak 백업
# - project.json.bak 백업
```

---

## 산출물 위치

| 산출물   | 경로                                  |
| -------- | ------------------------------------- |
| WBS YAML | `.orchay/projects/{project}/wbs.yaml` |

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
- **추적성**: 각 Task에 prdRef 연결
- **구조화**: requirements 블록에 관련 정보 그룹핑
- **파싱 안정성**: YAML 스키마 준수로 파싱 오류 제거

---

## 참조 문서

- `/plan:wbs` - 마크다운 형식 WBS 생성
- `/wf:start` - 설계 시작
- `/wf:build` - TDD 기반 구현
- `wbs-yaml-schema.md` - YAML 스키마 상세

<!--
orchay 프로젝트 - Command Documentation
Command: plan:wbs-yaml
Category: planning
Version: 1.0
-->
