# 자동 Git Commit (Lite)

> `/wf:*` 명령어 실행 후 자동 커밋

---

## 커밋 시점

| 명령어 | 커밋 대상 |
|--------|----------|
| `start` | `010-*.md`, `wbs.yaml` |
| `ui` | `011-ui-design.md`, `ui-assets/` |
| `draft` | `020-*.md`, `025-*.md`, `026-*.md`, `wbs.yaml` |
| `build` | 소스 코드, `030-*.md`, `wbs.yaml` |
| `test` | `070-*.md`, `test-results/` |
| `audit` | `021-*.md`, `031-*.md` |
| `patch` | 수정된 소스 코드 |
| `verify` | `070-integration-test.md`, `wbs.yaml` |
| `done` | `080-manual.md`, `wbs.yaml` |
| `fix` | 수정된 소스 코드, `wbs.yaml` |

---

## 커밋 메시지 형식

```
[{command}] {Task-ID}: {summary}

- {변경 내용}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 실행 절차

1. `git status --short` → 변경 파일 확인
2. 변경 있으면 → `git add` → `git commit`
3. 결과 출력: `📦 Git Commit: {hash} | {message} | {파일수}개`

---

## 스킵 조건

| 조건 | 동작 |
|------|------|
| 변경 파일 없음 | 스킵 |
| git 저장소 아님 | 경고 후 스킵 |
| 커밋 실패 | 에러 출력, 명령어는 성공 |

---

<!--
wf-auto-commit-lite.md
Version: 1.0
-->
