#!/usr/bin/env node
/**
 * html2pptx CLI - Convert HTML slides directory to PPTX
 *
 * Usage:
 *   node html2pptx-cli.js <slides-dir> <output.pptx>
 *
 * Example:
 *   node html2pptx-cli.js output/session/slides output/session/output.pptx
 */

const path = require('path');
const fs = require('fs');
const pptxgen = require('pptxgenjs');
const html2pptx = require('./html2pptx');

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log('Usage: node html2pptx-cli.js <slides-dir> <output.pptx>');
    console.log('Example: node html2pptx-cli.js ./slides ./output.pptx');
    process.exit(1);
  }

  const slidesDir = path.resolve(args[0]);
  const outputPath = path.resolve(args[1]);

  // Check slides directory exists
  if (!fs.existsSync(slidesDir)) {
    console.error(`Error: Slides directory not found: ${slidesDir}`);
    process.exit(1);
  }

  // Find all HTML files
  const htmlFiles = fs.readdirSync(slidesDir)
    .filter(f => f.endsWith('.html'))
    .sort();  // Sort alphabetically (slide-001.html, slide-002.html, ...)

  if (htmlFiles.length === 0) {
    console.error(`Error: No HTML files found in ${slidesDir}`);
    process.exit(1);
  }

  console.log(`Found ${htmlFiles.length} HTML slides`);

  // Create presentation
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = 'Claude Code PPT Generator';
  pptx.title = 'Generated Presentation';

  // Convert each HTML file
  for (let i = 0; i < htmlFiles.length; i++) {
    const htmlFile = htmlFiles[i];
    const htmlPath = path.join(slidesDir, htmlFile);

    console.log(`[${i + 1}/${htmlFiles.length}] Converting: ${htmlFile}`);

    try {
      const { slide, placeholders } = await html2pptx(htmlPath, pptx);

      if (placeholders && placeholders.length > 0) {
        console.log(`  - Found ${placeholders.length} placeholders`);
      }
    } catch (err) {
      console.error(`  Error converting ${htmlFile}: ${err.message}`);
      // Continue with other slides
    }
  }

  // Save PPTX
  console.log(`\nSaving to: ${outputPath}`);
  await pptx.writeFile(outputPath);
  console.log('Done!');
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
