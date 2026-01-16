# PPTX 변환 도구

PowerPoint(PPTX) 파일을 HTML, PNG로 변환하는 도구입니다.

## 폴더 구조

```
ppt2html/
├── PPTXjs/              # 원본 PPTXjs 라이브러리 (https://github.com/meshesha/PPTXjs)
│   ├── css/             # 스타일시트
│   ├── js/              # JavaScript 파일
│   ├── index.html       # 원본 데모 페이지
│   └── Sample_12.pptx   # 샘플 파일
├── pptxjs-cli/          # CLI 변환 도구
│   ├── extract.js       # 메인 추출 스크립트
│   └── package.json     # 의존성
├── auto-save.html       # 웹 기반 자동 저장 페이지
└── README.md            # 이 파일
```

---

## PPTXjs 설치

PPTXjs 라이브러리를 프로젝트에 설치합니다.

### Git Clone

```bash
cd ppt2html
git clone https://github.com/meshesha/PPTXjs.git
```

### 수동 다운로드

1. [PPTXjs GitHub](https://github.com/meshesha/PPTXjs.git)에서 ZIP 다운로드
2. 압축 해제 후 `PPTXjs/` 폴더를 `ppt2html/` 디렉토리에 배치

### 필수 파일 구조

설치 후 다음 파일들이 있어야 합니다:

```
PPTXjs/
├── css/
│   └── pptxjs.css
├── js/
│   ├── pptxjs.js
│   ├── divs2slides.js
│   └── ...
└── index.html
```

---

## pptxjs-cli 사용법

### 설치

#### 요구사항

- Node.js 18 이상
- npm

#### 의존성 설치

```bash
cd pptxjs-cli
npm install
```

### 기본 사용법

```bash
node extract.js <PPTX파일경로> [출력폴더] [옵션]
```

#### 인자 설명

| 인자             | 필수 | 설명                                   |
| ---------------- | ---- | -------------------------------------- |
| `<PPTX파일경로>` | O    | 변환할 PPTX 파일 경로 (절대/상대 경로) |
| `[출력폴더]`     | X    | 결과물 저장 폴더 (기본값: `./output`)  |
| `[옵션]`         | X    | 추가 옵션 (아래 참조)                  |

#### 옵션

| 옵션      | 설명                                                 |
| --------- | ---------------------------------------------------- |
| `--debug` | 디버그 모드 활성화 (브라우저 창 표시, DevTools 열림) |

### 사용 예시

```bash
# 기본 사용 - 현재 폴더의 output에 저장
node extract.js ../PPTXjs/Sample_12.pptx

# 출력 폴더 지정
node extract.js ../PPTXjs/Sample_12.pptx ./my-output

# 절대 경로 사용
node extract.js "C:/Users/user/Documents/프레젠테이션.pptx" ./output

# 한글 파일명
node extract.js "../PPTXjs/깔끔이 딥그린.pptx" ./output

# 디버그 모드 (브라우저 창에서 결과 확인 가능)
node extract.js ../PPTXjs/Sample_12.pptx ./output --debug
```

### 출력 결과

변환이 완료되면 출력 폴더에 다음 파일들이 생성됩니다:

```
output/
├── 파일명(전체).html       # 모든 슬라이드가 포함된 전체 HTML
├── 파일명_slide1.html      # 슬라이드 1 개별 HTML
├── 파일명_slide2.html      # 슬라이드 2 개별 HTML
├── ...
├── 파일명_slideN.html      # 슬라이드 N 개별 HTML
├── 파일명_slide1.png       # 슬라이드 1 PNG 이미지
├── 파일명_slide2.png       # 슬라이드 2 PNG 이미지
├── ...
└── 파일명_slideN.png       # 슬라이드 N PNG 이미지
```

#### 출력 파일 설명

| 파일 형식            | 설명                                                           |
| -------------------- | -------------------------------------------------------------- |
| `파일명(전체).html`  | 모든 슬라이드를 세로로 나열한 단일 HTML 파일. CSS 인라인 포함. |
| `파일명_slideN.html` | 각 슬라이드별 독립 HTML 파일. 개별 공유/편집에 적합.           |
| `파일명_slideN.png`  | 각 슬라이드의 PNG 스크린샷. 고화질 이미지.                     |

### 디버그 모드

`--debug` 옵션을 사용하면:

1. Puppeteer 브라우저가 헤드리스 모드 대신 실제 창으로 열림
2. Chrome DevTools 자동 열림
3. 변환 결과를 브라우저에서 직접 확인 가능
4. 콘솔에 슬라이드별 SVG/Drawing 요소 정보 출력
5. Enter 키를 눌러야 다음 단계로 진행

```bash
node extract.js ../PPTXjs/Sample_12.pptx ./output --debug
```

디버그 모드 출력 예시:

```
슬라이드별 SVG/Drawing 요소:
  슬라이드 1: SVG 3개, Drawing 2개
  슬라이드 2: SVG 5개, Drawing 0개
  ...

전체 SVG: 18개, 슬라이드 내부: 18개

========================================
디버그 모드: 브라우저에서 결과를 확인하세요.
계속하려면 Enter 키를 누르세요...
========================================
```

### 주의사항

1. **포트 사용**: 변환 시 내부적으로 HTTP 서버(포트 9999)를 사용합니다. 포트가 사용 중이면 오류가 발생합니다.

2. **메모리**: 큰 PPTX 파일(50+ 슬라이드)은 메모리를 많이 사용할 수 있습니다.

3. **타임아웃**: 변환에 최대 2분이 소요될 수 있습니다. 복잡한 슬라이드는 더 오래 걸릴 수 있습니다.

4. **한글 경로**: 한글이 포함된 파일 경로도 정상 지원됩니다.

---

## 웹 인터페이스 사용법

브라우저에서 파일을 선택하고 다운로드합니다.

### 실행 방법

1. VS Code에서 `auto-save.html` 우클릭 → **Open with Live Server**
2. 또는 로컬 웹 서버로 `auto-save.html` 열기

### 사용 방법

1. PPTX 파일 선택
2. 변환 완료 대기 (진행률 표시)
3. 원하는 형식으로 다운로드

### 다운로드 옵션

| 버튼                | 설명                               |
| ------------------- | ---------------------------------- |
| HTML 전체 저장      | 모든 슬라이드를 하나의 HTML 파일로 |
| HTML 개별 저장      | 각 슬라이드를 개별 HTML 파일로     |
| PNG 개별 저장       | 각 슬라이드를 개별 PNG 파일로      |
| PNG 전체 저장 (ZIP) | 모든 PNG를 ZIP 파일로              |

---

## 지원 기능

- 텍스트 (서식, 정렬, 글꼴)
- 도형 (사각형, 원, 화살표 등)
- 이미지 (PNG, JPG, GIF)
- 테이블
- 다이어그램 (SmartArt 일부)
- 테마/스타일 적용
- 다중 슬라이드 처리
- 배경 이미지/색상

## 제한 사항

| 기능          | 지원 여부 | 비고                               |
| ------------- | --------- | ---------------------------------- |
| 차트 (Chart)  | 부분 지원 | nvd3 라이브러리로 일부 차트 렌더링 |
| SmartArt      | 부분 지원 | 기본 도형으로 변환                 |
| 애니메이션    | 미지원    | 정적 이미지로만 변환               |
| 동영상/오디오 | 미지원    |                                    |
| 3D 효과       | 미지원    |                                    |
| 그라데이션    | 지원      |                                    |
| 투명도        | 지원      |                                    |

---

## 문제 해결

### 포트 사용 중 오류

```
오류: listen EADDRINUSE: address already in use 127.0.0.1:9999
```

**해결**: 기존 프로세스 종료 후 재시도

```bash
# Windows
netstat -aon | findstr :9999
taskkill /F /PID <PID번호>

# Mac/Linux
lsof -i :9999
kill -9 <PID>
```

### 브라우저 실행 오류

```
Error: Failed to launch browser
```

**해결**: Puppeteer 재설치

```bash
cd pptxjs-cli
npm uninstall puppeteer
npm install puppeteer
```

### 한글 깨짐

HTML 파일에서 한글이 깨지는 경우, 브라우저에서 인코딩을 UTF-8로 설정하세요.
생성된 HTML은 `<meta charset="utf-8">`을 포함합니다.

---

## 라이선스

- PPTXjs 원본: MIT License (https://github.com/meshesha/PPTXjs)
