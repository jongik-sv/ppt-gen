import yaml
import sys

# Define the design descriptions mapping by slide number
# These descriptions are generated based on the "Deep Green" theme and specific content of each slide
# strictly following the user's request for detailed, professional design instructions.

DESIGNS = {
    1: """## 레이아웃 및 배경
- 배경: Deep Green (#1B4D3E) 단색 배경이 아닌, 미묘한 사선 패턴이 들어간 그라데이션 배경 (Deep Green → Darker Teal)으로 깊이감을 줍니다.
- 메인 타이틀은 슬라이드 중앙에서 약간 상단에 위치하여 시선을 집중시킵니다.
- 하단 20% 영역에 곡선형의 Accent Graphic 요소(연한 Mint 또는 Teal 컬러)를 배치하여 현대적인 느낌을 제공합니다.

## 타이포그래피 (Deep Green 테마)
- 태그라인("2025년..."): 상단 중앙, Regular 16pt, Opacity 80% White (#FFFFFF). 자간을 넓게(letter-spacing 2px) 주어 세련되게 표현합니다.
- 메인 타이틀: Bold 48pt, Pure White (#FFFFFF). 세리프가 없는 깔끔한 산세리프 폰트(Pretendard/Montserrat)를 사용합니다. 그림자(Drop Shadow)를 부드럽게 적용(blur 10px, alpha 0.3)하여 배경과 분리합니다.
- 서브타이틀: Semi-Bold 24pt, Light Mint (#A8E6CF). 메인 타이틀 하단 16px 간격.
- 수행사/작성자 정보: 하단 우측 정렬, Regular 14pt, White. 로고가 있다면 좌측 하단에 배치하고 텍스트는 우측에 두어 균형을 맞춥니다.

## 시각적 요소
- 로고: 발주사((주)글로벌물류)와 수행사((주)테크솔루션) 로고를 흰색 단색(Monochrome)으로 변환하여 하단 좌우에 배치하거나 상단 우측에 나란히 배치하여 깔끔함을 유지합니다.
- 장식 요소: 타이틀 주변에 얇은 선(Line)이나 기하학적 도형을 최소한으로 사용하여 "스마트", "기술", "연결"의 이미지를 추상적으로 전달합니다.""",

    2: """## 레이아웃 및 구조
- 2단 레이아웃: 좌측(30%)은 섹션 타이틀 영역, 우측(70%)은 목차 리스트 영역으로 분할합니다.
- 좌측 영역: 배경을 연한 회색(#F5F5F5)으로 처리하고 세로형 장식 바를 두어 영역을 구분합니다.

## 좌측 타이틀 영역
- "CONTENTS" 텍스트를 세로쓰기 또는 굵은 영문으로 크게 배치(Bold 64pt, Color #E0E0E0)하여 배경처럼 활용합니다.
- 실제 한글 제목 "목차"는 그 위에 선명하게(Deep Green #1B4D3E, Bold 32pt) 배치합니다.

## 우측 목차 리스트 (5개 항목)
- 리스트 스타일: 각 항목을 카드 형태가 아닌, 깔끔한 'Open List' 스타일로 배치합니다.
- 번호(Number): "01", "02" 등 두 자리 숫자로 표기. Font: Oswald/Roboto Condensed, Bold 24pt, Color: Deep Green (#1B4D3E).
- 항목명(Title): 번호 우측 24px 간격. Bold 20pt, Dark Gray (#333333).
- 설명(Description): 항목명 하단 8px. Regular 14pt, Medium Gray (#777777). 
- 구분선: 각 항목 사이에 1px 실선(#EEEEEE)을 긋되 좌우 여백을 주어 답답하지 않게 합니다.
- 인터랙션/강조: 마우스 오버 시(또는 강조용 정적 디자인 시) 해당 항목의 번호 배경에 원형의 Deep Green 포인트가 생기거나, 텍스트 컬러가 Highlight 되는 효과를 연출합니다.""",

    3: """## 간지(Divider) 디자인
- 전체 배경: 깨끗한 흰색 배경에 중앙에 거대한 타이포그래피와 이미지가 결합된 형태.
- 배경 이미지: "물류", "네트워크" 관련 고해상도 이미지를 우측 50% 영역에 배치하되, Deep Green 컬러 오버레이(Opacity 90%)를 씌워 텍스트 가독성을 높이고 차분한 분위기를 연출합니다.

## 타이포그래피
- 섹션 번호: 좌측 상단 또는 중앙 상단에 매우 크게 "01" (Outline Font 또는 연한 회색)으로 배치하여 배경처럼 보이게 합니다.
- 섹션 제목("프로젝트 개요"): 화면 중앙(좌측 텍스트 영역의 수직 중앙). Bold 40pt, Deep Green (#1B4D3E). 좌측에 굵은 세로 바(Width 8px, Height 100%)를 두어 강렬한 인상을 줍니다.
- 상세 설명: 제목 하단 24px. Regular 16pt, Dark Gray. 줄바꿈을 적절히 하여 가독성을 높입니다.

## 장식 요소
- 기술적인 느낌을 주는 얇은 그리드 패턴이나 점선(Dotted Line)을 배경에 은은하게 깔아 "설계", "구조"의 뉘앙스를 풍깁니다.""",

    4: """## 레이아웃: 3단 수평 분할 (현황 -> 목표 -> 효과)
- 슬라이드를 수직으로 3등분하여 상단부터 '문제점', '목표', '효과'의 논리적 흐름(Flow)을 시각화합니다.
- 각 행(Row)은 좌측에 굵은 아이콘/헤딩 영역, 우측에 상세 설명 영역을 가집니다.

## 디자인 디테일 (행별)
1. **현황 및 문제점 (Top)**:
   - 아이콘: 'Warning' 또는 'Legacy' 아이콘 (Line Style, Dark Red/Orange 계열 포인트 사용).
   - 배경: 아주 연한 웜그레이(#FAF8F8)로 '개선 필요' 뉘앙스.
   - 텍스트: 문제점 키워드("속도 저하", "연동 한계")를 Bold 처리.

2. **추진 목표 (Middle)**:
   - 아이콘: 'Target' 또는 'Arrow' 아이콘 (Deep Green).
   - 시각적 연결: 위/아래 행과 연결되는 화살표 그래픽을 좌측 라인에 배치하여 "전환"을 표현합니다.
   - 배경: 흰색. 가장 밝고 명확하게.

3. **기대 효과 (Bottom)**:
   - 아이콘: 'Chart-up' 또는 'Star' 아이콘 (Bright Blue or Teal).
   - 데이터 강조: 설명 텍스트 내 숫자("30%", "99.5%", "20%")를 **매우 크게(Bold 24pt)** 그리고 컬러(Deep Green)로 강조합니다. 단순히 텍스트 줄글이 아니라, 숫자+단위만 별도로 떼어내어 우측이나 중앙에 배치하는 'Key Figure' 스타일도 좋습니다.

## 전체 스타일
- 아이콘 스타일: 48px x 48px, 원형 배경(Soft Fill) 안에 라인 아이콘.
- 여백: 각 행 사이 16px 간격. 세련된 그림자(Shadow-sm)를 각 블록에 적용하여 카드 느낌을 줍니다.""",

    5: """## 레이아웃: 4컬럼 카드 그리드
- "4개 핵심 모듈"을 1x4 그리드로 배치하여 동등한 위계질서를 보여줍니다.
- 카드 간 간격(Gap): 20px. 슬라이드 좌우 여백 충분히 확보(60px).

## 카드 디자인 (Card UI)
- 형태: 둥근 모서리(Border Radius 12px), 흰색 배경, 미세한 테두리(Border 1px #E0E0E0).
- 헤더(상단): 각 시스템(WMS, TMS, OMS, Dashboard)의 영문 약어를 **타이포그래피 로고**처럼 디자인합니다. (예: WMS는 굵고 강하게, Dashboard는 얇고 세련되게).
- 서브텍스트(한글명): 영문 약어 바로 아래 12pt, Gray(#666666).
- 아이콘: 각 카드의 중앙 또는 우측 상단에 옅은 워터마크 형태로 관련 아이콘(창고, 트럭, 장바구니, 차트)을 배경 처럼 배치(Opacity 10%)하여 직관성을 높입니다.
- 본문(기능 리스트): 하단에 Bullet Point로 핵심 기능 2-3개를 나열. Font: Regular 13pt.
- 하단 포인트: 각 카드 하단에 4px 높이의 컬러 바(Color Bar)를 두어 구분감을 줍니다.
    - WMS: Deep Green (#1B4D3E)
    - TMS: Ocean Blue (#2C7A7B)
    - OMS: Warm Orange (#DD6B20)
    - Dashboard: Purple (#805AD5)

## 타이틀 영역
- "프로젝트 범위" 타이틀과 "4개 핵심 시스템 구축" 서브타이틀은 좌측 정렬.
- 타이틀 우측 여백에 범례나 전체를 아우르는 아이콘(시스템 통합 아이콘)을 작게 배치할 수 있습니다.""",

    6: """## 챕터 간지 (Divider)
- 배경: Slide 3과 일관성을 유지하되, 이번에는 "전략", "체스", "나침반" 등의 이미지를 은유적으로 사용하여 "방향성"과 "전략"을 시각화합니다.
- 컬러 테마: Deep Green 바탕에 흰색 라인 아트(Line Art) 스타일의 전략 다이어그램(화살표, 프로세스 맵)이 배경에 깔려있습니다.
- 텍스트: "02" 숫자 크게, 제목 "추진 전략 및 방법론".
- 서브타이틀("안정적 전환...")은 이탤릭체나 명조 계열(Serif)을 사용하여 진정성과 무게감을 더합니다.""",

    7: """## 레이아웃: 3-Step Process Flow
- 좌측에서 우측으로 흐르는 수평 프로세스형 레이아웃입니다.
- 단순 나열이 아닌, "순환"과 "발전"을 의미하는 연결 고리 디자인을 적용합니다.

## 각 단계 디자인 (원형 + 텍스트 박스)
1. **단계적 전환**: "안정성"을 상징하는 방패(Shield) 모양 또는 큐브 아이콘.
2. **애자일 기반**: "속도/유연성"을 상징하는 회전 화살표(Loop) 아이콘.
3. **현업 밀착**: "협력"을 상징하는 악수(Handshake) 또는 사람 그룹 아이콘.

## 시각적 흐름 (Connector)
- 각 단계 아이콘 사이에 점선 또는 실선 화살표를 배치합니다.
- Deep Green 컬러의 그라데이션 라인(좌→우)이 전체를 관통하여 "하나의 통합된 전략"임을 보여줍니다.

## 텍스트 디자인
- 타이틀: 각 아이콘 하단에 중앙 정렬, Bold 18pt.
- 본문: 타이틀 아래 박스 형태로 설명. 배경색을 아주 연한 Mint(#F0FAF5)로 깔아 텍스트 가독성을 높입니다.
- 키워드 강조: "모듈별 순차", "2주 단위", "주 2회" 등 핵심 수치/단어는 Deep Green Color + Bold 처리합니다.""",

    8: """## 디자인: 방사형(Radial) 다이어그램
- 중앙 핵심 코어(Core)와 이를 둘러싼 5개의 위성(Satellite) 노드 구조.
- 중앙: "Smart Logistics Platform"이라는 텍스트가 적힌 육각형 또는 원형 허브. 입체감(Gradient + Shadow)을 주어 가장 중요함을 강조.

## 노드 디자인 및 배치 (Tech Stack)
- 5방향(Frontend, Backend, DB, Infra, AI/ML)으로 뻗어나가는 연결선(Node Link) 디자인.
- 각 노드: 아이콘(상단) + 기술스택 명세(하단)의 결합.
    - **Frontend**: Vue.js 로고 컬러(Green) 활용.
    - **Backend**: Spring Leaf 아이콘 활용.
    - **Database**: 실린더 아이콘.
    - **Infra**: AWS 구름 아이콘.
    - **AI/ML**: 뇌/회로도 아이콘.
- 텍스트 박스: 각 노드 옆에 말풍선 또는 카드 형태로 상세 버전 정보(v3.4, v3.2 등)를 명시. 폰트는 작지만 명확하게(Consolas/Monospace 계열 추천하여 개발/기술 느낌 강조).

## 배경 그래픽
- 전체적으로 희미한 회로도(Circuit) 패턴이나 네트워크 메쉬(Mesh) 패턴을 배경에 깔아 "IT 아키텍처"의 전문성을 부각시킵니다.""",

    9: """## 챕터 간지 (Divider)
- 테마: "사람", "조직", "협력".
- 배경 이미지: 팀원들이 회의하거나 함께 모니터를 보고 있는 비즈니스 미팅 사진(흑백 처리 + Green Overlay).
- 텍스트: "03 프로젝트 조직".
- 디자인 포인트: 조직도 모양의 아이콘을 타이틀 옆에 배치하여 주제를 암시합니다.""",

    10: """## 레이아웃: 인물 카드형 (Profile Card)
- 4명의 핵심 인력을 소개하는 프로필 카드 디자인입니다. 단순 텍스트 나열이 아닌, "신뢰감"을 주는 명함/프로필 스타일.

## 카드 디자인 디테일
- 상단: 추상적인 아바타(Avatar) 또는 역할 아이콘(PM, Architect, Dev Leader). 실제 사진이 없다면 세련된 **Line Art Illustration** 사용.
- 이름 및 직급: 이름은 크게(20pt Bold), 직급은 작게(14pt Regular).
- 구분선: 이름 아래 짧은 Deep Green 밑줄.
- R&R(역할): 카드 하단에 회색 박스로 영역을 만들어 주요 책임을 기술.
- 색상 코딩:
    - **발주기관 PM**: 가장 짙은 색상 또는 테두리 강조 (최종 승인권자).
    - **수행사 PM**: 메인 테마 컬러.
    - **아키텍트/리더**: 보조 컬러 (Teal/BlueGreen).
- 배치: 발주기관 PM을 가장 좌측(또는 별도 상단)에 두어 위계를 표현하거나, 4명을 대등하게 두되 카드 헤더 색상으로 소속(발주/수행)을 구분합니다.""",

    11: """## 인포그래픽: Dot Matrix & Big Number
- "8명, 78MM"라는 데이터를 시각적으로 강력하게 전달하기 위한 인포그래픽 슬라이드입니다.
- 일반적인 표(Table) 대신, 시각적 비중을 보여주는 디자인을 사용합니다.

## 시각화 요소
1. **인원 구성(8명)**:
   - 8개의 사람 아이콘(Iconography)을 배치.
   - 역할별로 색상을 다르게 적용 (PM: Dark Green, Dev: Medium Green, DBA/QA: Light Green).
   - 각 그룹 아래에 라벨링.

2. **투입 공수(78MM)**:
   - 우측에 거대한 원형 차트(Donut Chart) 또는 숫자 타이포그래피 배치.
   - "78" 숫자를 매우 크게(100pt 이상, Deep Green) 배치하고, "MM" 단위를 작게 붙임.
   - 하단에 "총 12개월 프로젝트"라는 기간 정보를 타임라인 바(Bar) 형태로 보조 표기.

## 레이아웃 밸런스
- 좌측: 인력 구성 (Who) - 정성적/사람 중심.
- 우측: 투입 규모 (How Much) - 정량적/데이터 중심.
- 중앙에 세로 구분선을 점선으로 넣어 두 정보를 분리하되 연관성을 유지.""",

    12: """## 챕터 간지 (Divider)
- 테마: "시간", "일정", "마일스톤".
- 배경: 캘린더나 시계, 로드맵을 형상화한 그래픽 요소.
- 텍스트: "04 추진 일정".
- 역동성: 우상향하는 화살표나 타임라인 그래픽을 배경에 사용하여 프로젝트가 앞으로 나아감을 표현.""",

    13: """## 레이아웃: Gantt Chart 스타일 타임라인
- 좌측에 단계명(착수, 분석, 설계...), 우측에 1월~12월까지의 가로 막대(Bar)가 있는 간트 차트 형식.
- 단순 표가 아닌, **현대적인 로드맵 디자인**을 적용합니다.

## 타임라인 디자인 (Horizontal Bar)
- 헤더(월): 상단에 1월~12월을 표기하고 분기(Q1~Q4)별로 배경색을 옅게 달리하여 구분.
- 단계별 막대(Bar):
    - **개발 단계(6~9월)**: 가장 길고 중요한 구간이므로 진한 Deep Green + 빗금 패턴 또는 그라데이션으로 강조.
    - 나머지 단계: 중간 톤의 Green/Gray.
    - 막대 안에 "4주", "16주" 등 기간 텍스트를 흰색으로 넣어 직관성 확보.
- 오늘(Present) 시점: 현재 시점(가상)에 붉은색 세로 점선을 그어 "현재 위치"를 표시하는 디테일 추가 가능.

## 텍스트 및 범례
- 각 단계명 아래에 주요 활동 키워드(킥오프, 요구사항 등)를 작은 폰트(10pt, Gray)로 병기하여 막대만 보고도 내용을 알 수 있게 합니다.""",

    14: """## 디자인: Road Map (Journey Map)
- 직선형 타임라인이 아닌, 약간의 곡선(S-Curve) 또는 지그재그 길 형태의 "여정"을 표현합니다.
- 시작(1월)부터 끝(12월)까지의 길 위에 6개의 깃발(M1~M6)이 꽂혀있는 디자인.

## 마일스톤 마커 (Milestone Marker)
- 형태: 다이아몬드 또는 육각형 마커.
- 색상:
    - 일반 마일스톤: 테두리만 있는 스타일(Outline).
    - 주요 마일스톤(M6 오픈 등): 채워진 스타일(Solid Fill) + 별 표시(Star).
- 라벨링:
    - 날짜(2025-01-10)를 마커 위에 볼드체로.
    - 행사명(착수보고)을 마커 아래에.
    - 산출물(수행계획서)을 더 작은 글씨로 박스 처리하여 배치.

## 시각적 흐름
- M1에서 M6로 이어지는 길(Path)을 점선으로 연결.
- M6(오픈) 지점 도착 시 팡파레나 결승선(Finish Line) 그래픽을 넣어 목표 달성의 이미지를 줍니다.""",

    15: """## 챕터 간지 (Divider)
- 테마: "품질", "보안", "방패".
- 배경: 체크리스트, 돋보기, 방패(Shield) 아이콘 등을 패턴화.
- 텍스트: "05 품질 및 위험 관리".
- 신뢰감: 안정감을 주는 Blue-Green 계열의 색상을 보조적으로 사용하여 "안전함"을 강조.""",

    16: """## 디자인: 3-Checkpoints List
- "검토", "리뷰", "분석"이라는 3가지 검증 관문을 시각화합니다.
- 단순 리스트보다는 **3단계 필터(Filter) 또는 게이트(Gate)** 형태로 디자인하여, "이 과정을 거쳐야 품질이 완성된다"는 메시지를 전달합니다.

## 아이콘 및 그래픽
1. **산출물 검토**: 문서 아이콘 + 체크마크(✔️). "승인" 도장 느낌.
2. **코드 리뷰**: 코드 브래킷 `< >` + 사람 아이콘. "동료 검토" 느낌.
3. **정적 분석**: 돋보기 또는 스캔 아이콘. "자동화 분석" 느낌.

## 레이아웃 구성
- 좌측: 큰 아이콘 및 제목 ("코드 리뷰").
- 중앙: 핵심 문구 ("GitHub PR 필수").
- 우측: 세부 설명 또는 효과.
- 각 행을 둥근 박스로 감싸고, 위에서 아래로 화살표가 내려오며 "순차적 품질 확보"를 보여줍니다.""",

    17: """## 디자인: Risk Matrix Cards
- 4개의 리스크를 카드 형태로 보여주되, **신호등(Traffic Light)** 컬러 시스템을 적용하여 경각심을 줍니다.

## 리스크 카드 디자인
- 헤더: 리스크 등급에 따른 컬러 바 적용.
    - **상(High)**: Red/Coral 컬러 (#FF6B6B). (요구사항 변경, 일정 지연, 인력 이탈)
    - **중(Medium)**: Orange/Yellow 컬러 (#FFD93D). (기술적 난제)
- 아이콘: 각 리스크의 성격을 대변하는 경고 스타일 아이콘.
- 내용 배치:
    1. 리스크명 (Bold)
    2. 영향도/확률 그래프 (작은 Bar Chart로 시각화: High는 가득 찬 바, Medium은 절반)
    3. 대응 방안 (Highlight Box: "CCB 통제", "PoC 선행" 등 핵심 단어 배경색 처리)

## 전체 조화
- 슬라이드 제목 옆에 "사전 대응 원칙" 같은 문구를 작게 넣어 리스크 관리의 능동성을 강조합니다.
- 4개 카드를 2x2 그리드보다는 1x4 수평 배치로 깔끔하게 정리하되, '상' 등급 카드를 시각적으로 조금 더 앞으로 튀어나오게(Scale 1.05) 처리할 수도 있습니다.""",

    18: """## 디자인: Communication Rhythm
- 회의 체계를 "주기(Cycle)"와 "리듬"으로 표현합니다.
- 달력/시계 메타포를 활용하여 정기적인 소통을 시각화.

## 섹션 구성
1. **일일(Daily)**:
   - 아이콘: 해(Sun) 또는 아침 시계(9:30).
   - 스타일: 작고 빠른 순환을 의미하는 얇은 원형 화살표.
   - 키워드: "신속 공유", "블로커 해결".

2. **주간(Weekly)**:
   - 아이콘: 달력(Calendar)의 한 주.
   - 스타일: 안정적인 사각형 프레임.
   - 키워드: "진척 관리", "이슈 해결".

3. **스프린트(Sprint/Bi-weekly)**:
   - 아이콘: 순환 루프(Loop) 또는 데모 화면.
   - 스타일: 역동적인 점선 테두리.
   - 키워드: "피드백", "데모".

## 레이아웃
- 3가지 카드를 수평 배치하되, 서로 연결된 고리처럼 디자인하여 "끊임없는 소통"을 표현합니다.
- 하단에 "협조 요청 사항"을 띠지(Banner) 형태로 얇게 배치하여, "성공적인 소통을 위한 전제조건"으로 보여줍니다.""",

    19: """## 디자인: Closing & Contact
- 마지막 인상을 남기는 슬라이드. Cover Slide와 수미상관(Mirroring) 구조.
- 배경: Deep Green 풀 배경 또는 Cover와 동일한 패턴.

## 콘텐츠 배치
- 중앙: "감사합니다" (Thank You) - Bold 48pt, White.
- 하단 중앙: Q&A - Regular 24pt, Mint.
- 연락처 정보:
    - PM 김철수 / 010-1234-5678 / cs.kim@techsol.com
    - 아이콘(전화, 메일)을 사용하여 깔끔하게 가로로 나열.
- 로고: 하단 중앙 또는 우측 하단에 테크솔루션/글로벌물류 로고 배치.
- 마무리 그래픽: 우측 상단이나 좌측 하단에 "성공적 완료"를 암시하는 체크마크나 상승하는 그래프 등의 은유적 그래픽을 투명하게 배치."""
}

input_file = "working/ppt-20260112-123607/session-gemini.yaml"
output_file = "working/ppt-20260112-123607/session-gemini.yaml"

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
current_slide_number = None

for line in lines:
    stripped = line.strip()
    
    # Identify slide number
    if "- slide_number:" in stripped:
        try:
            current_slide_number = int(stripped.split(":")[1].strip())
        except ValueError:
            current_slide_number = None
    
    # Identify content block start and inject design_description before it
    if stripped.startswith("content:") and current_slide_number in DESIGNS:
        # Get indentation of the content line to match it
        indent = line[:line.find("content:")]
        
        # Prepare description block with proper indentation
        desc = DESIGNS[current_slide_number]
        formatted_desc = f"{indent}design_description: |\n"
        for desc_line in desc.split('\n'):
            formatted_desc += f"{indent}  {desc_line}\n"
            
        new_lines.append(formatted_desc)
        # We don't remove current_slide_number from dict to allow multiple passes if needed, 
        # but logically we are done for this slide.
        # current_slide_number = None # Keep it valid until next slide number parsing
    
    new_lines.append(line)

with open(output_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Successfully injected design descriptions for {len(DESIGNS)} slides.")
