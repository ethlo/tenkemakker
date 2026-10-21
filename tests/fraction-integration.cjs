// Uses an existing Playwright/browser installation; never installs or calls a live AI.
const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),file=pathToFileURL(path.join(root,'index.html')).href;
const screenshotDir=process.env.TEST_SCREENSHOTS;
if(screenshotDir)fs.mkdirSync(screenshotDir,{recursive:true});
let passed=0;
const check=(ok,label)=>{assert(ok,label);passed++;};
async function tab(p,name){
 const mobile=(p.viewportSize()?.width||1200)<=700;
 await p.locator(mobile?'[data-v="'+name+'"]':'#tab-'+name).click();
}
async function teach(p){await tab(p,'brok');await p.locator('#f-answer').fill('11/12');await p.locator('#f-answer').press('Enter');await p.locator('#f-advance').click();}
async function send(p,text='Vi gjør bitene like store uten å endre mengden.'){
 await p.locator('#f-explanation').fill(text);await p.locator('#f-explanation-form button[type=submit]').click();
 await p.waitForFunction(()=>document.getElementById('f-transfer')&&!document.getElementById('f-transfer').disabled);
}
async function shot(p,name){if(screenshotDir)await p.screenshot({path:path.join(screenshotDir,name+'.png'),fullPage:true});}
(async()=>{
 const server=http.createServer((req,res)=>{
  if(req.url==='/'||req.url==='/index.html'){res.setHeader('content-type','text/html');res.end(fs.readFileSync(path.join(root,'index.html')));}
  else{res.statusCode=404;res.end();}
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const url='http://127.0.0.1:'+server.address().port+'/';
 let browser;
 try{
 browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_CHANNEL?{channel:process.env.CHROMIUM_CHANNEL}:{})});
 const contexts=[];
 const page=async(options={})=>{const c=await browser.newContext({viewport:{width:1200,height:900},reducedMotion:'reduce',...options});contexts.push(c);const p=await c.newPage();p.setDefaultTimeout(10000);return p;};
 // Full local flow, both languages, themes and narrow/wide layouts.
 for(const lang of ['nb','en'])for(const dark of [false,true]){
  const mobile=dark,p=await page({viewport:{width:mobile?390:1200,height:900},colorScheme:dark?'dark':'light'}),errors=[];
  p.on('pageerror',e=>errors.push(e.message));await p.goto(file);if(lang==='en')await p.locator('#lang-en').click();
  check(await p.locator('#view-elev').isVisible(),'Task remains the start screen');
  await tab(p,'forelder');check(!(await p.locator('#fraction-parent').isVisible()),'Unused experiment does not clutter parent card');
  const initialWeek=await p.locator('#k-solved').innerText(),initialPoints=await p.locator('#k-tp').innerText();
  await tab(p,'laerer');const initialTeacher=await p.locator('#t-grid tr.me').innerText();
  await tab(p,'brok');check((await p.locator('.f-prototype').innerText()).includes(lang==='en'?'optional':'valgfritt'),'Lab labelled optional');
  for(const bad of ['3/7','11/0','100000/120000']){await p.locator('#f-answer').fill(bad);await p.locator('#f-answer').press('Enter');check(!(await p.locator('#f-advance').count()),'Invalid/incorrect fraction rejected: '+bad);}
  await p.locator('#f-explore summary').click();await p.locator('#f-denominator').fill('12');await p.locator('#f-equalize').click();
  check(await p.locator('.f-piece.filled:not(.second)').count()===8&&await p.locator('.f-piece.filled.second').count()===3,'First model preserves amounts');
  await p.locator('[data-rep="line"]').click();check(await p.locator('.f-line').count()===2,'Number lines render');
  await p.locator('[data-rep="symbols"]').click();await p.locator('#f-part-0').fill('8');await p.locator('#f-part-1').fill('3');await p.locator('#f-parts button').click();
  check((await p.locator('#f-parts-feedback').innerText()).length>0,'Equivalent feedback shown');
  await p.locator('#f-part-0').fill('9');check(await p.locator('#f-parts-feedback').innerText()==='','Edited equivalent clears stale approval');
  await p.locator('#f-answer').fill('22/24');await p.locator('#f-answer').press('Enter');await p.locator('#f-advance').click();
  await p.locator('#f-explanation').fill('Fictional draft');await tab(p,'laerer');await tab(p,'brok');check(await p.locator('#f-explanation').inputValue()==='Fictional draft','Draft survives tab switch');
  for(let i=0;i<6;i++)await send(p,'Vi gjør bitene like store. Dette er en oppdiktet forklaring som bevarer mengden, nummer '+i+'.');
  check(await p.locator('.f-chat').evaluate(e=>e.scrollHeight-e.clientHeight-e.scrollTop<4),'Newest follow-up visible');
  check(await p.evaluate(()=>document.activeElement.id==='f-explanation'),'Reply does not focus next-task button');
  await p.locator('.f-chat').evaluate(e=>e.scrollTop=30);await p.waitForFunction(()=>document.querySelector('.f-chat').scrollTop===30);
  await p.locator('#f-explore summary').click();check(await p.locator('.f-chat').evaluate(e=>Math.abs(e.scrollTop-30)<2),'Model toggle preserves reading position');
  await send(p);await shot(p,'chat-'+lang+'-'+(dark?'dark':'light'));
  await p.locator('#f-transfer').click();check(await p.locator('#f-explore').getAttribute('open')===null,'Transfer starts with closed model');
  await p.locator('#f-explore summary').click();await p.locator('#f-denominator').fill('10');await p.locator('#f-equalize').click();
  check(await p.locator('.f-piece.filled:not(.second)').count()===5&&await p.locator('.f-piece.filled.second').count()===2,'Transfer preserves amounts');
  await p.locator('#f-answer').fill('14/20');await p.locator('#f-answer').press('Enter');await p.locator('#f-advance').click();
  const dl=p.waitForEvent('download');await p.locator('#f-download').click();const note=JSON.parse(fs.readFileSync(await (await dl).path(),'utf8'));
  check(note.tasks.every(t=>t.solved)&&note.explanations.length===7,'Export retains task activity and explanations');
  await tab(p,'forelder');check(await p.locator('#fraction-parent').isVisible(),'Started lab has its own parent card');
  check(await p.locator('#k-solved').innerText()===initialWeek&&await p.locator('#k-tp').innerText()===initialPoints,'Experimental activity does not change main scores');
  check((await p.locator('[data-i18n="fWeekScope"]').innerText()).includes(lang==='en'?'Task tab':'Oppgave-fanen'),'Week card scoped to main tasks');
  check((await p.locator('#week .today').innerText()).includes(lang==='en'?'Task tab':'Oppgave-fanen'),'Empty-day message scoped');
  check(!(await p.locator('#fraction-parent').innerText()).includes('nummer 0'),'Parent card excludes transcript');
  check(await p.locator('#fraction-parent .f-dinner').isVisible(),'Lab dinner starter appears on its own card');
  await shot(p,'parent-'+lang+'-'+(dark?'dark':'light'));
  await tab(p,'laerer');check(await p.locator('#t-grid tr.me').innerText()===initialTeacher,'Lab does not claim teacher assessment');
  check((await p.locator('[data-i18n="fTeacherScope"]').innerText()).includes(lang==='en'?'not included':'inngår ikke'),'Teacher scope explicit');
  // Original three tasks still award progress and reach teacher/parent views.
  await tab(p,'elev');await p.locator('#stuck').click();
  for(const [answer,explanation] of [['22/24','Fellesnevner og like store biter, common denominator.'],['600','25 prosent er en firedel, percent means quarter.'],['5','Vi deler begge sider på tre, divide both sides.']]){
   await p.locator('#answer').fill(answer);await p.locator('#answer').press('Enter');check(await p.locator('#answer').isDisabled(),'Original task accepts '+answer);
   await p.locator('#explain').fill(explanation);await p.locator('#send').click();await p.locator('#next').click();
  }
  await tab(p,'forelder');check(Number(await p.locator('#k-solved').innerText())===Number(initialWeek)+3,'Week card includes main tasks exactly once');
  await tab(p,'laerer');check(await p.locator('#t-grid tr.me').innerText()!==initialTeacher,'Teacher row updates for main tasks');
  await tab(p,'elev');await p.locator('.new-topic').click();await p.locator('#topic').fill('brøk');await p.locator('#make-task').click();check(await p.locator('#answer').isEnabled(),'Additional task bank still works');
  await tab(p,'brok');await p.locator('#f-restart').click();await tab(p,'forelder');check(!(await p.locator('#fraction-parent').isVisible()),'Restart clears lab parent card');
  check(Number(await p.locator('#k-solved').innerText())===Number(initialWeek)+3,'Lab restart preserves main progress');
  check(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No horizontal overflow');check(errors.length===0,'No runtime errors: '+errors);
  await p.context().close();
 }
 // Old, future, disabled and supported capabilities; response version is also checked.
 for(const mode of ['old','future','off','new','wrong-response','failure','timeout']){
  const p=await page();let calls=0;
  await p.route('**/api/health',r=>r.fulfill({json:{ai:mode!=='off',...(mode==='old'?{}:{capabilities:{fractionSequence:mode==='future'?2:1}})}}));
  await p.route('**/api/makker',r=>{calls++;return mode==='timeout'?new Promise(()=>{}):r.fulfill({status:mode==='failure'?503:200,json:{reply:'SIMULATED FOLLOW-UP',...(mode==='wrong-response'?{}:{sequenceVersion:1})}});});
  if(mode==='timeout')await p.addInitScript(()=>{const t=window.setTimeout;window.setTimeout=(fn,ms,...a)=>t(fn,ms===15000?30:ms,...a);});
  await p.goto(url);if(mode!=='off')await p.waitForFunction(()=>document.getElementById('mode-pill').classList.contains('live'));
  await teach(p);await send(p);const content=await p.locator('.f-chat').innerText();
  check(calls===(['old','future','off'].includes(mode)?0:1),'Capability controls requests: '+mode);
  check(content.includes('SIMULATED FOLLOW-UP')===(mode==='new'),'Only versioned success displayed: '+mode);
  check((await p.locator('#f-assessment').innerText()).includes(mode==='new'?'KI-veiledning':'Øvingsmodus'),'Honest mode label: '+mode);
  if(mode==='old'){await tab(p,'elev');await p.locator('#stuck').click();await p.locator('#explain').fill('like store deler');await p.locator('#send').click();await p.waitForFunction(()=>!document.getElementById('send').disabled);check(calls===1,'Old backend still serves original hints');}
  await p.context().close();
 }
 // A late capability response must not recreate the input or drop keyboard focus.
 {const p=await page();let release;const ready=new Promise(r=>release=r);
 await p.route('**/api/health',async r=>{await ready;await r.fulfill({json:{ai:true,capabilities:{fractionSequence:1}}});});
 await p.goto(url,{waitUntil:'domcontentloaded'});await tab(p,'brok');await p.locator('#f-answer').fill('11/');release();
 await p.waitForFunction(()=>document.getElementById('mode-pill').classList.contains('live'));
 check(await p.evaluate(()=>document.activeElement.id==='f-answer')&&await p.locator('#f-answer').inputValue()==='11/','Late health preserves focus/draft');await p.context().close();}
 // A reply arriving while another view is active must not steal focus or lose the reply.
 {const p=await page();let release;const ready=new Promise(r=>release=r);
 await p.route('**/api/health',r=>r.fulfill({json:{ai:true,capabilities:{fractionSequence:1}}}));
 await p.route('**/api/makker',async r=>{await ready;await r.fulfill({json:{reply:'DELAYED FOLLOW-UP',sequenceVersion:1}});});
 await p.goto(url);await p.waitForFunction(()=>document.getElementById('mode-pill').classList.contains('live'));await teach(p);
 await p.locator('#f-explanation').fill('Like store deler');await p.locator('#f-explanation-form button[type=submit]').click();await tab(p,'elev');await p.locator('#answer').fill('11/');release();
 await p.waitForFunction(()=>document.getElementById('f-transfer')&&!document.getElementById('f-transfer').disabled);
 check(await p.evaluate(()=>document.activeElement.id==='answer'),'Delayed lab reply preserves main input focus');
 await tab(p,'brok');check((await p.locator('.f-chat').innerText()).includes('DELAYED FOLLOW-UP'),'Reply survives tab switch');
 check(await p.locator('.f-chat').evaluate(e=>e.scrollHeight-e.clientHeight-e.scrollTop<4),'Returning to lab reveals newest reply');await p.context().close();}
 // Artifact path stays independent of Worker capabilities and has a fallback.
 for(const fail of [false,true]){const p=await page();await p.addInitScript(fail=>{window.claude={use:async()=>({json:async()=>{if(fail)throw Error('simulated');return {reply:'ARTIFACT FOLLOW-UP'};}})};},fail);await p.goto(file);await teach(p);await send(p);check((await p.locator('.f-chat').innerText()).includes('ARTIFACT FOLLOW-UP')===!fail,'Artifact path/fallback '+fail);await p.context().close();}
 // Explicit speech bypasses automatic-read setting, uses only matching local voices,
 // and reports missing voices/errors in the lab. No actual audio or microphone access.
 for(const mode of ['local','missing','remote','error']){
  const p=await page();await p.addInitScript(mode=>{
   window.spoken=[];window.SpeechSynthesisUtterance=class{constructor(text){this.text=text;}};
   Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>mode==='missing'?[]:[{localService:mode!=='remote',lang:'nb-NO',name:'Norsk'}],cancel(){},speak(u){if(mode==='error'){u.onerror?.({error:'synthesis-failed'});return;}window.spoken.push(u.text);}}});
  },mode);await p.goto(file);await p.locator('details.settings summary').click();await p.locator('#speak-toggle').uncheck();await teach(p);
  const before=await p.evaluate(()=>window.spoken.length);await p.locator('#f-read').click();
  check(await p.evaluate(()=>window.spoken.length)===(mode==='local'?before+1:before),'Explicit/local speech behavior '+mode);
  check((await p.locator('#f-voice-note').innerText()).length>0=== (mode!=='local'),'Visible speech status '+mode);
  if(mode==='local'){await p.locator('#lang-en').click();const n=await p.evaluate(()=>window.spoken.length);await p.locator('#f-read').click();check(await p.evaluate(()=>window.spoken.length)===n,'No Norwegian voice for English');check((await p.locator('#f-voice-note').innerText()).includes('No English voice'),'Missing language visible');}
  await p.context().close();
 }
 console.log(JSON.stringify({passed,liveAICalls:0,realMicrophoneAccess:false}));
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
