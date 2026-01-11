# document-update 워크플로우

기존 문서 양식을 새 PPTX 파일로 업데이트.

## 트리거

- "양식 업데이트해줘"
- "동국시스템즈 양식을 v2로 업데이트해줘"
- "이 파일로 기존 양식 덮어써줘"

## 입력

- PPTX 파일 (새 버전)
- 기존 문서 ID 또는 source_file 자동 매칭

## 출력

- 기존 문서 양식 덮어쓰기
- 연관 콘텐츠 삭제 (선택)

## 프로세스

### 1. 기존 문서 검색

```bash
# registry.yaml에서 source_file 또는 ID로 검색
python ppt_extract.py document-update input.pptx --id dongkuk-standard
```

검색 방식:
- **파일명 매칭** (기본): 새 파일명 → registry의 source_file 비교
- **ID 지정**: `--id` 옵션으로 명시적 타겟팅

### 2. 연관 콘텐츠 감지

```
기존 문서: dongkuk-standard
    │
    ▼
연관 콘텐츠 검색:
├── contents/body/dongkuk-*      (3개)
├── contents/timeline/dongkuk-*  (2개)
└── contents/grid/dongkuk-*      (1개)

총 6개 콘텐츠가 이 문서를 참조합니다.
```

### 3. 삭제 확인 프롬프트

```
[시스템] 문서 업데이트 확인:

📁 대상 문서: dongkuk-standard
📄 연관 콘텐츠: 6개

⚠️ 업데이트 시 연관 콘텐츠와의 호환성이 깨질 수 있습니다.

1. 문서만 업데이트 (콘텐츠 유지)
2. 문서 + 연관 콘텐츠 모두 삭제 후 재추출
3. 취소

선택: _
```

### 4. 기존 콘텐츠 삭제

선택에 따라:
- 옵션 1: 문서 양식만 삭제
- 옵션 2: 문서 + 연관 콘텐츠 모두 삭제

### 5. 새 파일 추출

```bash
# document-extract 재실행
python ppt_extract.py document-extract input.pptx --group {기존그룹} --name {기존이름} --force
```

### 6. 레지스트리 업데이트

```bash
# registry.yaml 자동 갱신
python scripts/registry_manager.py
```

## 옵션

| 옵션 | 설명 |
|------|------|
| `--id <id>` | 업데이트할 문서 ID 지정 |
| `--force` | 확인 없이 덮어쓰기 |
| `--cascade` | 연관 콘텐츠도 함께 삭제 |
| `--keep-contents` | 콘텐츠는 유지 (기본) |
| `--new` | 기존 유지, 새 ID로 등록 |

## 사용 예시

```bash
# 파일명으로 자동 매칭
python ppt_extract.py document-update 동국시스템즈-문서양식_v2.pptx

# ID로 명시적 지정
python ppt_extract.py document-update new-template.pptx --id dongkuk-standard

# 연관 콘텐츠 함께 삭제
python ppt_extract.py document-update new-template.pptx --id dongkuk-standard --cascade

# 확인 없이 덮어쓰기
python ppt_extract.py document-update new-template.pptx --id dongkuk-standard --force
```
