# style-extract 워크플로우

이미지 또는 PPTX에서 테마(색상, 폰트) 추출.

## 트리거

- "이 이미지 스타일로"
- "색상 팔레트 추출해줘"
- "이 PPT 테마로"

## 입력

- 이미지 파일 (.png, .jpg, .webp)
- 또는 PPTX 파일

## 출력

- `templates/themes/{theme_id}/theme.yaml`

## 프로세스

### A. PPTX에서 추출

```bash
python scripts/style-extractor.py input.pptx --output templates/themes/new-theme/theme.yaml
```

자동 추출:
1. `ppt/theme/theme1.xml` 파싱
2. 색상 스킴 (`<a:clrScheme>`) 추출
3. 폰트 스킴 (`<a:fontScheme>`) 추출

### B. 이미지에서 추출

```bash
python scripts/image-vectorizer.py reference.png --output templates/themes/new-theme/theme.yaml
```

또는 직접:

```bash
python scripts/style-extractor.py reference.png --output templates/themes/new-theme/theme.yaml
```

분석 과정:
1. K-means 클러스터링으로 주요 색상 8개 추출
2. 색상 역할 자동 분류:
   - 가장 밝은 색 → background
   - 가장 어두운 색 → text
   - 채도 높은 색 → primary, accent
3. 레이아웃/스타일 힌트 추출

## 출력 스키마

```yaml
id: deepgreen
name: "딥그린 테마"

colors:
  primary: "#1a5f4a"      # 주요 색상
  secondary: "#2d7a5e"    # 보조 색상
  accent: "#4a9d7f"       # 강조 색상
  background: "#f5f9f7"   # 배경색
  surface: "#ffffff"      # 표면색 (카드 등)
  text: "#1a1a1a"        # 텍스트색
  muted: "#6b7c74"       # 비활성 텍스트

fonts:
  major: "Pretendard"     # 제목용
  minor: "Pretendard"     # 본문용

style_hints:
  border_radius: "16px"   # 모서리 둥글기
  shadow: "0 4px 12px rgba(0,0,0,0.08)"
```

## 추가 분석 (--analyze-only)

```bash
python scripts/image-vectorizer.py reference.png --analyze-only
```

출력:
```json
{
  "colors": [
    {"hex": "#1a5f4a", "percentage": 25.3, "role": "primary"},
    {"hex": "#ffffff", "percentage": 40.1, "role": "background"},
    ...
  ],
  "layout": {
    "type": "grid",
    "columns": 3
  },
  "style": {
    "mood": "modern",
    "has_shadows": true
  },
  "dominant_hue": "cool",
  "contrast_level": "high"
}
```

## 폰트 처리

추출된 폰트가 시스템에 없을 경우:

```bash
python scripts/font-manager.py resolve "Pretendard"
```

대체 순서:
1. 시스템 확인
2. 대체 폰트 매핑 (font-mappings.yaml)
3. 기본 폰트 (맑은 고딕 / Arial)

## 테마 썸네일

테마 미리보기용 색상 팔레트 이미지 자동 생성:

```
templates/thumbnails/themes/{theme_id}.png
```

320x180 크기로 색상 팔레트 시각화.
