// Connected-learning behavior checks, using the existing browser installation.
const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const file=pathToFileURL(path.resolve(__dirname,'../index.html')).href;
let passed=0;const check=(v,label)=>{assert(v,label);passed++;};
const artifactDir=process.env.TEST_SCREENSHOTS;
async function answer(p,value){await p.locator('#f-answer').fill(value);await p.locator('#f-answer').press('Enter');}
async function choose(p,value){await p.locator('#f-denominator').fill(String(value));await p.locator('#f-denominator').press('Enter');}
async function download(p){const d=p.waitForEvent('download');await p.locator('#f-download').click();return JSON.parse(fs.readFileSync(await(await d).path(),'utf8'));}
(async()=>{
 const b=await chromium.launch({channel:process.env.CHROMIUM_CHANNEL||'chrome',headless:true});
 try{
 for(const lang of ['nb','en'])for(const width of [390,1200]){
  const p=await b.newPage({viewport:{width,height:1000},colorScheme:width===390?'dark':'light',reducedMotion:'reduce'}),errors=[];
  p.on('pageerror',e=>errors.push(e.message));
  await p.goto(file);if(lang==='en')await p.locator('#lang-en').click();
  await p.locator(width===390?'[data-v="brok"]':'#tab-brok').click();
  const overflow=async()=>check(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No overflow at '+width);
  check(!(await p.locator('#f-explore').getAttribute('open')),'First task starts without model');
  await answer(p,'3/7');
  await p.locator('#f-explore summary').click();
  // Every permitted denominator, plus invalid format and range cases.
  for(const n of [1,...Array.from({length:23},(_,i)=>i+2),25,'2.5','abc']){
   await choose(p,n);const valid=[12,24].includes(n);
   check(await p.locator('#f-parts').count()===(valid?1:0),'Common denominator validation '+n);
   check(await p.locator('.f-piece').count()===(valid?2*n:7),'Partition count '+n);
   check(await p.locator('.f-piece.filled:not(.second)').count()===(valid?n*2/3:2),'First quantity preserved '+n);
   check(await p.locator('.f-piece.filled.second').count()===(valid?n/4:1),'Second quantity preserved '+n);
  }
  await choose(p,12);
  await p.locator('#f-part-0').fill('8');await p.locator('#f-part-1').fill('3');await p.locator('#f-parts button').click();
  check((await p.locator('#f-parts-feedback').innerText()).includes(lang==='en'?'correct':'stemmer'),'Exact equivalents validated');
  await p.locator('[data-piece="0:0"]').focus();await p.keyboard.press('Space');
  check(await p.locator('[data-expression-row="0"]').first().evaluate(e=>e.classList.contains('selected')),'Keyboard marking links expression');
  check(await p.evaluate(()=>document.activeElement.dataset.piece==='0:0'),'Mark keeps keyboard focus');
  await p.locator('[data-rep="line"]').click();
  const points=await p.locator('.f-line circle').evaluateAll(es=>es.map(e=>e.getAttribute('cx')));
  await choose(p,24);
  check(JSON.stringify(points)===JSON.stringify(await p.locator('.f-line circle').evaluateAll(es=>es.map(e=>e.getAttribute('cx')))),'New partition never moves the quantities');
  check(await p.locator('#f-part-0').inputValue()===''&&await p.locator('#f-parts-feedback').innerText()==='','Partition clears old equivalents and approval');
  await p.locator('[data-line-row="1"]').focus();await p.keyboard.press('Enter');
  check(await p.locator('[data-expression-row="1"]').first().evaluate(e=>e.classList.contains('selected')),'Line keyboard selection links expression');
  await p.locator('#f-part-0').fill('16');await p.locator('#f-part-1').fill('6');await p.locator('#f-parts button').click();
  await p.locator('#f-part-1').fill('7');check(await p.locator('#f-parts-feedback').innerText()==='','Editing clears equivalent feedback');
  await p.locator('#f-hint').click();await overflow();
  if(artifactDir){fs.mkdirSync(artifactDir,{recursive:true});await p.screenshot({path:path.join(artifactDir,`model-${lang}-${width}.png`),fullPage:true});}
  await answer(p,'22/24');await p.locator('#f-advance').click();
  await p.locator('#f-explanation').fill('Fictional private explanation: equal-sized pieces.');
  await p.locator('#f-explanation-form button[type=submit]').click();await p.waitForFunction(()=>!document.getElementById('f-transfer').disabled);
  await p.locator('#f-transfer').click();
  check(!(await p.locator('#f-explore').getAttribute('open')),'Transfer closes model');
  check(await p.locator('.f-hints p').count()===0,'Transfer clears hints');
  await p.locator('#f-explore summary').click();check(await p.locator('#f-denominator').inputValue()==='','Transfer clears denominator');
  check(await p.locator('.f-piece[aria-pressed=true]').count()===0,'Transfer clears marks');
  await choose(p,12);check(await p.locator('#f-parts').count()===0,'Twelve is not a common denominator for transfer');
  for(const n of [10,20]){await choose(p,n);check(await p.locator('.f-piece.filled:not(.second)').count()===n/2&&await p.locator('.f-piece.filled.second').count()===n/5,'Transfer amount preserved '+n);}
  await answer(p,'3/7');await p.locator('#f-skip').click();
  check((await p.locator('.f-result').nth(1).innerText()).includes(lang==='en'?'without a resolved':'uten avklart'),'Unresolved task visible');
  const note=await download(p);
  check(note.version===2&&note.tasks[0].solved&&!note.tasks[1].solved&&note.tasks[1].endedUnresolved,'Export version and outcomes');
  check(note.tasks[0].attempts[0].support.representations.length===0&&note.tasks[0].attempts[0].support.denominatorChoices.length===0,'First attempt support snapshot immutable');
  check(note.tasks[0].attempts[1].support.denominator===24&&note.tasks[0].attempts[1].support.hints===1,'Correct attempt retains its actual support');
  check(note.tasks[1].attempts[0].support.denominator===20&&note.tasks[1].attempts[0].support.hints===0,'Transfer has independent support');
  check(note.explanations[0].support.denominator===24,'Explanation retains pointing context');
  await overflow();
  await p.evaluate(()=>{window.print=()=>{};});await p.locator('#f-print').click();
  await p.emulateMedia({media:'print'});
  check(await p.locator('#f-print-page').isVisible()&&!(await p.locator('.wrap').isVisible()),'Print contains follow-up only');
  check((await p.locator('#f-print-page').innerText()).includes('1/3 + 1/6'),'Delayed follow-up uses new numbers');
  if(artifactDir)await p.screenshot({path:path.join(artifactDir,`print-${lang}-${width}.png`),fullPage:true});
  await p.evaluate(()=>window.dispatchEvent(new Event('afterprint')));await p.emulateMedia({media:'screen'});
  check(await p.locator('#f-print-page').count()===0,'Print cleanup restores screen');
  await p.locator(width===390?'[data-v="forelder"]':'#tab-forelder').click();
  check(!(await p.locator('#fraction-parent').innerText()).includes('Fictional private'),'Parent card never includes explanation text');
  await p.locator(width===390?'[data-v="brok"]':'#tab-brok').click();await p.locator('#f-restart').click();
  await p.locator('#f-skip').click();await p.locator('#f-transfer').click();await p.locator('#f-skip').click();
  const skipped=await download(p);check(skipped.tasks.every(t=>t.endedUnresolved&&t.attempts.length===0)&&skipped.explanations.length===0,'Entire flow can finish without fabricated success');
  check((await p.locator('.f-summary').innerText()).includes(lang==='en'?'No explanation':'Ingen forklaring'),'No false explanation receipt');
  check(!errors.length,'No browser errors '+errors.join(';'));await p.close();
 }
 // Browser-native UI paths with a speech adapter: read, stop, replay and math text.
 const p=await b.newPage();await p.addInitScript(()=>{
  window.spoken=[];window.stops=0;window.SpeechSynthesisUtterance=class{constructor(text){this.text=text;}};
  Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[{localService:true,lang:'nb-NO',name:'Norsk'}],cancel(){window.stops++;},speak(u){window.spoken.push(u.text);}}});
 });await p.goto(file);await p.locator('#tab-brok').click();
 await p.locator('#f-read').click();check((await p.evaluate(()=>window.spoken.at(-1))).includes('2 over 3 pluss 1 over 4'),'Math-aware task speech');
 await p.locator('#f-read-instruction').click();check((await p.evaluate(()=>window.spoken.at(-1))).includes('Prøv først selv'),'Visible instruction read');
 const stops=await p.evaluate(()=>window.stops);await p.locator('#f-stop').click();check(await p.evaluate(()=>window.stops)===stops+1,'Stop cancels speech');
 await p.locator('#f-read').click();check((await p.evaluate(()=>window.spoken.at(-1))).includes('2 over 3'),'Replay works');
 await p.locator('#f-skip').click();await p.locator('#f-explanation').fill('like store deler');await p.locator('#f-explanation-form button').click();
 await p.locator('#f-read-reply').click();check((await p.evaluate(()=>window.spoken.at(-1))).includes('uten å endre mengden'),'Follow-up is read aloud');
 await p.close();
 console.log(JSON.stringify({passed,liveAICalls:0,realMicrophoneAccess:false}));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
