const { chromium } = require('playwright-core');
const bundled = require('@sparticuz/chromium');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const zlib = require('node:zlib');

const pages = ['index','executive-summary','lines','players','correlations','strategies','gates','leaderboard','luck','sources','requirements','audit','review'];

(async () => {
  const libRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'nba-hub-browser-'));
  const bundle = path.join(path.dirname(require.resolve('@sparticuz/chromium')), '../../bin/al2023.tar.br');
  const tar = path.join(libRoot, 'support.tar');
  fs.writeFileSync(tar, zlib.brotliDecompressSync(fs.readFileSync(bundle)));
  require('node:child_process').execFileSync('tar', ['xf', tar, '-C', libRoot]);
  const browser = await chromium.launch({ executablePath: await bundled.executablePath(), args: bundled.args, headless: true, env: { ...process.env, LD_LIBRARY_PATH: path.join(libRoot, 'lib') } });
  const page = await browser.newPage({ javaScriptEnabled: false });
  let count = 0;
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const name of pages) {
      const response = await page.goto(`http://127.0.0.1:3000/nba-research-hub/${name}.html`);
      if (response.status() !== 200) throw new Error(`${name} HTTP ${response.status()}`);
      if (await page.locator('h1').count() !== 1) throw new Error(`${name} heading`);
      if (await page.locator('nav a').count() !== 13) throw new Error(`${name} nav`);
      if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error(`${name} overflow`);
      const rows = await page.locator('tbody tr').count();
      if (rows > 0) {
        const unsourced = await page.evaluate(() => Array.from(document.querySelectorAll('tbody tr')).filter(tr => !tr.querySelector('a[href^="https://"]')).length);
        if (unsourced) throw new Error(`${name} has ${unsourced} unsourced rows`);
      }
      if (name === 'lines') {
        const blanks = await page.locator('[data-blank="true"]').count();
        if (blanks < 27) throw new Error('lines missing blank market flags');
      }
      count++;
    }
  }
  await browser.close();
  console.log(`PASS ${count} desktop/mobile no-JavaScript hub page checks`);
})().catch(e => { console.error(e); process.exit(1); });
