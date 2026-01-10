# Design Search Workflow

웹에서 PPT 디자인 레퍼런스를 검색하고 스타일을 추출합니다.

## Triggers

- "PPT 디자인 찾아줘"
- "미니멀한 스타일 레퍼런스 보여줘"
- "발표자료 디자인 검색해줘"

## Workflow

### 1. Design Search (WebSearch)

```
사용자: "미니멀한 테크 스타트업 PPT 디자인 찾아줘"
```

검색 쿼리 생성:
- "minimal tech startup presentation design"
- 영문 키워드가 결과 품질 향상

### 2. Recommended Sources

| 소스 | 특징 | 검색 예시 |
|------|------|----------|
| Pinterest | 다양한 스타일 | "presentation design inspiration" |
| Dribbble | 전문 디자이너 작품 | "pitch deck UI" |
| Behance | 완성도 높은 프로젝트 | "corporate presentation" |
| SlideShare | 실제 발표자료 | "startup pitch deck" |

### 3. Image Analysis

검색 결과에서:
1. 유망한 디자인 선별
2. **출처 URL 기록** (Pinterest, Dribbble, Behance 등)
3. LLM Vision으로 각 이미지 분석
4. 스타일 패턴 추출

### 4. Style Guide Proposal

3-5개 스타일 가이드 제시:
- 컬러 팔레트
- 레이아웃 패턴
- 타이포그래피 스타일

### 5. Apply (Optional)

사용자 선택 시:
- html2pptx 워크플로우에 스타일 적용
- 선택한 스타일로 PPT 생성

## Search Query Tips

| 스타일 | 영문 키워드 |
|--------|------------|
| 미니멀 | minimal, clean, simple |
| 전문적 | corporate, professional, business |
| 창의적 | creative, bold, colorful |
| 테크 | tech, modern, digital |
| 고급 | luxury, premium, elegant |
