import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import puppeteer from 'puppeteer-core';

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../../_site');
const output=path.resolve(here,'../../.work/site-review');fs.mkdirSync(output,{recursive:true});
const mime={'.html':'text/html','.js':'application/javascript','.css':'text/css','.png':'image/png','.gif':'image/gif','.svg':'image/svg+xml','.mp4':'video/mp4'};
const server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  const target=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
  if(!target.startsWith(root+path.sep)||!fs.existsSync(target)||fs.statSync(target).isDirectory()){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':mime[path.extname(target)]||'application/octet-stream'});fs.createReadStream(target).pipe(res);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const url=`http://127.0.0.1:${server.address().port}`;
const browser=await puppeteer.launch({executablePath:'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',headless:true,args:['--no-sandbox']});
const results={};
try{
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
  await page.setViewport({width:1440,height:1050,deviceScaleFactor:1});
  await page.goto(url,{waitUntil:'networkidle0'});
  assert.equal(await page.$eval('h1',e=>e.textContent),'Retake');
  assert.ok((await page.$eval('.retake-identity',e=>e.src)).endsWith('.gif'));
  await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
  await page.click('[data-motion-toggle]');
  assert.ok((await page.$eval('.retake-identity',e=>e.src)).endsWith('.png'));
  results.pause=true;
  await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
  await page.reload({waitUntil:'networkidle0'});
  assert.ok((await page.$eval('.retake-identity',e=>e.src)).endsWith('.png'));results.reducedMotion=true;
  for(const width of [390,768]){
    await page.setViewport({width,height:844,deviceScaleFactor:1});
    await page.reload({waitUntil:'networkidle0'});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`Horizontal overflow at ${width}`);
    await page.screenshot({path:path.join(output,`width-${width}.png`),fullPage:true});
  }
  results.responsiveWidths=[390,768,1440];
  await page.setJavaScriptEnabled(false);await page.reload({waitUntil:'networkidle0'});
  assert.ok((await page.$eval('.retake-identity',e=>e.src)).endsWith('.png'));results.noJavaScriptFallback=true;
  assert.deepEqual(errors,[]);results.browserErrors=[];
  fs.writeFileSync(path.join(output,'browser-check.json'),JSON.stringify(results,null,2));console.log(results);
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
