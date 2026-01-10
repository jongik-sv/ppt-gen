# Color Palettes

PPT 생성에 사용할 수 있는 색상 팔레트 모음.

---

## 색상 표기 규칙

### PowerPoint 호환 형식

```javascript
// 올바른 표기 (# 제외)
color: "FF0000"      // O
chartColors: ["4472C4", "ED7D31"]  // O

// 잘못된 표기
color: "#FF0000"     // X (파일 손상 가능)
```

### RGB → HEX 변환

```
rgb(255, 0, 0)     → FF0000
rgba(0, 0, 0, 0.5) → 000000 + transparency: 50
```

---

## 브랜드 팔레트

### 동국그룹

```yaml
Primary:    002452    # 네이비 (제목, 강조)
Secondary:  C51F2A    # 레드 (포인트, CTA)
Dark Text:  262626    # 진회색 (본문)
Light Bg:   FFFFFF    # 흰색 (배경)
Gray:       B6B6B6    # 회색 (구분선, 비활성)

Accents:
  - 757575    # 중간 회색
  - 4B6580    # 청회색
  - B7D0D4    # 연청록
  - D55633    # 주황-빨강
  - E9B86E    # 금색

Chart Sequence:
  - 002452
  - C51F2A
  - 4B6580
  - D55633
  - E9B86E
```

---

## 범용 팔레트

### 1. Classic Blue
**특성**: 전문성, 신뢰, 기업

```yaml
Primary:    1C2833    # 진남색
Secondary:  2E4053    # 청회색
Accent:     AAB7B8    # 연회색
Background: F8F9FA    # 밝은 배경
Text:       1C2833    # 진남색

Chart: [1C2833, 2E4053, 5D6D7E, AAB7B8]
```

### 2. Teal & Coral
**특성**: 현대적, 균형, 활력

```yaml
Primary:    5EA8A7    # 틸
Secondary:  FE4447    # 코랄
Accent:     F8B500    # 옐로우
Background: FFFFFF    # 흰색
Text:       2D3436    # 진회색

Chart: [5EA8A7, FE4447, F8B500, 2D3436]
```

### 3. Bold Red
**특성**: 에너지, 열정, 긴급

```yaml
Primary:    C0392B    # 딥레드
Secondary:  E74C3C    # 레드
Accent:     F39C12    # 오렌지
Background: FFFFFF    # 흰색
Text:       2C3E50    # 진회색

Chart: [C0392B, E74C3C, F39C12, ECF0F1]
```

### 4. Warm Blush
**특성**: 따뜻함, 우아함, 부드러움

```yaml
Primary:    A49393    # 웜그레이
Secondary:  EED6D3    # 블러시
Accent:     E8B4B8    # 핑크
Background: FDF6F6    # 연한 핑크
Text:       5D4E4E    # 브라운그레이

Chart: [A49393, E8B4B8, EED6D3, 5D4E4E]
```

### 5. Burgundy Luxury
**특성**: 고급스러움, 권위, 클래식

```yaml
Primary:    5D1D2E    # 버건디
Secondary:  951233    # 와인
Accent:     C15937    # 테라코타
Background: FBF7F4    # 크림
Text:       2D2D2D    # 진회색

Chart: [5D1D2E, 951233, C15937, A67B5B]
```

### 6. Deep Purple & Emerald
**특성**: 신비, 창의, 안정

```yaml
Primary:    B165FB    # 퍼플
Secondary:  181B24    # 진회색
Accent:     40695B    # 에메랄드
Background: F5F5F7    # 연회색
Text:       181B24    # 진회색

Chart: [B165FB, 40695B, 181B24, 9B7BCC]
```

### 7. Cream & Forest Green
**특성**: 자연, 조화, 친환경

```yaml
Primary:    40695B    # 포레스트그린
Secondary:  FFE1C7    # 크림
Accent:     8FBC8F    # 세이지
Background: FFFEF7    # 아이보리
Text:       2F4F4F    # 다크슬레이트

Chart: [40695B, 8FBC8F, FFE1C7, 2F4F4F]
```

### 8. Pink & Purple
**특성**: 활기, 창의, 젊음

```yaml
Primary:    F8275B    # 핫핑크
Secondary:  FF574A    # 코랄레드
Accent:     3D2F68    # 딥퍼플
Background: FFFFFF    # 흰색
Text:       2D2D2D    # 진회색

Chart: [F8275B, FF574A, 3D2F68, FFB6C1]
```

### 9. Lime & Plum
**특성**: 신선, 대비, 독특

```yaml
Primary:    C5DE82    # 라임
Secondary:  7C3A5F    # 플럼
Accent:     FD8C6E    # 피치
Background: FAFAFA    # 연회색
Text:       3D3D3D    # 진회색

Chart: [C5DE82, 7C3A5F, FD8C6E, A8D08D]
```

### 10. Black & Gold
**특성**: 권위, 프리미엄, 격식

```yaml
Primary:    000000    # 블랙
Secondary:  BF9A4A    # 골드
Accent:     8B7355    # 브론즈
Background: F4F6F6    # 연회색
Text:       000000    # 블랙

Chart: [BF9A4A, 000000, 8B7355, D4AF37]
```

### 11. Sage & Terracotta
**특성**: 자연, 따뜻함, 균형

```yaml
Primary:    87A96B    # 세이지
Secondary:  E07A5F    # 테라코타
Accent:     F4F1DE    # 크림
Background: FDFCF8    # 아이보리
Text:       3D405B    # 네이비그레이

Chart: [87A96B, E07A5F, F2CC8F, 3D405B]
```

### 12. Charcoal & Red
**특성**: 강렬, 현대적, 대비

```yaml
Primary:    292929    # 차콜
Secondary:  E33737    # 레드
Accent:     CCCBCB    # 실버그레이
Background: FFFFFF    # 흰색
Text:       292929    # 차콜

Chart: [E33737, 292929, CCCBCB, FF6B6B]
```

### 13. Vibrant Orange
**특성**: 활력, 친근, 에너지

```yaml
Primary:    F96D00    # 오렌지
Secondary:  222831    # 진회색
Accent:     F2F2F2    # 연회색
Background: FFFFFF    # 흰색
Text:       222831    # 진회색

Chart: [F96D00, 222831, FFB347, F2F2F2]
```

### 14. Forest Green
**특성**: 성장, 안정, 자연

```yaml
Primary:    4E9F3D    # 그린
Secondary:  1E5128    # 다크그린
Accent:     D8E9A8    # 라이트그린
Background: 191A19    # 다크배경 or FFFFFF
Text:       191A19    # 진회색

Chart: [4E9F3D, 1E5128, D8E9A8, 7BC74D]
```

### 15. Retro Rainbow
**특성**: 창의, 다양, 레트로

```yaml
Primary:    722880    # 퍼플
Secondary:  D72D51    # 레드
Accent1:    EB5C18    # 오렌지
Accent2:    F08800    # 옐로우오렌지
Background: FFFFFF    # 흰색
Text:       333333    # 진회색

Chart: [722880, D72D51, EB5C18, F08800]
```

### 16. Vintage Earthy
**특성**: 따뜻함, 빈티지, 자연

```yaml
Primary:    E3B448    # 머스타드
Secondary:  CBD18F    # 올리브
Accent:     3A6B35    # 포레스트
Background: FAF8F0    # 크림
Text:       3A3A3A    # 진회색

Chart: [E3B448, 3A6B35, CBD18F, 8B4513]
```

### 17. Coastal Rose
**특성**: 우아, 부드러움, 해안

```yaml
Primary:    AD7670    # 더스티로즈
Secondary:  B49886    # 토프
Accent:     F3ECDC    # 크림
Background: FFFFFF    # 흰색
Text:       4A4A4A    # 진회색

Chart: [AD7670, B49886, D4A5A5, 8B7D6B]
```

### 18. Orange & Turquoise
**특성**: 균형, 현대, 에너지

```yaml
Primary:    FC993E    # 오렌지
Secondary:  667C6F    # 세이지그린
Accent:     40E0D0    # 터쿼이즈
Background: FCFCFC    # 흰색
Text:       333333    # 진회색

Chart: [FC993E, 667C6F, 40E0D0, FFB366]
```

---

## 팔레트 선택 가이드

### 산업별 권장

| 산업 | 권장 팔레트 |
|------|------------|
| 금융/컨설팅 | Classic Blue, Black & Gold |
| 기술/IT | Teal & Coral, Deep Purple & Emerald |
| 헬스케어 | Sage & Terracotta, Cream & Forest Green |
| 교육 | Vibrant Orange, Forest Green |
| 패션/뷰티 | Warm Blush, Coastal Rose |
| 제조/건설 | Charcoal & Red, Bold Red |
| 친환경/ESG | Forest Green, Sage & Terracotta |

### 무드별 권장

| 무드 | 권장 팔레트 |
|------|------------|
| 전문적/신뢰 | Classic Blue, Black & Gold |
| 활기/에너지 | Bold Red, Vibrant Orange |
| 따뜻함/친근 | Warm Blush, Vintage Earthy |
| 고급/프리미엄 | Burgundy Luxury, Black & Gold |
| 창의/혁신 | Pink & Purple, Retro Rainbow |
| 자연/지속가능 | Forest Green, Sage & Terracotta |

---

## 색상 조합 규칙

### 3색 조합 (권장)

```
Primary (60%) - 주요 색상
Secondary (30%) - 보조 색상
Accent (10%) - 강조 색상
```

### 5색 조합 (최대)

```
Primary (40%)
Secondary (25%)
Tertiary (15%)
Accent1 (10%)
Accent2 (10%)
```

### 대비 확인

```
밝은 배경 + 어두운 텍스트: 권장
어두운 배경 + 밝은 텍스트: 최소 4.5:1 대비

도구: https://webaim.org/resources/contrastchecker/
```

---

## 차트 색상 시퀀스

### 기본 시퀀스 (4색)

```javascript
// 범용
chartColors: ['4472C4', 'ED7D31', 'A5A5A5', 'FFC000']

// 동국그룹
chartColors: ['002452', 'C51F2A', '4B6580', 'E9B86E']
```

### 단일 강조

```javascript
// 세 번째 항목만 강조
chartColors: ['E0E0E0', 'E0E0E0', '4472C4', 'E0E0E0']
```

### 그라데이션 (같은 색 계열)

```javascript
// 블루 그라데이션
chartColors: ['1C4587', '3D85C6', '6FA8DC', 'A4C2F4']

// 그린 그라데이션
chartColors: ['1E5128', '4E9F3D', '7BC74D', 'D8E9A8']
```

### 긍정/부정 색상

```javascript
// 증가/감소
positiveColor: '00B050'  // 초록
negativeColor: 'FF0000'  // 빨강

// 장/단점
prosColor: '00B050'      // 초록
consColor: 'C00000'      // 어두운 빨강
```

---

## Quick Reference

### 자주 사용하는 색상

| 용도 | HEX |
|------|-----|
| 긍정/증가 | 00B050 |
| 부정/감소 | FF0000 |
| 중립/회색 | A5A5A5 |
| 링크 | 0563C1 |
| 경고 | FFC000 |
| 정보 | 00B0F0 |
| 흰색 텍스트 | FFFFFF |
| 검정 텍스트 | 000000 |
| 진회색 텍스트 | 333333 |

### 배경색

| 용도 | HEX |
|------|-----|
| 흰색 | FFFFFF |
| 연회색 | F5F5F5 |
| 크림 | FFFEF7 |
| 다크 | 1A1A1A |
