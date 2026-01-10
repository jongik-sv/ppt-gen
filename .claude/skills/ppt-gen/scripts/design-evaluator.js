/**
 * Design Evaluator - 슬라이드 디자인 품질 평가 모듈 (v5.7)
 *
 * HTML 슬라이드의 디자인 품질을 평가하고 합격/불합격을 판정합니다.
 * - 자동 검사: overflow, contrast, element_count, content_missing
 * - LLM 평가: 레이아웃, 타이포그래피, 색상, 콘텐츠 적합성, 시각 요소
 */

const fs = require('fs').promises;
const path = require('path');

// 슬라이드 크기 (pt)
const SLIDE_WIDTH = 720;
const SLIDE_HEIGHT = 405;

// 합격 기준
const PASS_THRESHOLD = 70;

// 카테고리별 최대 점수
const CATEGORY_MAX = {
  layout: 25,
  typography: 20,
  color: 20,
  content_fit: 25,
  visual: 10
};

/**
 * 색상 대비 계산 (WCAG 기준)
 */
function getLuminance(hex) {
  const rgb = hexToRgb(hex);
  if (!rgb) return 0;

  const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(v => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function hexToRgb(hex) {
  if (!hex) return null;
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

function getContrastRatio(color1, color2) {
  const l1 = getLuminance(color1);
  const l2 = getLuminance(color2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * HTML에서 색상 쌍 추출
 */
function extractColorPairs(html) {
  const pairs = [];

  // background-color와 color 패턴 매칭
  const bgPattern = /background(?:-color)?:\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}|rgba?\([^)]+\))/gi;
  const colorPattern = /(?<!background-)color:\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}|rgba?\([^)]+\))/gi;

  const bgColors = [...html.matchAll(bgPattern)].map(m => m[1]);
  const textColors = [...html.matchAll(colorPattern)].map(m => m[1]);

  // 기본 배경색 (white)
  const defaultBg = '#FFFFFF';

  for (const textColor of textColors) {
    const hex = normalizeColor(textColor);
    if (hex) {
      // 가장 가까운 배경색 찾기 (간단화: 첫 번째 배경색 사용)
      const bgHex = bgColors.length > 0 ? normalizeColor(bgColors[0]) : defaultBg;
      if (bgHex) {
        pairs.push({ bg: bgHex, fg: hex });
      }
    }
  }

  return pairs;
}

function normalizeColor(color) {
  if (!color) return null;

  // HEX
  if (color.startsWith('#')) {
    if (color.length === 4) {
      // #RGB -> #RRGGBB
      return '#' + color[1] + color[1] + color[2] + color[2] + color[3] + color[3];
    }
    return color.toUpperCase();
  }

  // rgba/rgb - 간단히 불투명 색상만 처리
  const rgbMatch = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (rgbMatch) {
    const [, r, g, b] = rgbMatch;
    return '#' + [r, g, b].map(v => parseInt(v).toString(16).padStart(2, '0')).join('').toUpperCase();
  }

  return null;
}

/**
 * 자동 검사 수행
 */
function runAutoChecks(html, slide, template) {
  const failures = [];
  const issues = [];

  // 1. Overflow 검사
  const widthMatch = html.match(/width:\s*(\d+)pt/);
  const heightMatch = html.match(/height:\s*(\d+)pt/);

  if (widthMatch && parseInt(widthMatch[1]) > SLIDE_WIDTH) {
    failures.push('overflow');
    issues.push(`너비 초과: ${widthMatch[1]}pt > ${SLIDE_WIDTH}pt`);
  }
  if (heightMatch && parseInt(heightMatch[1]) > SLIDE_HEIGHT) {
    failures.push('overflow');
    issues.push(`높이 초과: ${heightMatch[1]}pt > ${SLIDE_HEIGHT}pt`);
  }

  // 2. 색상 대비 검사 (WCAG AA: 4.5:1)
  const colorPairs = extractColorPairs(html);
  for (const pair of colorPairs) {
    const ratio = getContrastRatio(pair.bg, pair.fg);
    if (ratio < 4.5) {
      failures.push('contrast_failure');
      issues.push(`대비 부족: ${pair.fg}/${pair.bg} = ${ratio.toFixed(2)} (최소 4.5)`);
      break; // 첫 번째 실패만 기록
    }
  }

  // 3. Element Count 검사
  if (template && template.element_count && slide.content_bindings?.items) {
    const contentCount = slide.content_bindings.items.length;
    const templateCount = template.element_count;
    const diff = Math.abs(contentCount - templateCount);

    if (diff >= 2) {
      failures.push('element_count_mismatch');
      issues.push(`요소 수 불일치: 콘텐츠 ${contentCount}개, 템플릿 ${templateCount}개 (차이 ${diff})`);
    }
  }

  // 4. 필수 콘텐츠 검사
  const hasTitle = html.includes(slide.title) ||
                   html.toLowerCase().includes('<h1') ||
                   html.toLowerCase().includes('<h2');

  if (!hasTitle && slide.title) {
    failures.push('content_missing');
    issues.push('제목 누락');
  }

  return {
    hasCriticalFailure: failures.length > 0,
    failures: [...new Set(failures)], // 중복 제거
    issues
  };
}

/**
 * LLM 평가 결과 파싱
 */
function parseLLMResponse(response) {
  try {
    // JSON 블록 추출
    const jsonMatch = response.match(/```json\s*([\s\S]*?)\s*```/) ||
                      response.match(/\{[\s\S]*"total_score"[\s\S]*\}/);

    if (jsonMatch) {
      const jsonStr = jsonMatch[1] || jsonMatch[0];
      return JSON.parse(jsonStr);
    }
  } catch (e) {
    console.error('LLM 응답 파싱 실패:', e.message);
  }

  // 파싱 실패 시 기본값
  return {
    total_score: 50,
    passed: false,
    details: {
      layout: { score: 12, max: 25, issues: ['평가 파싱 실패'] },
      typography: { score: 10, max: 20, issues: [] },
      color: { score: 10, max: 20, issues: [] },
      content_fit: { score: 12, max: 25, issues: [] },
      visual: { score: 6, max: 10, issues: [] }
    },
    critical_failures: null,
    improvement_suggestions: ['LLM 평가 재시도 권장'],
    alternative_templates: []
  };
}

/**
 * 결과 병합
 */
function mergeResults(autoChecks, llmResult) {
  // Critical failure가 있으면 불합격
  if (autoChecks.hasCriticalFailure) {
    return {
      current_score: 0,
      passed: false,
      selected_reason: null,
      details: llmResult?.details || null,
      critical_failures: autoChecks.failures,
      improvement_suggestions: autoChecks.issues,
      alternative_templates: llmResult?.alternative_templates || []
    };
  }

  // LLM 결과 사용
  const score = llmResult.total_score;
  const passed = score >= PASS_THRESHOLD;

  return {
    current_score: score,
    passed,
    selected_reason: passed ? 'passed' : null,
    details: llmResult.details,
    critical_failures: llmResult.critical_failures,
    improvement_suggestions: llmResult.improvement_suggestions || [],
    alternative_templates: llmResult.alternative_templates || []
  };
}

/**
 * 디자인 평가 메인 함수
 *
 * @param {Object} options
 * @param {string} options.html - HTML 슬라이드 코드
 * @param {Object} options.slide - 슬라이드 정보 (purpose, title, key_points, content_bindings)
 * @param {Object} options.template - 템플릿 정보 (id, category, element_count)
 * @param {Object} options.theme - 테마 정보 (colors)
 * @param {Function} options.llmEvaluate - LLM 평가 함수 (optional, for testing)
 * @returns {Object} 평가 결과
 */
async function evaluate(options) {
  const { html, slide, template, theme, llmEvaluate } = options;

  // 1. 자동 검사
  const autoChecks = runAutoChecks(html, slide, template);

  // Critical failure 발견 시 LLM 스킵
  if (autoChecks.hasCriticalFailure) {
    return {
      attempt_number: 1,
      current_score: 0,
      passed: false,
      selected_reason: null,
      details: null,
      critical_failures: autoChecks.failures,
      improvement_suggestions: autoChecks.issues,
      alternative_templates: []
    };
  }

  // 2. LLM 평가 (제공된 함수 사용 또는 기본 점수)
  let llmResult;
  if (llmEvaluate && typeof llmEvaluate === 'function') {
    const response = await llmEvaluate({
      html,
      slide,
      template,
      theme
    });
    llmResult = parseLLMResponse(response);
  } else {
    // LLM 없이 자동 검사 통과 시 기본 점수 부여
    llmResult = {
      total_score: 75,
      passed: true,
      details: {
        layout: { score: 20, max: 25, issues: [] },
        typography: { score: 15, max: 20, issues: [] },
        color: { score: 15, max: 20, issues: [] },
        content_fit: { score: 18, max: 25, issues: [] },
        visual: { score: 7, max: 10, issues: [] }
      },
      critical_failures: null,
      improvement_suggestions: [],
      alternative_templates: []
    };
  }

  // 3. 결과 병합
  const result = mergeResults(autoChecks, llmResult);

  return {
    attempt_number: 1, // 호출자가 업데이트
    ...result
  };
}

/**
 * 여러 슬라이드 평가 (병렬)
 */
async function evaluateAll(slides, options = {}) {
  const { theme, registry, llmEvaluate } = options;

  const results = await Promise.all(
    slides.map(async (slide) => {
      const html = await fs.readFile(slide.html_file, 'utf-8').catch(() => '');
      const template = registry?.find(t => t.id === slide.template_id);

      const evaluation = await evaluate({
        html,
        slide,
        template,
        theme,
        llmEvaluate
      });

      return {
        index: slide.index,
        evaluation,
        needs_retry: !evaluation.passed
      };
    })
  );

  return results;
}

/**
 * 평가 루프 실행 (최대 3회)
 *
 * @param {Object} slide - 슬라이드 데이터
 * @param {Object} options - 옵션 (theme, registry, llmEvaluate, rematcher)
 * @returns {Object} 최종 평가 결과 (evaluation, attempt_history)
 */
async function runEvaluationLoop(slide, options) {
  const { theme, registry, llmEvaluate, rematcher, generateHtml } = options;

  const attemptHistory = [];
  let currentSlide = { ...slide };
  let bestAttempt = null;

  for (let attempt = 1; attempt <= 3; attempt++) {
    // HTML 읽기
    const html = await fs.readFile(currentSlide.html_file, 'utf-8').catch(() => '');
    const template = registry?.find(t => t.id === currentSlide.template_id);

    // 평가
    const evaluation = await evaluate({
      html,
      slide: currentSlide,
      template,
      theme,
      llmEvaluate
    });

    evaluation.attempt_number = attempt;

    // 기록
    const attemptRecord = {
      attempt,
      template_id: currentSlide.template_id,
      html_file: currentSlide.html_file,
      score: evaluation.current_score,
      passed: evaluation.passed,
      critical_failures: evaluation.critical_failures,
      issues: evaluation.improvement_suggestions,
      timestamp: new Date().toISOString()
    };
    attemptHistory.push(attemptRecord);

    // 최고 점수 업데이트
    if (!bestAttempt || evaluation.current_score > bestAttempt.score) {
      bestAttempt = attemptRecord;
    }

    // 합격 시 종료
    if (evaluation.passed) {
      return {
        evaluation: {
          ...evaluation,
          selected_reason: 'passed'
        },
        attempt_history: attemptHistory,
        final_template_id: currentSlide.template_id,
        final_html_file: currentSlide.html_file
      };
    }

    // 3회 실패 시 best_of_3 선택
    if (attempt === 3) {
      return {
        evaluation: {
          attempt_number: bestAttempt.attempt,
          current_score: bestAttempt.score,
          passed: false,
          selected_reason: 'best_of_3',
          details: null, // 상세 정보는 attempt_history에서 확인
          critical_failures: bestAttempt.critical_failures
        },
        attempt_history: attemptHistory,
        final_template_id: bestAttempt.template_id,
        final_html_file: bestAttempt.html_file
      };
    }

    // 재매칭
    if (rematcher && typeof rematcher === 'function') {
      const failedTemplates = attemptHistory.map(a => a.template_id);
      const newTemplate = await rematcher(currentSlide, failedTemplates, registry);

      if (newTemplate) {
        currentSlide.template_id = newTemplate.id;

        // HTML 재생성 (generateHtml 함수 제공 시)
        if (generateHtml && typeof generateHtml === 'function') {
          const newHtmlFile = await generateHtml(currentSlide, newTemplate, theme);
          currentSlide.html_file = newHtmlFile;
        }
      }
    }
  }

  // fallback (도달하지 않음)
  return {
    evaluation: { passed: false, current_score: 0 },
    attempt_history: attemptHistory
  };
}

module.exports = {
  evaluate,
  evaluateAll,
  runEvaluationLoop,
  runAutoChecks,
  getContrastRatio,
  PASS_THRESHOLD,
  CATEGORY_MAX
};
