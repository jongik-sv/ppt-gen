#!/usr/bin/env node
/**
 * Icon Resolver Module (v5.5)
 * Stage-4에서 아이콘을 실제로 생성하고 삽입
 *
 * v5.5 변경사항:
 * - assets_generated.icons 형식으로 결과 반환
 * - session-manager.js와 연동 가능한 구조
 *
 * Usage:
 *   const { resolveIcons, insertIconsToHtml } = require('./icon-resolver');
 *   const result = await resolveIcons(slide, iconDecision, theme, outputDir);
 *
 *   // 결과를 세션에 저장
 *   await session.updateSlide(index, {
 *     assets_generated: { icons: result.icons, images: [] }
 *   });
 */

const path = require('path');
const fs = require('fs').promises;
const { rasterize } = require('./rasterize-icon');

/**
 * 슬라이드용 아이콘 일괄 생성 (v5.5 스키마)
 * @param {Object} slide - 슬라이드 데이터
 * @param {Object} iconDecision - icon-decision의 출력
 * @param {Object} theme - 테마 색상 정보 { colors: { primary, secondary, ... } }
 * @param {string} outputDir - 출력 디렉토리
 * @returns {Object} assets_generated.icons 형식의 결과
 *
 * 반환 형식 (v5.5):
 * {
 *   icons: [
 *     { id: "wms", react_icon: "fa/FaWarehouse", file: "icons/wms.png", color: "#2563EB", size: 256, keyword: "창고" },
 *     ...
 *   ],
 *   generated: true,
 *   icon_dir: "/abs/path/to/icons",
 *   count: 4
 * }
 */
async function resolveIcons(slide, iconDecision, theme, outputDir) {
  if (!iconDecision || !iconDecision.needs_icons) {
    return { icons: [], generated: false, count: 0 };
  }

  const iconDir = path.join(outputDir, 'icons');
  await fs.mkdir(iconDir, { recursive: true });

  const generatedIcons = [];
  const primaryColor = theme?.colors?.primary || '#2563EB';
  const iconSize = 256; // 2x 해상도

  for (const match of iconDecision.matched_keywords) {
    const iconPath = match.icon;
    const safeName = sanitizeFilename(match.keyword);
    const outputFile = path.join(iconDir, `${safeName}.png`);
    const relativePath = `icons/${safeName}.png`;

    try {
      await rasterize(iconPath, primaryColor, iconSize, outputFile);

      // v5.5 스키마: assets_generated.icons 형식
      generatedIcons.push({
        id: safeName,
        react_icon: iconPath,
        file: relativePath,
        color: primaryColor,
        size: iconSize,
        keyword: match.keyword,
        match_type: match.match_type || 'direct'
      });

      console.log(`  Generated: ${match.keyword} → ${safeName}.png`);
    } catch (err) {
      console.error(`  Failed to generate icon for "${match.keyword}": ${err.message}`);

      // 실패 시 기본 아이콘으로 대체 시도
      try {
        const fallbackIcon = 'fa/FaCircle';
        await rasterize(fallbackIcon, primaryColor, iconSize, outputFile);

        generatedIcons.push({
          id: safeName,
          react_icon: fallbackIcon,
          file: relativePath,
          color: primaryColor,
          size: iconSize,
          keyword: match.keyword,
          match_type: 'fallback',
          original_icon: iconPath
        });
      } catch (fallbackErr) {
        // 완전 실패 - 에러 기록
        generatedIcons.push({
          id: safeName,
          react_icon: iconPath,
          file: null,
          keyword: match.keyword,
          error: err.message
        });
      }
    }
  }

  return {
    icons: generatedIcons,
    generated: true,
    icon_dir: iconDir,
    count: generatedIcons.filter(i => i.file).length
  };
}

/**
 * HTML 템플릿에 아이콘 삽입 (v5.5 스키마)
 * @param {string} htmlContent - 원본 HTML
 * @param {Array} icons - 생성된 아이콘 정보 (v5.5 형식)
 * @param {Object} options - 삽입 옵션
 * @returns {string} 아이콘이 삽입된 HTML
 */
function insertIconsToHtml(htmlContent, icons, options = {}) {
  const {
    iconWidth = '30pt',
    iconHeight = '30pt',
    iconClass = 'icon-img'
  } = options;

  let result = htmlContent;

  // 방법 1: placeholder 마커 교체 ({{ICON:keyword}})
  for (const icon of icons) {
    // v5.5 스키마: file 필드 사용
    const iconFile = icon.file || icon.relative_path;  // 하위 호환
    if (!iconFile) continue;

    const placeholder = new RegExp(`\\{\\{ICON:${escapeRegex(icon.keyword)}\\}\\}`, 'gi');
    const imgTag = `<img src="${iconFile}" class="${iconClass}" ` +
                   `style="width: ${iconWidth}; height: ${iconHeight};" ` +
                   `alt="${icon.keyword}">`;

    result = result.replace(placeholder, imgTag);
  }

  // 방법 2: 텍스트 기반 아이콘 교체 (<p>W</p> → <img>)
  // 이것은 특정 패턴에서만 사용
  for (const icon of icons) {
    const iconFile = icon.file || icon.relative_path;
    if (!iconFile) continue;

    // 첫 글자만 있는 경우 (예: <p>W</p>)
    const firstChar = icon.keyword.charAt(0).toUpperCase();
    const textPattern = new RegExp(
      `<p[^>]*>\\s*${escapeRegex(firstChar)}\\s*</p>`,
      'g'
    );

    // 패턴이 있으면 교체 (한 번만)
    if (textPattern.test(result)) {
      result = result.replace(textPattern, (match) => {
        return `<img src="${iconFile}" class="${iconClass}" ` +
               `style="width: ${iconWidth}; height: ${iconHeight};" ` +
               `alt="${icon.keyword}">`;
      });
    }
  }

  return result;
}

/**
 * 키워드에서 최적 아이콘 찾기
 * @param {string} keyword - 검색 키워드
 * @param {Object} iconMappings - icon-mappings.yaml 데이터
 * @param {string} category - 카테고리 힌트 (optional)
 * @returns {Object|null} 매칭된 아이콘 정보
 */
function findBestIcon(keyword, iconMappings, category = null) {
  const mappings = iconMappings?.mappings || {};
  const defaults = iconMappings?.defaults || {};

  const lowerKeyword = keyword.toLowerCase();

  // 1. 직접 매칭
  if (mappings[keyword]) {
    return { icon: mappings[keyword].icon, match_type: 'direct' };
  }

  // 2. 대소문자 무시 매칭
  for (const [key, value] of Object.entries(mappings)) {
    if (key.toLowerCase() === lowerKeyword) {
      return { icon: value.icon, match_type: 'case_insensitive' };
    }
  }

  // 3. Alias 매칭
  for (const [key, value] of Object.entries(mappings)) {
    if (value.aliases?.some(a => a.toLowerCase() === lowerKeyword)) {
      return { icon: value.icon, match_type: 'alias' };
    }
  }

  // 4. 부분 매칭 (키워드가 다른 키워드를 포함)
  for (const [key, value] of Object.entries(mappings)) {
    if (lowerKeyword.includes(key.toLowerCase()) ||
        key.toLowerCase().includes(lowerKeyword)) {
      return { icon: value.icon, match_type: 'partial' };
    }
  }

  // 5. 카테고리 기본값
  if (category && defaults[category]) {
    return { icon: defaults[category], match_type: 'category_default' };
  }

  // 6. 전역 기본값
  return { icon: defaults.fallback || 'fa/FaCircle', match_type: 'fallback' };
}

/**
 * 슬라이드에 아이콘 바인딩 생성
 * @param {Array} items - 슬라이드 항목들 (key_points 등)
 * @param {Object} iconMappings - 아이콘 매핑
 * @param {string} category - 카테고리
 * @returns {Array} 아이콘 바인딩 배열
 */
function createIconBindings(items, iconMappings, category = null) {
  const bindings = [];

  for (let i = 0; i < items.length; i++) {
    const item = typeof items[i] === 'string' ? items[i] : (items[i].title || items[i].name || '');
    const keywords = item.match(/[\uAC00-\uD7A3]+|[a-zA-Z]+/g) || [];

    let bestMatch = null;
    for (const keyword of keywords) {
      const match = findBestIcon(keyword, iconMappings, category);
      if (match.match_type !== 'fallback') {
        bestMatch = { keyword, ...match };
        break;
      }
    }

    if (!bestMatch) {
      // 첫 번째 의미있는 키워드 사용
      const fallback = findBestIcon(keywords[0] || item, iconMappings, category);
      bestMatch = { keyword: keywords[0] || item, ...fallback };
    }

    bindings.push({
      index: i,
      item_text: item,
      keyword: bestMatch.keyword,
      icon: bestMatch.icon,
      match_type: bestMatch.match_type
    });
  }

  return bindings;
}

/**
 * 파일명 안전 문자열로 변환
 */
function sanitizeFilename(str) {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9가-힣]/g, '_')
    .replace(/_+/g, '_')
    .substring(0, 50);
}

/**
 * 정규식 특수문자 이스케이프
 */
function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// CLI 테스트 모드
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args[0] === '--test') {
    console.log('Running icon-resolver tests...\n');

    const { loadIconMappings } = require('./icon-decision');
    const mappingsPath = path.join(__dirname, '../../../../templates-bak/assets/icon-mappings.yaml');

    let iconMappings = { mappings: {}, defaults: {} };
    const fs = require('fs');
    if (fs.existsSync(mappingsPath)) {
      iconMappings = loadIconMappings(mappingsPath);
    }

    // 테스트: findBestIcon
    console.log('Test findBestIcon:');
    console.log('  "보안":', findBestIcon('보안', iconMappings));
    console.log('  "창고":', findBestIcon('창고', iconMappings));
    console.log('  "unknown":', findBestIcon('unknown', iconMappings, 'technology'));
    console.log();

    // 테스트: createIconBindings
    const items = ['창고관리시스템', '배송관리시스템', '주문관리시스템', '통합모니터링'];
    console.log('Test createIconBindings:');
    const bindings = createIconBindings(items, iconMappings, 'technology');
    for (const b of bindings) {
      console.log(`  ${b.index}: "${b.item_text}" → ${b.icon} (${b.match_type})`);
    }
  }
}

module.exports = {
  resolveIcons,
  insertIconsToHtml,
  findBestIcon,
  createIconBindings,
  sanitizeFilename
};
