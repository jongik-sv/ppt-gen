#!/usr/bin/env node
/**
 * Icon Decision Module
 * Stage-3에서 아이콘 필요성을 자동 판단
 *
 * Usage:
 *   const { analyzeIconNeed } = require('./icon-decision');
 *   const decision = analyzeIconNeed(slideData, templateData, iconMappings);
 *
 * Returns:
 *   {
 *     needs_icons: boolean,
 *     confidence: number (0~1),
 *     matched_keywords: Array<{keyword, icon, match_type}>,
 *     reason: string
 *   }
 */

const fs = require('fs');
const path = require('path');

// 아이콘 적합 카테고리 (높은 적합도)
const ICON_SUITABLE_CATEGORIES = ['grid', 'feature', 'stats', 'process', 'comparison'];

// 중간 적합도 카테고리
const ICON_MODERATE_CATEGORIES = ['timeline', 'content'];

// 아이콘 불필요 카테고리
const ICON_NOT_SUITABLE = ['cover', 'closing', 'toc', 'section', 'table', 'quote'];

// 아이콘 적합 항목 수 범위
const ICON_OPTIMAL_RANGE = { min: 3, max: 6 };
const ICON_ACCEPTABLE_RANGE = { min: 2, max: 8 };

/**
 * 아이콘 필요성 분석
 * @param {Object} slide - 슬라이드 데이터 (Stage-2 출력)
 * @param {Object} template - 매칭된 템플릿 정보
 * @param {Object} iconMappings - icon-mappings.yaml 데이터
 * @returns {Object} 아이콘 결정 정보
 */
function analyzeIconNeed(slide, template, iconMappings) {
  const factors = {
    category_score: 0,
    element_count_score: 0,
    keyword_score: 0,
    template_supports: false
  };

  // 1. 카테고리 적합도 분석
  const category = template?.category || slide.purpose || '';
  factors.category_score = calculateCategoryScore(category);

  // 2. 항목 수 적합도 분석
  const elementCount = getElementCount(slide);
  factors.element_count_score = calculateElementCountScore(elementCount);

  // 3. 키워드 매핑 가능성 분석
  const keywords = extractKeywords(slide);
  const matchedKeywords = matchKeywordsToIcons(keywords, iconMappings);
  factors.keyword_score = keywords.length > 0
    ? matchedKeywords.length / Math.min(keywords.length, 6)
    : 0;

  // 4. 템플릿 아이콘 지원 여부
  factors.template_supports = checkTemplateIconSupport(template);

  // 가중치 적용 점수 계산
  const weights = {
    category_score: 0.30,
    element_count_score: 0.25,
    keyword_score: 0.25,
    template_supports: 0.20
  };

  const totalScore =
    factors.category_score * weights.category_score +
    factors.element_count_score * weights.element_count_score +
    factors.keyword_score * weights.keyword_score +
    (factors.template_supports ? 1 : 0) * weights.template_supports;

  // 결정 (임계값: 0.5)
  const needsIcons = totalScore >= 0.5;
  const confidence = Math.min(totalScore, 1.0);

  return {
    needs_icons: needsIcons,
    confidence: parseFloat(confidence.toFixed(2)),
    factors,
    element_count: elementCount,
    matched_keywords: matchedKeywords,
    reason: generateReason(factors, needsIcons, category, elementCount)
  };
}

/**
 * 카테고리 적합도 점수 계산
 */
function calculateCategoryScore(category) {
  const cat = category.toLowerCase();

  if (ICON_SUITABLE_CATEGORIES.includes(cat)) {
    return 1.0;
  }
  if (ICON_MODERATE_CATEGORIES.includes(cat)) {
    return 0.5;
  }
  if (ICON_NOT_SUITABLE.includes(cat)) {
    return 0.0;
  }
  return 0.3; // 알 수 없는 카테고리
}

/**
 * 항목 수 적합도 점수 계산
 */
function calculateElementCountScore(count) {
  if (count >= ICON_OPTIMAL_RANGE.min && count <= ICON_OPTIMAL_RANGE.max) {
    return 1.0;
  }
  if (count >= ICON_ACCEPTABLE_RANGE.min && count <= ICON_ACCEPTABLE_RANGE.max) {
    return 0.7;
  }
  if (count === 1) {
    return 0.3;
  }
  if (count > ICON_ACCEPTABLE_RANGE.max) {
    return 0.4; // 너무 많으면 아이콘이 작아짐
  }
  return 0.0;
}

/**
 * 슬라이드에서 항목 수 추출
 */
function getElementCount(slide) {
  // 명시적 element_count가 있으면 사용
  if (slide.element_count) {
    return slide.element_count;
  }

  // key_points 배열 길이
  if (Array.isArray(slide.key_points)) {
    return slide.key_points.length;
  }

  // items 배열
  if (Array.isArray(slide.items)) {
    return slide.items.length;
  }

  // data_slots의 cards 배열
  if (slide.data_slots?.cards) {
    return slide.data_slots.cards.length;
  }

  return 0;
}

/**
 * 슬라이드에서 키워드 추출
 */
function extractKeywords(slide) {
  const keywords = [];

  // 제목에서 추출
  if (slide.title) {
    keywords.push(...tokenize(slide.title));
  }

  // key_points에서 추출
  if (Array.isArray(slide.key_points)) {
    for (const point of slide.key_points) {
      if (typeof point === 'string') {
        keywords.push(...tokenize(point));
      } else if (point.title) {
        keywords.push(...tokenize(point.title));
      }
    }
  }

  // items에서 추출
  if (Array.isArray(slide.items)) {
    for (const item of slide.items) {
      if (typeof item === 'string') {
        keywords.push(...tokenize(item));
      } else if (item.title || item.name) {
        keywords.push(...tokenize(item.title || item.name));
      }
    }
  }

  // 중복 제거
  return [...new Set(keywords)].filter(k => k.length >= 2);
}

/**
 * 텍스트 토큰화 (한글, 영문, 숫자)
 */
function tokenize(text) {
  if (!text) return [];
  const tokens = text.match(/[\uAC00-\uD7A3]+|[a-zA-Z]+/g) || [];
  return tokens.filter(t => t.length >= 2);
}

/**
 * 키워드를 아이콘에 매핑
 */
function matchKeywordsToIcons(keywords, iconMappings) {
  if (!iconMappings?.mappings) {
    return [];
  }

  const mappings = iconMappings.mappings;
  const matched = [];

  for (const keyword of keywords) {
    const lowerKeyword = keyword.toLowerCase();

    // 1. 직접 매칭
    if (mappings[keyword]) {
      matched.push({
        keyword,
        icon: mappings[keyword].icon,
        match_type: 'direct'
      });
      continue;
    }

    // 2. 대소문자 무시 매칭
    for (const [key, value] of Object.entries(mappings)) {
      if (key.toLowerCase() === lowerKeyword) {
        matched.push({
          keyword,
          icon: value.icon,
          match_type: 'case_insensitive'
        });
        break;
      }
    }

    // 3. Alias 매칭
    for (const [key, value] of Object.entries(mappings)) {
      if (value.aliases?.some(a => a.toLowerCase() === lowerKeyword)) {
        matched.push({
          keyword,
          icon: value.icon,
          match_type: 'alias'
        });
        break;
      }
    }
  }

  // 중복 제거 (같은 아이콘이 여러 키워드에 매칭될 수 있음)
  const uniqueIcons = [];
  const seenIcons = new Set();

  for (const match of matched) {
    if (!seenIcons.has(match.icon)) {
      seenIcons.add(match.icon);
      uniqueIcons.push(match);
    }
  }

  return uniqueIcons;
}

/**
 * 템플릿의 아이콘 지원 여부 확인
 */
function checkTemplateIconSupport(template) {
  if (!template) return false;

  // template_id에 icon 포함
  if (template.id?.toLowerCase().includes('icon')) return true;

  // design_intent에 icon 포함
  if (template.design_intent?.toLowerCase().includes('icon')) return true;

  // metadata 태그에 icon 포함
  if (template.metadata?.tags?.includes('icon')) return true;

  // icon_support 명시
  if (template.icon_support) return true;

  return false;
}

/**
 * 판단 이유 생성
 */
function generateReason(factors, needsIcons, category, elementCount) {
  const reasons = [];

  if (factors.category_score >= 0.7) {
    reasons.push(`category:${category}`);
  }
  if (factors.element_count_score >= 0.7) {
    reasons.push(`elements:${elementCount}`);
  }
  if (factors.keyword_score >= 0.5) {
    reasons.push('keyword_match');
  }
  if (factors.template_supports) {
    reasons.push('template_support');
  }

  if (reasons.length === 0) {
    return needsIcons ? 'general_recommendation' : 'not_suitable';
  }

  return reasons.join('+');
}

/**
 * icon-mappings.yaml 로드
 */
function loadIconMappings(filePath) {
  try {
    const yaml = require('js-yaml');
    const content = fs.readFileSync(filePath, 'utf-8');
    return yaml.load(content);
  } catch (err) {
    console.error(`Failed to load icon mappings: ${err.message}`);
    return { mappings: {}, defaults: {} };
  }
}

// CLI 테스트 모드
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args[0] === '--test') {
    console.log('Running icon-decision tests...\n');

    // 테스트 케이스 1: grid 카테고리 + 4개 항목
    const slide1 = {
      title: '시스템 범위',
      purpose: 'grid',
      key_points: ['창고관리', '배송관리', '주문관리', '모니터링']
    };

    const template1 = { category: 'grid', id: 'deepgreen-grid-icon1' };

    // icon-mappings.yaml 로드
    const mappingsPath = path.join(__dirname, '../../../../templates-bak/assets/icon-mappings.yaml');
    let iconMappings = { mappings: {} };

    if (fs.existsSync(mappingsPath)) {
      iconMappings = loadIconMappings(mappingsPath);
    }

    const result1 = analyzeIconNeed(slide1, template1, iconMappings);
    console.log('Test 1 - Grid with 4 items:');
    console.log('  needs_icons:', result1.needs_icons);
    console.log('  confidence:', result1.confidence);
    console.log('  reason:', result1.reason);
    console.log('  matched:', result1.matched_keywords.length, 'keywords');
    console.log();

    // 테스트 케이스 2: cover 슬라이드
    const slide2 = {
      title: '제안서 표지',
      purpose: 'cover'
    };

    const template2 = { category: 'cover', id: 'deepgreen-cover1' };
    const result2 = analyzeIconNeed(slide2, template2, iconMappings);

    console.log('Test 2 - Cover slide:');
    console.log('  needs_icons:', result2.needs_icons);
    console.log('  confidence:', result2.confidence);
    console.log('  reason:', result2.reason);
    console.log();

    // 테스트 케이스 3: stats 슬라이드
    const slide3 = {
      title: '기대효과',
      purpose: 'stats',
      key_points: ['효율 30% 향상', '비용 20% 절감', '품질 99% 달성']
    };

    const template3 = { category: 'stats', id: 'deepgreen-stats1' };
    const result3 = analyzeIconNeed(slide3, template3, iconMappings);

    console.log('Test 3 - Stats with 3 items:');
    console.log('  needs_icons:', result3.needs_icons);
    console.log('  confidence:', result3.confidence);
    console.log('  reason:', result3.reason);
    console.log('  matched:', result3.matched_keywords.map(m => m.keyword).join(', '));
    console.log();

    console.log('All tests completed.');
  }
}

module.exports = {
  analyzeIconNeed,
  extractKeywords,
  matchKeywordsToIcons,
  checkTemplateIconSupport,
  loadIconMappings,
  ICON_SUITABLE_CATEGORIES,
  ICON_OPTIMAL_RANGE
};
