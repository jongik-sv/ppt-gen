# Stage 2: 아웃라인 생성 프롬프트

## 입력
- 사용자 요청 (주제, 목적)
- session.yaml의 settings

## 출력
slides[] 배열에 outline 추가:
```yaml
slides:
  - index: 1
    type: cover
    outline:
      title: "슬라이드 제목"
      subtitle: "부제목 (선택)"
      content_type: comparison  # 콘텐츠 유형 (필수, type=content일 때)

      # 디자인 의도 (필수, type=content/chart일 때)
      design_intent:
        visual_type: card-grid     # 시각화 유형
        layout: equal-weight       # 레이아웃 방식
        emphasis: title            # 강조 요소
        icon_needed: true          # 아이콘 필요 여부
        description: |             # 자유 형식 설명
          슬라이드 시각화 의도를 구체적으로 서술.
          어떤 느낌으로 만들고 싶은지 설명.

      key_points:
        - "핵심 포인트 1"
        - "핵심 포인트 2"
      speaker_notes: "발표자 노트"
      data: { ... }  # 차트/테이블 데이터 (선택)
```

## content_type (콘텐츠 유형)

**type=content인 슬라이드에 필수.** 템플릿 매칭에 사용.

| content_type | 설명 | 키워드 힌트 | 매핑 카테고리 |
|--------------|------|-------------|--------------|
| comparison | 병렬 비교, 독립 항목 | 특징, 서비스, 팀, 요청사항 | grid, diagram |
| sequence | 순서, 단계, 흐름 | 단계, 프로세스, 전략, 절차 | process |
| timeline | 시간순 일정 | 일정, 월, 기간, 마일스톤 | timeline |
| hierarchy | 계층, 구조, 목록 | 조직, 구조, 위험, 이슈 | list, diagram |
| metrics | 수치, KPI, 퍼센트 | %, 억원, 증가, 절감 | infographic, chart |

**분류 규칙:**
1. title/key_points에 "단계", "프로세스", "전략" → `sequence`
2. title에 "일정", "마일스톤" 또는 key_points에 월/기간 → `timeline`
3. key_points에 %, 억원, 수치 강조 → `metrics`
4. title에 "조직", "위험", "이슈" → `hierarchy`
5. 그 외 독립 항목 나열 → `comparison` (기본값)

## design_intent (디자인 의도)

**type=content/chart인 슬라이드에 필수.** Stage 3 템플릿 매칭과 Stage 4 콘텐츠 생성에 핵심적으로 사용.

### 구조화 필드 (필수)

| 필드 | 옵션 | 설명 |
|------|------|------|
| visual_type | card-grid, timeline, flowchart, list, diagram, infographic, comparison-table, metrics-highlight | 시각화 유형 |
| layout | equal-weight, hierarchical, centered, split, circular, radial | 배치 방식 |
| emphasis | title, number, icon, description, image, data | 강조할 요소 |
| icon_needed | true, false | 아이콘 사용 여부 |

### visual_type 선택 가이드

| visual_type | 적합한 경우 | 예시 |
|-------------|------------|------|
| card-grid | 독립적인 항목 나열 (3~6개) | 서비스 소개, 팀 소개 |
| timeline | 시간순 진행/일정 | 프로젝트 일정, 마일스톤 |
| flowchart | 순서/단계/프로세스 | 업무 프로세스, 의사결정 흐름 |
| list | 계층적 목록/구조 | 조직도, 이슈 목록 |
| diagram | 관계/구조 시각화 | 시스템 구조, 관계도 |
| infographic | 데이터/수치 강조 | KPI 대시보드, 통계 |
| comparison-table | 항목 간 비교 | 기능 비교, 가격 비교 |
| metrics-highlight | 핵심 수치 1~3개 강조 | 매출 성장률, 비용 절감 |

### layout 선택 가이드

| layout | 적합한 경우 |
|--------|------------|
| equal-weight | 모든 항목이 동등한 비중 |
| hierarchical | 중요도/순서에 따른 계층 |
| centered | 중앙 요소 강조 |
| split | 좌우/상하 분할 비교 |
| circular | 순환 구조/사이클 |
| radial | 중심에서 방사형 확장 |

### description 작성 가이드

자유 형식으로 다음 내용을 포함:
- **시각화 의도**: "4개 서비스를 카드 형태로 균등 배치"
- **강조 포인트**: "약어(WMS, TMS)가 눈에 띄도록 큰 폰트"
- **분위기/느낌**: "깔끔하고 전문적인 느낌", "친근하고 부드러운 분위기"
- **특별 요청**: "아이콘 색상은 서비스별로 다르게"

## 슬라이드 타입

| 타입 | 용도 | 필수 필드 |
|------|------|----------|
| cover | 표지 | title, subtitle |
| toc | 목차 | title, key_points (섹션 목록) |
| section | 섹션 구분 | title |
| content | 본문 | title, key_points |
| chart | 차트 | title, data |
| closing | 마무리 | title, key_points (연락처 등) |

## 생성 규칙

### 슬라이드 수 가이드
| duration | 권장 슬라이드 |
|----------|--------------|
| 5min | 5~7장 |
| 10min | 8~12장 |
| 20min | 15~20장 |
| 30min+ | 20장+ |

### 콘텐츠 밀도
- 본문 5줄 이하
- key_points 3~5개
- 한 슬라이드, 한 핵심 메시지

### 청중별 톤
| audience | 특징 |
|----------|------|
| executive | 핵심만, 의사결정 중심, 숫자 강조 |
| team | 상세 내용, 실행 계획 |
| customer | 가치 중심, 스토리텔링 |
| investor | ROI, 성장 잠재력, 경쟁력 |
| public | 쉬운 용어, 시각적 강조 |

## 예시

### 입력
```
주제: 스마트 물류 시스템 제안
settings:
  document_type: proposal
  audience: executive
  duration: 10min
  tone: formal
```

### 출력
```yaml
slides:
  - index: 1
    type: cover
    outline:
      title: "스마트 물류 시스템 제안"
      subtitle: "효율성 혁신을 위한 솔루션"
      speaker_notes: "인사 후 회사 소개 간략히"

  - index: 2
    type: toc
    outline:
      title: "목차"
      key_points:
        - "현황 분석"
        - "솔루션 개요"
        - "기대 효과"
        - "투자 계획"

  - index: 3
    type: content
    outline:
      title: "현재 물류 시스템의 한계"
      content_type: metrics
      design_intent:
        visual_type: metrics-highlight
        layout: equal-weight
        emphasis: number
        icon_needed: true
        description: |
          3개의 핵심 문제점을 수치와 함께 강조.
          각 항목에 경고/주의 아이콘 배치.
          빨간색 계열로 문제의 심각성 표현.
          숫자(15%, 200건, 5억원)가 가장 눈에 띄도록.
      key_points:
        - "수작업 재고 관리로 인한 오류율 15%"
        - "배송 지연 월평균 200건"
        - "재고 과잉으로 연간 5억원 손실"
      speaker_notes: "고객사 실제 데이터 활용하여 신뢰도 확보"

  - index: 4
    type: content
    outline:
      title: "핵심 서비스 4가지"
      content_type: comparison
      design_intent:
        visual_type: card-grid
        layout: equal-weight
        emphasis: title
        icon_needed: true
        description: |
          4개 서비스를 균등한 카드 형태로 배치.
          WMS, TMS 등 약어가 크게 보이도록 제목 강조.
          각 서비스에 관련 아이콘 배치.
          깔끔하고 전문적인 그리드 레이아웃.
      key_points:
        - "WMS: 창고 관리 시스템"
        - "TMS: 운송 관리 시스템"
        - "OMS: 주문 관리 시스템"
        - "WCS: 창고 제어 시스템"
      speaker_notes: "각 서비스의 핵심 가치 간략히 설명"

  - index: 5
    type: content
    outline:
      title: "도입 일정"
      content_type: timeline
      design_intent:
        visual_type: timeline
        layout: hierarchical
        emphasis: data
        icon_needed: false
        description: |
          6개월 프로젝트 일정을 타임라인 형태로 표시.
          각 단계별 기간과 마일스톤 명확히 표시.
          현재 진행 단계 강조.
          완료/진행중/예정을 색상으로 구분.
      key_points:
        - "1~2월: 현황 분석 및 설계"
        - "3~4월: 시스템 개발"
        - "5월: 테스트 및 검증"
        - "6월: 전사 배포"
      speaker_notes: "현실적인 일정임을 강조"

  - index: 6
    type: chart
    outline:
      title: "비용 절감 효과"
      design_intent:
        visual_type: infographic
        layout: split
        emphasis: data
        icon_needed: false
        description: |
          현재 vs 도입 후 비용 비교를 막대 차트로.
          35% 절감 효과를 크게 강조.
          녹색으로 긍정적인 변화 표현.
      data:
        type: bar
        labels: ["현재", "도입 후"]
        datasets:
          - label: "운영비용"
            data: [100, 65]
      speaker_notes: "구체적인 절감 금액도 언급"
```

## 프롬프트 템플릿

```
당신은 프레젠테이션 전문가입니다.

사용자 요청: {user_request}
설정:
- 문서 종류: {document_type}
- 청중: {audience}
- 발표 시간: {duration}
- 톤: {tone}

위 정보를 바탕으로 슬라이드 아웃라인을 YAML 형식으로 생성하세요.

규칙:
1. 슬라이드 수는 duration에 맞게
2. 청중에 맞는 내용 깊이
3. 각 슬라이드는 하나의 핵심 메시지
4. key_points는 3~5개
5. 차트가 필요한 경우 data 필드 포함
6. type=content/chart인 슬라이드에 content_type 필수:
   - 단계/프로세스/전략 → sequence
   - 일정/월/기간 → timeline
   - %/억원/수치 → metrics
   - 조직/위험/이슈 → hierarchy
   - 그 외 → comparison
7. **type=content/chart인 슬라이드에 design_intent 필수:**
   - visual_type: 시각화 유형 선택
     (card-grid, timeline, flowchart, list, diagram, infographic, comparison-table, metrics-highlight)
   - layout: 배치 방식 선택
     (equal-weight, hierarchical, centered, split, circular, radial)
   - emphasis: 강조할 요소
     (title, number, icon, description, image, data)
   - icon_needed: 아이콘 필요 여부 (true/false)
   - description: 자유 형식으로 시각화 의도 상세 서술
     (어떻게 표현하고 싶은지, 어떤 느낌을 원하는지 구체적으로)

**중요: design_intent.description에 슬라이드를 어떻게 시각화할지 구체적으로 서술하세요.**
이 정보가 템플릿 선택과 콘텐츠 생성의 핵심 기준이 됩니다.
```
