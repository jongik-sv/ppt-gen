/**
 * Stage 4 렌더링 스크립트
 * YAML 템플릿 기반 HTML 생성 (Option C 구현)
 *
 * Usage:
 *   node stage4-render.js <session-dir>
 *   node stage4-render.js output/2026-01-09_project-plan
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// html-templates.js에서 함수 가져오기
const { renderFromYaml, loadTemplate, CANVAS } = require('./html-templates');

// 세션 디렉토리
const sessionDir = process.argv[2];

if (!sessionDir) {
  console.error('Usage: node stage4-render.js <session-dir>');
  process.exit(1);
}

// 경로 설정
const stage4Path = path.join(sessionDir, 'stage-4-content.json');
const slidesDir = path.join(sessionDir, 'slides');

// 테마 색상 (deepgreen-clean)
const DEEPGREEN_THEME = {
  primary: '#153325',
  secondary: '#22523B',
  accent: '#479374',
  background: '#FFFFFF',
  surface: '#A1BFB4',
  dark_text: '#183C2B',
  light: '#FFFFFF',
  gray: '#859C80'
};

/**
 * 템플릿 로드 (로컬 버전)
 * YAML 구조: content_template, design_meta, canvas, shapes가 동일 레벨
 */
async function loadTemplateLocal(templateId) {
  const templatesBase = path.join(__dirname, '../../../../templates/contents/templates');

  // 카테고리 디렉토리 목록
  const categories = [
    'chart', 'closing', 'comparison', 'content', 'cover', 'cycle',
    'diagram', 'feature', 'flow', 'grid', 'hierarchy', 'matrix',
    'process', 'quote', 'section', 'stats', 'table', 'timeline', 'toc'
  ];

  for (const category of categories) {
    const templatePath = path.join(templatesBase, category, `${templateId}.yaml`);
    if (fs.existsSync(templatePath)) {
      try {
        const content = fs.readFileSync(templatePath, 'utf-8');
        const template = yaml.load(content);

        // YAML 구조: content_template, shapes 등이 동일 레벨
        // content_template 내부 속성과 루트 레벨 속성 병합
        const merged = {
          ...(template.content_template || {}),
          shapes: template.shapes || [],
          canvas: template.canvas || {},
          design_meta: template.design_meta || {},
          zones: template.zones || [],
          layout: template.layout || {},
          _category: category
        };

        // id가 없으면 content_template에서 가져오기
        if (!merged.id && template.content_template?.id) {
          merged.id = template.content_template.id;
        }
        // 기본 형태의 템플릿 (content_template 없이 바로 shapes)
        if (!template.content_template && template.shapes) {
          return {
            ...template,
            _category: category
          };
        }

        return merged;
      } catch (err) {
        console.warn(`Failed to load ${templatePath}: ${err.message}`);
      }
    }
  }

  console.warn(`Template not found: ${templateId}`);
  return null;
}

/**
 * shape_source가 description인지 확인
 */
function hasDescriptionShapes(template) {
  if (!template || !template.shapes || !Array.isArray(template.shapes)) {
    return false;
  }

  // 모든 shapes가 description 타입인 경우만 true
  return template.shapes.every(shape =>
    shape.shape_source === 'description' || !shape.shape_source
  );
}

/**
 * content_bindings를 YAML placeholders에 맞게 매핑
 * YAML placeholders: 중제목, 소제목, 본문, title, subtitle 등
 *
 * v2.0: 섹션별 0-based 인덱싱 지원
 * - 중제목_0, 중제목_1 형식으로 각 섹션에 다른 데이터 바인딩
 * - html-templates.js의 sectionIndex와 연동
 */
function mapBindingsToPlaceholders(template, bindings, slideTitle) {
  // bindings 데이터를 YAML placeholders에 맞게 변환
  const mapped = { ...bindings };
  const templateId = template?.id || template?.content_template?.id || '';

  // 슬라이드 제목을 중제목으로 사용 (전역)
  if (slideTitle) {
    mapped['중제목'] = slideTitle;
    mapped['title'] = slideTitle;
  }

  // ============================================================
  // content-stack1: 2섹션 세로 레이아웃 (0-based 인덱싱)
  // shape 0-1 → section 0, shape 2-3 → section 1
  // ============================================================
  if (templateId.includes('content-stack1') || bindings.sections?.length === 2) {
    const sections = bindings.sections || [];

    // 섹션별 데이터 매핑
    sections.forEach((section, i) => {
      mapped[`중제목_${i}`] = section.title || section.중제목 || '';
      mapped[`소제목_${i}`] = section.subtitle || section.소제목 || '';
      mapped[`본문_${i}`] = Array.isArray(section.content)
        ? section.content.join('\n')
        : (section.content || section.본문 || '');
    });

    // 레거시: project_name이 있으면 기존 방식으로도 매핑
    if (bindings.project_name && !bindings.sections) {
      mapped['중제목_0'] = '프로젝트 정보';
      mapped['소제목_0'] = bindings.project_name;
      mapped['본문_0'] = [
        bindings.contract_amount ? `계약금액: ${bindings.contract_amount}` : '',
        bindings.duration ? `기간: ${bindings.duration}` : '',
        bindings.client ? `발주처: ${bindings.client}` : '',
        bindings.vendor ? `수행사: ${bindings.vendor}` : ''
      ].filter(Boolean).join('\n');

      // 두 번째 섹션은 빈 데이터 또는 추가 정보
      mapped['중제목_1'] = bindings.section2_title || '';
      mapped['소제목_1'] = bindings.section2_subtitle || '';
      mapped['본문_1'] = bindings.section2_content || '';
    }
  }

  // ============================================================
  // content-stack2: 3섹션 세로 레이아웃 (0-based 인덱싱)
  // shape 0-1 → section 0, shape 2-3 → section 1, shape 4-5 → section 2
  // ============================================================
  if (templateId.includes('content-stack2') || bindings.sections?.length === 3) {
    const sections = bindings.sections || [];

    sections.forEach((section, i) => {
      mapped[`중제목_${i}`] = section.title || section.중제목 || '';
      mapped[`소제목_${i}`] = section.subtitle || section.소제목 || '';
      mapped[`본문_${i}`] = Array.isArray(section.content)
        ? section.content.join('\n')
        : (section.content || section.본문 || '');
    });

    // 레거시: current_state/goals/effects 형식
    if ((bindings.current_state || bindings.goals) && !bindings.sections) {
      // 3개 섹션에 분배
      const items = [];
      if (bindings.current_state) items.push({ title: '현황', content: bindings.current_state });
      if (bindings.goals) items.push({ title: '목표', content: bindings.goals });
      if (Array.isArray(bindings.effects)) {
        bindings.effects.forEach((effect, idx) => {
          items.push({ title: `효과 ${idx + 1}`, content: effect });
        });
      }

      items.slice(0, 3).forEach((item, i) => {
        mapped[`중제목_${i}`] = item.title;
        mapped[`소제목_${i}`] = item.content;
        mapped[`본문_${i}`] = '';
      });
    }
  }

  // ============================================================
  // grid-2col1: 좌우 2열 분할 (0-based 인덱싱)
  // shape 0,2 → column 0, shape 1,3 → column 1
  // ============================================================
  if (templateId.includes('grid-2col') || bindings.business_scope || bindings.quality) {
    // 좌측 (column 0 = section 0)
    mapped['중제목_0'] = bindings.business_scope ? '업무 범위' : '프로젝트 범위';
    mapped['소제목_0'] = '';
    mapped['본문_0'] = Array.isArray(bindings.business_scope)
      ? '• ' + bindings.business_scope.join('\n• ')
      : (bindings.business_scope || '');

    // 우측 (column 1 = section 1)
    mapped['중제목_1'] = bindings.system_scope ? '시스템 범위' : '프로젝트 범위';
    mapped['소제목_1'] = '';
    mapped['본문_1'] = Array.isArray(bindings.system_scope)
      ? '• ' + bindings.system_scope.join('\n• ')
      : (bindings.system_scope || '');
  }

  // ============================================================
  // grid-4col: 4열 그리드 (0-based 인덱싱)
  // ============================================================
  if (Array.isArray(bindings.tech_stack)) {
    bindings.tech_stack.forEach((item, i) => {
      if (typeof item === 'object') {
        mapped[`중제목_${i}`] = item.area || item.title || '';
        mapped[`소제목_${i}`] = item.tech || item.desc || '';
      }
    });
  }

  // ============================================================
  // process-linear: 단계별 프로세스 (0-based 인덱싱)
  // ============================================================
  if (Array.isArray(bindings.phases)) {
    bindings.phases.forEach((phase, i) => {
      const num = String(i + 1).padStart(2, '0');
      mapped[`${num}`] = num;
      mapped[`소제목_${i}`] = phase;
      mapped[`본문_${i}`] = '';
    });
  }

  // ============================================================
  // hierarchy: 조직 정보 (0-based 인덱싱)
  // ============================================================
  if (bindings.total_members || bindings.roles) {
    mapped['중제목_0'] = '투입 인력';
    mapped['본문_0'] = `${bindings.total_members || 0}명`;
    mapped['중제목_1'] = '투입 공수';
    mapped['본문_1'] = `${bindings.total_mm || 0} M/M`;
    mapped['중제목_2'] = '역할';
    mapped['본문_2'] = Array.isArray(bindings.roles) ? bindings.roles.join(', ') : '';
  }

  // ============================================================
  // 배열 데이터 플랫화 (0-based 인덱싱)
  // ============================================================
  if (Array.isArray(bindings.items)) {
    bindings.items.forEach((item, i) => {
      if (typeof item === 'string') {
        mapped[`item_${i}`] = item;
      } else if (typeof item === 'object') {
        Object.keys(item).forEach(key => {
          mapped[`${key}_${i}`] = item[key];
        });
      }
    });
  }

  if (Array.isArray(bindings.strategies)) {
    bindings.strategies.forEach((strategy, i) => {
      if (typeof strategy === 'object') {
        mapped[`중제목_${i}`] = strategy.title || '';
        mapped[`본문_${i}`] = strategy.desc || '';
      }
    });
  }

  return mapped;
}

/**
 * 단일 슬라이드 렌더링
 */
async function renderSlide(slide, theme) {
  const { template_id, content_bindings, html_file, title } = slide;

  console.log(`\nProcessing: ${title} (${template_id})`);

  // 템플릿 로드
  const template = await loadTemplateLocal(template_id);

  if (!template) {
    console.log(`  → Template not found, skipping (keep existing HTML)`);
    return { status: 'skipped', reason: 'template_not_found' };
  }

  // shapes 배열 확인
  if (!template.shapes || template.shapes.length === 0) {
    console.log(`  → No shapes array (zones only), skipping`);
    return { status: 'skipped', reason: 'no_shapes' };
  }

  // shape_source 확인
  const hasOoxml = template.shapes.some(s => s.shape_source === 'ooxml');
  if (hasOoxml) {
    console.log(`  → Contains OOXML shapes, skipping (requires special handling)`);
    return { status: 'skipped', reason: 'ooxml_shapes' };
  }

  // description 기반 shapes만 있는 경우 렌더링
  if (hasDescriptionShapes(template)) {
    console.log(`  → Rendering with YAML shapes (${template.shapes.length} shapes)`);

    // bindings 매핑 (slideTitle 전달)
    const mappedBindings = mapBindingsToPlaceholders(template, content_bindings, title);

    // HTML 생성
    const html = renderFromYaml(template, mappedBindings, theme);

    if (html) {
      return { status: 'rendered', html, template };
    } else {
      console.log(`  → renderFromYaml returned null`);
      return { status: 'failed', reason: 'render_failed' };
    }
  }

  console.log(`  → Unknown shape source type`);
  return { status: 'skipped', reason: 'unknown_shape_source' };
}

/**
 * 메인 실행
 */
async function main() {
  console.log('='.repeat(60));
  console.log('Stage 4 렌더링: YAML 템플릿 기반 HTML 생성');
  console.log('='.repeat(60));

  // stage-4-content.json 로드
  if (!fs.existsSync(stage4Path)) {
    console.error(`Error: ${stage4Path} not found`);
    process.exit(1);
  }

  const stage4 = JSON.parse(fs.readFileSync(stage4Path, 'utf-8'));
  const slides = stage4.slides || [];

  console.log(`\nSession: ${stage4.session?.id || sessionDir}`);
  console.log(`Total slides: ${slides.length}`);
  console.log(`Theme: ${stage4.setup?.theme?.id || 'default'}`);

  // 테마 설정
  const theme = stage4.setup?.theme?.colors || DEEPGREEN_THEME;

  // slides 디렉토리 확인
  if (!fs.existsSync(slidesDir)) {
    fs.mkdirSync(slidesDir, { recursive: true });
  }

  // 결과 통계
  const stats = {
    rendered: 0,
    skipped: 0,
    failed: 0
  };

  const results = [];

  // 각 슬라이드 처리
  for (const slide of slides) {
    const result = await renderSlide(slide, theme);
    results.push({ ...result, slide });

    if (result.status === 'rendered') {
      // HTML 파일 저장
      const outputPath = path.join(sessionDir, slide.html_file);
      fs.writeFileSync(outputPath, result.html, 'utf-8');
      console.log(`  ✅ Saved: ${slide.html_file}`);
      stats.rendered++;
    } else if (result.status === 'skipped') {
      console.log(`  ⏭️  Skipped: ${result.reason}`);
      stats.skipped++;
    } else {
      console.log(`  ❌ Failed: ${result.reason}`);
      stats.failed++;
    }
  }

  // 결과 요약
  console.log('\n' + '='.repeat(60));
  console.log('결과 요약');
  console.log('='.repeat(60));
  console.log(`✅ Rendered: ${stats.rendered}`);
  console.log(`⏭️  Skipped: ${stats.skipped}`);
  console.log(`❌ Failed: ${stats.failed}`);

  // 스킵된 슬라이드 상세
  const skippedResults = results.filter(r => r.status === 'skipped');
  if (skippedResults.length > 0) {
    console.log('\n스킵된 슬라이드 (기존 HTML 유지):');
    skippedResults.forEach(r => {
      console.log(`  - ${r.slide.title} (${r.slide.template_id}): ${r.reason}`);
    });
  }

  console.log('\n렌더링 완료!');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
