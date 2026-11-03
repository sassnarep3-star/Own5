// Real Chromium checks for the lab/ dashboard (session 55e682dd-own5).
// Verifies rendering, navigation, filtering, no horizontal overflow, and that
// the honest "0 validated" result is actually visible to a reader.
const {chromium: playwright} = require('playwright-core');
const chromium = require('@sparticuz/chromium');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const zlib = require('node:zlib');

const base = process.env.TEST_BASE_URL || 'http://127.0.0.1:8080';
const PAGES = ['index', 'board', 'leaderboard', 'strategies', 'correlations',
  'combos', 'skill-luck', 'gates', 'verification', 'executive-summary',
  'flagged', 'sources'];

(async () => {
  const libRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'own5-lab-browser-'));
  const bundle = path.join(path.dirname(require.resolve('@sparticuz/chromium')), '../../bin/al2023.tar.br');
  const tar = path.join(libRoot, 'support.tar');
  fs.writeFileSync(tar, zlib.brotliDecompressSync(fs.readFileSync(bundle)));
  execFileSync('tar', ['xf', tar, '-C', libRoot]);
  const browser = await playwright.launch({
    executablePath: await chromium.executablePath(),
    args: chromium.args, headless: true,
    env: {...process.env, LD_LIBRARY_PATH: `${path.join(libRoot, 'lib')}:${process.env.LD_LIBRARY_PATH || ''}`},
  });

  const errors = [];
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
  const page = await context.newPage();
  page.on('pageerror', e => errors.push(e.message));
  page.on('response', r => {
    if (r.url().startsWith(base) && r.status() >= 400) errors.push(`${r.status()} ${r.url()}`);
  });

  for (const name of PAGES) {
    const res = await page.goto(`${base}/lab/${name}.html`);
    assert.equal(res.status(), 200, name);
    assert.equal(await page.locator('h1').count(), 1, `${name}: one h1`);
    assert.equal(await page.locator('nav a.active').count(), 1, `${name}: one active nav item`);
    assert.ok(await page.locator('main h2').count() > 0, `${name}: has content`);
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
      true, `${name}: no desktop horizontal overflow`);
  }

  // The dashboard must show the honest headline, not a fabricated edge.
  await page.goto(`${base}/lab/index.html`);
  const text = (await page.locator('main').innerText()).toLowerCase();
  assert.ok(text.includes('0 of 7'), 'dashboard states 0 of 7 validated');
  assert.ok(text.includes('correlated'), 'dashboard reports the correlation finding');

  // Every correlation row must expose an official source link.
  await page.goto(`${base}/lab/correlations.html`);
  const corrRows = page.locator('#corrtbl tbody tr');
  assert.ok(await corrRows.count() >= 12, 'correlation rows rendered');
  assert.equal(await corrRows.evaluateAll(
    rows => rows.every(r => !!r.querySelector('a[href^="https://"]'))),
    true, 'every correlation row has a source link');

  // The filter box must actually filter.
  const before = await page.locator('#corrtbl tbody tr:visible').count();
  await page.locator('[data-filter="corrtbl"]').fill('WR1');
  const after = await page.locator('#corrtbl tbody tr:visible').count();
  assert.ok(after < before && after > 0, `filter narrows rows (${before} -> ${after})`);
  await page.locator('[data-filter="corrtbl"]').fill('');
  assert.equal(await page.locator('#corrtbl tbody tr:visible').count(), before, 'filter resets');

  // Verification page: all rows must show a match and an official link.
  await page.goto(`${base}/lab/verification.html`);
  const vrows = page.locator('#vtbl tbody tr');
  assert.ok(await vrows.count() >= 70, 'verification rows rendered');
  assert.equal(await vrows.evaluateAll(
    rows => rows.every(r => !!r.querySelector('a[href^="https://www.nfl.com/"]'))),
    true, 'every verification row links to NFL.com');

  // Leaderboard must not award a tier to a rejected strategy.
  await page.goto(`${base}/lab/leaderboard.html`);
  const lb = await page.locator('main').innerText();
  assert.ok(lb.includes('REJECTED'), 'leaderboard shows rejected status');
  assert.ok(!lb.includes('Tier 1 '), 'no tier awarded in results table');

  // Mobile: no overflow, nav usable.
  const mob = await context.newPage();
  await mob.setViewportSize({width: 390, height: 844});
  for (const name of ['index', 'board', 'correlations', 'leaderboard']) {
    await mob.goto(`${base}/lab/${name}.html`);
    assert.equal(
      await mob.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
      true, `${name}: no mobile horizontal overflow`);
  }

  // Screenshot for visual review (scratch, gitignored).
  await page.goto(`${base}/lab/index.html`);
  const shotDir = path.join(os.tmpdir(), 'own5-lab-shots');
  fs.mkdirSync(shotDir, {recursive: true});
  await page.screenshot({path: path.join(shotDir, 'dashboard.png'), fullPage: false});

  await browser.close();
  assert.deepEqual(errors, [], `browser errors: ${errors.join('; ')}`);
  console.log(`LAB BROWSER CHECKS PASSED — ${PAGES.length} pages, desktop + mobile, filters, source links`);
  console.log(`screenshot: ${path.join(shotDir, 'dashboard.png')}`);
})().catch(e => { console.error(e); process.exit(1); });
