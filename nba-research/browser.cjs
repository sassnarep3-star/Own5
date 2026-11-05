const { chromium } = require('playwright-core');
const bundled = require('@sparticuz/chromium');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const zlib = require('node:zlib');
const { execFileSync } = require('node:child_process');

(async () => {
  const base = process.env.BASE_URL || 'http://127.0.0.1:3000';
  const libRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'nba-research-browser-'));
  const bundle = path.join(path.dirname(require.resolve('@sparticuz/chromium')), '../../bin/al2023.tar.br');
  const tar = path.join(libRoot, 'support.tar');
  fs.writeFileSync(tar, zlib.brotliDecompressSync(fs.readFileSync(bundle)));
  execFileSync('tar', ['xf', tar, '-C', libRoot]);
  const browser = await chromium.launch({
    executablePath: await bundled.executablePath(),
    args: bundled.args,
    headless: true,
    env: { ...process.env, LD_LIBRARY_PATH: path.join(libRoot, 'lib') },
  });
  const page = await browser.newPage({ javaScriptEnabled: false });
  const pages = ['index.html','pages/lines.html','pages/correlations.html','pages/strategies.html','pages/leaderboard.html','pages/teams.html','pages/players.html','pages/evidence.html','pages/audit.html','pages/review.html','pages/methodology.html'];
  let count = 0;
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const name of pages) {
      const response = await page.goto(`${base}/nba-research/${name}`, { waitUntil: 'load' });
      if (!response || response.status() !== 200) throw new Error(`${name} HTTP ${response && response.status()}`);
      if (await page.locator('h1').count() !== 1) throw new Error(`${name} heading`);
      if (await page.locator('nav a').count() !== 11) throw new Error(`${name} nav`);
      if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) throw new Error(`${name} horizontal overflow`);
      const rowsWithoutSource = await page.evaluate(() =>
        Array.from(document.querySelectorAll('table tbody tr')).filter(tr => !tr.querySelector('a')).length
      );
      if (rowsWithoutSource) throw new Error(`${name} ${rowsWithoutSource} rows without source`);
      if (name === 'pages/leaderboard.html') {
        const empty = await page.evaluate(() => document.querySelector('table tbody').children.length === 0);
        if (!empty) throw new Error('leaderboard must be empty');
      }
      count++;
    }
  }
  await browser.close();
  console.log(`PASS ${count} desktop/mobile no-JavaScript page checks`);
})().catch(e => { console.error(e); process.exit(1); });
