#!/usr/bin/env node
/**
 * Image Prompt Generator
 * 슬라이드 콘텐츠를 분석하여 이미지 생성 서비스용 프롬프트 생성
 *
 * Usage:
 *   node image-prompt-generator.js --subject "AI 기술" --purpose hero --industry tech
 *   node image-prompt-generator.js --json slides.json
 *
 * Output:
 *   { prompt: "...", negative_prompt: "...", aspect_ratio: "16:9", ... }
 *
 * Dependencies:
 *   - js-yaml (템플릿 로드)
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// 템플릿 경로
const TEMPLATES_PATH = path.resolve(__dirname, '../../../templates/assets/image-prompt-templates.yaml');

/**
 * 템플릿 로드
 */
function loadTemplates() {
  if (!fs.existsSync(TEMPLATES_PATH)) {
    throw new Error(`Templates not found: ${TEMPLATES_PATH}`);
  }
  return yaml.load(fs.readFileSync(TEMPLATES_PATH, 'utf-8'));
}

/**
 * 플레이스홀더 치환
 * @param {string} template - 템플릿 문자열
 * @param {object} values - 치환값
 */
function replacePlaceholders(template, values) {
  let result = template;
  for (const [key, value] of Object.entries(values)) {
    result = result.replace(new RegExp(`\\{${key}\\}`, 'g'), value || '');
  }
  return result;
}

/**
 * 이미지 생성 프롬프트 생성
 * @param {object} options - 옵션
 * @param {string} options.subject - 이미지 주제
 * @param {string} options.purpose - 이미지 용도 (hero, background, illustration, etc.)
 * @param {string} options.industry - 산업 분야 (tech, finance, healthcare, etc.)
 * @param {string} options.context - 추가 컨텍스트 (팀 이미지 등)
 * @param {string} options.style - 추가 스타일 지정
 * @param {boolean} options.highQuality - 품질 향상 프롬프트 추가
 */
function generatePrompt(options) {
  const templates = loadTemplates();
  const {
    subject,
    purpose = 'hero',
    industry = null,
    context = '',
    style = null,
    highQuality = true
  } = options;

  // 용도별 템플릿 로드
  const purposeTemplate = templates.templates[purpose];
  if (!purposeTemplate) {
    throw new Error(`Unknown purpose: ${purpose}. Available: ${Object.keys(templates.templates).join(', ')}`);
  }

  // 기본 프롬프트 생성
  let prompt = replacePlaceholders(purposeTemplate.base, { subject, context });

  // 용도별 modifier 추가
  const modifiers = [...purposeTemplate.modifiers];

  // 산업별 스타일 추가
  if (industry && templates.industry_styles[industry]) {
    const industryStyle = templates.industry_styles[industry];
    modifiers.push(...industryStyle.modifiers);
    modifiers.push(industryStyle.color_mood);
  }

  // 품질 향상 프롬프트 추가
  if (highQuality) {
    modifiers.push(...templates.quality_boosters.high_quality.slice(0, 2));
  }

  // 커스텀 스타일 추가
  if (style) {
    modifiers.push(style);
  }

  // 프롬프트 조합
  prompt = `${prompt}, ${modifiers.join(', ')}`;

  // 부정 프롬프트 생성
  const negativePrompts = [
    ...templates.negative_prompts.common,
    ...templates.negative_prompts.professional
  ];

  // 종횡비
  const aspectRatio = purposeTemplate.aspect_ratio || '16:9';
  const dimensions = templates.aspect_ratios[aspectRatio];

  return {
    prompt: prompt.trim(),
    negative_prompt: negativePrompts.join(', '),
    aspect_ratio: aspectRatio,
    width: dimensions?.width || 1920,
    height: dimensions?.height || 1080,
    purpose: purpose,
    industry: industry,
    description: purposeTemplate.description
  };
}

/**
 * 슬라이드 목록에서 이미지 프롬프트 일괄 생성
 * @param {Array} slides - 슬라이드 정보 배열
 *
 * 입력 형식:
 * [
 *   { id: 1, title: "AI 기술 소개", purpose: "hero", industry: "tech" },
 *   { id: 2, title: "팀 소개", purpose: "team", context: "discussing project" },
 *   ...
 * ]
 */
function generateBatch(slides) {
  const results = [];

  for (const slide of slides) {
    try {
      const prompt = generatePrompt({
        subject: slide.subject || slide.title,
        purpose: slide.purpose || 'hero',
        industry: slide.industry,
        context: slide.context,
        style: slide.style,
        highQuality: slide.highQuality !== false
      });

      results.push({
        slide_id: slide.id,
        title: slide.title,
        ...prompt
      });
    } catch (err) {
      results.push({
        slide_id: slide.id,
        title: slide.title,
        error: err.message
      });
    }
  }

  return results;
}

/**
 * 사용 가능한 용도 목록 출력
 */
function listPurposes() {
  const templates = loadTemplates();
  console.log('\n📋 Available image purposes:\n');

  for (const [key, value] of Object.entries(templates.templates)) {
    console.log(`  ${key.padEnd(15)} - ${value.description}`);
  }

  console.log('\n🏢 Available industries:\n');
  for (const key of Object.keys(templates.industry_styles)) {
    console.log(`  ${key}`);
  }
}

// CLI 실행
function main() {
  const args = process.argv.slice(2);

  // 도움말
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Image Prompt Generator
======================

Usage:
  node image-prompt-generator.js [options]

Options:
  --subject <text>     Image subject (required)
  --purpose <type>     Image purpose: hero, background, illustration, product, team, tech, data, nature, icon
  --industry <type>    Industry style: tech, finance, healthcare, manufacturing, retail, education, government
  --context <text>     Additional context (for team images, etc.)
  --style <text>       Custom style to add
  --no-quality         Disable quality boosters
  --json <file>        Batch generate from JSON file
  --list               List available purposes and industries
  --output <file>      Output to JSON file

Examples:
  node image-prompt-generator.js --subject "AI technology" --purpose hero --industry tech
  node image-prompt-generator.js --json slides.json --output prompts.json
  node image-prompt-generator.js --list
`);
    return;
  }

  // 목록 출력
  if (args.includes('--list')) {
    listPurposes();
    return;
  }

  // JSON 배치 모드
  const jsonIndex = args.indexOf('--json');
  if (jsonIndex !== -1) {
    const jsonPath = args[jsonIndex + 1];
    if (!jsonPath || !fs.existsSync(jsonPath)) {
      console.error('Error: JSON file not found');
      process.exit(1);
    }

    const slides = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
    const results = generateBatch(slides);

    // 출력 파일 지정 시
    const outputIndex = args.indexOf('--output');
    if (outputIndex !== -1 && args[outputIndex + 1]) {
      fs.writeFileSync(args[outputIndex + 1], JSON.stringify(results, null, 2));
      console.log(`✅ Output saved to: ${args[outputIndex + 1]}`);
    } else {
      console.log(JSON.stringify(results, null, 2));
    }
    return;
  }

  // 단일 프롬프트 생성
  const getArg = (name) => {
    const idx = args.indexOf(`--${name}`);
    return idx !== -1 ? args[idx + 1] : null;
  };

  const subject = getArg('subject');
  if (!subject) {
    console.error('Error: --subject is required');
    console.error('Run with --help for usage information');
    process.exit(1);
  }

  try {
    const result = generatePrompt({
      subject,
      purpose: getArg('purpose') || 'hero',
      industry: getArg('industry'),
      context: getArg('context'),
      style: getArg('style'),
      highQuality: !args.includes('--no-quality')
    });

    // 출력 파일 지정 시
    const outputIndex = args.indexOf('--output');
    if (outputIndex !== -1 && args[outputIndex + 1]) {
      fs.writeFileSync(args[outputIndex + 1], JSON.stringify(result, null, 2));
      console.log(`✅ Output saved to: ${args[outputIndex + 1]}`);
    } else {
      console.log('\n🎨 Generated Image Prompt:\n');
      console.log('Prompt:');
      console.log(`  ${result.prompt}\n`);
      console.log('Negative Prompt:');
      console.log(`  ${result.negative_prompt}\n`);
      console.log(`Aspect Ratio: ${result.aspect_ratio} (${result.width}x${result.height})`);
      console.log(`Purpose: ${result.purpose}`);
      if (result.industry) console.log(`Industry: ${result.industry}`);
    }
  } catch (err) {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  }
}

main();

// 모듈 export
module.exports = { generatePrompt, generateBatch, listPurposes };
