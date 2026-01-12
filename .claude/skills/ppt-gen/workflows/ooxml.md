# OOXML 직접 편집 워크플로우

PPTX 파일의 XML을 직접 편집하여 정밀 수정.

## 사용 시점

- 기존 PPT 수정
- 특정 요소만 변경
- 디자인 유지하며 텍스트 교체
- 애니메이션/전환 효과 유지

## 도구

```
lib/ooxml/scripts/
├── unpack.py      # PPTX → 폴더
├── pack.py        # 폴더 → PPTX
├── validate.py    # XML 검증
└── rearrange.py   # 슬라이드 재배열
```

## 기본 워크플로우

### 1. PPTX 언팩
```bash
python lib/ooxml/scripts/unpack.py input.pptx unpacked/
```

### 2. 구조 확인
```
unpacked/
├── [Content_Types].xml
├── _rels/
├── docProps/
└── ppt/
    ├── presentation.xml
    ├── slides/
    │   ├── slide1.xml
    │   ├── slide2.xml
    │   └── _rels/
    ├── slideMasters/
    ├── slideLayouts/
    ├── theme/
    └── media/
```

### 3. XML 편집

**슬라이드 텍스트 수정**:
```
ppt/slides/slide1.xml
```

**테마 색상 수정**:
```
ppt/theme/theme1.xml
```

**슬라이드 마스터 수정**:
```
ppt/slideMasters/slideMaster1.xml
```

### 4. 검증
```bash
python lib/ooxml/scripts/validate.py unpacked/ --original input.pptx
```

### 5. 재패킹
```bash
python lib/ooxml/scripts/pack.py unpacked/ output.pptx
```

## 주요 XML 구조

### 텍스트 요소
```xml
<p:sp>
  <p:txBody>
    <a:p>
      <a:r>
        <a:rPr lang="ko-KR" sz="1800" b="1"/>
        <a:t>텍스트 내용</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>
```

### 색상
```xml
<!-- 테마 색상 -->
<a:solidFill>
  <a:schemeClr val="accent1"/>
</a:solidFill>

<!-- RGB 색상 -->
<a:solidFill>
  <a:srgbClr val="22523B"/>
</a:solidFill>
```

### 위치/크기
```xml
<p:spPr>
  <a:xfrm>
    <a:off x="914400" y="914400"/>  <!-- EMU 단위 -->
    <a:ext cx="5486400" cy="3657600"/>
  </a:xfrm>
</p:spPr>
```

**EMU 변환**: 1인치 = 914400 EMU

## 슬라이드 재배열

```bash
python lib/ooxml/scripts/rearrange.py input.pptx output.pptx 0,3,5,3,7
```

- 0-based 인덱스
- 중복 허용 (슬라이드 복제)
- 순서 변경

## 일반적인 작업

### 텍스트 교체
1. `slide*.xml`에서 `<a:t>` 태그 찾기
2. 텍스트 내용 교체
3. 검증 및 패킹

### 이미지 교체
1. `ppt/media/`에서 이미지 교체
2. 같은 파일명, 같은 크기 권장
3. 관계 파일 수정 불필요

### 슬라이드 삭제
1. `ppt/slides/slide*.xml` 삭제
2. `ppt/_rels/presentation.xml.rels` 수정
3. `ppt/presentation.xml` 수정

### 슬라이드 복제
1. `slide*.xml` 복사
2. `_rels/slide*.xml.rels` 복사
3. 관계 파일 업데이트

## 주의사항

### XML 특수문자 이스케이프
```
& → &amp;
< → &lt;
> → &gt;
" → &quot;
' → &apos;
```

### 관계 파일 일관성
- 모든 리소스는 `.rels` 파일에 등록
- rId는 고유해야 함

### 검증 필수
- 편집 후 반드시 `validate.py` 실행
- PowerPoint에서 열어 확인
