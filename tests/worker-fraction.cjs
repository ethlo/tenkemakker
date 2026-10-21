// No network calls: exercise the real Worker handlers with a simulated model.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
let sent;
const ctx = {Request, Response, URL, TextEncoder, TextDecoder, atob, Uint8Array, Date,
  crypto: require('node:crypto').webcrypto,
  fetch: async (_url, options) => {
    sent = JSON.parse(options.body);
    return Response.json({content: [{type:'text', text:JSON.stringify({reply:'Why must the parts have equal sizes?'})}]});
  }};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../worker/worker.js'),'utf8').replace('export default','const worker =') +
  '\nglobalThis.testWorker=worker;globalThis.testMakker=makker;',ctx);
const request = body => new Request('https://example.test/api/makker',{method:'POST',body:JSON.stringify(body)});
(async()=>{
 const env={ANTHROPIC_API_KEY:'fictional-test-key'};
 // Auth remains required. Only subsequent handler tests bypass it inside this VM.
 assert.equal((await ctx.testWorker.fetch(new Request('https://example.test/api/health'),{},{})).status,401);
 vm.runInContext('verifyAccess=async()=>"fictional-test-user";',ctx);
 for(const enabled of [true,false]){
  const r=await ctx.testWorker.fetch(new Request('https://example.test/api/health'),enabled?env:{},{});
  assert.deepEqual(await r.json(),{ok:true,ai:enabled,capabilities:{fractionSequence:1}});
 }
 for(const lang of ['nb','en']){
  const r=await ctx.testMakker(request({task:0,sequence:true,mode:'teach',lang,history:[{role:'user',content:'We need equal parts.'}]}),env);
  assert.equal(r.status,200);assert.equal((await r.json()).sequenceVersion,1);
  assert(sent.messages[0].content.includes(lang==='en'?'engelsk':'norsk bokmål'));
  assert(sent.messages[0].content.includes('ikke en automatisk godkjenning'));
  assert(sent.messages[0].content.includes('Ikke gi fasiten'));
 }
 assert.equal((await ctx.testMakker(request({task:1,sequence:true}),env)).status,400);
 assert.equal((await ctx.testMakker(request({task:0,sequence:true}),{})).status,503);
 const normal=await ctx.testMakker(request({task:1,mode:'hint',hint:2}),env);
 assert.equal(normal.status,200);assert(!('sequenceVersion' in await normal.json()));
 assert(sent.messages[0].content.includes('800 kr'));
 console.log('Worker contract: auth, capabilities, versioned sequence, language, task bounds and legacy route passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
