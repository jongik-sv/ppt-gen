# document-delete 워크플로우

문서 양식 및 연관 콘텐츠 삭제.

## 트리거

- "양식 지워줘"
- "동국시스템즈 양식을 삭제해줘"
- "이 문서 템플릿 제거해"

## 입력

- 문서 ID 또는 그룹명/이름

## 출력

- 삭제된 항목 목록

## 프로세스

### 1. 문서 검색

```bash
python ppt_extract.py document-delete dongkuk-standard
# 또는
python ppt_extract.py document-delete --group dongkuk --name "동국시스템즈-문서양식"
```

검색 우선순위:
1. 정확한 ID 매칭
2. group + name 조합
3. 이름 부분 매칭 (확인 필요)

### 2. 연관 콘텐츠 감지

```
검색된 문서: dongkuk-동국시스템즈-문서양식
    │
    ▼
연관 항목 스캔:
├── documents/dongkuk/동국시스템즈-문서양식/  (문서 양식)
├── contents/body/dongkuk-body-*              (5개)
├── contents/team/dongkuk-team-*              (3개)
└── thumbnails/...                            (8개)
```

### 3. 삭제 범위 계산

```
삭제 대상 요약:
┌─────────────────┬───────┐
│      항목       │ 개수  │
├─────────────────┼───────┤
│ 문서 양식       │   1   │
├─────────────────┼───────┤
│ 연관 콘텐츠     │   8   │
├─────────────────┼───────┤
│ 썸네일          │   9   │
├─────────────────┼───────┤
│ 총 파일         │  42   │
└─────────────────┴───────┘
```

### 4. 삭제 확인 프롬프트

```
[시스템] "동국시스템즈-문서양식" 삭제 확인:

📁 문서 양식: 1개
📄 연관 콘텐츠: 8개
🖼️ 썸네일: 9개

⚠️ 이 작업은 되돌릴 수 없습니다.

1. 전체 삭제 (문서 + 콘텐츠)
2. 문서 양식만 삭제 (콘텐츠 유지)
3. 취소

선택: _
```

### 5. 삭제 실행

```bash
# 전체 삭제
rm -rf templates/documents/dongkuk/동국시스템즈-문서양식/
rm -rf templates/contents/*/dongkuk-*

# 또는 문서만 삭제
rm -rf templates/documents/dongkuk/동국시스템즈-문서양식/
```

### 6. 레지스트리 업데이트

```bash
# registry.yaml 재빌드
python scripts/registry_manager.py
```

## 옵션

| 옵션 | 설명 |
|------|------|
| `--cascade` | 연관 콘텐츠 모두 삭제 |
| `--keep-contents` | 문서 양식만 삭제 (콘텐츠 유지) |
| `--force` | 확인 없이 삭제 |
| `--dry-run` | 삭제하지 않고 대상만 표시 |
| `--group <group>` | 그룹 지정 |
| `--name <name>` | 이름 지정 |

## 사용 예시

```bash
# ID로 삭제 (확인 프롬프트 표시)
python ppt_extract.py document-delete dongkuk-standard

# 미리보기 (실제 삭제 안함)
python ppt_extract.py document-delete dongkuk-standard --dry-run

# 연관 콘텐츠 포함 삭제
python ppt_extract.py document-delete dongkuk-standard --cascade

# 문서만 삭제 (콘텐츠 유지)
python ppt_extract.py document-delete dongkuk-standard --keep-contents

# 확인 없이 전체 삭제
python ppt_extract.py document-delete dongkuk-standard --cascade --force

# 그룹/이름으로 삭제
python ppt_extract.py document-delete --group dongkuk --name "동국시스템즈-문서양식"
```

## 삭제 규칙

### 연관 콘텐츠 판단 기준

1. **source_document 일치**: 콘텐츠의 `source_document` 필드가 문서 ID와 일치
2. **ID 접두사 매칭**: 콘텐츠 ID가 `{group}-` 접두사로 시작

### 삭제 순서

1. 썸네일 파일
2. 콘텐츠 폴더 (cascade 시)
3. 문서 양식 폴더
4. 레지스트리 업데이트

### 안전 장치

- `--dry-run`: 항상 먼저 실행 권장
- 확인 프롬프트: `--force` 없으면 항상 표시
- 삭제 로그: 삭제된 항목 출력
