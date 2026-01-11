# Template Management Workflow

등록된 템플릿 목록 조회, 삭제, 정리를 수행합니다.

## Triggers

- "템플릿 목록 보여줘"
- "동국 템플릿 상세 보여줘"
- "old-template 삭제해줘"
- "사용 안 하는 템플릿 정리해줘"

## List Templates

```
사용자: "템플릿 목록 보여줘"
```

1. `templates/registry.yaml` 읽기
2. 각 템플릿 정보 표시:
   - 이름, ID, 회사/데이터타입
   - 썸네일 이미지 (있는 경우)
   - 사용 횟수, 마지막 사용일
   - 상태 (active/archived)

## View Template Details

```
사용자: "동국 템플릿 상세 보여줘"
```

1. `templates/documents/dongkuk/config.yaml` 읽기 (테마)
2. `templates/documents/dongkuk/registry.yaml` 읽기 (양식 목록)
3. 표시:
   - 테마 정보 (색상, 폰트, 계열사)
   - 양식 목록 및 설명

## Delete Template

```
사용자: "old-template 삭제해줘"
```

1. **삭제 전 확인** (AskUserQuestion):
   - 템플릿 정보 표시
   - 사용 횟수 확인

2. 확인 후 삭제:
   - YAML 파일 삭제
   - 썸네일 삭제 (있는 경우)
   - `registry.yaml`에서 항목 제거

## Cleanup Templates

```
사용자: "사용 안 하는 템플릿 정리해줘"
```

1. `registry.yaml` 분석

2. 정리 대상 식별:
   - 30일 이상 미사용
   - 사용 횟수 0회
   - status: deprecated

3. 목록 제시 후 선택적 삭제

## Archive Templates

완전 삭제 대신 아카이브:

- `status: archived`로 변경
- 일반 목록에서 숨김
- "아카이브된 템플릿 보여줘"로 조회 가능
- 복원 가능: "old-template 복원해줘"

## Registry Structure

```yaml
# templates/registry.yaml (master registry)
documents:
  - group: dongkuk
    path: documents/dongkuk/registry.yaml
    last_used: 2026-01-06
    usage_count: 15

contents:
  - id: comparison1
    path: contents/templates/comparison1.yaml
    last_used: 2026-01-05
    usage_count: 8
    status: active

assets:
  - id: chart-line
    path: assets/icons/chart-line.svg
    usage_count: 3
```
