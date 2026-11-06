// Desktop, mobile, and no-JS smoke tests against the static GitHub Pages path.
const {chromium: playwright} = require('playwright-core');
const chromium = require('@sparticuz/chromium');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const zlib = require('node:zlib');
const base = (process.env.SF_TEST_BASE_URL || 'http://127.0.0.1:3000/sf-rent-review').replace(/\/$/, '');
const paths = ['index.html', 'units.html', 'rules.html', 'notice.html', 'fairness.html', 'practice.html', 'review.html', 'sources.html'];

(async () => {
  // Extract Chromium's bundled support libraries to a throwaway system directory.
  const libRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'sf-review-browser-'));
  const bundle = path.join(path.dirname(require.resolve('@sparticuz/chromium')), '../../bin/al2023.tar.br');
  const tar = path.join(libRoot, 'support.tar');
  fs.writeFileSync(tar, zlib.brotliDecompressSync(fs.readFileSync(bundle)));
  execFileSync('tar', ['xf', tar, '-C', libRoot]);
  const browser = await playwright.launch({executablePath: await chromium.executablePath(), args: chromium.args,
    headless: true, env: {...process.env, LD_LIBRARY_PATH: `${path.join(libRoot,'lib')}:${process.env.LD_LIBRARY_PATH || ''}`}});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, javaScriptEnabled: false});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', err => errors.push(err.message));
  page.on('response', response => { if (response.url().startsWith(base) && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
  for (const viewport of [{width:1440,height:1000}, {width:390,height:844}, {width:320,height:700}]) {
    await page.setViewportSize(viewport);
    for (const p of paths) {
      const response = await page.goto(`${base}/${p}`);
      assert.equal(response.status(), 200, p);
      assert.equal(await page.locator('h1').count(), 1, p);
      assert.equal(await page.locator('nav [aria-current="page"]').count(), 1, p);
      assert.ok(await page.locator('tbody tr').count() > 0, p);
      assert.equal(await page.locator('tbody tr').evaluateAll(rows => rows.every(row => !!row.querySelector('a[href^="https://"]'))), true, p);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, `${p} at ${viewport.width}: page overflow`);
      assert.ok(await page.locator('h1').isVisible(), p);
    }
    await page.goto(`${base}/units.html`);
    assert.equal(await page.locator('#unit-records .empty-value').count(), 16);
    if (viewport.width < 570) {
      const box = page.locator('#unit-records .table-scroll');
      assert.equal(await box.evaluate(el => el.scrollWidth > el.clientWidth), true, 'mobile table can scroll horizontally');
      assert.ok(await box.evaluate(el => { el.scrollLeft = el.scrollWidth; return el.scrollLeft > 0; }), 'source links reachable');
    }
    await page.goto(`${base}/notice.html`);
    assert.ok(await page.getByText('NOT READY TO SERVE').isVisible());
    if (process.env.SF_SCREENSHOT_DIR && viewport.width !== 320) {
      await page.goto(`${base}/index.html`);
      await page.screenshot({path: path.join(process.env.SF_SCREENSHOT_DIR, `sf-home-${viewport.width}.png`), fullPage: true});
    }
  }
  await page.setViewportSize({width: 1440, height: 1000});
  await page.goto(`${base}/index.html`);
  await page.getByRole('navigation', {name:'Site navigation'}).getByRole('link', {name:/Flagged for review/}).click();
  assert.ok(page.url().endsWith('/review.html'));
  assert.equal(await page.locator('#review-register tbody tr').count(), 15);
  await page.getByRole('navigation', {name:'Site navigation'}).getByRole('link', {name:/Source library/}).click();
  assert.equal(await page.locator('#source-register tbody tr').count(), 28);
  assert.deepEqual(errors, []);
  await browser.close();
  fs.rmSync(libRoot, {recursive:true, force:true});
  console.log('PASS: 8 routes at desktop and 2 mobile widths, scoped table scrolling, sourced rows, navigation, blank values and no-JS rendering.');
})().catch(err => {console.error(err); process.exit(1);});
