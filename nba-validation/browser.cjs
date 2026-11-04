const {chromium}=require('playwright-core');
const bundled=require('@sparticuz/chromium');
(async()=>{
 const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),zlib=require('node:zlib');
 const libRoot=fs.mkdtempSync(path.join(os.tmpdir(),'nba-browser-'));
 const bundle=path.join(path.dirname(require.resolve('@sparticuz/chromium')),'../../bin/al2023.tar.br');
 const tar=path.join(libRoot,'support.tar');
 fs.writeFileSync(tar,zlib.brotliDecompressSync(fs.readFileSync(bundle)));
 require('node:child_process').execFileSync('tar',['xf',tar,'-C',libRoot]);
 const browser=await chromium.launch({executablePath:await bundled.executablePath(),args:bundled.args,headless:true,env:{...process.env,LD_LIBRARY_PATH:path.join(libRoot,'lib')}});
 const page=await browser.newPage({javaScriptEnabled:false});
 let count=0;
 for(const width of [1440,390]) {
  await page.setViewportSize({width,height:900});
  for(const name of ['index','data','strategies','lines','correlations','gates','leaderboard','review']) {
   const response=await page.goto(`http://127.0.0.1:3000/nba-validation/${name}.html`);
   if(response.status()!==200)throw Error(name+' HTTP');
   if(await page.locator('h1').count()!==1)throw Error(name+' heading');
   if(await page.locator('nav a').count()!==8)throw Error(name+' nav');
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error(name+' overflow');
   count++;
  }

 }
 await browser.close(); console.log(`PASS ${count} desktop/mobile no-JavaScript page checks`);
})().catch(e=>{console.error(e);process.exit(1)});
