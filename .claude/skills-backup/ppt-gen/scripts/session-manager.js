/**
 * Session Manager for PPT Generation Pipeline (v5.6)
 *
 * 슬라이드별 플랫 구조 PPT 생성 파이프라인 세션 관리:
 * 1단계(Setup) → 2단계(Outline) → 3단계(Matching) → 4단계(Content) → 5단계(PPTX)
 *
 * 데이터 구조:
 * - setup: 전역 설정 (1단계)
 * - slides[]: 슬라이드별 플랫 데이터 (2~5단계 누적)
 *
 * v5.6 확장 필드:
 * - Stage-2: source_content (원본 콘텐츠)
 * - Stage-3: layout_match, content_template, icon_decision (매칭 결정)
 * - Stage-4: content_bindings, style_applied, assets_generated, image_prompts
 * - Stage-5: generation (생성 메타)
 *
 * 생성 방식:
 * - HTML 기반: html_file, assets, text_content
 * - OOXML 기반: ooxml_bindings (문서양식 편집)
 * - SVG: 정적 그래픽으로만 사용 (바인딩 불가)
 *
 * USAGE:
 *   const SessionManager = require('./session-manager');
 *
 *   // 새 세션 생성
 *   const session = await SessionManager.create('스마트 물류 제안서');
 *
 *   // 1단계: 전역 설정
 *   await session.completeSetup({ presentation: {...}, theme: {...} });
 *
 *   // 2~5단계: 슬라이드별 데이터 누적 (deep merge 지원)
 *   await session.updateSlide(0, { title: '표지', purpose: 'cover' });
 *   await session.updateSlide(0, { content_template: { id: 'cover-centered1', match_score: 0.9 } });
 *   await session.updateSlide(0, { content_bindings: { title: '표지', items: [...] } });
 *   await session.updateSlide(0, { generation: { method: 'html2pptx' } });
 *
 *   // 세션 재개
 *   const session = await SessionManager.resume('2026-01-09_143025_a7b2c3d4');
 *
 *   // 슬라이드 재실행
 *   const ctx = await session.rerunSlide(3, 4);  // Stage-4부터 재실행
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

const DEFAULT_OUTPUT_DIR = path.join(process.cwd(), 'output');

/**
 * Deep merge utility - 중첩 객체를 재귀적으로 병합
 * 배열은 교체, 객체는 재귀 병합
 * @param {Object} target - 대상 객체
 * @param {Object} source - 소스 객체
 * @returns {Object} 병합된 객체
 */
function deepMerge(target, source) {
  if (!source || typeof source !== 'object') return target;
  if (!target || typeof target !== 'object') return source;

  const result = { ...target };

  for (const key of Object.keys(source)) {
    const sourceVal = source[key];
    const targetVal = result[key];

    if (Array.isArray(sourceVal)) {
      // 배열은 교체 (병합하지 않음)
      result[key] = [...sourceVal];
    } else if (sourceVal && typeof sourceVal === 'object' && !Array.isArray(sourceVal)) {
      // 객체는 재귀 병합
      if (targetVal && typeof targetVal === 'object' && !Array.isArray(targetVal)) {
        result[key] = deepMerge(targetVal, sourceVal);
      } else {
        result[key] = { ...sourceVal };
      }
    } else {
      // 원시값은 직접 대입
      result[key] = sourceVal;
    }
  }

  return result;
}

const STATUS = {
  IN_PROGRESS: 'in_progress',
  PAUSED: 'paused',
  COMPLETED: 'completed',
  FAILED: 'failed'
};

const STAGE_FILES = {
  1: 'stage-1-setup.json',
  2: 'stage-2-outline.json',
  3: 'stage-3-matching.json',
  4: 'stage-4-content.json',
  5: 'stage-5-generation.json'
};

/**
 * 세션 ID 생성
 * @param {string} name - 프로젝트 이름 (선택적)
 * @returns {string} 형식: YYYY-MM-DD_HHMMSS_name (예: 2026-01-09_134636_project-plan)
 */
function generateSessionId(name = null) {
  const now = new Date();
  const date = now.toISOString().split('T')[0];
  const time = now.toTimeString().split(' ')[0].replace(/:/g, '');

  if (name) {
    // 프로젝트 이름을 URL-safe 형식으로 변환
    const safeName = name
      .toLowerCase()
      .replace(/[가-힣]+/g, (match) => {
        // 한글은 영문 키워드로 변환 (간단한 매핑)
        const mappings = {
          '프로젝트': 'project', '계획': 'plan', '수행': 'execution',
          '보고서': 'report', '제안서': 'proposal', '발표': 'presentation'
        };
        for (const [kr, en] of Object.entries(mappings)) {
          if (match.includes(kr)) return en;
        }
        return 'doc';
      })
      .replace(/[^a-z0-9]+/g, '-')  // 특수문자 → 하이픈
      .replace(/^-+|-+$/g, '')       // 앞뒤 하이픈 제거
      .substring(0, 30);             // 최대 30자

    return `${date}_${time}_${safeName || 'untitled'}`;
  }

  // 이름 없으면 랜덤 해시 사용 (기존 방식)
  const hash = crypto.randomBytes(4).toString('hex');
  return `${date}_${time}_${hash}`;
}

/**
 * Session 클래스 - 슬라이드별 플랫 구조
 */
class Session {
  constructor(id, sessionDir, state = {}) {
    this.id = id;
    this.sessionDir = sessionDir;
    this.state = state;
  }

  async save(stageNum) {
    this.state.session.updated_at = new Date().toISOString();
    const stageFile = path.join(this.sessionDir, STAGE_FILES[stageNum]);
    await fs.writeFile(stageFile, JSON.stringify(this.state, null, 2), 'utf-8');
  }

  // === 1단계: Setup (전역 설정) ===
  async completeSetup(data) {
    this.state.setup = {
      ...data,
      completed_at: new Date().toISOString()
    };
    this.state.current_stage = 1;
    this.state.slides = [];
    await this.save(1);
    return this.state.setup;
  }

  // === 2~5단계: 슬라이드 데이터 누적 (deep merge) ===
  async updateSlide(index, data) {
    await this._loadLatestState();

    // 슬라이드 찾기 또는 생성
    let slideIndex = this.state.slides.findIndex(s => s.index === index);
    if (slideIndex === -1) {
      this.state.slides.push({ index });
      this.state.slides.sort((a, b) => a.index - b.index);
      slideIndex = this.state.slides.findIndex(s => s.index === index);
    }

    // Deep merge로 중첩 객체 병합 지원
    const slide = deepMerge(this.state.slides[slideIndex], data);
    this.state.slides[slideIndex] = slide;

    // 현재 단계 추론
    const stage = this._inferStage(slide);
    this.state.current_stage = Math.max(this.state.current_stage || 1, stage);

    await this.save(stage);
    return slide;
  }

  // 슬라이드 데이터에서 현재 단계 추론 (v5.5 확장)
  _inferStage(slide) {
    // Stage-5: 생성 완료
    if (slide.generated || slide.generation) return 5;

    // Stage-4: 콘텐츠 바인딩 + 에셋 생성
    if (slide.content_bindings || slide.style_applied ||
        slide.html_file || slide.ooxml_bindings) return 4;

    // Stage-3: 템플릿 매칭
    if (slide.layout_match || slide.content_template ||
        slide.template_id || slide.icon_decision) return 3;

    // Stage-2: 아웃라인
    if (slide.source_content || slide.title || slide.purpose) return 2;

    return 1;
  }

  // === 5단계: 최종 생성 완료 ===
  async completeGeneration(outputData) {
    await this._loadLatestState();

    this.state.output = {
      ...outputData,
      completed_at: new Date().toISOString()
    };
    this.state.session.status = STATUS.COMPLETED;
    this.state.current_stage = 5;

    await this.save(5);
    return this.state.output;
  }

  // === 유틸리티 ===
  async _loadLatestState() {
    for (let i = 5; i >= 1; i--) {
      const stageFile = path.join(this.sessionDir, STAGE_FILES[i]);
      try {
        const content = await fs.readFile(stageFile, 'utf-8');
        this.state = JSON.parse(content);
        return;
      } catch (err) {
        if (err.code !== 'ENOENT') throw err;
      }
    }
  }

  async readLatestState() {
    await this._loadLatestState();
    return this.state;
  }

  getSlide(index) {
    return this.state.slides?.find(s => s.index === index);
  }

  getSlidesDir() {
    return path.join(this.sessionDir, 'slides');
  }

  getAssetsDir() {
    return path.join(this.sessionDir, 'assets');
  }

  getOutputPath() {
    return path.join(this.sessionDir, 'output.pptx');
  }

  getThumbnailsDir() {
    return path.join(this.sessionDir, 'thumbnails');
  }

  getSummary() {
    return {
      id: this.id,
      title: this.state.session?.title,
      status: this.state.session?.status,
      current_stage: this.state.current_stage,
      slide_count: this.state.slides?.length || 0,
      created_at: this.state.session?.created_at,
      updated_at: this.state.session?.updated_at,
      path: this.sessionDir
    };
  }

  // === 슬라이드 재실행 지원 (v5.5) ===

  /**
   * 특정 슬라이드 재실행 컨텍스트 생성
   * @param {number} index - 슬라이드 인덱스
   * @param {number} fromStage - 시작 단계 (2~5)
   * @returns {Object} 재실행에 필요한 컨텍스트
   */
  async rerunSlide(index, fromStage = 3) {
    await this._loadLatestState();

    const slideIndex = this.state.slides.findIndex(s => s.index === index);
    if (slideIndex === -1) {
      throw new Error(`Slide ${index} not found`);
    }

    const slide = this.state.slides[slideIndex];
    const context = {
      slide: { ...slide },  // 복사본
      setup: this.state.setup,
      theme: this.state.setup?.theme,
      previous_slides: this.state.slides.filter(s => s.index < index),
      rerun_from: fromStage,
      preserved: {}
    };

    // Stage-2 데이터는 항상 유지 (source_content)
    if (slide.source_content) {
      context.preserved.source_content = slide.source_content;
    }

    // 재실행 시작점에 따라 상태 리셋
    if (fromStage <= 3) {
      delete slide.layout_match;
      delete slide.content_template;
      delete slide.icon_decision;
      delete slide.template_id;
      delete slide.match_score;
    }
    if (fromStage <= 4) {
      delete slide.content_bindings;
      delete slide.style_applied;
      delete slide.assets_generated;
      delete slide.image_prompts;
      delete slide.html_file;
    }
    if (fromStage <= 5) {
      delete slide.generation;
      delete slide.generated;
    }

    await this.save(Math.max(1, fromStage - 1));
    return context;
  }

  /**
   * 슬라이드 디자인 결정 요약 생성 (디버깅/문서화용)
   * @param {number} index - 슬라이드 인덱스
   * @returns {Object|null} 디자인 요약
   */
  getSlideDesignSummary(index) {
    const slide = this.getSlide(index);
    if (!slide) return null;

    return {
      index: slide.index,
      title: slide.title,
      purpose: slide.purpose,
      stage: this._inferStage(slide),
      decisions: {
        layout: slide.layout_match?.layout_name || slide.layout_name,
        layout_reason: slide.layout_match?.reason || slide.match_reason,
        template: slide.content_template?.id || slide.template_id,
        template_score: slide.content_template?.match_score || slide.match_score,
        icons_used: slide.icon_decision?.needs_icons || false,
        icon_count: slide.icon_decision?.matched_keywords?.length || 0
      },
      content: {
        bindings_count: slide.content_bindings?.items?.length || 0,
        has_source: !!slide.source_content
      },
      assets: {
        icons: slide.assets_generated?.icons?.length || 0,
        images: slide.assets_generated?.images?.length || 0,
        prompts: slide.image_prompts?.length || 0
      },
      style: {
        theme: slide.style_applied?.theme_id,
        tokens_used: slide.style_applied?.tokens_used?.length || 0
      },
      generated: !!(slide.generation?.generated_at || slide.generated),
      html_file: slide.html_file
    };
  }

  /**
   * 모든 슬라이드의 디자인 요약 목록
   * @returns {Array} 디자인 요약 배열
   */
  getAllSlideDesignSummaries() {
    if (!this.state.slides) return [];
    return this.state.slides.map(s => this.getSlideDesignSummary(s.index));
  }

  // === 디자인 평가 루프 지원 (v5.7) ===

  /**
   * 슬라이드 평가 결과 저장
   * @param {number} index - 슬라이드 인덱스
   * @param {Object} evaluation - 평가 결과 객체
   * @returns {Object} 업데이트된 슬라이드
   */
  async saveEvaluation(index, evaluation) {
    await this._loadLatestState();

    const slide = this.getSlide(index);
    if (!slide) throw new Error(`Slide ${index} not found`);

    // attempt_history 초기화 또는 추가
    if (!slide.attempt_history) slide.attempt_history = [];

    // 현재 시도 기록 추가
    const attemptRecord = {
      attempt: slide.attempt_history.length + 1,
      template_id: slide.template_id,
      html_file: slide.html_file,
      score: evaluation.current_score,
      passed: evaluation.passed,
      critical_failures: evaluation.critical_failures,
      issues: this._extractIssues(evaluation.details),
      timestamp: new Date().toISOString()
    };
    slide.attempt_history.push(attemptRecord);

    // 평가 결과 저장
    slide.evaluation = {
      attempt_number: attemptRecord.attempt,
      current_score: evaluation.current_score,
      passed: evaluation.passed,
      selected_reason: evaluation.selected_reason,
      details: evaluation.details,
      critical_failures: evaluation.critical_failures
    };

    await this.save(4);
    return slide;
  }

  /**
   * 평가 세부 정보에서 issues 배열 추출
   * @private
   */
  _extractIssues(details) {
    if (!details) return [];
    const issues = [];
    for (const category of ['layout', 'typography', 'color', 'content_fit', 'visual']) {
      if (details[category]?.issues) {
        issues.push(...details[category].issues);
      }
    }
    return issues;
  }

  /**
   * 재매칭을 위한 슬라이드 리셋
   * 평가 데이터(attempt_history)는 유지하고 템플릿/콘텐츠 관련만 리셋
   * @param {number} index - 슬라이드 인덱스
   * @returns {Object} 리셋된 슬라이드
   */
  async resetForRematching(index) {
    await this._loadLatestState();

    const slide = this.getSlide(index);
    if (!slide) throw new Error(`Slide ${index} not found`);

    // 평가 데이터는 유지
    const preservedData = {
      attempt_history: slide.attempt_history,
      evaluation: slide.evaluation
    };

    // 템플릿/콘텐츠 관련 리셋
    delete slide.template_id;
    delete slide.object_id;
    delete slide.match_score;
    delete slide.layout;
    delete slide.html_file;
    delete slide.assets;
    delete slide.text_content;
    delete slide.content_bindings;
    delete slide.ooxml_bindings;

    // 평가 데이터 복원
    Object.assign(slide, preservedData);

    await this.save(3);  // Stage 3으로 롤백
    return slide;
  }

  /**
   * 디자인 평가 루프 완료 처리
   * 3회 실패 시 best_of_3 선택
   * @param {number} index - 슬라이드 인덱스
   * @param {Object} bestAttempt - 최고 점수 시도 정보
   */
  async finalizeBestOf3(index, bestAttempt) {
    await this._loadLatestState();

    const slide = this.getSlide(index);
    if (!slide) throw new Error(`Slide ${index} not found`);

    // 최고 점수 시도의 데이터로 복원
    slide.template_id = bestAttempt.template_id;
    slide.html_file = bestAttempt.html_file;

    // 평가 결과 업데이트
    slide.evaluation = {
      ...slide.evaluation,
      attempt_number: bestAttempt.attempt,
      current_score: bestAttempt.score,
      passed: false,
      selected_reason: 'best_of_3'
    };

    await this.save(4);
    return slide;
  }

  /**
   * 슬라이드의 평가 상태 조회
   * @param {number} index - 슬라이드 인덱스
   * @returns {Object|null} 평가 상태 요약
   */
  getEvaluationStatus(index) {
    const slide = this.getSlide(index);
    if (!slide) return null;

    return {
      index: slide.index,
      template_id: slide.template_id,
      attempt_count: slide.attempt_history?.length || 0,
      current_score: slide.evaluation?.current_score,
      passed: slide.evaluation?.passed || false,
      selected_reason: slide.evaluation?.selected_reason,
      critical_failures: slide.evaluation?.critical_failures,
      best_score: slide.attempt_history?.reduce(
        (max, a) => Math.max(max, a.score), 0
      ) || 0
    };
  }

  /**
   * 모든 슬라이드의 평가 상태 조회
   * @returns {Array} 평가 상태 배열
   */
  getAllEvaluationStatus() {
    if (!this.state.slides) return [];
    return this.state.slides.map(s => this.getEvaluationStatus(s.index));
  }
}

/**
 * SessionManager 클래스
 */
class SessionManager {
  constructor(outputDir = DEFAULT_OUTPUT_DIR) {
    this.outputDir = outputDir;
  }

  async create(title = 'Untitled Presentation') {
    const sessionId = generateSessionId(title);
    const sessionDir = path.join(this.outputDir, sessionId);

    await fs.mkdir(sessionDir, { recursive: true });
    await fs.mkdir(path.join(sessionDir, 'slides'), { recursive: true });
    await fs.mkdir(path.join(sessionDir, 'assets'), { recursive: true });
    await fs.mkdir(path.join(sessionDir, 'assets', 'icons'), { recursive: true });
    await fs.mkdir(path.join(sessionDir, 'assets', 'images'), { recursive: true });
    await fs.mkdir(path.join(sessionDir, 'thumbnails'), { recursive: true });

    const state = {
      session: {
        id: sessionId,
        title: title,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: STATUS.IN_PROGRESS
      },
      current_stage: 0,
      setup: null,
      slides: [],
      output: null
    };

    return new Session(sessionId, sessionDir, state);
  }

  async resume(sessionId) {
    const sessionDir = path.join(this.outputDir, sessionId);
    const session = new Session(sessionId, sessionDir, {});
    await session._loadLatestState();

    if (!session.state.session) {
      throw new Error(`Session not found: ${sessionId}`);
    }

    return session;
  }

  async listSessions() {
    try {
      const dirs = await fs.readdir(this.outputDir);
      const sessions = [];

      for (const dir of dirs) {
        const sessionDir = path.join(this.outputDir, dir);
        const session = new Session(dir, sessionDir, {});

        try {
          await session._loadLatestState();
          if (session.state.session) {
            sessions.push(session.getSummary());
          }
        } catch (err) {
          // Skip invalid sessions
        }
      }

      sessions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      return sessions;
    } catch (err) {
      if (err.code === 'ENOENT') return [];
      throw err;
    }
  }

  async getInProgressSessions() {
    const sessions = await this.listSessions();
    return sessions.filter(s => s.status === STATUS.IN_PROGRESS || s.status === STATUS.PAUSED);
  }

  async deleteSession(sessionId) {
    const sessionDir = path.join(this.outputDir, sessionId);
    await fs.rm(sessionDir, { recursive: true, force: true });
  }
}

const defaultManager = new SessionManager();

module.exports = {
  SessionManager,
  Session,
  STATUS,
  STAGE_FILES,
  generateSessionId,
  deepMerge,  // v5.5: 유틸리티 함수 export
  create: (title) => defaultManager.create(title),
  resume: (sessionId) => defaultManager.resume(sessionId),
  listSessions: () => defaultManager.listSessions(),
  getInProgressSessions: () => defaultManager.getInProgressSessions(),
  deleteSession: (sessionId) => defaultManager.deleteSession(sessionId)
};
