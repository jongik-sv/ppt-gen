# ppt-extract 스킬 구현 TODO

> 생성일: 2026-01-11
> 상태: 계획 완료 → 구현 대기

## 현재 상태 분석

### 존재하는 것
- [x] PRD 문서 (PRD_PPT_Skills_Suite.md, Appendix)
- [x] 스킬 정의 (.claude/skills/ppt-extract/SKILL.md)
- [x] 워크플로우 문서 (workflows/*.md)
- [x] 샘플 PPTX 3개 (ppt-sample/)
- [x] 간트 템플릿 2개 (templates/contents/schedule/)

### 미구현
- [ ] 스크립트 7개 (scripts/)
- [ ] 저장 구조 (templates/documents/, themes/, objects/, assets/)
- [ ] 레지스트리 파일 (registry.yaml)

---

## 워크플로우별 구현 항목

### 1. document-extract (문서 양식 추출)
- [ ] 스크립트: slide-crawler.py (PPTX 파싱)
- [ ] 스크립트: template-analyzer.py (마스터/레이아웃 분석)
- [ ] 저장소: templates/documents/{group}/{template}/
- [ ] 출력: template.yaml, ooxml/, assets/

### 2. document-update (양식 업데이트)
- [ ] 기존 문서 감지 (source_file 매칭)
- [ ] 삭제 후 재등록 로직

### 3. document-delete (양식 삭제)
- [ ] 연관 콘텐츠 삭제 (--cascade)
- [ ] 확인 프롬프트

### 4. style-extract (테마 추출)
- [ ] 스크립트: style-extractor.py (색상/폰트 추출)
- [ ] 스크립트: image-vectorizer.py (이미지 색상 추출)
- [ ] 저장소: templates/themes/{theme_id}/
- [ ] 출력: theme.yaml

### 5. content-extract (콘텐츠 추출)
- [ ] 스크립트: content-analyzer.py (콘텐츠 영역 감지)
- [ ] LLM 플레이스홀더 판단 로직
- [ ] 3가지 포맷 동시 생성 (YAML, HTML, OOXML)
- [ ] 저장소: templates/contents/{category}/{id}/
- [ ] 출력: template.yaml, template.html, template.ooxml, thumbnail.png

### 6. content-create (라이브러리 기반 생성)
- [ ] 이미 간트 템플릿 존재 (참고용)
- [ ] 추가 라이브러리 템플릿 (Chart.js, Mermaid 등)

---

## 스크립트 구현 목록

| # | 스크립트 | 용도 | 우선순위 | 상태 |
|---|---------|------|---------|------|
| 1 | slide-crawler.py | PPTX 파싱, 도형/텍스트 추출 | P0 | ⬜ |
| 2 | content-analyzer.py | 콘텐츠 영역 감지, 플레이스홀더 | P0 | ⬜ |
| 3 | template-analyzer.py | 마스터/레이아웃 분석, 패턴 통합 | P0 | ⬜ |
| 4 | style-extractor.py | 색상 팔레트, 폰트 추출 | P1 | ⬜ |
| 5 | thumbnail.py | 썸네일 생성 | P1 | ⬜ |
| 6 | font-manager.py | 폰트 대체 매핑 | P2 | ⬜ |
| 7 | image-vectorizer.py | 이미지에서 색상/스타일 추출 | P2 | ⬜ |

---

## 공유 모듈

| 모듈 | 용도 | 상태 |
|------|------|------|
| shared/config.py | 경로 상수, 설정 | ⬜ |
| shared/xml_utils.py | OOXML 파싱 유틸리티 | ⬜ |
| shared/yaml_utils.py | YAML 읽기/쓰기 | ⬜ |
| shared/region_detector.py | 영역 감지 (title/footer/content) | ⬜ |

---

## 의존성

```
python-pptx>=0.6.21    # PPTX 파싱
PyYAML>=6.0            # YAML 처리
Pillow>=9.0            # 이미지 처리
```

선택적:
```
colorthief             # 색상 추출 (고품질)
vtracer                # 벡터화
easyocr                # OCR 텍스트 감지
opencv-python          # 이미지 처리
```

---

## 진행 기록

### 2026-01-11
- [ ] 구현 범위 확정 (사용자 확인)
- [ ] 계획 파일 작성
- [ ] 스크립트 구현 시작
