# 공통 모듈 (Lite)

> 워크플로우 실행에 필요한 핵심 정보만 포함

---

## 프로젝트 해결 규칙

### 입력 파싱
| 입력 형식 | 프로젝트 | Task ID |
|----------|----------|---------|
| `TSK-01-01` | 자동 해결/검색 | TSK-01-01 |
| `orchay/TSK-01-01` | orchay (명시) | TSK-01-01 |

### 해결 프로세스
1. **입력 파싱**: `/` 포함 여부 확인
   - 포함 → `{project}/{task-id}` 분리
   - 미포함 → Task ID만 추출

2. **프로젝트 수 확인**: `.orchay/projects/` 스캔

3. **프로젝트 1개**: 해당 프로젝트 자동 사용

4. **프로젝트 여러 개**:
   - **명시된 경우**: 해당 프로젝트 사용
   - **미명시**: 전체 검색 모드
     1. 모든 프로젝트의 `wbs.yaml` 검색
     2. Task ID가 존재하는 프로젝트 목록 수집
     3. **1개 발견**: 자동 선택
     4. **여러 개 발견**: 선택지 제시
     5. **0개 발견**: 에러

### 선택지 출력 형식
```
[INFO] Task '{task-id}'가 여러 프로젝트에 존재합니다:
  1. orchay - TSK-01-01: {task-title}
  2. orchay개선 - TSK-01-01: {task-title}

다음 형식으로 재실행: /wf:start {project}/{task-id}
```

### 에러 메시지
| 상황 | 메시지 |
|------|--------|
| Task ID 미발견 | `[ERROR] Task '{id}'를 찾을 수 없습니다` |
| 명시한 프로젝트 없음 | `[ERROR] 프로젝트 '{id}'를 찾을 수 없습니다` |
| 프로젝트에 Task 없음 | `[ERROR] 프로젝트 '{project}'에 Task '{id}'가 없습니다` |

---

## 경로 규칙

| 용도 | 경로 |
|------|------|
| WBS 파일 | `.orchay/projects/{project}/wbs.yaml` |
| Task 문서 | `.orchay/projects/{project}/tasks/{TSK-ID}/` |
| 템플릿 | `.orchay/templates/` |
| 프로젝트 설정 | `.orchay/projects/{project}/project.json` |

---

## ID 패턴

| 패턴 | 타입 | 예시 |
|------|------|------|
| `WP-XX` | Work Package | WP-01, WP-08 |
| `ACT-XX-XX` | Activity | ACT-01-01 |
| `TSK-XX-XX-XX` | Task (4단계) | TSK-01-01-01 |
| `TSK-XX-XX` | Task (3단계) | TSK-01-01 |

---

## 상태 코드

| 코드 | 의미 | Category | 칸반 |
|------|------|----------|------|
| `[  ]` | Todo | 공통 | Todo |
| `[bd]` | 기본설계 | development | Design |
| `[dd]` | 상세설계 | development, simple-dev | Detail |
| `[an]` | 분석 | defect | Detail |
| `[ds]` | 설계 | infrastructure | Detail |
| `[ap]` | 설계승인 | development | Approve |
| `[im]` | 구현 | dev/infra/simple-dev | Implement |
| `[fx]` | 수정 | defect | Implement |
| `[vf]` | 테스트 | dev/defect | Verify |
| `[xx]` | 완료 | 공통 | Done |

---

## 문서 번호 체계

| 번호 | 파일명 | 단계 |
|------|--------|------|
| 010 | `010-basic-design.md` | 기본설계 (development) |
| 010 | `010-design.md` | 통합설계 (simple-dev) |
| 011 | `011-ui-design.md` | 화면설계 |
| 020 | `020-detail-design.md` | 상세설계 |
| 021 | `021-design-review-{llm}-{n}.md` | 설계리뷰 |
| 025 | `025-traceability-matrix.md` | 추적성 매트릭스 |
| 026 | `026-test-specification.md` | 테스트 명세 |
| 030 | `030-implementation.md` | 구현 |
| 031 | `031-code-review-{llm}-{n}.md` | 코드리뷰 |
| 070 | `070-integration-test.md` | 통합테스트 |
| 080 | `080-manual.md` | 매뉴얼 |

---

## wbs.yaml 구조

```yaml
project:
  id: {project-id}
  name: {프로젝트명}
  status: active
workPackages:
  - id: WP-01
    title: {제목}
    status: planned
    priority: high
    tasks:
      - id: TSK-01-01
        title: {제목}
        category: development
        domain: frontend
        status: "[im]"
        priority: high
        assignee: "-"
        depends: [TSK-XX-XX]
        requirements:
          prdRef: PRD 섹션
          items:
            - 요구사항 1
            - 요구사항 2
          acceptance:
            - 수용 기준 1
```

---

## 상태 업데이트 형식

wbs.yaml에서 Task 상태 변경:
```yaml
status: "[코드]"
예: status: "[im]"
```

---

## Git 커밋 형식

```
[{command}] {Task-ID}: {summary}

- {변경 내용}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**명령어별 예시:**
| 명령어 | 메시지 |
|--------|--------|
| `/wf:start` | `[wf:start] TSK-01-01-01: 기본설계 완료` |
| `/wf:design` | `[wf:design] TSK-01-01: 통합설계 완료` |
| `/wf:draft` | `[wf:draft] TSK-01-01-01: 상세설계 완료` |
| `/wf:approve` | `[wf:approve] TSK-01-01-01: 설계승인 완료` |
| `/wf:build` | `[wf:build] TSK-01-01-01: 구현 완료` |
| `/wf:verify` | `[wf:verify] TSK-01-01-01: 통합테스트 완료` |
| `/wf:done` | `[wf:done] TSK-01-01-01: 작업 완료` |

---

## 리뷰 적용 완료 표시

적용 후 파일명 변경:
- `021-design-review-{llm}-{n}.md` → `021-design-review-{llm}-{n}(적용완료).md`
- `031-code-review-{llm}-{n}.md` → `031-code-review-{llm}-{n}(적용완료).md`

---

<!--
orchay - Workflow Common Module (Lite)
Version: 1.2
-->
