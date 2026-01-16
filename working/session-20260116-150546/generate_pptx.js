/**
 * Generate PPTX from HTML slides
 */
const PptxGenJS = require('pptxgenjs');
const html2pptx = require('../../.claude/skills/ppt-gen/scripts/html2pptx.js');
const path = require('path');
const fs = require('fs');

async function main() {
  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_16x9';
  pptx.title = '스마트 물류관리 시스템 구축 착수보고';
  pptx.author = '테크솔루션';
  pptx.subject = '착수보고회 발표자료';

  const slidesDir = path.join(__dirname, 'slides');

  // Get all HTML files sorted by number
  const htmlFiles = fs.readdirSync(slidesDir)
    .filter(f => f.endsWith('.html'))
    .sort((a, b) => {
      const numA = parseInt(a.match(/slide_(\d+)/)?.[1] || 0);
      const numB = parseInt(b.match(/slide_(\d+)/)?.[1] || 0);
      return numA - numB;
    });

  console.log(`Found ${htmlFiles.length} slides to process`);

  for (const htmlFile of htmlFiles) {
    const htmlPath = path.join(slidesDir, htmlFile);
    console.log(`Processing: ${htmlFile}`);

    try {
      await html2pptx(htmlPath, pptx);
    } catch (error) {
      console.error(`Error processing ${htmlFile}:`, error.message);
    }
  }

  const outputPath = path.join(__dirname, 'output', 'presentation.pptx');

  // Create output directory
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  await pptx.writeFile(outputPath);
  console.log(`\nCreated: ${outputPath}`);
}

main().catch(console.error);
