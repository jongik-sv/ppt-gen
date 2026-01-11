/**
 * Template Rematcher - 디자인 평가 실패 시 대안 템플릿 선택 (v5.7)
 *
 * 실패한 템플릿을 제외하고 최적의 대안 템플릿을 찾습니다.
 */

const fs = require('fs').promises;
const path = require('path');
const yaml = require('js-yaml');

/**
 * registry.yaml 로드
 */
async function loadRegistry(registryPath) {
  try {
    const content = await fs.readFile(registryPath, 'utf-8');
    return yaml.load(content);
  } catch (e) {
    console.error('Registry 로드 실패:', e.message);
    return [];
  }
}

/**
 * 대안 템플릿 선택
 *
 * @param {Object} slide - 슬라이드 정보 (purpose, content_bindings)
 * @param {string[]} failedTemplates - 실패한 템플릿 ID 목록
 * @param {Array} registry - 템플릿 레지스트리
 * @returns {Object|null} 선택된 대안 템플릿 또는 null
 */
function selectAlternative(slide, failedTemplates, registry) {
  if (!registry || !Array.isArray(registry)) {
    return null;
  }

  const purpose = slide.purpose;
  const contentCount = slide.content_bindings?.items?.length || 0;

  // 실패한 템플릿들의 design_intent 수집
  const failedIntents = new Set();
  for (const tid of failedTemplates) {
    const failed = registry.find(t => t.id === tid);
    if (failed?.design_intent) {
      failedIntents.add(failed.design_intent);
    }
  }

  // 1단계: 동일 category, 실패 템플릿 제외
  let candidates = registry.filter(t =>
    t.category === purpose &&
    !failedTemplates.includes(t.id)
  );

  // 2단계: element_count 근접 정렬
  if (contentCount > 0) {
    candidates.sort((a, b) => {
      const diffA = Math.abs((a.element_count || 0) - contentCount);
      const diffB = Math.abs((b.element_count || 0) - contentCount);
      return diffA - diffB;
    });
  }

  // 3단계: design_intent 다양성 (실패한 것과 다른 레이아웃 우선)
  const diverseCandidates = candidates.filter(c =>
    !failedIntents.has(c.design_intent)
  );

  if (diverseCandidates.length > 0) {
    return diverseCandidates[0];
  }

  // 4단계: 다양성 없으면 그냥 첫 번째 후보
  if (candidates.length > 0) {
    return candidates[0];
  }

  // 5단계: 같은 카테고리 없으면 다른 카테고리 확장 검색
  const relaxedCandidates = registry.filter(t =>
    !failedTemplates.includes(t.id) &&
    t.element_count &&
    contentCount >= (t.element_count - 1) &&
    contentCount <= (t.element_count + 2)
  );

  if (relaxedCandidates.length > 0) {
    // match_score 기준 정렬
    relaxedCandidates.sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
    return relaxedCandidates[0];
  }

  return null;
}

/**
 * 슬라이드별 재매칭 수행
 *
 * @param {Object} slide - 슬라이드 정보
 * @param {string[]} failedTemplates - 실패한 템플릿 ID 목록
 * @param {string} registryPath - registry.yaml 경로
 * @returns {Object} 재매칭 결과
 */
async function rematch(slide, failedTemplates, registryPath) {
  const registry = await loadRegistry(registryPath);
  const alternative = selectAlternative(slide, failedTemplates, registry);

  if (alternative) {
    return {
      success: true,
      template_id: alternative.id,
      template: alternative,
      match_score: alternative.match_score || 0.5,
      match_reason: `재매칭: ${failedTemplates.length}회 실패 후 대안 선택`,
      failed_templates: failedTemplates
    };
  }

  return {
    success: false,
    template_id: null,
    template: null,
    match_score: 0,
    match_reason: '대안 템플릿 없음',
    failed_templates: failedTemplates
  };
}

/**
 * 추천 대안 목록 반환 (평가 결과에 포함용)
 *
 * @param {Object} slide - 슬라이드 정보
 * @param {string[]} failedTemplates - 실패한 템플릿 ID 목록
 * @param {Array} registry - 템플릿 레지스트리
 * @param {number} limit - 최대 추천 수
 * @returns {string[]} 추천 템플릿 ID 목록
 */
function getAlternativeList(slide, failedTemplates, registry, limit = 3) {
  if (!registry || !Array.isArray(registry)) {
    return [];
  }

  const purpose = slide.purpose;
  const contentCount = slide.content_bindings?.items?.length || 0;

  // 동일 category, 실패 템플릿 제외
  let candidates = registry.filter(t =>
    t.category === purpose &&
    !failedTemplates.includes(t.id)
  );

  // element_count 근접 정렬
  if (contentCount > 0) {
    candidates.sort((a, b) => {
      const diffA = Math.abs((a.element_count || 0) - contentCount);
      const diffB = Math.abs((b.element_count || 0) - contentCount);
      return diffA - diffB;
    });
  }

  return candidates.slice(0, limit).map(t => t.id);
}

/**
 * 재매칭 가능 여부 확인
 *
 * @param {Object} slide - 슬라이드 정보
 * @param {string[]} failedTemplates - 실패한 템플릿 ID 목록
 * @param {Array} registry - 템플릿 레지스트리
 * @returns {boolean} 재매칭 가능 여부
 */
function canRematch(slide, failedTemplates, registry) {
  const alternative = selectAlternative(slide, failedTemplates, registry);
  return alternative !== null;
}

module.exports = {
  selectAlternative,
  rematch,
  getAlternativeList,
  canRematch,
  loadRegistry
};
