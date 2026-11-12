// Real Chromium smoke test for the isolated static NFL site; UI checks do not validate model skill.
const {chromium: playwright} = require('playwright-core');
const chromium = require('@sparticuz/chromium');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const zlib = require('node:zlib');
const base = (process.env.NFL_TEST_BASE_URL || 'http://127.0.0.1:3000/nfl-b34253a1').replace(/\/$/, '');

(async () => {
  // @sparticuz/chromium bundles support libraries needed by this sandbox's headless environment.
  const libRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'nfl-b34253a1-browser-'));
  const bundle = path.join(path.dirname(require.resolve('@sparticuz/chromium')), '../../bin/al2023.tar.br');
  const tar = path.join(libRoot, 'support.tar');
  fs.writeFileSync(tar, zlib.brotliDecompressSync(fs.readFileSync(bundle)));
  execFileSync('tar', ['xf', tar, '-C', libRoot]);
  const browser = await playwright.launch({
    executablePath: await chromium.executablePath(),
    args: chromium.args,
    headless: true,
    env: {...process.env, LD_LIBRARY_PATH: `${path.join(libRoot, 'lib')}:${process.env.LD_LIBRARY_PATH || ''}`},
  });
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}, acceptDownloads: true});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    if (response.url().startsWith(base) && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
  });
  const routes = [
    'index.html','results.html','lines.html','injuries.html','sources.html','correlations.html',
    'strategies.html','validation.html','leaderboard.html','questions.html','suggestions.html',
    'flagged.html','audit.html',
  ];
  for (const route of routes) {
    const response = await page.goto(`${base}/${route}`);
    assert.equal(response.status(), 200, route);
    assert.equal(await page.locator('h1').count(), 1, `${route}: one page heading`);
    assert.equal(await page.locator('nav [aria-current="page"]').count(), 1, `${route}: one current nav item`);
    assert.equal(await page.locator('main#main').count(), 1, `${route}: main landmark`);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${route}: desktop overflow`);
    assert.equal(await page.locator('table:not(:has(caption))').count(), 0, `${route}: accessible data captions`);
    assert.equal(await page.locator('th:not([scope="col"])').count(), 0, `${route}: scoped column headings`);
    if (route === 'index.html') {
      assert.equal(await page.locator('.page-card').count(), 12, 'overview exposes all twelve sections');
      assert.match(await page.locator('.hero').innerText(), /Not betting advice/i);
    } else if (['questions.html', 'suggestions.html', 'flagged.html', 'strategies.html'].includes(route)) {
      assert.ok(await page.locator('.content-card').count() > 0, `${route}: evidence cards present`);
    } else {
      assert.ok(await page.locator('tbody tr').count() > 0, `${route}: table data present`);
    }
  }

  // Check line and market records retain click-through evidence on every game/quote row.
  await page.goto(`${base}/lines.html`);
  for (const tableId of ['model-lines', 'quote-rows']) {
    const allLinked = await page.locator(`#${tableId} tbody tr`).evaluateAll(rows =>
      rows.every(row => row.querySelector('a[href^="https://"]'))
    );
    assert.equal(allLinked, true, `${tableId}: every row has a source link`);
  }
  await page.goto(`${base}/injuries.html`);
  assert.equal(await page.locator('#injury-table tbody tr').count(), 76);
  assert.equal(await page.locator('#chart-coverage tbody tr').count(), 32);
  assert.match(await page.locator('.callout').first().innerText(), /not an all-team/i);

  // Download a small CSV and ensure static/no-JavaScript content remains available.
  await page.goto(`${base}/validation.html`);
  const downloadPromise = page.waitForEvent('download');
  await page.locator('a[download][href="data/validation_gates_2026.csv"]').click();
  const download = await downloadPromise;
  const csv = fs.readFileSync(await download.path(), 'utf8');
  assert.match(csv, /G0/);
  assert.match(csv, /BLOCKED/);

  await page.setViewportSize({width: 390, height: 844});
  for (const route of routes) {
    await page.goto(`${base}/${route}`);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${route}: mobile overflow`);
    assert.equal(await page.locator('h1').isVisible(), true, `${route}: visible heading on mobile`);
  }
  const nojs = await browser.newContext({javaScriptEnabled: false});
  const staticPage = await nojs.newPage();
  await staticPage.goto(`${base}/sources.html`);
  assert.equal(await staticPage.locator('#source-register tbody tr').count(), 58, 'source register works without JavaScript');
  assert.deepEqual(errors, []);
  await browser.close();
  fs.rmSync(libRoot, {recursive: true, force: true});
  console.log('PASS: 13 desktop/mobile routes, accessible table headings, source links, CSV download, and no-JavaScript rendering.');
})().catch(error => { console.error(error); process.exit(1); });
