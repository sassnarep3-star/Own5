// Desktop/mobile and no-JS smoke tests; not a statistical or source audit.
const { chromium: playwright } = require('playwright-core');
const chromium = require('@sparticuz/chromium');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const zlib = require('node:zlib');
const { execFileSync } = require('node:child_process');
const base = process.env.TEST_BASE_URL || 'http://127.0.0.1:3000';
const routes = ['index', 'summary', 'lines', 'strategies', 'correlations', 'validation', 'leaderboard', 'data', 'sources', 'review'];
(async () => {
  const libRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'own5-nba-browser-'));
  const bundle = path.join(path.dirname(require.resolve('@sparticuz/chromium')), '../../bin/al2023.tar.br');
  const tar = path.join(libRoot, 'support.tar');
  fs.writeFileSync(tar, zlib.brotliDecompressSync(fs.readFileSync(bundle)));
  execFileSync('tar', ['xf', tar, '-C', libRoot]);
  const browser = await playwright.launch({executablePath: await chromium.executablePath(), args: chromium.args, headless: true,
    env: {...process.env, LD_LIBRARY_PATH: `${path.join(libRoot, 'lib')}:${process.env.LD_LIBRARY_PATH || ''}`}});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => { if (response.url().startsWith(base) && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
  for (const route of routes) {
    const response = await page.goto(`${base}/nba-integrity-lab/${route}.html`);
    assert.equal(response.status(), 200, route);
    assert.equal(await page.locator('h1').count(), 1, route);
    assert.equal(await page.locator('nav [aria-current="page"]').count(), 1, route);
    assert.ok(await page.locator('tbody tr').count() > 0, route);
    assert.equal(await page.locator('tbody tr').evaluateAll(rows => rows.every(row => !!row.querySelector('a[href^="https://"]'))), true, route);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${route}: desktop overflow`);
  }
  await page.goto(`${base}/nba-integrity-lab/strategies.html`);
  await page.locator('[data-search="strategies"]').fill('teammate');
  assert.equal(await page.locator('#strategies tbody tr:visible').count(), 1);
  await page.locator('[data-search="strategies"]').fill('not-a-candidate');
  assert.equal(await page.locator('[data-empty="strategies"]').isVisible(), true);
  await page.goto(`${base}/nba-integrity-lab/data.html`);
  await page.locator('[data-search="team-inputs"]').fill('Boston');
  assert.equal(await page.locator('#team-inputs tbody tr:visible').count(), 1);
  await page.goto(`${base}/nba-integrity-lab/lines.html`);
  assert.equal(await page.locator('td.missing').evaluateAll(cells => cells.length > 0 && cells.every(c => c.textContent === '' && !!c.getAttribute('aria-label'))), true);
  await page.goto(`${base}/nba-integrity-lab/review.html`);
  await page.locator('details').nth(1).locator('summary').click();
  await page.locator('[data-search="audit-rows"]').fill('nba-signal-lab');
  const found = await page.locator('#audit-rows tbody tr:visible').count();
  assert.ok(found > 0 && found < 369, `legacy row search: ${found}`);
  await page.goto(`${base}/nba-integrity-lab/index.html`);
  if (process.env.SNAPSHOT_DIR) {
    fs.mkdirSync(process.env.SNAPSHOT_DIR, {recursive: true});
    await page.screenshot({path: path.join(process.env.SNAPSHOT_DIR, 'nba-desktop.png'), fullPage: true});
  }
  await page.setViewportSize({width: 390, height: 844});
  for (const route of routes) {
    await page.goto(`${base}/nba-integrity-lab/${route}.html`);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${route}: mobile overflow`);
    assert.ok(await page.locator('h1').isVisible(), route);
  }
  await page.goto(`${base}/nba-integrity-lab/index.html`);
  if (process.env.SNAPSHOT_DIR) await page.screenshot({path: path.join(process.env.SNAPSHOT_DIR, 'nba-mobile.png'), fullPage: true});
  const nojs = await browser.newContext({javaScriptEnabled: false});
  const staticPage = await nojs.newPage();
  await staticPage.goto(`${base}/nba-integrity-lab/data.html`);
  assert.equal(await staticPage.locator('#player-inputs tbody tr').count(), 25);
  assert.deepEqual(errors, []);
  console.log('PASS: ten desktop/mobile routes, navigation, source-link presence, filtering, empty state, truly blank values, and no-JS tables.');
  await browser.close();
})().catch(error => {console.error(error); process.exit(1);});
