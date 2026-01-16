/**
 * PPTX to HTML 추출기
 *
 * 사용법:
 *   node extract.js <pptx파일> [출력폴더] [--debug]
 *
 * 예시:
 *   node extract.js ../Sample_12.pptx ./output
 *   node extract.js ../MyPresentation.pptx ./output --debug
 */

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const http = require('http');

// 설정
const SERVER_PORT = 9999;
const PROJECT_ROOT = path.resolve(__dirname, '..', 'PPTXjs');

async function main() {
    // 인자 파싱
    const args = process.argv.slice(2);

    if (args.length === 0) {
        console.log('사용법: node extract.js <pptx파일> [출력폴더]');
        console.log('예시: node extract.js ../Sample_12.pptx ./output');
        process.exit(1);
    }

    const debugMode = args.includes('--debug');
    const pptxArg = args.find(a => !a.startsWith('--'));
    const outputArg = args.find((a, i) => i > 0 && !a.startsWith('--'));

    const pptxPath = path.resolve(pptxArg);
    const outputDir = path.resolve(outputArg || './output');
    const baseName = path.basename(pptxPath, '.pptx');

    // PPTX 파일 확인
    if (!fsSync.existsSync(pptxPath)) {
        console.error(`오류: 파일을 찾을 수 없습니다: ${pptxPath}`);
        process.exit(1);
    }

    // 출력 폴더 생성
    await fs.mkdir(outputDir, { recursive: true });

    console.log(`입력: ${pptxPath}`);
    console.log(`출력: ${outputDir}`);
    console.log('');

    // PPTX 파일을 프로젝트 루트에 임시 복사
    const tempPptxName = '_temp_convert.pptx';
    const tempPptxPath = path.join(PROJECT_ROOT, tempPptxName);
    await fs.copyFile(pptxPath, tempPptxPath);

    // 동적 HTML 생성
    const converterHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>PPTXjs Converter</title>
<link rel="stylesheet" href="./css/pptxjs.css">
<link rel="stylesheet" href="./css/nv.d3.min.css">
<script src="./js/jquery-1.11.3.min.js"></script>
<script src="./js/jszip.min.js"></script>
<script src="./js/filereader.js"></script>
<script src="./js/d3.min.js"></script>
<script src="./js/nv.d3.min.js"></script>
<script src="./js/pptxjs.js"></script>
<style>
    html, body { margin: 0; padding: 0; background: white; }
    #result { width: 960px; margin: 0 auto; }
</style>
</head>
<body>
<div id="result"></div>
<script>
$("#result").pptxToHtml({
    pptxFileUrl: "./${tempPptxName}",
    slideMode: false,
    mediaProcess: true,
    themeProcess: true
});
</script>
</body>
</html>`;

    const tempHtmlPath = path.join(PROJECT_ROOT, '_temp_converter.html');
    await fs.writeFile(tempHtmlPath, converterHtml, 'utf-8');

    // 로컬 HTTP 서버 시작
    console.log('서버 시작...');
    const server = http.createServer((req, res) => {
        let filePath = path.join(PROJECT_ROOT, req.url === '/' ? 'index.html' : decodeURIComponent(req.url));

        const ext = path.extname(filePath).toLowerCase();
        const mimeTypes = {
            '.html': 'text/html; charset=utf-8',
            '.js': 'application/javascript',
            '.css': 'text/css',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.pptx': 'application/octet-stream'
        };

        fsSync.readFile(filePath, (err, content) => {
            if (err) {
                res.writeHead(404);
                res.end(`Not found: ${req.url}`);
            } else {
                res.writeHead(200, {
                    'Content-Type': mimeTypes[ext] || 'application/octet-stream',
                    'Cache-Control': 'no-cache'
                });
                res.end(content);
            }
        });
    });

    await new Promise((resolve, reject) => {
        server.listen(SERVER_PORT, '127.0.0.1', resolve);
        server.on('error', reject);
    });
    console.log(`서버 실행 중: http://127.0.0.1:${SERVER_PORT}`);

    // Puppeteer로 변환
    console.log('브라우저 시작...');
    const browser = await puppeteer.launch({
        headless: debugMode ? false : 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        devtools: debugMode
    });

    try {
        const page = await browser.newPage();

        // 디버그 로그
        page.on('console', msg => {
            const text = msg.text();
            if (text.includes('Error') || text.includes('error')) {
                console.log('  [Browser]', text);
            }
        });

        await page.setViewport({ width: 1200, height: 900 });

        // 변환 페이지 로드
        console.log('PPTX 변환 중...');
        await page.goto(`http://127.0.0.1:${SERVER_PORT}/_temp_converter.html`, {
            waitUntil: 'networkidle2',
            timeout: 60000
        });

        // 슬라이드 로딩 대기
        await page.waitForSelector('#result .slide', { timeout: 120000 });

        // 차트 렌더링 완료 대기 (SVG가 있으면 차트가 있는 것)
        console.log('렌더링 대기 중...');
        await new Promise(r => setTimeout(r, 3000));

        // 차트가 있는지 확인하고 추가 대기
        const hasCharts = await page.evaluate(() => {
            return document.querySelectorAll('#result svg.nvd3-svg, #result .nv-chart').length > 0;
        });

        if (hasCharts) {
            console.log('차트 감지됨, 추가 렌더링 대기...');
            await new Promise(r => setTimeout(r, 5000));
        }

        // 추가 렌더링 대기 (이미지 등)
        await new Promise(r => setTimeout(r, 2000));

        // 디버그 모드: 사용자가 확인할 수 있도록 대기
        if (debugMode) {
            // 슬라이드 내 SVG 요소 분석
            const svgInfo = await page.evaluate(() => {
                const slides = document.querySelectorAll('#result .slide');
                const info = [];
                slides.forEach((slide, idx) => {
                    const svgs = slide.querySelectorAll('svg');
                    const drawings = slide.querySelectorAll('.drawing');
                    info.push({
                        slide: idx + 1,
                        svgCount: svgs.length,
                        drawingCount: drawings.length
                    });
                });
                return info;
            });
            console.log('');
            console.log('슬라이드별 SVG/Drawing 요소:');
            svgInfo.forEach(s => console.log(`  슬라이드 ${s.slide}: SVG ${s.svgCount}개, Drawing ${s.drawingCount}개`));

            // #result 내 전체 SVG와 슬라이드 외부 SVG 확인
            const svgLocation = await page.evaluate(() => {
                const allSvgs = document.querySelectorAll('#result svg');
                const slideSvgs = document.querySelectorAll('#result .slide svg');
                const outsideSvgs = [];
                allSvgs.forEach(svg => {
                    if (!svg.closest('.slide')) {
                        outsideSvgs.push({
                            class: svg.className.baseVal || svg.className,
                            parent: svg.parentElement?.className || 'unknown'
                        });
                    }
                });
                return {
                    total: allSvgs.length,
                    insideSlide: slideSvgs.length,
                    outside: outsideSvgs
                };
            });
            console.log('');
            console.log(`전체 SVG: ${svgLocation.total}개, 슬라이드 내부: ${svgLocation.insideSlide}개`);
            if (svgLocation.outside.length > 0) {
                console.log('슬라이드 외부 SVG:');
                svgLocation.outside.forEach(s => console.log(`  class="${s.class}", parent="${s.parent}"`));
            }

            console.log('');
            console.log('========================================');
            console.log('디버그 모드: 브라우저에서 결과를 확인하세요.');
            console.log('계속하려면 Enter 키를 누르세요...');
            console.log('========================================');
            await new Promise(resolve => {
                process.stdin.once('data', resolve);
            });
        }

        const slideCount = await page.evaluate(() =>
            document.querySelectorAll('#result .slide').length
        );
        console.log(`${slideCount}개 슬라이드 발견`);

        // HTML 추출
        console.log('HTML 추출 중...');

        // CSS 읽기 (pptxjs.css + nv.d3.min.css 차트 스타일)
        const pptxCss = await fs.readFile(path.join(PROJECT_ROOT, 'css', 'pptxjs.css'), 'utf-8');
        const nvd3Css = await fs.readFile(path.join(PROJECT_ROOT, 'css', 'nv.d3.min.css'), 'utf-8').catch(() => '');
        const allCss = pptxCss + '\n' + nvd3Css;

        // 차트 SVG에 인라인 스타일 적용 (크기 고정)
        await page.evaluate(() => {
            // 모든 nvd3 차트 SVG에 계산된 크기를 인라인으로 적용
            document.querySelectorAll('svg.nvd3-svg, .nv-chart svg, .chartDiv svg').forEach(svg => {
                const rect = svg.getBoundingClientRect();
                if (rect.width > 0) svg.setAttribute('width', rect.width);
                if (rect.height > 0) svg.setAttribute('height', rect.height);
                svg.style.overflow = 'visible';
            });

            // 차트 컨테이너에도 크기 고정
            document.querySelectorAll('.chartDiv, .nv-chart').forEach(div => {
                const rect = div.getBoundingClientRect();
                if (rect.width > 0) div.style.width = rect.width + 'px';
                if (rect.height > 0) div.style.height = rect.height + 'px';
                div.style.overflow = 'visible';
            });
        });

        // 각 슬라이드 HTML 개별 저장
        console.log('개별 HTML 저장 중...');
        const slideHtmls = await page.evaluate(() => {
            const slides = document.querySelectorAll('#result .slide');
            return Array.from(slides).map(slide => slide.outerHTML);
        });

        for (let i = 0; i < slideHtmls.length; i++) {
            const slideHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>${baseName} - Slide ${i + 1}</title>
<style>
${allCss}
html, body { margin: 0; padding: 20px; background: #f0f0f0; }
.slide { margin: 0 auto; }
</style>
</head>
<body>
${slideHtmls[i]}
</body>
</html>`;
            const slideHtmlPath = path.join(outputDir, `${baseName}_slide${i + 1}.html`);
            await fs.writeFile(slideHtmlPath, slideHtml, 'utf-8');
            console.log(`  슬라이드 ${i + 1}/${slideCount} HTML 저장`);
        }

        // 전체 HTML 저장
        const resultHtml = await page.evaluate(() => {
            return document.getElementById('result').innerHTML;
        });

        const finalHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>${baseName}</title>
<style>
${allCss}
html, body { margin: 0; padding: 20px; background: #f0f0f0; }
.slide { margin: 0 auto 30px auto; }
</style>
</head>
<body>
${resultHtml}
</body>
</html>`;

        const htmlPath = path.join(outputDir, `${baseName}(전체).html`);
        await fs.writeFile(htmlPath, finalHtml, 'utf-8');
        console.log(`전체 HTML 저장됨: ${htmlPath}`);

        // PNG 스크린샷
        console.log('PNG 캡처 중...');
        const slides = await page.$$('#result .slide');
        for (let i = 0; i < slides.length; i++) {
            const pngPath = path.join(outputDir, `${baseName}_slide${i + 1}.png`);
            await slides[i].screenshot({ path: pngPath });
            console.log(`  슬라이드 ${i + 1}/${slideCount}`);
        }

        console.log('');
        console.log('완료!');
        console.log(`HTML (전체): ${htmlPath}`);
        console.log(`HTML (개별): ${outputDir}/${baseName}_slide*.html`);
        console.log(`PNG: ${outputDir}/${baseName}_slide*.png`);

    } finally {
        await browser.close();
        server.close();

        // 임시 파일 정리
        await fs.unlink(tempHtmlPath).catch(() => {});
        await fs.unlink(tempPptxPath).catch(() => {});
    }
}

main().catch(err => {
    console.error('오류:', err.message);
    process.exit(1);
});
