// Real Chromium smoke tests. Synthetic UI assertions, not statistical validation.
const {chromium: playwright} = require('playwright-core');
const chromium = require('@sparticuz/chromium');
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
  const bundle = path.join(path.dirname(require.resolve('@sparticuz/chromium')), '../../bin/al2023.tar.br');
  const tar = path.join(libRoot, 'support.tar');
  fs.writeFileSync(tar,zlib.brotliDecompressSync(fs.readFileSync(bundle)));
  execFileSync('tar',['xf',tar,'-C',libRoot]);
  const browser = await playwright.launch({executablePath: await chromium.executablePath(), args: chromium.args, headless:true, env:{...process.env, LD_LIBRARY_PATH:`${path.join(libRoot,'lib')}:${process.env.LD_LIBRARY_PATH || ''}`}});
  const context = await browser.newContext({viewport:{width:1440,height:1080},acceptDownloads:true});
  const page = await context.newPage();
  const errors=[];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {if(response.url().startsWith(base) && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);});
  const paths = ['index.html',...['strategies','markets','correlations','validation','leaderboard','sources','review'].map(s => `pages/${s}.html`)];
  for (const path of paths) {
    const response = await page.goto(`${base}/${path}`);
    assert.equal(response.status(),200,path);
    assert.equal(await page.locator('h1').count(),1,path);
    assert.equal(await page.locator('nav [aria-current="page"]').count(),1,path);
    assert.ok(await page.locator('tbody tr').count()>0,path);
    assert.equal(await page.locator('tbody tr').evaluateAll(rows => rows.every(row => !!row.querySelector('a[href^="https://"]'))),true,path);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`${path}: desktop page overflow`);
  }
  await page.goto(`${base}/pages/strategies.html`);
  await page.locator('[data-filter="strategies"]').selectOption('Prop combo');
  assert.equal(await page.locator('#strategies tbody tr:visible').count(),2);
  await page.locator('[data-search="strategies"]').fill('quarterback');
  assert.equal(await page.locator('#strategies tbody tr:visible').count(),1);
  const downloadPromise=page.waitForEvent('download');
  await page.locator('[data-export="strategies"]').click();
  const download=await downloadPromise;
  const csv=fs.readFileSync(await download.path(),'utf8');
  assert.ok(csv.includes('Quarterback × receiver'));
  assert.ok(csv.includes('https://nextgenstats.nfl.com/glossary'));
  assert.ok(!csv.includes('Game-script combo'));
  await page.locator('[data-search="strategies"]').fill('not-a-strategy');
  assert.equal(await page.locator('.empty:visible').count(),1);
  await page.goto(`${base}/pages/review.html`);
  await page.locator('[data-filter="review"]').selectOption('High');
  assert.equal(await page.locator('#review tbody tr:visible').count(),6);
  await page.goto(`${base}/pages/correlations.html`);
  assert.equal(await page.locator('td.missing').count(),24);
  assert.equal(await page.locator('td.missing').evaluateAll(cells=>cells.every(c=>c.textContent==='')),true);
  await page.goto(`${base}/index.html`);
  await page.screenshot({path:'research/browser-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  for (const path of paths) {
    await page.goto(`${base}/${path}`);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`${path}: mobile page overflow`);
    assert.ok(await page.locator('h1').isVisible(),path);
  }
  await page.goto(`${base}/index.html`);
  await page.screenshot({path:'research/browser-mobile.png',fullPage:true});
  const nojs=await browser.newContext({javaScriptEnabled:false});
  const staticPage=await nojs.newPage();
  await staticPage.goto(`${base}/pages/sources.html`);
  assert.equal(await staticPage.locator('#sources tbody tr').count(),14);
  assert.equal(await staticPage.locator('#facts tbody tr').count(),11);
  assert.deepEqual(errors,[]);
  console.log('PASS: eight desktop/mobile routes, no runtime errors, source links, search, category filters, empty state, filtered CSV, blank values and no-JS rendering.');
  await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});
