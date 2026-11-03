const {chromium}=require('playwright-core');
const bundled=require('@sparticuz/chromium');
(async()=>{
 const browser=await chromium.launch({executablePath:await bundled.executablePath(),args:bundled.args,headless:true});
 let count=0;
 for(const width of [1440,390]) {
  const page=await browser.newPage({viewport:{width,height:900},javaScriptEnabled:false});
  for(const name of ['index','data','strategies','lines','correlations','gates','leaderboard','review']) {
   const response=await page.goto(`http://127.0.0.1:3000/nba-validation/${name}.html`);
   if(response.status()!==200)throw Error(name+' HTTP');
   if(await page.locator('h1').count()!==1)throw Error(name+' heading');
   if(await page.locator('nav a').count()!==8)throw Error(name+' nav');
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error(name+' overflow');
   count++;
  }
  await page.close();
 }
 await browser.close(); console.log(`PASS ${count} desktop/mobile no-JavaScript page checks`);
})().catch(e=>{console.error(e);process.exit(1)});
