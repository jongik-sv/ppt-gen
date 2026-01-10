---
name: plan:ui_theme
description: "외부 사이트 UI/UX 테마 추출 및 프로젝트 적용 가이드 생성"
category: analysis
complexity: complex
wave-enabled: true
performance-profile: optimization
auto-flags:
  - --wave-mode force
  - --wave-strategy systematic
  - --seq
  - --play
  - --c7
  - --validate
mcp-servers: [sequential, playwright, context7]
personas: [analyzer, frontend, architect]
allowed-tools: [WebFetch, Read, Write, Glob, Grep, TodoWrite, Bash]
---

# /plan:ui_theme - UI/UX 테마 추출 시스템

> **목적**: 외부 사이트의 UI/UX 디자인 요소를 분석하여 현재 프로젝트의 기술 스택에 맞는 테마 가이드를 생성합니다.

## 트리거
- 참고할 외부 사이트의 디자인 시스템 분석 필요
- SaaS/프로젝트 관리 도구의 UX/UI 패턴 연구
- 커스텀 테마 생성 및 적용 가이드 작성

## 사용법
```bash
/plan:ui_theme "https://example.com/dashboard"
/plan:ui_theme "https://linear.app" --theme dark
/plan:ui_theme "https://notion.so" --theme light --focus "project-management"
```

### 옵션

| 옵션 | 설명 | 기본값 |
|-----|------|-------|
| `--theme` | 테마 타입 (dark, light, blue, custom 등) | `default` |
| `--focus` | 도메인별 분석 (project-management, dashboard, ecommerce) | - |
| `--analysis-depth` | 분석 깊이 (quick, normal, deep) | `normal` |

---

## 사전 준비: TRD 참조

> **중요**: 명령 실행 전 반드시 프로젝트의 TRD(기술 요구사항 정의서)를 확인합니다.

### TRD 탐색 순서
```
1. .orchay/{project}/orchay-trd.md
2. docs/trd.md
3. docs/technical-requirements.md
4. README.md의 기술 스택 섹션
```

### TRD에서 추출할 정보

| 항목 | TRD 섹션 | 추출 대상 |
|------|---------|----------|
| **프레임워크** | 핵심 기술 스택 | Vue/React/Angular/Svelte 등 |
| **CSS 프레임워크** | UI/스타일링 스택 | TailwindCSS/SCSS/styled-components 등 |
| **UI 컴포넌트 라이브러리** | UI/스타일링 스택 | PrimeVue/MUI/Vuetify/Chakra 등 |
| **테마 시스템** | 디자인 시스템 | CSS 변수/Preset 방식 |
| **컬러 팔레트** | 디자인 시스템 | Primary/Secondary/Semantic 색상 |

### 기술 스택별 산출물 맵핑

```yaml
# TRD 기반 동적 산출물 결정
vue_primevue_tailwind:
  theme_preset: "definePreset() 기반 프리셋"
  css_config: "tailwind.config.ts 확장"
  css_variables: "PrimeVue CSS 변수"

react_mui:
  theme_preset: "createTheme() 기반 테마"
  css_config: "MUI sx prop / styled()"
  css_variables: "CSS-in-JS 테마 토큰"

react_tailwind:
  theme_preset: "tailwind.config.js 확장"
  css_config: "Tailwind 유틸리티 클래스"
  css_variables: "CSS 커스텀 프로퍼티"

svelte_tailwind:
  theme_preset: "tailwind.config.js 확장"
  css_config: "Svelte 스타일 블록"
  css_variables: "CSS 커스텀 프로퍼티"
```

---

## Wave 자동 실행 플로우

### Wave 0: TRD 분석 및 스택 확인
**도구**: Read, Glob
**산출물**: 기술 스택 컨텍스트

**실행 단계**:
1. **TRD 파일 탐색**:
   - 프로젝트 내 TRD 문서 검색
   - 기술 스택 섹션 파싱
2. **스택 식별**:
   - 프레임워크 (Vue/React/Angular/Svelte)
   - CSS 솔루션 (Tailwind/SCSS/CSS-in-JS)
   - UI 라이브러리 (PrimeVue/MUI/Vuetify/Chakra/없음)
3. **산출물 형식 결정**:
   - 스택에 맞는 설정 파일 형식 선택
   - 컴포넌트 맵핑 테이블 구성

### Wave 1: 사이트 접근 및 스크린샷 수집
**MCP**: playwright
**산출물**: 멀티 뷰포트 스크린샷, DOM 구조

**실행 단계**:
1. **사이트 접근성 검증**:
   - Playwright로 URL 접근 확인
   - 로딩 완료 대기 (networkidle)
2. **스크린샷 캡처**:
   - 데스크톱: 1920x1080
   - 태블릿: 768x1024
   - 모바일: 375x667
3. **DOM 분석**:
   - 주요 컴포넌트 식별
   - CSS 변수 추출

### Wave 2: 디자인 토큰 추출
**MCP**: playwright + sequential
**산출물**: 색상 팔레트, 타이포그래피, 간격 시스템

**실행 단계**:
1. **색상 시스템**:
   - Primary/Secondary/Accent 컬러
   - Semantic 컬러 (success, warning, error, info)
   - 중성 컬러 (gray scale)
   - Surface/Background 컬러
2. **타이포그래피**:
   - 폰트 패밀리
   - 헤딩 스케일 (H1~H6)
   - 본문 텍스트 스타일
3. **간격 시스템**:
   - Spacing scale 추출
   - 컨테이너 너비
   - Grid 시스템

### Wave 3: 컴포넌트 패턴 분석
**MCP**: playwright + context7
**산출물**: UI 컴포넌트 스타일 가이드

**실행 단계**:
1. **기본 컴포넌트**:
   - 버튼 (variants, states)
   - 입력 필드 (text, select, checkbox)
   - 카드 컴포넌트
   - 네비게이션
2. **복합 컴포넌트**:
   - 데이터 테이블
   - 모달/다이얼로그
   - 드롭다운 메뉴
3. **상태 표현**:
   - Hover/Focus/Active
   - Loading/Disabled
   - 에러 상태

### Wave 4: 프로젝트 적용 가이드 생성
**MCP**: sequential + context7
**산출물**: 테마 설정 파일, 적용 가이드 문서

**실행 단계**:
1. **TRD 기반 설정 파일 생성**:
   - 프로젝트 스택에 맞는 형식으로 출력
   - 기존 테마 설정과 병합 가능한 구조
2. **컴포넌트 맵핑**:
   - 분석된 컴포넌트 → 프로젝트 UI 라이브러리 맵핑
3. **적용 가이드 문서 작성**

---

## 산출물 구조

> **산출물 위치 규칙**: 모든 산출물은 TRD 파일이 위치한 폴더에 생성됩니다.

### 산출물 경로 결정

```yaml
# TRD 위치에 따른 산출물 경로
trd_path: ".orchay/{project}/orchay-trd.md"
output_dir: ".orchay/{project}/"

trd_path: "docs/trd.md"
output_dir: "docs/"

trd_path: "docs/technical-requirements.md"
output_dir: "docs/"
```

### 파일명 규칙

| 산출물 | 파일명 패턴 | 예시 |
|-------|-----------|------|
| 적용 가이드 | `ui-theme-{theme-type}.md` | `ui-theme-dark.md` |
| 디자인 토큰 | `ui-theme-{theme-type}.json` | `ui-theme-dark.json` |
| 테마 설정 | `ui-theme-{theme-type}-preset.ts` | `ui-theme-dark-preset.ts` |

### 1. JSON 디자인 토큰
**위치**: `{trd-folder}/ui-theme-{theme-type}.json`

```json
{
  "metadata": {
    "source_url": "URL",
    "analysis_date": "YYYY-MM-DD",
    "target_stack": "{TRD에서 추출한 스택}"
  },
  "colors": {
    "primary": {
      "50": "#hex", "100": "#hex", "500": "#hex", "900": "#hex"
    },
    "secondary": {},
    "semantic": {
      "success": "#hex",
      "warning": "#hex",
      "error": "#hex",
      "info": "#hex"
    },
    "surface": {
      "ground": "#hex",
      "card": "#hex",
      "overlay": "#hex"
    }
  },
  "typography": {
    "fontFamily": {
      "sans": "font-name, sans-serif",
      "mono": "font-name, monospace"
    },
    "fontSize": {
      "xs": "0.75rem",
      "sm": "0.875rem",
      "base": "1rem",
      "lg": "1.125rem",
      "xl": "1.25rem"
    }
  },
  "spacing": {
    "scale": ["0.25rem", "0.5rem", "0.75rem", "1rem", "1.5rem", "2rem"],
    "container": {
      "sm": "640px",
      "md": "768px",
      "lg": "1024px",
      "xl": "1280px"
    }
  },
  "borderRadius": {
    "none": "0",
    "sm": "0.125rem",
    "md": "0.375rem",
    "lg": "0.5rem",
    "full": "9999px"
  },
  "shadows": {
    "sm": "box-shadow value",
    "md": "box-shadow value",
    "lg": "box-shadow value"
  }
}
```

### 2. 스택별 테마 설정 파일

#### TailwindCSS 프로젝트
**위치**: `{trd-folder}/ui-theme-{theme-type}-tailwind.ts`

```typescript
// tailwind.config.ts에 머지할 설정
export const themeExtend = {
  colors: {
    primary: {
      50: '#hex',
      // ...
    }
  },
  fontFamily: {
    sans: ['Font Name', 'sans-serif']
  }
}
```

#### PrimeVue 프로젝트
**위치**: `{trd-folder}/ui-theme-{theme-type}-preset.ts`

```typescript
import { definePreset } from '@primevue/themes';
import Aura from '@primevue/themes/aura';

export const CustomPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '{primary.50}',
      // ...
    }
  }
});
```

#### MUI (React) 프로젝트
**위치**: `{trd-folder}/ui-theme-{theme-type}-mui.ts`

```typescript
import { createTheme } from '@mui/material/styles';

export const customTheme = createTheme({
  palette: {
    primary: {
      main: '#hex',
      light: '#hex',
      dark: '#hex',
    }
  },
  typography: {
    fontFamily: 'Font Name, sans-serif',
  }
});
```

#### Vuetify 프로젝트
**위치**: `{trd-folder}/ui-theme-{theme-type}-vuetify.ts`

```typescript
export const customTheme = {
  dark: false,
  colors: {
    primary: '#hex',
    secondary: '#hex',
    success: '#hex',
    warning: '#hex',
    error: '#hex',
    info: '#hex',
  }
}
```

### 3. 적용 가이드 문서
**위치**: `{trd-folder}/ui-theme-{theme-type}.md`

**예시**:
- TRD가 `.orchay/myproject/orchay-trd.md`에 있고 `--theme dark` 옵션 사용 시
- 가이드 문서: `.orchay/myproject/ui-theme-dark.md`

**문서 구성**:
- 디자인 시스템 개요
- 색상 시스템 사용 가이드
- 타이포그래피 가이드
- 컴포넌트 스타일 가이드
- 프로젝트 적용 방법 (TRD 기반)
- 코드 예시

---

## 컴포넌트 맵핑 템플릿

> 분석된 UI 요소를 프로젝트의 UI 라이브러리에 맵핑합니다.

### PrimeVue 맵핑

| 분석 대상 | PrimeVue 컴포넌트 |
|----------|------------------|
| 버튼 | Button, SplitButton |
| 입력 필드 | InputText, InputNumber, Textarea |
| 선택 | Select, MultiSelect, Checkbox, RadioButton |
| 테이블 | DataTable |
| 카드 | Card, Panel |
| 모달 | Dialog |
| 메뉴 | Menu, Menubar, TieredMenu |
| 트리 | Tree, TreeTable |
| 태그 | Tag, Chip |
| 진행 | ProgressBar, ProgressSpinner |

### MUI 맵핑

| 분석 대상 | MUI 컴포넌트 |
|----------|-------------|
| 버튼 | Button, IconButton, ButtonGroup |
| 입력 필드 | TextField, Input |
| 선택 | Select, Autocomplete, Checkbox, Radio |
| 테이블 | Table, DataGrid |
| 카드 | Card, Paper |
| 모달 | Dialog, Modal |
| 메뉴 | Menu, AppBar |
| 트리 | TreeView |
| 태그 | Chip |
| 진행 | LinearProgress, CircularProgress |

### Vuetify 맵핑

| 분석 대상 | Vuetify 컴포넌트 |
|----------|-----------------|
| 버튼 | v-btn |
| 입력 필드 | v-text-field, v-textarea |
| 선택 | v-select, v-checkbox, v-radio |
| 테이블 | v-data-table |
| 카드 | v-card |
| 모달 | v-dialog |
| 메뉴 | v-menu, v-app-bar |
| 트리 | v-treeview |
| 태그 | v-chip |
| 진행 | v-progress-linear, v-progress-circular |

---

## 도메인별 분석 포인트 (선택적)

> `--focus` 옵션으로 특정 도메인에 맞는 분석을 수행합니다.

### 프로젝트 관리 도구 (`--focus project-management`)
```yaml
kanban_board:
  - 컬럼 스타일
  - 카드 디자인 및 드래그 인터랙션
  - 상태 표시 (badge, tag)

task_detail:
  - 폼 레이아웃
  - 문서 목록 표시
  - 탭 네비게이션

tree_view:
  - 트리 노드 스타일
  - 확장/축소 인터랙션
  - 계층 표시

timeline:
  - 타임라인 스타일
  - 바 컬러 (상태별)
  - 마일스톤 표시
```

### 대시보드 (`--focus dashboard`)
```yaml
metrics_card:
  - 숫자 표시 스타일
  - 트렌드 인디케이터
  - 아이콘 배치

charts:
  - 차트 컬러 팔레트
  - 레전드 스타일
  - 툴팁 디자인

data_table:
  - 헤더 스타일
  - 정렬/필터 UI
  - 페이지네이션
```

### E-commerce (`--focus ecommerce`)
```yaml
product_card:
  - 이미지 비율
  - 가격 표시
  - 뱃지 스타일

cart:
  - 아이템 리스트
  - 수량 조절 UI
  - 총액 표시

checkout:
  - 폼 레이아웃
  - 스텝 인디케이터
  - 결제 버튼
```

---

## 품질 검증

### 자동 검증 항목
- [ ] 색상 대비율 WCAG AA 준수 (4.5:1 이상)
- [ ] 폰트 크기 최소 14px 이상
- [ ] 터치 타겟 최소 44x44px
- [ ] UI 라이브러리 테마 변수 유효성

### 수동 검토 권장
- [ ] 브랜드 일관성
- [ ] 가독성 확인
- [ ] 반응형 레이아웃 테스트

---

## 예상 실행 시간
- **단순 사이트** (랜딩 페이지): 10-15분
- **중간 사이트** (SaaS 대시보드): 20-30분
- **복합 사이트** (엔터프라이즈): 35-50분

---

## 성공 조건
- TRD 기반 기술 스택 확인 완료
- `ui-theme-{theme-type}.json` 디자인 토큰 생성 완료
- `ui-theme-{theme-type}-*.ts` 스택별 설정 파일 생성
- `ui-theme-{theme-type}.md` 적용 가이드 문서 작성
- 모든 산출물이 TRD 폴더에 위치
- WCAG AA 색상 대비 준수

---

## 제한사항
- 로그인 필요 페이지는 분석 제한
- JavaScript 렌더링 콘텐츠는 로딩 후 분석
- 저작권 준수: 분석 목적으로만 사용, 디자인 복제 금지

<!--
Universal UI Theme Extract Command
Supports: Vue/React/Angular/Svelte + Any CSS Framework + Any UI Library
-->
