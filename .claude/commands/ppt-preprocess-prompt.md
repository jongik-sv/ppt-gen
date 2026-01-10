## Professional PPTX Generation Architecture

- 사람이 직접 디자인한 듯한 고품질(Apple/Stripe 스타일)의 PPTX를 LLM이 생성하기 위한 기술적 요구사항과 아키텍처를 정의합니다.
- 사용자의 디자인 만족을 위해 최대한 고품질의 이미지와 시각적 요소를 사용합니다.
- AskUserQuestion 도구를 적극활용, --ultrathink 사용
- 기본 밝은색 테마

## workflow

### 1단계: PPT 콘텐츠 구조 생성 (LLM Phase)

#### 목적

- 사용자 입력(주제, 목적, 대상 청중)을 기반으로 슬라이드별 구조화된 콘텐츠 생성
- 각 슬라이드에 적합한 마스터 레이아웃 및 시각적 요소 유형 결정

#### 입력
- 프레젠테이션 주제/목적
- 대상 청중 (경영진, 기술팀, 고객 등)
- 원본 자료 (문서, 데이터, 기존 PPT 등)

#### 마스터 레이아웃 정의

| layout_id | 레이아웃명                    | 용도                       | 플레이스홀더                       |
| --------- | ----------------------------- | -------------------------- | ---------------------------------- |
| 1         | White_Big K 버전              | 표지 슬라이드              | title, subtitle                    |
| 2         | 간지 1                        | 목차/Contents              | toc_numbers, toc_titles, toc_pages |
| 3         | 내지 (Action title 사용)      | 본문 (Action Title + 불릿) | main_title, action_title, body     |
| 4         | 내지 (Action title, Body삭제) | 본문 (자유 콘텐츠)         | main_title, action_title           |
| 5         | 내지 (Action Title 미사용)    | 본문 (넓은 영역)           | main_title, body                   |

#### 레이아웃 선택 기준

| 콘텐츠 유형             | 권장 layout_id | 이유                                   |
| ----------------------- | -------------- | -------------------------------------- |
| 표지                    | 1              | 전용 표지 디자인, Big K 요소           |
| 목차                    | 2              | 3열 구조 (번호, 제목, 페이지)          |
| 개요/설명 (불릿 리스트) | 3              | Action Title로 핵심 메시지 + 상세 불릿 |
| 차트/표/다이어그램      | 4              | 자유 배치 영역 확보                    |
| 단순 정보 전달          | 5              | Action Title 없이 넓은 본문            |
| 비교/워크플로우         | 4              | 복잡한 시각 요소 배치                  |

#### 출력: 구조화된 JSON Schema

```json
{
  "presentation": {
    "title": "프레젠테이션 제목",
    "author": "작성자_OOOO팀",
    "date": "2025.12.24",
    "slides": [
      {
        "slide_number": 1,
        "layout_id": 1,
        "placeholders": {
          "title": "문서 제목",
          "subtitle": "부서명 I 날짜"
        }
      },
      {
        "slide_number": 2,
        "layout_id": 2,
        "placeholders": {
          "toc_items": [
            { "number": "01", "title": "프로젝트 개요", "pages": "03-05" },
            { "number": "02", "title": "현황 및 문제점", "pages": "06-08" }
          ]
        }
      },
      {
        "slide_number": 3,
        "layout_id": 3,
        "placeholders": {
          "main_title": "1. 프로젝트 개요",
          "action_title": "공조설비 고장신고부터 수리완료까지 전 과정을 디지털화하는 설비 정비 관리 시스템입니다.",
          "body": [
            { "level": 1, "text": "QR코드 기반 즉시 고장신고" },
            { "level": 2, "text": "현장에서 스캔만으로 빠른 신고" },
            { "level": 1, "text": "실시간 프로세스 추적" }
          ]
        }
      },
      {
        "slide_number": 4,
        "layout_id": 4,
        "placeholders": {
          "main_title": "2. 시스템 구성도",
          "action_title": "모바일 앱, 웹 관리자, 백엔드 서버 3개 컴포넌트로 구성됩니다."
        },
        "custom_elements": [
          {
            "type": "diagram",
            "diagram_type": "architecture",
            "data": {}
          }
        ]
      },
      {
        "slide_number": 5,
        "layout_id": 4,
        "placeholders": {
          "main_title": "3. 기대 효과",
          "action_title": "시스템 도입으로 수리 완료 시간 50% 단축, 신고 누락 제로화가 가능합니다."
        },
        "custom_elements": [
          {
            "type": "chart",
            "chart_type": "bar",
            "data": {
              "labels": ["수리시간", "누락률", "추적률"],
              "series": [
                { "name": "As-Is", "values": [8, 15, 40] },
                { "name": "To-Be", "values": [4, 0, 100] }
              ]
            }
          }
        ]
      }
    ]
  }
}
```

#### 슬라이드 유형별 레이아웃 매핑

| 슬라이드 유형    | layout_id | 권장 요소                                     |
| ---------------- | --------- | --------------------------------------------- |
| title (표지)     | 1         | 제목, 부제목                                  |
| toc (목차)       | 2         | 번호, 제목, 페이지                            |
| content (불릿)   | 3         | main_title, action_title, body                |
| chart            | 4         | main_title, action_title + 차트               |
| table            | 4         | main_title, action_title + 표                 |
| diagram/workflow | 4         | main_title, action_title + 다이어그램         |
| simple_content   | 5         | main_title, body (넓은 영역)                  |
| screen_gallery   | 4         | main_title, action_title + 화면 이미지 갤러리 |

### 이미지 첨부 (Screen Gallery)

화면 스크린샷이나 이미지 파일을 슬라이드에 포함할 수 있습니다.

#### screen_gallery 타입 정의

```json
{
  "slide_number": 9,
  "layout_id": 4,
  "placeholders": {
    "main_title": "4. 주요 화면 - 모바일 앱",
    "action_title": "QR코드 스캔부터 수리요청까지의 직관적인 사용자 경험을 제공합니다."
  },
  "custom_elements": [
    {
      "type": "screen_gallery",
      "data": {
        "layout": "horizontal_3",
        "screens": [
          {
            "image_path": "/path/to/screen1.png",
            "label": "로그인",
            "description": "사번/비밀번호 입력\n간편 로그인 지원"
          },
          {
            "image_path": "/path/to/screen2.png",
            "label": "홈 화면",
            "description": "QR스캔 바로가기\n나의 요청 현황"
          },
          {
            "image_path": "/path/to/screen3.png",
            "label": "수리요청",
            "description": "고장유형 선택\n사진 첨부"
          }
        ]
      }
    }
  ]
}
```

#### screen_gallery 레이아웃 옵션

| layout 값         | 용도                         | 이미지 크기          |
| ----------------- | ---------------------------- | -------------------- |
| horizontal_3      | 모바일 앱 화면 3개 수평 배치 | 5cm × 8.9cm (세로형) |
| horizontal_3_wide | 웹 화면 3개 수평 배치        | 7.8cm × 5cm (가로형) |

#### 이미지 파일 지침

- 절대 경로 사용 권장
- PNG, JPG 형식 지원
- 모바일 화면: 세로 비율 (약 9:16)
- 웹 화면: 가로 비율 (약 16:9)
- 파일이 없을 경우 플레이스홀더 박스로 대체

#### LLM 프롬프트 전략

1. **구조 분석**: 원본 자료에서 핵심 메시지, 데이터 포인트, 논리 흐름 추출
2. **레이아웃 선택**: 각 슬라이드 콘텐츠 유형에 맞는 layout_id 결정
3. **콘텐츠 생성**: 간결하고 임팩트 있는 텍스트 생성 (슬라이드당 최대 6줄)
4. **데이터 구조화**: 차트/표용 데이터를 정형화된 형식으로 변환

#### 품질 기준

- 슬라이드당 핵심 메시지 1개
<!-- - 텍스트 밀도: 최소화 (읽지 않고 '보는' 슬라이드) -->
- 시각적 다양성: 연속 3장 이상 동일 layout_id 금지
- 스토리 흐름: 내러티브 아크 구조 유지 (아래 참조)
- Action Title: 핵심 메시지를 1~2문장으로 요약

**내러티브 아크 (Narrative Arc):**
| 단계 | 목적 | 슬라이드 비율 |
|------|------|-------------|
| 1막: 도입 (Setup) | 맥락, 문제 제시, Hook | 20% |
| 2막: 전개 (Confrontation) | 해결책, 상세 내용 | 60% |
| 3막: 결론 (Resolution) | 요약, 행동촉구 (CTA) | 20% |

**필수 요소:** Hook (첫 슬라이드 관심 유발) → Conflict (문제/과제 명확화) → Resolution (결론과 다음 단계)

#### 자동 이미지 생성 규칙

| 조건 | 트리거 | 추가 필드 |
|------|--------|-----------|
| 카드 채움률 < 50% | 텍스트 2줄 이하 | [`card_image_prompt`](#card_image_prompt-구조) |
| 페이지 여백 > 40% | custom_elements 부족 | [`fill_image_prompt`](#fill_image_prompt-구조) |

> ⚠️ 빈 공간은 콘텐츠와 연관된 의미 있는 비주얼로 채웁니다.

#### 타이포그래피 규칙

| 요소 | 권장 크기 | 비고 |
|------|----------|------|
| 메인 제목 | 36-44pt | Bold, 네이비 |
| 액션 타이틀 | 28-32pt | Regular |
| 본문 | 24-28pt | 가독성 우선 |
| 캡션/주석 | 14-18pt | 회색 계열 |

**폰트 사용 원칙:**
- Sans-serif 폰트 우선 (본고딕, Pretendard, Arial)
- 폰트 종류: 최대 2개 (제목용 + 본문용)
- 줄 간격: 1.3-1.5배
- 줄당 문자 수: 최대 45자 (한글 기준)
- Bold는 핵심 키워드에만 사용
- Italic 사용 자제 (가독성 저하)

#### 여백 및 레이아웃 규칙

**Apple 스타일 여백:**
- 슬라이드 가장자리: 최소 5% 마진
- 콘텐츠 영역: 최소 20% 여백 유지
- 요소 간 간격: 일관된 24px 또는 32px

**콘텐츠 밀도:**
- 슬라이드당 핵심 아이디어: 1개
- 불릿 포인트: 최대 4개
- 한 줄당 단어 수: 6-8개 (한글 기준)

**그리드 시스템:**
- 12열 또는 4열 그리드 기반 정렬
- 모든 요소는 그리드에 스냅
- 비대칭 레이아웃 허용 (단, 의도적 사용)

#### 접근성 규칙 (WCAG 2.2 기반)

**대비율 기준:**
| 텍스트 유형 | 최소 대비율 | 권장 대비율 |
|------------|------------|------------|
| 일반 텍스트 (24pt 미만) | 4.5:1 | 7:1 |
| 대형 텍스트 (24pt 이상) | 3:1 | 4.5:1 |
| 비텍스트 요소 (아이콘, 차트) | 3:1 | 4.5:1 |

**색상 사용:**
- 색맹 친화적 팔레트 사용 (적녹 조합 회피)
- 정보 전달 시 색상만으로 구분하지 않음 (패턴/아이콘 병행)
- 배경: 순백(#FFFFFF) 대신 오프화이트(#F8F9FA) 권장

**가독성:**
- 배경 이미지 위 텍스트: 반투명 오버레이 필수
- 그라데이션 배경 시 텍스트 영역 대비율 검증

#### 시각화 변환 규칙

**숫자표/데이터 → 차트 적극 활용**

- 숫자가 포함된 표(table)는 단순 텍스트 표가 아닌 **차트로 시각화** 필수
- 비교 데이터: Bar Chart 또는 Grouped Bar Chart
- 추이/변화: Line Chart 또는 Area Chart
- 비율/구성: Pie Chart 또는 Donut Chart
- 목표 대비 실적: Gauge Chart 또는 Progress Bar
- As-Is/To-Be 비교: Before-After Bar Chart (변화율 뱃지 포함)

**워크플로우/프로세스 → 인포그래픽 적극 활용**

- 순차적 단계: **Horizontal Process Flow** (원형/사각 노드 + 화살표)
- 분기/의사결정: **Flowchart** (다이아몬드 노드 포함)
- 역할별 흐름: **Swimlane Diagram** (역할별 컬러 구분)
- 시간 기반: **Timeline Infographic** (Gantt-style 또는 vertical timeline)
- 계층 구조: **Pyramid/Funnel Diagram**
- 순환 프로세스: **Circular Flow Diagram**

**텍스트/개념 → 시각적 카드 적극 활용**

- 정의/개념 설명: **Definition Card** (좌측 accent bar + 아이콘)
- 핵심 메시지/인용: **Quote Block** (큰따옴표 아이콘 + 강조 배경)
- 장단점/Pros-Cons: **Split Comparison** (좌우 컬러 대비)
- 핵심 수치 (1-3개): **Big Number Display** (대형 숫자 + KPI 라벨)
- 체크리스트/할일: **Visual Checklist** (✓ 아이콘 + 진행 상태 바)

**관계/구조 → 다이어그램 적극 활용**

- 부분-전체 관계: **Donut/Pie Breakdown** (중앙 라벨 포함)
- 원인-결과 분석: **Fishbone Diagram** (Ishikawa)
- 포함/교집합 관계: **Venn Diagram** (2-3개 원)
- 의존성/연결 관계: **Network Graph** (노드 + 엣지)
- 계층적 분류: **Tree Map / Sunburst** (카테고리 구조)

**비교/평가 → 매트릭스 적극 활용**

- 2차원 포지셔닝: **Quadrant Matrix** (2×2 그리드, 축 라벨)
- 다차원 비교: **Radar/Spider Chart** (5-7개 축 권장)
- 우선순위 결정: **Priority Matrix** (긴급×중요, Eisenhower)
- 옵션/기능 비교: **Feature Comparison Table** (✓/✗/◐ 아이콘)

**상태/진행 → 시각적 지표 적극 활용**

- 달성률/완료율: **Progress Ring/Bar** (퍼센트 라벨)
- 목표 대비 실적: **Bullet Chart** (목표선 + 실적 바)
- 상태 표시: **Traffic Light / Status Badge** (빨강/노랑/초록)
- 위험도/심각도: **Heat Indicator** (컬러 그라데이션 스케일)

**리스트/열거 → 카드 그리드 적극 활용**

- 순위 (Top N): **Ranking Visual** (메달/트로피 스타일, 1-2-3 강조)
- 특징/기능 나열: **Icon Card Grid** (아이콘 + 제목 + 설명)
- 단계별 설명: **Numbered Step Cards** (원형 번호 + 설명)
- 기술 스택: **Tech Logo Grid** (로고 아이콘 배열)

**복잡한 데이터/흐름 → 고급 차트 적극 활용**

- 다차원 상관관계: **Scatter Plot / Bubble Chart** (3개 변수 표현)
- 유량/이동 경로: **Sankey Diagram** (화살표 두께로 수량 표현)
- 데이터 분포/집중: **Heatmap** (색상 강도로 밀도 표현)

**신뢰/증거 → 소셜 프루프 적극 활용**

- 고객사/파트너: **Monochrome Logo Grid** (그레이스케일 로고 정렬)
- 수상/인증: **Badge / Certificate Row** (공식 마크 나열)
- 사용자 후기: **Testimonial Card** (프로필 사진 + 말풍선 + 별점)

**스크린샷/데모 → 디바이스 목업 적극 활용**

- 모바일 앱: **Smartphone Frame** (최신 기기 프레임 적용)
- 웹 서비스: **Browser Window Frame** (섀도우/주소창 포함)
- 서비스 흐름: **Connected Device Flow** (기기 간 연결선)

**추상적 개념 → 메타포 그래픽 적극 활용**

- 통합/결합: **Puzzle / Gear Assembly**
- 보안/방어: **Shield / Lock Layers**
- 성장/확산: **Ripple Effect / Rising Steps**

> ⚠️ **핵심 원칙**: 3줄 이상의 불릿 리스트는 반드시 시각 요소로 변환.
> 청중의 인지 부하를 줄이고 정보 전달 효율을 극대화.

> ⚠️ **중요**: 숫자 나열이나 단계 설명을 텍스트로만 표현하지 말 것.
> 청중이 "읽지 않고 보는" 슬라이드를 목표로 시각 요소 우선 설계.

#### 데이터 시각화 무결성 규칙

**차트 기본 원칙:**
- Bar 차트 Y축: 항상 0에서 시작 (왜곡 방지)
- Pie 차트: 5개 이하 항목만 (초과 시 "기타" 통합)
- 3D 차트: 사용 금지 (왜곡 발생)

**차트정크(Chartjunk) 제거:**
- 불필요한 그리드라인 제거
- 장식적 요소 최소화
- 데이터 직접 레이블링 권장 (범례 의존 최소화)

**대시보드 원칙:**
- 핵심 차트: 3-5개 제한
- 점진적 공개: 상위 요약 → 클릭 시 상세

#### 애니메이션 및 트랜지션 규칙

**기본 원칙:**
- 애니메이션: 목적 있는 사용만 (강조, 순차 공개)
- 트랜지션: 덱 전체에서 1-2가지만 사용

**권장 설정:**
| 요소 | 권장 효과 | 지속 시간 |
|------|----------|----------|
| 슬라이드 전환 | Fade / Push | 0.3-0.5초 |
| 텍스트 등장 | Fade In | 0.3초 |
| 차트 등장 | Wipe / Grow | 0.5-0.8초 |
| 강조 효과 | Pulse / Grow-Shrink | 0.3초 |

**금지 사항:**
- 회전, 바운스, 스핀 등 화려한 효과
- 슬라이드마다 다른 트랜지션
- 0.5초 미만의 너무 빠른 애니메이션
- 2초 이상의 너무 느린 애니메이션

**Morph 트랜지션 활용:**
- 동일 객체의 위치/크기 변화 시 권장
- 스토리 연결감 강화에 효과적

#### 색상 심리학 가이드

| 색상 | 의미/감정 | 적합한 사용처 |
|------|----------|--------------|
| 네이비 (#002452) | 신뢰, 전문성, 안정 | 기업 프레젠테이션, 보고서 |
| 레드 (#C51F2A) | 긴급, 중요, 행동촉구 | CTA, 경고, 강조 |
| 그린 (#2E7D32) | 성장, 긍정, 환경 | 성과, 목표달성, ESG |
| 골드 (#E9B86E) | 프리미엄, 성공, 가치 | 수상, 핵심 성과 |
| 그레이 (#666666) | 중립, 전문성, 균형 | 보조 텍스트, 배경 |

**색상 사용 원칙:**
- 주요 색상: 2-3개로 제한
- 강조 색상: 전체의 10% 이하
- 배경/전경 대비: 항상 검증

---

### 디자인 프롬프트 생성 (Design Prompt)

표지(layout_id: 1)와 목차(layout_id: 2)를 제외한 모든 슬라이드에는 `design_prompt` 객체를 추가합니다.
전문 디자이너가 직접 만든 듯한 고품질 슬라이드를 생성하기 위한 상세 지시사항입니다.

#### design_prompt 구조

```json
{
  "design_prompt": {
    "concept": "슬라이드 디자인 컨셉 (한 문장)",
    "layout": {
      "grid": "그리드 배치 (예: 4열 균등 배치, 2x2 그리드)",
      "spacing": "요소 간 간격",
      "vertical_position": "수직 위치 (예: 슬라이드 중앙)"
    },
    "card_style": {
      "background": "배경색/그라데이션",
      "border": "테두리 스타일",
      "border_radius": "모서리 둥글기",
      "shadow": "그림자 효과"
    },
    "icon_style": {
      "size": "아이콘 크기 (예: 48px)",
      "style": "Material Icons Outlined",
      "color": "색상 지정"
    },
    "typography": {
      "title": "제목 폰트 스타일 (예: Bold, 16pt, 네이비)",
      "desc": "설명 폰트 스타일 (예: Regular, 12pt, 회색)"
    },
    "color_scheme": {
      "primary": "#002452 (네이비)",
      "secondary": "#C51F2A (레드)",
      "accent": ["#4B6580", "#E9B86E"],
      "background": "#FFFFFF"
    },
    "visual_hierarchy": "시선 유도 순서 설명",
    "animation_hint": "애니메이션 힌트 (발표 시 활용)"
  }
}
```

#### 슬라이드 유형별 디자인 가이드

| 슬라이드 유형                 | 디자인 컨셉             | 핵심 요소                                 |
| ----------------------------- | ----------------------- | ----------------------------------------- |
| 기능 카드 (icon_box_grid)     | Premium Feature Cards   | 좌측 accent bar, 아이콘 강조, 미니멀 카드 |
| 문제점 표 (table)             | Problem-Solution Matrix | 헤더 네이비, 심각도 컬러 코딩             |
| Pain Point (pain_point_cards) | User Pain Cards         | 역할별 컬러, 연한 빨강 배경               |
| 아키텍처 (diagram)            | System Architecture     | 3-tier 레이어, 그라데이션 박스, 연결선    |
| 프로세스 (process_flow)       | Horizontal Flow         | 원형 노드, 색상으로 역할 구분, 화살표     |
| 비교 차트 (comparison_chart)  | Before/After Bars       | As-Is 회색, To-Be 강조색, 변화율 뱃지     |
| 타임라인 (timeline)           | Gantt-style Timeline    | Phase 바, 주차 헤더, 마일스톤             |

#### 디자인 프롬프트 작성 원칙

1. **구체적 수치 명시**: px, pt, cm 등 정확한 크기 지정
2. **색상 코드 사용**: HEX 코드로 정확한 색상 지정 (#002452)
3. **레이아웃 비율**: 퍼센트 또는 그리드 기반 배치
4. **시각적 계층**: 정보의 중요도에 따른 크기/색상 차등
5. **일관성 유지**: 슬라이드 간 디자인 언어 통일

---

### 이미지 생성 프롬프트 (Image Generation Prompt)

시각적 요소가 필요한 슬라이드에는 `image_generation_prompt` 객체를 추가합니다.
AI 이미지 생성 도구 (DALL-E, Midjourney, Gemini 등)에서 사용할 수 있는 프롬프트입니다.

#### image_generation_prompt 구조

```json
{
  "image_generation_prompt": {
    "main_visual": {
      "prompt": "영문 이미지 생성 프롬프트 (상세하고 구체적으로)",
      "style": "스타일 키워드 (flat design, isometric, photorealistic 등)",
      "size": "권장 크기 (예: 1920x1080)",
      "negative_prompt": "제외할 요소 (optional)"
    },
    "icon_set": {
      "prompt": "아이콘 세트 생성 프롬프트",
      "style": "line art, filled, gradient 등",
      "usage": "사용 위치 설명"
    }
  }
}
```

#### 이미지 생성 프롬프트 예시

**아키텍처 다이어그램용:**

```json
{
  "prompt": "Clean system architecture diagram, 3-tier layout, mobile app and web admin on left connecting to central backend server, database and external API on right, navy blue and green color scheme, flat design, white background, professional enterprise software style, Korean labels",
  "style": "flat design, technical diagram, enterprise",
  "negative_prompt": "3D, complex, dark background, cartoon"
}
```

**프로세스 플로우용:**

```json
{
  "prompt": "Horizontal business process flow with 6 circular nodes connected by arrows, alternating navy and orange colors, small notification icons above arrows, clean infographic style, white background",
  "style": "infographic, flat design, process flow"
}
```

**대시보드 목업용:**

```json
{
  "prompt": "Chrome browser mockup showing admin dashboard, dark navy sidebar, 4 KPI cards at top, data table in center, small charts on right, green accent colors, modern enterprise SaaS design",
  "style": "UI screenshot, browser mockup, enterprise software"
}
```

#### 이미지 생성 시 고려사항

1. **일관된 스타일**: 모든 생성 이미지가 동일한 디자인 언어 사용
2. **브랜드 색상**: 네이비(#002452), 레드(#C51F2A), 그린(#2E7D32) 계열
3. **심플함 유지**: 복잡한 요소 최소화, 핵심만 표현
4. **텍스트 최소화**: 이미지 내 텍스트는 라벨 수준만
5. **해상도**: 최소 1920x1080 (Full HD) 권장

---

### 완전한 슬라이드 JSON 예시

```json
{
  "slide_number": 3,
  "layout_id": 4,
  "placeholders": {
    "main_title": "1. 프로젝트 개요",
    "action_title": "공조설비 고장신고부터 수리완료까지 전 과정을 디지털화합니다."
  },
  "custom_elements": [
    {
      "type": "icon_box_grid",
      "data": {
        "columns": 4,
        "items": [
          {
            "icon": "qr_code",
            "title": "QR코드 기반",
            "desc": "현장 스캔으로 즉시 고장신고",
```

##### card_image_prompt 구조

카드 채움률 50% 미만 시 추가:

```json
            "card_image_prompt": {
              "trigger": "fill_below_50%",
              "prompt": "QR code scanner icon, line art, 2px stroke, #002452, 96px, transparent bg"
            }
```

```json
          },
          {
            "icon": "sync",
            "title": "실시간 추적",
            "desc": "요청→승인→수리→완료 전 과정"
          },
          {
            "icon": "analytics",
            "title": "데이터 기반",
            "desc": "고장 통계 및 정비 이력 분석"
          },
          {
            "icon": "notifications",
            "title": "자동 알림",
            "desc": "카카오톡 실시간 통보"
          }
        ]
      }
    }
  ],
  "design_prompt": {
    "concept": "Premium Feature Cards - 핵심 가치를 한눈에 전달",
    "layout": {
      "grid": "4열 균등 배치, 카드 간 간격 24px",
      "card_size": "width: 200px, height: 180px",
      "vertical_position": "슬라이드 중앙 (y: 50%)"
    },
    "card_style": {
      "background": "#FFFFFF with shadow (0 4px 12px rgba(0,0,0,0.08))",
      "border": "좌측 4px accent bar",
      "border_radius": "8px (우측만)",
      "accent_colors": ["#002452", "#C51F2A", "#4B6580", "#E9B86E"]
    },
    "icon_style": {
      "size": "48px",
      "style": "Material Icons Outlined, 2px stroke",
      "color": "각 카드의 accent 컬러와 동일"
    },
    "typography": {
      "title": "본고딕 Bold, 16pt, #002452",
      "desc": "본고딕 Regular, 12pt, #666666, line-height: 150%"
    },
    "visual_hierarchy": "아이콘 → 타이틀 → 설명 순으로 시선 유도"
  },
  "image_generation_prompt": {
    "icon_set": {
      "prompt": "Set of 4 line icons: QR code scanner, sync arrows, analytics chart, notification bell, consistent 2px stroke weight, navy blue color, 64px size each, transparent background",
      "style": "line icon, minimal, consistent",
      "usage": "각 카드 상단에 배치"
    }
  },
```

##### fill_image_prompt 구조

페이지 여백 40% 이상 시 추가:

```json
  "fill_image_prompt": {
    "trigger": "whitespace_above_40%",
    "prompt": "Isometric business process illustration, navy/green palette, white bg, 16:9",
    "placement": "content_area_right",
    "size": "fill_remaining_space"
  }
}
```
