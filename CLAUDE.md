# PPT Skills Suite - 프로젝트 컨텍스트

> 이 파일은 AI 어시스턴트가 프로젝트를 이해하는 데 사용됩니다.

## 개요

Claude Code 환경에서 **전문 디자이너 수준의 PPT**를 자동 생성하고 관리하는 통합 서비스.

**구조**: 2개 스킬 + 1 앱
- `ppt-extract` - 추출 (문서 양식, 테마, 콘텐츠, 오브젝트)
- `ppt-gen` - 생성 (5단계 파이프라인)
- `ppt-manager` - 관리 (Electron 앱, 미구현)

## 핵심 설계 원칙

### 템플릿 시스템
| 유형 | 저장 위치 | 설명 |
|------|----------|------|
| 문서 양식 | `templates/documents/` | 회사별 양식 (OOXML) |
| 테마 | `templates/themes/` | 색상, 폰트 정의 |
| 콘텐츠 | `templates/contents/` | 슬라이드 레이아웃 패턴 |
| 오브젝트 | `templates/objects/` | 복잡한 도형/다이어그램 |
| 에셋 | `templates/assets/` | 아이콘, 이미지 |

### 품질 옵션
| 옵션 | 포맷 | 재현율 | 테마 변경 |
|------|------|--------|----------|
| high | OOXML | 100% | ❌ |
| medium | HTML | 85~95% | ✅ |
| low | 시맨틱 | 70~85% | ✅ |

### HTML → PPTX 변환 규칙
- ✅ DOM 파싱 → 편집 가능한 도형
- ❌ 스크린샷 이미지 방식 금지
- ❌ 텍스트를 이미지로 변환 금지
- ⚠️ **예외**: 라이브러리 기반 차트 (스크린샷 허용)

### 콘텐츠 생성용 라이브러리 (content-create)

추출할 원본 없이 **동적 콘텐츠 템플릿 직접 생성**:

| 카테고리 | 라이브러리 | 용도 | CDN |
|---------|-----------|------|-----|
| **일정** | Frappe Gantt | 간트 차트 | `frappe-gantt/+esm` |
| **일정** | Pure CSS | 간트 (정적) | - |
| **차트** | Chart.js | 막대/선/파이 | `chart.js` |
| **차트** | ApexCharts | 대시보드 | `apexcharts` |
| **다이어그램** | Mermaid | 플로우/시퀀스 | `mermaid` |
| **아이콘** | Lucide | 라인 아이콘 | `lucide` |
| **일러스트** | unDraw | SVG 일러스트 | undraw.co |

**렌더링 방식**: `render_method: library` → HTML + 라이브러리 → 스크린샷 → 이미지 삽입
**제약**: 편집 불가, 수정 시 재생성 필요

**완료된 템플릿:**
- `templates/contents/schedule/gantt-yearly/` - 연간 간트 (Dark, Pure CSS)
- `templates/contents/schedule/gantt-01/` - 분기 간트 (Light, Pure CSS)

### 카테고리 확장 정책
- 초기 19개 카테고리 제공
- LLM이 새 카테고리를 자유롭게 추가 가능
- 폴더명: 영문 케밥케이스 (예: `team-intro`)

### 오브젝트 자동 추출
content-extract 중 LLM이 자동 감지:
- 도형 그룹 5개 이상
- 비선형 배치 (원형, 방사형)
- 커넥터 포함 (플로우차트)
- 수치 데이터 시각화 (차트)

## 주요 파일 참조

| 파일 | 설명 |
|------|------|
| [PRD_PPT_Skills_Suite.md](./PRD_PPT_Skills_Suite.md) | 전체 PRD 문서 |
| [PRD_PPT_Skills_Suite_Appendix.md](./PRD_PPT_Skills_Suite_Appendix.md) | 상세 스키마/코드 |
| `.claude/agents/ppt-designer.md` | PPT 디자이너 에이전트 정의 |

## 폴더 구조

```
ppt-gen/
├── templates/
│   ├── documents/{group}/{template}/
│   ├── themes/{theme_id}/
│   ├── contents/{category}/{template_id}/
│   ├── objects/{category}/{object_id}/
│   └── assets/icons/, images/
│
├── research/           # 조사 문서
├── .claude/agents/     # 에이전트 정의
└── PRD_*.md           # 요구사항 문서
```

## 세션 컨텍스트

PPT 생성 시 `output/session.yaml`에 진행 상태 저장:
- settings: Stage 1 설정 (문서 종류, 양식, 청중, 톤)
- slides[]: 슬라이드별 아웃라인, 템플릿 매칭, 평가 결과
- output: 최종 파일 경로


## 기타
- 채팅 중 내가 todo 항목으로 기록하라는 것은 idea.md 파일에 남겨줘