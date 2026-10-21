// Regressions found by the pre-pilot critical review. No live AI or mic.
const {chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('node:fs'),path=require('node:path'),http=require('node:http');const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),file=pathToFileURL(path.join(root,'index.html')).href;
let passed=0;const check=(ok,msg)=>{assert(ok,msg);passed++;};
async function lab(p){await p.locator((p.viewportSize().width<=700)?'[data-v="brok"]':'#tab-brok').click();}
async function choose(p,n){await p.locator('#f-denominator').fill(String(n));await p.locator('#f-equalize').click();}
async function exportNote(p){const d=p.waitForEvent('download');await p.locator('#f-download').click();return JSON.parse(fs.readFileSync(await(await d).path(),'utf8'));}
(async()=>{
 const server=http.createServer((q,r)=>{if(q.url==='/'){r.setHeader('Content-Type','text/html');r.end(fs.readFileSync(path.join(root,'index.html')));}else{r.statusCode=404;r.end();}});await new Promise(r=>server.listen(0,'127.0.0.1',r));const url='http://127.0.0.1:'+server.address().port;
 const b=await chromium.launch({channel:process.env.CHROMIUM_CHANNEL||'chrome'});
 try{
 for(const lang of ['nb','en'])for(const dark of [false,true]){
  const p=await b.newPage({viewport:{width:390,height:844},colorScheme:dark?'dark':'light'}),errors=[];p.on('pageerror',e=>errors.push(e.message));await p.goto(file);if(lang==='en')await p.locator('#lang-en').click();await lab(p);
  await p.locator('#f-explore summary').click();await choose(p,12);await p.locator('#f-part-0').fill('8');await p.locator('#f-part-1').fill('3');await p.locator('#f-parts button').click();
  await p.locator('#f-equalize').click();check(await p.locator('#f-part-0').inputValue()==='8','Reapplying same partition keeps work');
  await p.locator('#f-denominator').fill('24');check((await p.locator('#f-den-feedback').innerText()).includes('12'),'Pending draft identifies current model');check(await p.locator('#f-parts button').isDisabled(),'Cannot validate twelve-part model against pending choice');
  await p.locator('#f-equalize').click();check(await p.locator('#f-part-0').inputValue()==='','New applied partition clears old numerators');
  const target=await p.locator('[data-toggle-piece="0"]').boundingBox();check(target.width>=44&&target.height>=44,'Accessible alternative to tiny piece targets');
  const emptyFill=await p.locator('[data-piece="0:23"]').evaluate(e=>getComputedStyle(e).backgroundColor);
  await p.locator('#f-piece-choice-0').selectOption('24');await p.locator('[data-toggle-piece="0"]').click();check(await p.locator('[data-piece="0:23"]').getAttribute('aria-pressed')==='true','Touch-friendly alternative marks exact chosen piece');check(await p.locator('[data-piece="0:23"]').evaluate(e=>getComputedStyle(e).backgroundColor)===emptyFill,'Pointing does not change the quantity color');
  check(await p.locator('[data-piece="0:23"]').evaluate(e=>getComputedStyle(e).color!==getComputedStyle(e).backgroundColor),'Unfilled marked piece visible');
  await p.locator('[data-toggle-piece="0"]').click();check(await p.locator('[data-piece="0:23"]').getAttribute('aria-pressed')==='false','Alternative unmarks same piece');
  await p.locator('#f-original').click();check(await p.locator('.f-piece').count()===7,'Can compare against original partition');
  check(await p.locator('#f-denominator').inputValue()==='','Return to original clears applied choice');
  for(let i=0;i<3;i++)await p.locator('#f-hint').click();check(await p.evaluate(()=>document.activeElement.id)==='f-hint-text-2','Third hint keeps meaningful focus');
  check(await p.locator('[data-read-hint]').count()===3,'Every visible hint can be read aloud');
  check(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No mobile overflow');
  await p.locator('#f-skip').click();await p.locator('#f-explanation').fill('Unsent fictional draft');check(await p.locator('#f-draft-notice').isVisible(),'Unsent-draft consequence visible');
  await p.locator('#f-transfer').click();await p.locator('#f-skip').click();const before=await exportNote(p);await p.locator('#f-read').click();const after=await exportNote(p);
  check(JSON.stringify(before.tasks)===JSON.stringify(after.tasks),'Summary reading cannot modify task records');check(after.summaryReadAloud.includes('question'),'Summary audio recorded separately');
  check((await p.locator('.f-summary').innerText()).includes(lang==='en'?'includes your written':'inneholder svar og forklaringer'),'Export discloses inclusion of learner text');
  check(!errors.length,'No runtime errors');await p.close();
 }
 // Delayed AI reply: retain denominator input, caret, and scroll while learner explores.
 {const p=await b.newPage();let release;const ready=new Promise(r=>release=r);await p.route('**/api/health',r=>r.fulfill({json:{ai:true,capabilities:{fractionSequence:1}}}));await p.route('**/api/makker',async r=>{await ready;await r.fulfill({json:{reply:'Can you show the same amount?',sequenceVersion:1}});});await p.goto(url);await p.waitForFunction(()=>document.querySelector('#mode-pill').classList.contains('live'));await lab(p);await p.locator('#f-skip').click();await p.locator('#f-explanation').fill('Equal parts');await p.locator('#f-explanation-form button').click();await p.locator('#f-explore summary').click();await p.locator('#f-denominator').fill('12');await p.locator('#f-denominator').press('ArrowLeft');const y=await p.evaluate(()=>scrollY);release();await p.waitForFunction(()=>!document.querySelector('#f-transfer').disabled);check(await p.evaluate(()=>document.activeElement.id)==='f-denominator','Delayed reply does not steal model focus');check(await p.locator('#f-denominator').inputValue()==='12','Delayed reply keeps draft');check(await p.locator('#f-denominator').evaluate(e=>e.selectionStart)===1,'Delayed reply preserves caret');check(Math.abs((await p.evaluate(()=>scrollY))-y)<3,'Delayed reply preserves reading position');await p.close();}
 for(const target of ['#lang-en','.f-chat','#f-explore-toggle','#f-check-parts']){
  const p=await b.newPage();let release;const ready=new Promise(r=>release=r);
  await p.route('**/api/health',r=>r.fulfill({json:{ai:true,capabilities:{fractionSequence:1}}}));
  await p.route('**/api/makker',async r=>{await ready;await r.fulfill({json:{reply:'Can you show equal parts?',sequenceVersion:1}});});
  await p.goto(url);await p.waitForFunction(()=>document.querySelector('#mode-pill').classList.contains('live'));await lab(p);await p.locator('#f-skip').click();await p.locator('#f-explanation').fill('Equal parts');await p.locator('#f-explanation-form button').click();if(target==='#f-check-parts'){await p.locator('#f-explore summary').click();await choose(p,12);}await p.locator(target).focus();release();await p.waitForFunction(()=>!document.querySelector('#f-transfer').disabled);
  check(await p.locator(target).evaluate(e=>e===document.activeElement),'Delayed reply preserves navigation/chat focus '+target);await p.close();
 }
 for(const backend of ['artifact','worker'])for(const reply of ['   ','x'.repeat(1300)]){
  const p=await b.newPage();if(backend==='artifact')await p.addInitScript(reply=>{window.claude={use:async()=>({json:async()=>({reply})})};},reply);else{await p.route('**/api/health',r=>r.fulfill({json:{ai:true,capabilities:{fractionSequence:1}}}));await p.route('**/api/makker',r=>r.fulfill({json:{reply,sequenceVersion:1}}));}
  await p.goto(backend==='artifact'?file:url);if(backend==='worker')await p.waitForFunction(()=>document.querySelector('#mode-pill').classList.contains('live'));await lab(p);await p.locator('#f-skip').click();await p.locator('#f-explanation').fill('Equal parts');await p.locator('#f-explanation-form button').click();await p.waitForFunction(()=>!document.querySelector('#f-transfer').disabled);check((await p.locator('#f-assessment').innerText()).includes('Øvingsmodus'),'Unusable reply falls back '+backend);check((await p.locator('.f-chat .msg').last().innerText()).trim().length>5,'Fallback has actual guidance');await p.close();
 }
 {const p=await b.newPage();await p.addInitScript(()=>{window.audio=[];window.cancels=0;window.SpeechSynthesisUtterance=class{constructor(t){this.text=t;}};Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[{lang:'nb-NO',localService:true,name:'Nora'}],cancel(){window.cancels++;},speak(u){window.audio.push(u.text);}}});});await p.goto(file);await lab(p);await p.locator('#f-hint').click();await p.locator('[data-read-hint="0"]').click();check((await p.evaluate(()=>audio.at(-1))).includes('brøkstreken'),'Reads actual visible hint');const n=await p.evaluate(()=>cancels);await p.locator('#tab-forelder').click();check(await p.evaluate(()=>cancels)===n+1,'Leaving lab stops its speech');await p.close();}
 console.log(JSON.stringify({passed,liveAI:false,realMicrophone:false}));
 }finally{await b.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
