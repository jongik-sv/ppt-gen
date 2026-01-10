#!/usr/bin/env node
/**
 * React Icon Rasterizer
 * react-icons를 PNG로 래스터라이즈하여 PPT에 삽입 가능한 형태로 변환
 *
 * Usage:
 *   node rasterize-icon.js <icon-path> <color> <size> <output>
 *
 * Examples:
 *   node rasterize-icon.js fa/FaShieldAlt "#1E5128" 256 shield.png
 *   node rasterize-icon.js hi/HiTrendingUp "#4E9F3D" 128 growth.png
 *
 * Arguments:
 *   icon-path: react-icons 경로 (패키지/아이콘명)
 *   color: 아이콘 색상 (hex)
 *   size: 출력 크기 (px)
 *   output: 출력 파일 경로
 *
 * Dependencies:
 *   - react-icons
 *   - react
 *   - react-dom/server
 *   - sharp
 */

const React = require('react');
const ReactDOMServer = require('react-dom/server');
const sharp = require('sharp');
const path = require('path');
const fs = require('fs');

/**
 * react-icons 패키지에서 아이콘 컴포넌트 로드
 * @param {string} iconPath - 패키지/아이콘명 (예: fa/FaShieldAlt)
 * @returns {React.Component} 아이콘 컴포넌트
 */
async function getIcon(iconPath) {
  const [lib, iconName] = iconPath.split('/');

  if (!lib || !iconName) {
    throw new Error(`Invalid icon path: ${iconPath}. Expected format: package/IconName`);
  }

  try {
    const pkg = require(`react-icons/${lib}`);
    const Icon = pkg[iconName];

    if (!Icon) {
      throw new Error(`Icon "${iconName}" not found in react-icons/${lib}`);
    }

    return Icon;
  } catch (err) {
    if (err.code === 'MODULE_NOT_FOUND') {
      throw new Error(`Package react-icons/${lib} not found. Install with: npm install react-icons`);
    }
    throw err;
  }
}

/**
 * 아이콘을 PNG로 래스터라이즈
 * @param {string} iconPath - react-icons 경로
 * @param {string} color - 색상 (hex)
 * @param {number} size - 크기 (px)
 * @param {string} output - 출력 파일 경로
 */
async function rasterize(iconPath, color, size, output) {
  const Icon = await getIcon(iconPath);

  // React 엘리먼트 생성 및 SVG로 렌더링
  const element = React.createElement(Icon, {
    color: color,
    size: String(size)
  });

  const svgString = ReactDOMServer.renderToStaticMarkup(element);

  // SVG를 PNG로 변환
  const outputPath = path.resolve(output);
  const outputDir = path.dirname(outputPath);

  // 출력 디렉토리 생성
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  await sharp(Buffer.from(svgString))
    .resize(size, size)
    .png()
    .toFile(outputPath);

  return outputPath;
}

/**
 * 여러 아이콘을 일괄 래스터라이즈 (JSON 입력)
 * @param {string} jsonPath - 아이콘 목록 JSON 파일 경로
 *
 * JSON 형식:
 * {
 *   "icons": [
 *     { "path": "fa/FaShieldAlt", "color": "#1E5128", "size": 256, "output": "shield.png" },
 *     ...
 *   ]
 * }
 */
async function batchRasterize(jsonPath) {
  const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
  const results = [];

  for (const icon of data.icons) {
    try {
      const outputPath = await rasterize(icon.path, icon.color, icon.size, icon.output);
      results.push({ success: true, path: icon.path, output: outputPath });
      console.log(`✅ ${icon.path} → ${outputPath}`);
    } catch (err) {
      results.push({ success: false, path: icon.path, error: err.message });
      console.error(`❌ ${icon.path}: ${err.message}`);
    }
  }

  return results;
}

// CLI 실행
async function main() {
  const args = process.argv.slice(2);

  // 배치 모드 (--batch flag)
  if (args[0] === '--batch') {
    if (!args[1]) {
      console.error('Usage: node rasterize-icon.js --batch <json-file>');
      process.exit(1);
    }
    await batchRasterize(args[1]);
    return;
  }

  // 단일 아이콘 모드
  if (args.length < 4) {
    console.error('Usage: node rasterize-icon.js <icon-path> <color> <size> <output>');
    console.error('Example: node rasterize-icon.js fa/FaShieldAlt "#1E5128" 256 shield.png');
    console.error('\nBatch mode: node rasterize-icon.js --batch icons.json');
    process.exit(1);
  }

  const [iconPath, color, sizeStr, output] = args;
  const size = parseInt(sizeStr, 10);

  if (isNaN(size) || size <= 0) {
    console.error(`Invalid size: ${sizeStr}. Must be a positive integer.`);
    process.exit(1);
  }

  try {
    const outputPath = await rasterize(iconPath, color, size, output);
    console.log(`✅ Created: ${outputPath}`);
  } catch (err) {
    console.error(`❌ Error: ${err.message}`);
    process.exit(1);
  }
}

// CLI로 직접 실행할 때만 main() 호출
if (require.main === module) {
  main().catch(console.error);
}

// 모듈 export (다른 스크립트에서 사용 가능)
module.exports = { rasterize, batchRasterize, getIcon };
