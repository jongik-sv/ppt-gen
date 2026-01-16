# 깔끔이 딥그린 표지 (Cover Deep Green 01)

## Quick Start

This is a professional corporate cover slide template extracted from `깔끔이-딥그린.pptx`.

### Files

- **template.yaml** - Complete template metadata and configuration
- **template.html** - Handlebars template for rendering
- **example.html** - Ready-to-use example with sample data
- **EXTRACTION_REPORT.md** - Detailed technical specifications

### Placeholders

The template supports 4 main content areas:

```
{{label}}            # Top label (required)
{{title}}            # Main title (required)
{{description}}      # Description text (optional)
{{presenter}}        # Presenter information (optional)
```

### Example Usage

#### With Handlebars.js

```javascript
const template = Handlebars.compile(templateHtml);
const result = template({
  label: "2024년 Q1 평가보고회",
  title: "사업 성과 보고서",
  description: "분기별 성과 요약...",
  presenter: "부서명 이름 직급"
});
```

#### Static HTML

Open `example.html` in a browser for immediate preview.

### Customization

All styling is in the `<style>` section of template.html:

**Colors**
- Deep Green: `#22523B` (Primary)
- Dark Green: `#153325` (Accent)
- Light Gray: `#666666` (Secondary text)

**Fonts**
- Label: 코트라 볼드체 (18pt)
- Title: 코트라 볼드체 (44pt)
- Description: 나눔바른펜 (12pt)
- Presenter: 카페24 써라운드 (16pt)

### Layout Structure

```
┌─────────────────────────────────────┐
│  Label (Deep Green Background)      │  7.2%
├─────────────────────────────────────┤
│                                     │
│     Main Title (44pt Bold)          │  28.4%
│                                     │
│     Description Text (12pt)         │  45.5%
│     Multi-line supported            │
│                                     │
│  ▼ (Triangle Accent)               │  71.9%
│     Presenter Info (16pt)          │  80.5%
│                                     │
└─────────────────────────────────────┘
```

### Specifications

| Property | Value |
|----------|-------|
| **Canvas Size** | 1920×1080px (16:9) |
| **Quality Score** | 8.5/10 |
| **Type** | Professional Corporate |
| **Theme** | Deep Green |
| **Language** | Korean (한글) |
| **Status** | Production Ready |

### Content Guidelines

- **Label:** 10-30 characters (company/event name)
- **Title:** 10-40 characters (main topic)
- **Description:** 200-500 characters (supporting text, multi-line OK)
- **Presenter:** 10-50 characters (name and title)

### Use Cases

1. Company quarterly performance reports
2. Executive board presentations
3. Corporate compliance training
4. Company policy announcements
5. Business development pitches
6. Official company presentations

### Browser Support

- Chrome, Firefox, Safari, Edge (latest versions)
- Responsive scaling to different resolutions
- Mobile devices compatible (with CSS scaling)

### Font Requirements

Install these fonts for accurate rendering:

- 코트라 볼드체 (Koritra Bold)
- 나눔바른펜 (Nanum Barun Pen)
- 카페24 써라운드 (Cafe24 Surround)

Fallback to system sans-serif if unavailable.

### Integration

To integrate with your PPT generation pipeline:

1. Copy this directory to your templates/contents/cover/ path
2. Load template.yaml for metadata
3. Use template.html with your template engine
4. Reference the thumbnail for preview

### Generated From

**Source:** ppt-sample/깔끔이-딥그린.pptx (Slide 1)
**Extraction Date:** 2026-01-16
**Template ID:** cover-deep-green-01

### Notes

- All text areas are centered aligned
- Decorative lines and accent elements are non-editable
- Supports Korean text wrapping and line breaking
- CSS Grid-based responsive layout

---

For detailed technical specifications, see **EXTRACTION_REPORT.md**

For template configuration, see **template.yaml**

For live preview, open **example.html** in your browser
