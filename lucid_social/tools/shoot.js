// shoot.js - render each HTML page of a manifest to a PNG at its exact pixel size (Chromium via Playwright)
// usage: node shoot.js manifest.json      manifest = [{html, png, w, h}, ...]
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  for (const j of jobs) {
    const page = await browser.newPage({ viewport: { width: j.w, height: j.h }, deviceScaleFactor: 1 });
    await page.goto('file://' + j.html, { waitUntil: 'load' });
    await page.waitForSelector('body[data-ready="1"]', { timeout: 30000 });
    await page.waitForTimeout(150);
    await page.screenshot({ path: j.png, clip: { x: 0, y: 0, width: j.w, height: j.h } });
    await page.close();
    console.log('ok', j.png.split('/').pop());
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
