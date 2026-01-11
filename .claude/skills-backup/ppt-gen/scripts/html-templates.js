/**
 * HTML Templates for PPT Content Design
 *
 * 콘텐츠 템플릿별 HTML 렌더러
 * - 템플릿 YAML의 shapes/geometry를 HTML로 변환
 * - 테마 색상 토큰을 CSS 변수로 변환
 * - html2pptx.js와 함께 사용
 *
 * v2.0: 템플릿 YAML 기반 렌더링 추가
 * - loadTemplate(): 템플릿 YAML 로드
 * - renderFromYaml(): shapes 배열을 HTML로 변환
 * - shape_source 타입별 처리 (ooxml, svg, html, description)
 *
 * Usage:
 *   const { renderTemplate, renderFromYaml } = require('./html-templates');
 *   // 방법 1: 템플릿 ID로 렌더링 (YAML 자동 로드)
 *   const html = await renderTemplate('timeline-horizontal', data, theme);
 *   // 방법 2: 로드된 템플릿으로 직접 렌더링
 *   const template = await loadTemplate('timeline-horizontal');
 *   const html = renderFromYaml(template, data, theme);
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// 캔버스 크기 (16:9, 720pt x 405pt)
const CANVAS = {
  width: 720,  // pt
  height: 405, // pt
};

/**
 * 템플릿 YAML 파일 로드
 * @param {string} templateId - 템플릿 ID (예: 'timeline-horizontal')
 * @param {string} basePath - 템플릿 기본 경로
 * @returns {object|null} 로드된 템플릿 객체 또는 null
 */
async function loadTemplate(templateId, basePath = null) {
  const templatesDir = basePath || path.resolve(__dirname, '../../../../templates/contents/templates');

  // 카테고리별 디렉토리 순회
  const categories = [
    'chart', 'closing', 'comparison', 'content', 'cover', 'cycle',
    'diagram', 'feature', 'flow', 'grid', 'hierarchy', 'matrix',
    'process', 'quote', 'roadmap', 'section', 'stats', 'table',
    'timeline', 'toc', 'funnel', 'infographic'
  ];

  for (const category of categories) {
    const templatePath = path.join(templatesDir, category, `${templateId}.yaml`);
    if (fs.existsSync(templatePath)) {
      try {
        const content = fs.readFileSync(templatePath, 'utf-8');
        const template = yaml.load(content);
        template._source_path = templatePath;
        template._category = category;
        return template;
      } catch (err) {
        console.error(`Error loading template ${templateId}:`, err.message);
        return null;
      }
    }
  }

  console.warn(`Template not found: ${templateId}`);
  return null;
}

/**
 * % 단위를 pt로 변환
 * @param {string|number} value - % 값 (예: '25%' 또는 25)
 * @param {string} axis - 'x' 또는 'y'
 * @returns {number} pt 값
 */
function percentToPt(value, axis) {
  const percent = typeof value === 'string' ? parseFloat(value) : value;
  const base = axis === 'x' || axis === 'cx' ? CANVAS.width : CANVAS.height;
  return (percent / 100) * base;
}

/**
 * 디자인 토큰을 테마 색상으로 치환
 * @param {string} token - 색상 토큰 (예: 'primary', 'accent')
 * @param {object} theme - 테마 색상 맵
 * @returns {string} 실제 색상값
 */
function resolveColorToken(token, theme) {
  if (!token) return 'transparent';
  if (token.startsWith('#')) return token;
  if (token.startsWith('rgb')) return token;
  return theme[token] || token;
}

/**
 * shape의 style을 CSS 문자열로 변환
 * @param {object} shape - shape 객체
 * @param {object} theme - 테마 색상
 * @returns {string} CSS 스타일 문자열
 */
function shapeStyleToCSS(shape, theme) {
  const styles = [];
  const { geometry, style } = shape;

  // 위치 및 크기
  if (geometry) {
    styles.push(`position: absolute`);
    if (geometry.x !== undefined) styles.push(`left: ${percentToPt(geometry.x, 'x')}pt`);
    if (geometry.y !== undefined) styles.push(`top: ${percentToPt(geometry.y, 'y')}pt`);
    if (geometry.cx !== undefined) styles.push(`width: ${percentToPt(geometry.cx, 'cx')}pt`);
    if (geometry.cy !== undefined) styles.push(`height: ${percentToPt(geometry.cy, 'cy')}pt`);
  }

  if (!style) return styles.join('; ');

  // 배경/채움
  if (style.fill) {
    if (style.fill.type === 'solid' && style.fill.color) {
      styles.push(`background: ${resolveColorToken(style.fill.color, theme)}`);
    } else if (style.fill.type === 'gradient' && style.fill.stops) {
      // 그라디언트는 solid 색상으로 대체 (html2pptx 제한)
      const firstStop = style.fill.stops[0];
      if (firstStop && firstStop.color) {
        styles.push(`background: ${resolveColorToken(firstStop.color, theme)}`);
      }
    }
  }

  // 테두리
  if (style.border) {
    const borderColor = resolveColorToken(style.border.color, theme) || '#000';
    const borderWidth = style.border.width || 1;
    styles.push(`border: ${borderWidth}pt solid ${borderColor}`);
  }

  // 둥근 모서리
  if (style.rounded_corners) {
    styles.push(`border-radius: ${style.rounded_corners}pt`);
  }

  // 그림자 (CSS box-shadow로 변환)
  if (style.shadow) {
    const shadowColor = 'rgba(0,0,0,0.2)';
    styles.push(`box-shadow: 2pt 2pt 4pt ${shadowColor}`);
  }

  return styles.join('; ');
}

/**
 * shape의 text를 HTML로 변환
 * @param {object} textDef - text 정의 객체
 * @param {object} theme - 테마 색상
 * @param {object} data - 바인딩 데이터
 * @param {number} sectionIndex - 섹션 인덱스 (섹션별 바인딩용)
 * @returns {string} HTML 텍스트 요소
 */
function renderTextContent(textDef, theme, data, sectionIndex = null) {
  if (!textDef) return '';

  // placeholders 배열 형식 처리 (YAML v4.0 형식)
  if (textDef.placeholders && Array.isArray(textDef.placeholders)) {
    return textDef.placeholders.map((placeholder, index) => {
      const styles = [];

      // 개별 placeholder 폰트 설정
      if (placeholder.font_size) styles.push(`font-size: ${placeholder.font_size}pt`);
      if (placeholder.font_weight || textDef.font_weight) {
        styles.push(`font-weight: ${placeholder.font_weight || textDef.font_weight}`);
      }
      if (placeholder.font_color || textDef.font_color) {
        styles.push(`color: ${resolveColorToken(placeholder.font_color || textDef.font_color, theme)}`);
      }
      if (textDef.alignment) styles.push(`text-align: ${textDef.alignment}`);

      // placeholder 텍스트 치환 (sectionIndex 전달)
      let content = placeholder.text || '';
      content = bindPlaceholders(content, data, sectionIndex);

      // 빈 placeholder는 기본 텍스트로
      if (content.match(/^\{\{.+\}\}$/)) {
        // 치환되지 않은 placeholder - 섹션별 키 먼저 시도
        const placeholderName = content.replace(/[{}]/g, '');
        if (sectionIndex !== null) {
          const indexedKey = `${placeholderName}_${sectionIndex}`;
          content = data[indexedKey] || data[placeholderName] || content;
        } else {
          content = data[placeholderName] || content;
        }
      }

      const styleStr = styles.length > 0 ? ` style="${styles.join('; ')}"` : '';
      return `<p${styleStr}>${escapeHtml(content)}</p>`;
    }).join('\n    ');
  }

  // content 배열 형식 처리 (OOXML 형식)
  if (textDef.content && Array.isArray(textDef.content)) {
    return textDef.content.map(line => {
      const content = bindPlaceholders(line, data, sectionIndex);
      return `<p>${escapeHtml(content)}</p>`;
    }).join('\n    ');
  }

  // 기존 단일 텍스트 형식
  const styles = [];

  // 폰트 설정
  if (textDef.font_size) styles.push(`font-size: ${textDef.font_size}pt`);
  if (textDef.font_weight) styles.push(`font-weight: ${textDef.font_weight}`);
  if (textDef.font_color) styles.push(`color: ${resolveColorToken(textDef.font_color, theme)}`);
  if (textDef.text_align || textDef.alignment) styles.push(`text-align: ${textDef.text_align || textDef.alignment}`);
  if (textDef.line_height) styles.push(`line-height: ${textDef.line_height}`);
  if (textDef.letter_spacing) styles.push(`letter-spacing: ${textDef.letter_spacing}`);

  // 텍스트 내용 (placeholder 치환, sectionIndex 전달)
  let content = textDef.content || textDef.placeholder || '';
  content = bindPlaceholders(content, data, sectionIndex);

  const styleStr = styles.length > 0 ? ` style="${styles.join('; ')}"` : '';
  return `<p${styleStr}>${escapeHtml(content)}</p>`;
}

/**
 * placeholder를 데이터로 치환 (섹션 인덱스 지원)
 * @param {string} text - 템플릿 텍스트 (예: '{{title}}')
 * @param {object} data - 바인딩 데이터
 * @param {number} sectionIndex - 섹션 인덱스 (선택)
 * @returns {string} 치환된 텍스트
 *
 * 키 검색 우선순위:
 * 1. `data['중제목_0']` (섹션별 키)
 * 2. `data['중제목']` (전역 키)
 * 3. 원본 placeholder 유지
 */
function bindPlaceholders(text, data, sectionIndex = null) {
  if (!text || !data) return text;
  return text.replace(/\{\{(\w+(?:\.\w+)*)\}\}/g, (match, path) => {
    // 1. 섹션별 키 시도 (sectionIndex가 있을 때)
    if (sectionIndex !== null && sectionIndex !== undefined) {
      const indexedKey = `${path}_${sectionIndex}`;
      const indexedValue = getNestedValue(data, indexedKey);
      if (indexedValue !== undefined) {
        return indexedValue;
      }
    }

    // 2. 전역 키 시도
    const value = getNestedValue(data, path);
    return value !== undefined ? value : match;
  });
}

/**
 * 중첩 객체에서 값 추출
 * @param {object} obj - 객체
 * @param {string} path - 경로 (예: 'items.0.title')
 * @returns {any} 값
 */
function getNestedValue(obj, path) {
  return path.split('.').reduce((current, key) => {
    return current && current[key] !== undefined ? current[key] : undefined;
  }, obj);
}

/**
 * HTML 이스케이프
 */
function escapeHtml(text) {
  if (typeof text !== 'string') return text;
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * 단일 shape를 HTML로 변환
 * @param {object} shape - shape 정의
 * @param {object} theme - 테마 색상
 * @param {object} data - 바인딩 데이터
 * @param {number} shapeIndex - shape 인덱스 (섹션 구분용)
 * @param {string} layoutType - 레이아웃 타입 ('row' | 'column')
 * @param {number} totalShapes - 전체 shape 수
 * @returns {string} HTML 요소
 */
function renderShape(shape, theme, data, shapeIndex = 0, layoutType = 'row', totalShapes = 4) {
  const shapeSource = shape.shape_source || 'description';

  switch (shapeSource) {
    case 'html':
      // HTML snippet 직접 사용
      return shape.html?.fragment || '';

    case 'svg':
      // SVG를 div로 감싸서 반환 (나중에 래스터라이즈)
      if (shape.svg?.fragment) {
        const css = shapeStyleToCSS(shape, theme);
        return `<div class="svg-shape" data-shape-id="${shape.id}" style="${css}">${shape.svg.fragment}</div>`;
      }
      break;

    case 'ooxml':
      // OOXML은 HTML로 변환 불가, placeholder div 생성
      const ooxmlCss = shapeStyleToCSS(shape, theme);
      return `<div class="ooxml-placeholder" data-shape-id="${shape.id}" style="${ooxmlCss}; display: flex; align-items: center; justify-content: center;">
        <p style="color: #999; font-size: 10pt;">[OOXML Shape]</p>
      </div>`;

    case 'reference':
      // Reference는 별도 로드 필요, placeholder 생성
      return `<div class="reference-placeholder" data-ref="${shape.reference?.object}" style="${shapeStyleToCSS(shape, theme)}"></div>`;

    case 'description':
    default:
      // description 기반 HTML 생성 (shapeIndex, layoutType 전달)
      return renderDescriptionShape(shape, theme, data, shapeIndex, layoutType, totalShapes);
  }

  return '';
}

/**
 * description 타입 shape를 HTML로 변환
 * @param {object} shape - shape 정의
 * @param {object} theme - 테마 색상
 * @param {object} data - 바인딩 데이터
 * @param {number} shapeIndex - shape 인덱스
 * @param {string} layoutType - 레이아웃 타입 ('row' | 'column')
 * @param {number} totalShapes - 전체 shape 수
 * @returns {string} HTML 요소
 */
function renderDescriptionShape(shape, theme, data, shapeIndex = 0, layoutType = 'row', totalShapes = 4) {
  const css = shapeStyleToCSS(shape, theme);
  const shapeType = shape.type || 'rectangle';
  const shapeId = shape.id || '';

  // sectionIndex 계산 (레이아웃 타입에 따라 다름)
  let sectionIndex;
  if (layoutType === 'column') {
    // 열 기반 레이아웃 (grid-2col): shape 0,2 → col 0, shape 1,3 → col 1
    const numColumns = 2; // 기본 2열
    sectionIndex = shapeIndex % numColumns;
  } else {
    // 행 기반 레이아웃 (content-stack): shape 0-1 → row 0, shape 2-3 → row 1
    sectionIndex = Math.floor(shapeIndex / 2);
  }

  let innerContent = '';

  // 텍스트 콘텐츠 (sectionIndex 전달)
  if (shape.text) {
    innerContent = renderTextContent(shape.text, theme, data, sectionIndex);
  }

  // 이미지
  if (shape.type === 'picture' && shape.image) {
    const imgDesc = shape.image.description || 'Image placeholder';
    innerContent = `<div class="image-placeholder" style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #f0f0f0;">
      <p style="color: #666; font-size: 10pt;">[${imgDesc}]</p>
    </div>`;
  }

  // shape 타입별 추가 스타일
  let extraStyle = '';
  if (shapeType === 'oval' || shapeType === 'circle') {
    extraStyle = 'border-radius: 50%;';
  }

  return `<div class="shape shape-${shapeType}" data-shape-id="${shapeId}" style="${css}; ${extraStyle}">
    ${innerContent}
  </div>`;
}

/**
 * 템플릿 YAML을 HTML로 렌더링
 * @param {object} template - 로드된 템플릿 객체
 * @param {object} data - 바인딩 데이터
 * @param {object} theme - 테마 색상
 * @returns {string} 완성된 HTML
 */
function renderFromYaml(template, data, theme) {
  if (!template || !template.shapes) {
    console.warn('Invalid template: missing shapes array');
    return null;
  }

  const colors = { ...DEEPGREEN_THEME, ...theme };

  // 배경 설정
  let backgroundStyle = `background: ${colors.background || '#FFFFFF'}`;
  if (template.background) {
    if (template.background.type === 'solid' && template.background.color) {
      backgroundStyle = `background: ${resolveColorToken(template.background.color, colors)}`;
    }
  }

  // 레이아웃 타입 감지 (템플릿 ID 기반)
  const templateId = template.id || template.content_template?.id || 'unknown';
  let layoutType = 'row'; // 기본값: 행 기반

  // 열 기반 레이아웃 템플릿
  if (templateId.includes('grid-2col') || templateId.includes('grid-3col') || templateId.includes('grid-4col')) {
    layoutType = 'column';
  }

  const totalShapes = template.shapes.length;

  // shapes 렌더링 (index, layoutType 전달하여 섹션별 바인딩 지원)
  const shapesHtml = template.shapes
    .map((shape, index) => renderShape(shape, colors, data, index, layoutType, totalShapes))
    .filter(html => html)
    .join('\n    ');

  // 메타데이터
  const templateCategory = template._category || 'unknown';

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="template-id" content="${templateId}">
  <meta name="template-category" content="${templateCategory}">
  <style>
    ${generateThemeCSS(colors)}
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
      width: ${CANVAS.width}pt;
      height: ${CANVAS.height}pt;
      overflow: hidden;
      ${backgroundStyle};
      position: relative;
    }
    .shape {
      overflow: hidden;
    }
    .svg-shape svg {
      width: 100%;
      height: 100%;
    }
  </style>
</head>
<body>
    ${shapesHtml}
</body>
</html>`;
}

// 기본 테마 색상 (동국시스템즈)
const DEFAULT_THEME = {
  primary: '#002452',
  secondary: '#C51F2A',
  accent: '#A1BFB4',
  dark: '#153325',
  dark_text: '#262626',
  light: '#FFFFFF',
  gray: '#B6B6B6',
  surface: '#F8F9FA',
  background: '#FFFFFF'
};

// Deep Green 테마
const DEEPGREEN_THEME = {
  primary: '#22523B',
  secondary: '#153325',
  accent: '#A1BFB4',
  dark: '#153325',
  dark_text: '#183C2B',
  light: '#FFFFFF',
  gray: '#B6B6B6',
  surface: '#F5F7F6',
  background: '#FFFFFF'
};

/**
 * 테마 색상을 CSS 변수로 변환
 */
function generateThemeCSS(theme) {
  const colors = { ...DEFAULT_THEME, ...theme };
  return `
    :root {
      --primary: ${colors.primary};
      --secondary: ${colors.secondary};
      --accent: ${colors.accent};
      --dark: ${colors.dark};
      --dark-text: ${colors.dark_text};
      --light: ${colors.light};
      --gray: ${colors.gray};
      --surface: ${colors.surface};
      --background: ${colors.background};
    }
  `;
}

/**
 * 기본 슬라이드 스타일
 */
const BASE_STYLES = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif;
    width: 1084px;
    height: 750px;
    overflow: hidden;
    background: var(--background);
  }
  .slide {
    width: 1084px;
    height: 750px;
    padding: 35px 40px;
    position: relative;
  }
  h1.main-title {
    font-size: 19px;
    color: var(--primary);
    font-weight: 600;
    margin-bottom: 8px;
  }
  p.action-title {
    font-size: 17px;
    color: var(--dark-text);
    font-weight: 500;
    margin-bottom: 25px;
    line-height: 1.5;
  }
  p.footer {
    position: absolute;
    bottom: 15px;
    right: 30px;
    font-size: 8px;
    color: var(--gray);
  }
`;

/**
 * 3열 그리드 템플릿 (deepgreen-grid-3col1)
 */
function renderGrid3Col(data, theme) {
  const { title, subtitle, cards = [] } = data;
  const colors = { ...DEEPGREEN_THEME, ...theme };

  const cardHTML = cards.slice(0, 6).map((card, i) => {
    const isTopRow = i < 3;
    const bgColor = isTopRow ? colors.primary : colors.secondary;

    return `
      <div class="card" style="background: ${bgColor}; position: relative;">
        <div class="card-decoration" style="
          position: absolute;
          top: 0;
          left: 0;
          width: 0;
          height: 0;
          border-style: solid;
          border-width: 80px 80px 0 0;
          border-color: rgba(255,255,255,0.08) transparent transparent transparent;
        "></div>
        <div class="number-badge" style="
          position: absolute;
          top: -12px;
          left: -8px;
          width: 36px;
          height: 36px;
          background: ${colors.accent};
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 14px;
          color: ${colors.dark};
          box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        "><p style="margin:0;">${card.number || i + 1}</p></div>
        <div class="card-content" style="padding: 20px 15px 15px 15px;">
          <h3 class="card-title" style="
            font-size: 14px;
            font-weight: 600;
            color: ${colors.light};
            margin-bottom: 8px;
          ">${card.title || ''}</h3>
          <p class="card-desc" style="
            font-size: 11px;
            color: rgba(255,255,255,0.85);
            line-height: 1.6;
          ">${(card.description || '').replace(/\n/g, '<br>')}</p>
        </div>
      </div>
    `;
  }).join('');

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  ${generateThemeCSS(colors)}
  ${BASE_STYLES}
  .grid-container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-top: 30px;
  }
  .card {
    border-radius: 12px;
    min-height: 160px;
    overflow: hidden;
  }
</style>
</head><body>
<div class="slide">
  <h1 class="main-title">${title || ''}</h1>
  <p class="action-title">${subtitle || ''}</p>
  <div class="grid-container">
    ${cardHTML}
  </div>
</div>
</body></html>`;
}

/**
 * 아이콘 그리드 템플릿 (deepgreen-grid-icon1)
 */
function renderGridIcon(data, theme) {
  const { title, subtitle, items = [] } = data;
  const colors = { ...DEEPGREEN_THEME, ...theme };

  const itemHTML = items.slice(0, 4).map((item, i) => `
    <div class="icon-card" style="
      background: ${colors.surface};
      border-radius: 12px;
      padding: 25px 20px;
      text-align: center;
    ">
      <div class="icon-box" style="
        width: 60px;
        height: 60px;
        background: ${colors.primary};
        border-radius: 12px;
        margin: 0 auto 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        color: ${colors.light};
      "><p style="margin:0;">${item.icon || '📦'}</p></div>
      <h3 class="icon-title" style="
        font-size: 15px;
        color: ${colors.dark_text};
        font-weight: 600;
        margin-bottom: 8px;
      ">${item.title || ''}</h3>
      <p class="icon-desc" style="
        font-size: 12px;
        color: ${colors.gray};
        line-height: 1.5;
      ">${(item.description || '').replace(/\n/g, '<br>')}</p>
    </div>
  `).join('');

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  ${generateThemeCSS(colors)}
  ${BASE_STYLES}
  .icon-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-top: 30px;
  }
</style>
</head><body>
<div class="slide">
  <h1 class="main-title">${title || ''}</h1>
  <p class="action-title">${subtitle || ''}</p>
  <div class="icon-grid">
    ${itemHTML}
  </div>
</div>
</body></html>`;
}

/**
 * 타임라인 템플릿 (deepgreen-timeline1)
 */
function renderTimeline(data, theme) {
  const { title, subtitle, steps = [] } = data;
  const colors = { ...DEEPGREEN_THEME, ...theme };

  const stepHTML = steps.slice(0, 5).map((step, i) => `
    <div class="step" style="
      text-align: center;
      width: 160px;
      position: relative;
      z-index: 1;
    ">
      <div class="step-number" style="
        width: 60px;
        height: 60px;
        background: ${colors.primary};
        border-radius: 50%;
        color: ${colors.light};
        font-size: 24px;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      "><p style="margin:0;">${step.number || i + 1}</p></div>
      <h3 class="step-title" style="
        font-size: 14px;
        color: ${colors.dark_text};
        font-weight: 600;
        margin-bottom: 6px;
      ">${step.title || ''}</h3>
      <p class="step-desc" style="
        font-size: 11px;
        color: ${colors.gray};
        line-height: 1.4;
      ">${step.description || ''}</p>
    </div>
  `).join('');

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  ${generateThemeCSS(colors)}
  ${BASE_STYLES}
  .timeline {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-top: 50px;
    position: relative;
    padding: 0 30px;
  }
  .timeline::before {
    content: '';
    position: absolute;
    top: 30px;
    left: 80px;
    right: 80px;
    height: 3px;
    background: linear-gradient(90deg, ${colors.primary} 0%, ${colors.accent} 100%);
  }
</style>
</head><body>
<div class="slide">
  <h1 class="main-title">${title || ''}</h1>
  <p class="action-title">${subtitle || ''}</p>
  <div class="timeline">
    ${stepHTML}
  </div>
</div>
</body></html>`;
}

/**
 * 통계 카드 템플릿 (deepgreen-feature-cards1)
 */
function renderStats(data, theme) {
  const { title, subtitle, stats = [] } = data;
  const colors = { ...DEEPGREEN_THEME, ...theme };

  const statColors = [colors.primary, colors.secondary, colors.gray];

  const statHTML = stats.slice(0, 3).map((stat, i) => `
    <div class="stat-card" style="
      width: 280px;
      background: ${colors.surface};
      border-radius: 16px;
      padding: 35px 25px;
      text-align: center;
    ">
      <div class="stat-value" style="
        font-size: 52px;
        font-weight: 700;
        color: ${statColors[i] || colors.primary};
        margin-bottom: 8px;
        display: flex; justify-content: center;
      "><p style="margin:0;">${stat.value || '0'}</p></div>
      <h3 class="stat-label" style="
        font-size: 16px;
        font-weight: 600;
        color: ${statColors[i] || colors.primary};
        margin-bottom: 8px;
      ">${stat.label || ''}</h3>
      <p class="stat-desc" style="
        font-size: 12px;
        color: ${colors.gray};
      ">${stat.description || ''}</p>
    </div>
  `).join('');

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  ${generateThemeCSS(colors)}
  ${BASE_STYLES}
  .stats-grid {
    display: flex;
    gap: 30px;
    margin-top: 40px;
    justify-content: center;
  }
</style>
</head><body>
<div class="slide">
  <h1 class="main-title">${title || ''}</h1>
  <p class="action-title">${subtitle || ''}</p>
  <div class="stats-grid">
    ${statHTML}
  </div>
</div>
</body></html>`;
}

/**
 * 불릿 리스트 템플릿 (텍스트 중심)
 */
function renderBulletList(data, theme) {
  const { title, subtitle, items = [] } = data;
  const colors = { ...DEFAULT_THEME, ...theme };

  const itemHTML = items.map(item => `
    <li style="margin-bottom: 12px;">${item}</li>
  `).join('');

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  ${generateThemeCSS(colors)}
  ${BASE_STYLES}
  .bullet-list {
    font-size: 16px;
    color: ${colors.dark_text};
    line-height: 2.0;
    list-style: none;
    padding-left: 25px;
  }
  .bullet-list li::before {
    content: "▐";
    color: ${colors.primary};
    margin-right: 15px;
    font-size: 12px;
  }
</style>
</head><body>
<div class="slide">
  <h1 class="main-title">${title || ''}</h1>
  <p class="action-title">${subtitle || ''}</p>
  <ul class="bullet-list">
    ${itemHTML}
  </ul>
</div>
</body></html>`;
}

/**
 * Q&A / 클로징 슬라이드
 */
function renderClosing(data, theme) {
  const { title = 'Q&A', subtitle = '', description = '' } = data;
  const colors = { ...DEFAULT_THEME, ...theme };

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  ${generateThemeCSS(colors)}
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Malgun Gothic', Arial, sans-serif;
    width: 1084px;
    height: 750px;
    overflow: hidden;
  }
  .closing-slide {
    width: 1084px;
    height: 750px;
    background: ${colors.primary};
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
  }
  .closing-title {
    color: ${colors.light};
    font-size: 56px;
    font-weight: 700;
    margin-bottom: 25px;
  }
  .closing-subtitle {
    color: ${colors.accent};
    font-size: 20px;
    margin-bottom: 10px;
  }
  .closing-desc {
    color: rgba(255,255,255,0.7);
    font-size: 16px;
  }
</style>
</head><body>
<div class="closing-slide">
  <h1 class="closing-title">${title}</h1>
  <p class="closing-subtitle">${subtitle}</p>
  <p class="closing-desc">${description}</p>
</div>
</body></html>`;
}

/**
 * 막대 차트 템플릿 (deepgreen-chart-bar1)
 */
function renderBarChart(data, theme) {
  const { title, subtitle, chart_data = {} } = data;
  const colors = { ...DEFAULT_THEME, ...theme };

  const categories = chart_data.categories || [];
  const series = chart_data.series || [];

  // 최대값 계산
  let maxVal = 0;
  series.forEach(s => {
    (s.values || []).forEach(v => {
      if (v > maxVal) maxVal = v;
    });
  });
  if (maxVal === 0) maxVal = 1;

  // 시리즈 색상
  const seriesColors = [colors.primary, colors.secondary, colors.accent];

  // 막대 생성
  let barsHTML = '';
  const barWidth = 100 / categories.length;

  categories.forEach((cat, catIdx) => {
    const groupLeft = catIdx * barWidth + barWidth * 0.1;
    const groupWidth = barWidth * 0.8;

    series.forEach((ser, serIdx) => {
      const values = ser.values || [];
      const value = values[catIdx] || 0;
      const heightPct = (value / maxVal) * 100;
      const barColor = seriesColors[serIdx % seriesColors.length];
      const seriesBarWidth = groupWidth / series.length;
      const barLeft = groupLeft + serIdx * seriesBarWidth;

      barsHTML += `
        <div class="bar" style="
          position: absolute;
          left: ${barLeft}%;
          bottom: 50px;
          width: ${seriesBarWidth * 0.8}%;
          height: ${heightPct * 0.8}%;
          background: ${barColor};
          border-radius: 4px 4px 0 0;
          display: flex;
          flex-direction: column;
          align-items: center;
        ">
          <div class="bar-value" style="
            position: absolute;
            top: -25px;
            font-size: 12px;
            font-weight: 600;
            color: ${colors.dark_text};
            display: flex; justify-content: center;
          "><p style="margin:0;">${value}</p></div>
        </div>
      `;
    });

    // 카테고리 레이블
    barsHTML += `
      <div class="cat-label" style="
        position: absolute;
        left: ${groupLeft}%;
        bottom: 15px;
        width: ${groupWidth}%;
        text-align: center;
        font-size: 12px;
        color: ${colors.gray};
      "><p style="margin:0;">${cat}</p></div>
    `;
  });

  // 범례
  let legendHTML = '';
  series.forEach((ser, idx) => {
    const color = seriesColors[idx % seriesColors.length];
    legendHTML += `
      <div style="display: flex; align-items: center; margin-right: 20px;">
        <div style="width: 16px; height: 16px; background: ${color}; border-radius: 3px; margin-right: 6px;"></div>
        <span style="font-size: 12px; color: ${colors.dark_text};">${ser.name || `시리즈 ${idx + 1}`}</span>
      </div>
    `;
  });

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  ${generateThemeCSS(colors)}
  ${BASE_STYLES}
  .chart-container {
    position: relative;
    width: 100%;
    height: 450px;
    margin-top: 20px;
    background: ${colors.surface};
    border-radius: 12px;
    padding: 20px;
  }
  .chart-area {
    position: relative;
    height: 350px;
    border-bottom: 2px solid ${colors.gray};
    border-left: 2px solid ${colors.gray};
    margin-left: 40px;
  }
  .legend {
    display: flex;
    justify-content: center;
    margin-top: 15px;
  }
</style>
</head><body>
<div class="slide">
  <h1 class="main-title">${title || ''}</h1>
  <p class="action-title">${subtitle || ''}</p>
  <div class="chart-container">
    <div class="chart-area">
      ${barsHTML}
    </div>
    <div class="legend">
      ${legendHTML}
    </div>
  </div>
</div>
</body></html>`;
}

/**
 * 프로세스/플로우 템플릿
 */
function renderProcess(data, theme) {
  const { title, subtitle, steps = [] } = data;
  const colors = { ...DEEPGREEN_THEME, ...theme };

  const stepsHTML = steps.slice(0, 5).map((step, i) => {
    const isLast = i === steps.length - 1;
    return `
      <div class="process-step" style="
        display: flex;
        align-items: center;
        flex: 1;
      ">
        <div class="step-box" style="
          background: ${i % 2 === 0 ? colors.primary : colors.secondary};
          border-radius: 12px;
          padding: 20px 25px;
          text-align: center;
          min-width: 140px;
        ">
          <div style="
            font-size: 28px;
            font-weight: 700;
            color: ${colors.light};
            margin-bottom: 8px;
          "><p style="margin:0;">${step.number || i + 1}</p></div>
          <h3 style="
            font-size: 14px;
            font-weight: 600;
            color: ${colors.light};
            margin-bottom: 5px;
          ">${step.title || ''}</h3>
          <p style="
            font-size: 11px;
            color: rgba(255,255,255,0.8);
          ">${step.description || ''}</p>
        </div>
        ${!isLast ? `
          <div class="arrow" style="
            width: 40px;
            height: 2px;
            background: ${colors.accent};
            position: relative;
            margin: 0 5px;
          ">
            <div style="
              position: absolute;
              right: -8px;
              top: -6px;
              width: 0;
              height: 0;
              border-left: 10px solid ${colors.accent};
              border-top: 7px solid transparent;
              border-bottom: 7px solid transparent;
            "></div>
          </div>
        ` : ''}
      </div>
    `;
  }).join('');

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  ${generateThemeCSS(colors)}
  ${BASE_STYLES}
  .process-container {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 50px;
    padding: 0 20px;
  }
</style>
</head><body>
<div class="slide">
  <h1 class="main-title">${title || ''}</h1>
  <p class="action-title">${subtitle || ''}</p>
  <div class="process-container">
    ${stepsHTML}
  </div>
</div>
</body></html>`;
}

/**
 * 템플릿 렌더러 매핑
 */
const TEMPLATE_RENDERERS = {
  'deepgreen-grid-3col1': renderGrid3Col,
  'deepgreen-grid-icon1': renderGridIcon,
  'deepgreen-grid-text1': renderGrid3Col,
  'deepgreen-timeline1': renderTimeline,
  'deepgreen-feature-cards1': renderStats,
  'deepgreen-stats1': renderStats,
  'deepgreen-closing1': renderClosing,
  'deepgreen-chart-bar1': renderBarChart,
  'deepgreen-process1': renderProcess,
  'deepgreen-bullets1': renderBulletList,
  // 별칭
  'grid-3col': renderGrid3Col,
  'grid-icon': renderGridIcon,
  'timeline': renderTimeline,
  'stats': renderStats,
  'bullets': renderBulletList,
  'closing': renderClosing,
  'chart-bar': renderBarChart,
  'process': renderProcess,
};

/**
 * 메인 렌더 함수 (v2.0: YAML 기반 렌더링 우선)
 *
 * 렌더링 우선순위:
 * 1. 템플릿 YAML 파일 로드 시도 → renderFromYaml()
 * 2. YAML 로드 실패 시 → 하드코딩된 렌더러 (TEMPLATE_RENDERERS)
 * 3. 둘 다 없으면 → renderBulletList() fallback
 *
 * @param {string} templateId - 콘텐츠 템플릿 ID
 * @param {Object} data - 바인딩할 데이터
 * @param {Object} theme - 테마 색상 (옵션)
 * @param {Object} options - 추가 옵션
 * @param {boolean} options.useYaml - YAML 렌더링 사용 여부 (기본: true)
 * @param {string} options.basePath - 템플릿 기본 경로
 * @returns {Promise<string>|string} 렌더링된 HTML
 */
async function renderTemplate(templateId, data, theme = {}, options = {}) {
  const { useYaml = true, basePath = null } = options;

  // 방법 1: YAML 기반 렌더링 시도 (기본값)
  if (useYaml) {
    try {
      const template = await loadTemplate(templateId, basePath);
      if (template && template.shapes && template.shapes.length > 0) {
        console.log(`[renderTemplate] Using YAML template: ${templateId} (${template.shapes.length} shapes)`);
        return renderFromYaml(template, data, theme);
      }
    } catch (err) {
      console.warn(`[renderTemplate] YAML load failed for ${templateId}:`, err.message);
    }
  }

  // 방법 2: 하드코딩된 렌더러 사용
  const renderer = TEMPLATE_RENDERERS[templateId];
  if (renderer) {
    console.log(`[renderTemplate] Using hardcoded renderer: ${templateId}`);
    return renderer(data, theme);
  }

  // 방법 3: Fallback to bullet list
  console.warn(`[renderTemplate] Unknown template: ${templateId}, falling back to bullet list`);
  return renderBulletList(data, theme);
}

/**
 * 동기 버전 렌더 함수 (기존 호환용)
 * 하드코딩된 렌더러만 사용
 */
function renderTemplateSync(templateId, data, theme = {}) {
  const renderer = TEMPLATE_RENDERERS[templateId];
  if (renderer) {
    return renderer(data, theme);
  }
  console.warn(`Unknown template: ${templateId}, falling back to bullet list`);
  return renderBulletList(data, theme);
}

/**
 * 지원되는 템플릿 목록 반환
 */
function getSupportedTemplates() {
  return Object.keys(TEMPLATE_RENDERERS);
}

module.exports = {
  // v2.0: YAML 기반 렌더링 함수
  renderTemplate,        // async, YAML 우선
  renderTemplateSync,    // sync, 하드코딩만
  renderFromYaml,        // 로드된 템플릿 직접 렌더링
  loadTemplate,          // 템플릿 YAML 로드

  // 유틸리티
  getSupportedTemplates,
  percentToPt,
  resolveColorToken,
  shapeStyleToCSS,
  bindPlaceholders,

  // 개별 렌더러 내보내기 (하드코딩)
  renderGrid3Col,
  renderGridIcon,
  renderTimeline,
  renderStats,
  renderBulletList,
  renderClosing,
  renderBarChart,
  renderProcess,

  // 테마
  DEFAULT_THEME,
  DEEPGREEN_THEME,
  generateThemeCSS,
  BASE_STYLES,

  // 상수
  CANVAS,
};
