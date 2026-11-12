// Real Chromium smoke tests. Synthetic UI assertions, not statistical validation.
const {chromium: playwright} = require('../node_modules/playwright-core');
const chromium = require('../node_modules/@sparticuz/chromium');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const base = process.env.TEST_BASE_URL || 'http://127.0.0.1:3000';
(async () => {
  // The sandbox may lack NSS/NSPR; the Chromium npm package includes these libraries.
  // Extract only its bundled support libraries to the OS temp directory (never Git).
  const os = require('node:os');
  const path = require('node:path');
  const {execFileSync} = require('node:child_process');
  const zlib = require('node:zlib');
  const libRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'own5-browser-'));
  const bundle = path.join(path.dirname(require.resolve('../node_modules/@sparticuz/chromium')), '../../bin/al2023.tar.br');
  const tar = path.join(libRoot, 'support.tar');
  fs.writeFileSync(tar,zlib.brotliDecompressSync(fs.readFileSync(bundle)));
  execFileSync('tar',['xf',tar,'-C',libRoot]);
  const browser = await playwright.launch({executablePath: await chromium.executablePath(), args: chromium.args, headless:true, env:{...process.env, LD_LIBRARY_PATH:`${path.join(libRoot,'lib')}:${process.env.LD_LIBRARY_PATH || ''}`}});
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  const pages=['index','questions','injuries','strategies','correlations','leaderboard','suggestions','flagged','sources'];
  for (const width of [1440,390]) {
    await page.setViewportSize({width,height:900});
    for (const slug of pages) {
      assert.equal((await page.goto(`${base}/nfl-decision-desk/${slug}.html`)).status(),200);
      assert.equal(await page.locator('h1').count(),1);
      assert.equal(await page.locator('[aria-current="page"]').count(),1);
      assert.ok(await page.locator('tbody tr').count()>0);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),slug);
    }
  }
  await page.locator('#filter').fill('nonexistentxyz');
  assert.equal(await page.locator('tbody tr:visible').count(),0);
  await page.locator('#filter').fill('');
  assert.ok(await page.locator('tbody tr:visible').count()>0);
  const nojs=await browser.newContext({javaScriptEnabled:false});
  const p=await nojs.newPage(); await p.goto(`${base}/nfl-decision-desk/index.html`);
  assert.ok(await p.locator('tbody tr').count()>0);
  assert.deepEqual(errors,[]);
  await browser.close(); console.log('PASS: 18 desktop/mobile page checks; search; no-JavaScript tables; no browser errors');
})().catch(e=>{console.error(e);process.exit(1)});
