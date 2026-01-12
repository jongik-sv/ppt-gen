const PptxGenJS = require('pptxgenjs');

const pptx = new PptxGenJS();

// 슬라이드 설정
pptx.defineLayout({ name: 'WIDE', width: 13.333, height: 7.5 });
pptx.layout = 'WIDE';
pptx.title = '스마트 물류관리 시스템 구축';
pptx.author = '(주)테크솔루션';

// 테마 색상
const colors = {
  primary: '22523B',
  secondary: '153325',
  accent: '479374',
  muted: '6F886A',
  light: 'C4D6D0',
  white: 'FFFFFF',
  black: '333333'
};

// 공통 스타일
const titleStyle = { fontSize: 28, bold: true, color: colors.secondary };
const bodyStyle = { fontSize: 14, color: colors.black };
const cardStyle = { fill: { color: colors.light }, line: { color: colors.primary, width: 1 } };

// Slide 1: 표지
let slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.roundRect, { x: 3.5, y: 1.5, w: 6.3, h: 0.8, fill: { color: colors.primary }, rounding: 0.3 });
slide.addText('프로젝트 수행계획 보고', { x: 3.5, y: 1.5, w: 6.3, h: 0.8, align: 'center', valign: 'middle', color: colors.white, fontSize: 18 });
slide.addText('스마트 물류관리 시스템 구축', { x: 1.5, y: 2.8, w: 10.3, h: 1.2, align: 'center', fontSize: 44, bold: true, color: colors.secondary });
slide.addText('AI 기반 물류 최적화 및 실시간 추적 시스템', { x: 2, y: 4.2, w: 9.3, h: 0.6, align: 'center', fontSize: 18, color: colors.muted });
slide.addText('2025.01.06 ~ 2025.12.31 (12개월)\n(주)테크솔루션 | PM 김철수', { x: 3, y: 5.5, w: 7.3, h: 1, align: 'center', fontSize: 14, color: colors.secondary });
slide.addShape(pptx.ShapeType.line, { x: 1.5, y: 1.8, w: 10.3, h: 0, line: { color: colors.primary, width: 2 } });
slide.addShape(pptx.ShapeType.line, { x: 1.5, y: 5.2, w: 10.3, h: 0, line: { color: colors.primary, width: 2 } });

// Slide 2: 프로젝트 개요
slide = pptx.addSlide();
slide.addText('프로젝트 개요', { x: 0.5, y: 0.3, w: 12, h: 0.8, ...titleStyle });
slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 1.1, w: 12.3, h: 0.05, fill: { color: colors.primary } });

const overview = [
  { num: '01', title: '발주기관', desc: '(주)글로벌물류\n국내 Top 5 물류기업' },
  { num: '02', title: '계약금액', desc: '15억원\n(VAT 별도)' },
  { num: '03', title: '계약기간', desc: '2025.01 ~ 2025.12\n(총 12개월)' },
  { num: '04', title: '핵심목표', desc: 'AI 기반 물류 최적화\n실시간 추적 시스템' }
];
overview.forEach((item, i) => {
  const x = 0.7 + i * 3.1;
  slide.addShape(pptx.ShapeType.roundRect, { x, y: 1.8, w: 2.8, h: 4.2, fill: { color: 'E8F5F0' }, rounding: 0.1 });
  slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.9, y: 5.3, w: 1, h: 1, fill: { color: colors.primary } });
  slide.addText(item.num, { x: x + 0.9, y: 5.3, w: 1, h: 1, align: 'center', valign: 'middle', color: colors.white, fontSize: 18, bold: true });
  slide.addText(item.title, { x, y: 2, w: 2.8, h: 0.6, align: 'center', fontSize: 18, bold: true, color: colors.primary });
  slide.addText(item.desc, { x, y: 2.8, w: 2.8, h: 2, align: 'center', fontSize: 13, color: colors.black });
});

// Slide 3: 현황 및 기대효과
slide = pptx.addSlide();
slide.addText('현황 및 기대효과', { x: 0.5, y: 0.3, w: 12, h: 0.8, ...titleStyle });
slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 1.1, w: 12.3, h: 0.05, fill: { color: colors.primary } });

const effects = [
  { num: '01', title: '현황', desc: '10년+ 레거시 시스템\n처리 속도 저하\n연동 한계' },
  { num: '02', title: '효율 향상', desc: '물류 처리 효율\n30% 향상' },
  { num: '03', title: '정확도', desc: '재고 정확도\n99.5% 달성' },
  { num: '04', title: '비용 절감', desc: '운영 비용\n20% 절감' }
];
effects.forEach((item, i) => {
  const x = 0.7 + i * 3.1;
  slide.addShape(pptx.ShapeType.roundRect, { x, y: 1.8, w: 2.8, h: 4.2, fill: { color: i === 0 ? 'FFF3E0' : 'E8F5F0' }, rounding: 0.1 });
  slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.9, y: 5.3, w: 1, h: 1, fill: { color: i === 0 ? 'FF9800' : colors.primary } });
  slide.addText(item.num, { x: x + 0.9, y: 5.3, w: 1, h: 1, align: 'center', valign: 'middle', color: colors.white, fontSize: 18, bold: true });
  slide.addText(item.title, { x, y: 2, w: 2.8, h: 0.6, align: 'center', fontSize: 18, bold: true, color: i === 0 ? 'E65100' : colors.primary });
  slide.addText(item.desc, { x, y: 2.8, w: 2.8, h: 2, align: 'center', fontSize: 13, color: colors.black });
});

// Slide 4: 시스템 범위
slide = pptx.addSlide();
slide.addText('시스템 범위', { x: 0.5, y: 0.3, w: 12, h: 0.8, ...titleStyle });
slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 1.1, w: 12.3, h: 0.05, fill: { color: colors.primary } });

const systems = [
  { num: '01', title: 'WMS', desc: '창고관리시스템\n입출고, 재고\n피킹/패킹' },
  { num: '02', title: 'TMS', desc: '배송관리시스템\n배차, 경로최적화\n실시간 추적' },
  { num: '03', title: 'OMS', desc: '주문관리시스템\n주문접수, 할당\n정산' },
  { num: '04', title: 'Dashboard', desc: '통합모니터링\n실시간 현황\nKPI, 리포트' }
];
systems.forEach((item, i) => {
  const x = 0.7 + i * 3.1;
  slide.addShape(pptx.ShapeType.roundRect, { x, y: 1.8, w: 2.8, h: 4.2, fill: { color: 'E8F5F0' }, rounding: 0.1 });
  slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.9, y: 5.3, w: 1, h: 1, fill: { color: colors.primary } });
  slide.addText(item.num, { x: x + 0.9, y: 5.3, w: 1, h: 1, align: 'center', valign: 'middle', color: colors.white, fontSize: 18, bold: true });
  slide.addText(item.title, { x, y: 2, w: 2.8, h: 0.6, align: 'center', fontSize: 20, bold: true, color: colors.primary });
  slide.addText(item.desc, { x, y: 2.8, w: 2.8, h: 2, align: 'center', fontSize: 13, color: colors.black });
});

// Slide 5: 추진 전략
slide = pptx.addSlide();
slide.addText('추진 전략', { x: 0.5, y: 0.3, w: 12, h: 0.8, ...titleStyle });
slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 1.1, w: 12.3, h: 0.05, fill: { color: colors.primary } });

const strategies = [
  { title: '단계적 전환', desc: '모듈별 순차 전환으로\n리스크 최소화' },
  { title: '애자일 기반', desc: '2주 단위 스프린트로\n빠른 피드백' },
  { title: '현업 밀착', desc: '주 2회 현업 리뷰로\n정합성 확보' }
];
strategies.forEach((item, i) => {
  const x = 1.5 + i * 3.8;
  slide.addShape(pptx.ShapeType.ellipse, { x, y: 2.2, w: 2.8, h: 2.8, fill: { color: colors.primary } });
  slide.addText(item.title, { x, y: 2.8, w: 2.8, h: 0.8, align: 'center', valign: 'middle', fontSize: 18, bold: true, color: colors.white });
  slide.addText(item.desc, { x: x - 0.3, y: 5.3, w: 3.4, h: 1.2, align: 'center', fontSize: 14, color: colors.black });
  if (i < 2) {
    slide.addShape(pptx.ShapeType.rightArrow, { x: x + 2.9, y: 3.2, w: 0.8, h: 0.5, fill: { color: colors.accent } });
  }
});

// Slide 6: 마스터 일정
slide = pptx.addSlide();
slide.addText('마스터 일정', { x: 0.5, y: 0.3, w: 12, h: 0.8, ...titleStyle });
slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 1.1, w: 12.3, h: 0.05, fill: { color: colors.primary } });

const schedule = [
  { num: '01', title: '착수', period: '1월 (4주)', desc: '킥오프\n환경구축\n표준정의' },
  { num: '02', title: '분석/설계', period: '2~5월 (16주)', desc: '요구사항 확정\n아키텍처 설계' },
  { num: '03', title: '개발', period: '6~9월 (16주)', desc: '코딩\n단위테스트' },
  { num: '04', title: '테스트/이행', period: '10~12월 (12주)', desc: '오픈\n안정화' }
];
schedule.forEach((item, i) => {
  const x = 0.7 + i * 3.1;
  slide.addShape(pptx.ShapeType.roundRect, { x, y: 1.8, w: 2.8, h: 4.2, fill: { color: 'E8F5F0' }, rounding: 0.1 });
  slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.9, y: 5.3, w: 1, h: 1, fill: { color: colors.primary } });
  slide.addText(item.num, { x: x + 0.9, y: 5.3, w: 1, h: 1, align: 'center', valign: 'middle', color: colors.white, fontSize: 18, bold: true });
  slide.addText(item.title, { x, y: 2, w: 2.8, h: 0.5, align: 'center', fontSize: 18, bold: true, color: colors.primary });
  slide.addText(item.period, { x, y: 2.5, w: 2.8, h: 0.4, align: 'center', fontSize: 12, color: colors.accent, bold: true });
  slide.addText(item.desc, { x, y: 3.1, w: 2.8, h: 1.8, align: 'center', fontSize: 13, color: colors.black });
});

// Slide 7: 투입 인력
slide = pptx.addSlide();
slide.addText('투입 인력', { x: 0.5, y: 0.3, w: 12, h: 0.8, ...titleStyle });
slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 1.1, w: 12.3, h: 0.05, fill: { color: colors.primary } });

const team = [
  { num: '01', title: 'PM', desc: '김철수 차장\n(12개월)' },
  { num: '02', title: 'AA', desc: '박준형 책임\n(10개월)' },
  { num: '03', title: '개발팀', desc: 'PL 1명\nBackend 2명\nFrontend 1명' },
  { num: '04', title: 'QA/DBA', desc: 'QA 1명 (6개월)\nDBA 1명 (8개월)' }
];
team.forEach((item, i) => {
  const x = 0.7 + i * 3.1;
  slide.addShape(pptx.ShapeType.roundRect, { x, y: 1.8, w: 2.8, h: 4.2, fill: { color: 'E8F5F0' }, rounding: 0.1 });
  slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.9, y: 5.3, w: 1, h: 1, fill: { color: colors.primary } });
  slide.addText(item.num, { x: x + 0.9, y: 5.3, w: 1, h: 1, align: 'center', valign: 'middle', color: colors.white, fontSize: 18, bold: true });
  slide.addText(item.title, { x, y: 2, w: 2.8, h: 0.6, align: 'center', fontSize: 18, bold: true, color: colors.primary });
  slide.addText(item.desc, { x, y: 2.8, w: 2.8, h: 2, align: 'center', fontSize: 13, color: colors.black });
});
slide.addText('총 8명 | 78MM', { x: 4.5, y: 6.5, w: 4.3, h: 0.5, align: 'center', fontSize: 16, bold: true, color: colors.primary });

// Slide 8: 주요 위험 및 대응
slide = pptx.addSlide();
slide.addText('주요 위험 및 대응', { x: 0.5, y: 0.3, w: 12, h: 0.8, ...titleStyle });
slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 1.1, w: 12.3, h: 0.05, fill: { color: colors.primary } });

const risks = [
  { title: '요구사항 변경', impact: '상', response: 'CCB 통해 통제\n영향도 분석 필수' },
  { title: '일정 지연', impact: '중', response: '주간 진척관리\nCritical Path 모니터링' },
  { title: '데이터 마이그레이션', impact: '상', response: '사전 검증\n롤백 계획 수립' }
];
risks.forEach((item, i) => {
  const y = 1.8 + i * 1.7;
  slide.addShape(pptx.ShapeType.ellipse, { x: 0.8, y, w: 1.2, h: 1.2, fill: { color: item.impact === '상' ? 'E53935' : 'FF9800' } });
  slide.addText(item.impact, { x: 0.8, y, w: 1.2, h: 1.2, align: 'center', valign: 'middle', fontSize: 20, bold: true, color: colors.white });
  slide.addShape(pptx.ShapeType.roundRect, { x: 2.3, y: y + 0.1, w: 10.2, h: 1, fill: { color: 'F5F5F5' }, rounding: 0.1 });
  slide.addText(item.title, { x: 2.5, y: y + 0.1, w: 3, h: 1, valign: 'middle', fontSize: 16, bold: true, color: colors.secondary });
  slide.addText(item.response, { x: 5.5, y: y + 0.1, w: 6.8, h: 1, valign: 'middle', fontSize: 13, color: colors.black });
});

// Slide 9: 협조 요청 사항
slide = pptx.addSlide();
slide.addText('협조 요청 사항', { x: 0.5, y: 0.3, w: 12, h: 0.8, ...titleStyle });
slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 1.1, w: 12.3, h: 0.05, fill: { color: colors.primary } });

const requests = [
  { num: '01', title: '환경', desc: '프로젝트 룸 10석\nVPN, 출입증' },
  { num: '02', title: '데이터', desc: '테스트용 샘플 데이터\n(개인정보 비식별화)' },
  { num: '03', title: '인프라', desc: 'AWS 계정\n권한 부여' },
  { num: '04', title: '참여', desc: '현업 담당자 인터뷰\nUAT 지원' }
];
requests.forEach((item, i) => {
  const x = 0.7 + i * 3.1;
  slide.addShape(pptx.ShapeType.roundRect, { x, y: 1.8, w: 2.8, h: 4.2, fill: { color: 'E8F5F0' }, rounding: 0.1 });
  slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.9, y: 5.3, w: 1, h: 1, fill: { color: colors.primary } });
  slide.addText(item.num, { x: x + 0.9, y: 5.3, w: 1, h: 1, align: 'center', valign: 'middle', color: colors.white, fontSize: 18, bold: true });
  slide.addText(item.title, { x, y: 2, w: 2.8, h: 0.6, align: 'center', fontSize: 18, bold: true, color: colors.primary });
  slide.addText(item.desc, { x, y: 2.8, w: 2.8, h: 2, align: 'center', fontSize: 13, color: colors.black });
});

// Slide 10: 마무리
slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.line, { x: 1.5, y: 1.8, w: 10.3, h: 0, line: { color: colors.primary, width: 2 } });
slide.addShape(pptx.ShapeType.line, { x: 1.5, y: 5.5, w: 10.3, h: 0, line: { color: colors.primary, width: 2 } });
slide.addText('감사합니다', { x: 1.5, y: 2.5, w: 10.3, h: 1.5, align: 'center', fontSize: 48, bold: true, color: colors.secondary });
slide.addText('스마트 물류관리 시스템 구축 프로젝트', { x: 2, y: 4, w: 9.3, h: 0.6, align: 'center', fontSize: 18, color: colors.muted });
slide.addText('PM: 김철수 (kim@techsolution.co.kr)\n(주)테크솔루션', { x: 3, y: 5.8, w: 7.3, h: 1, align: 'center', fontSize: 14, color: colors.secondary });

// 저장
pptx.writeFile({ fileName: 'output/smart-logistics-report.pptx' })
  .then(() => console.log('PPTX 생성 완료: output/smart-logistics-report.pptx'))
  .catch(err => console.error('오류:', err));
