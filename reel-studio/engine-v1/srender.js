const {chromium}=require('playwright');const {spawn}=require('child_process');
const [dir,cut,outFile,fps]=process.argv.slice(2);const vo=JSON.parse(require('fs').readFileSync(dir+'/vo_dur.json'))[cut];const dq=encodeURIComponent(JSON.stringify(Object.fromEntries(vo)));
(async()=>{const b=await chromium.launch({args:['--allow-file-access-from-files']});
const p=await b.newPage({viewport:{width:1080,height:1920}});
p.on('pageerror',e=>console.log('PAGEERR',e.message));
await p.goto(`file://${dir}/story.html?render=1&story=${cut}&fps=${fps}&d=${dq}`);await p.evaluate(()=>window.READY);
const dur=await p.evaluate(()=>DURATION), n=Math.round(dur*fps);
const ff=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',outFile],{stdio:['pipe','inherit','inherit']});
const t0=Date.now();
for(let i=0;i<n;i++){const d=await p.evaluate(i=>{frame(i);return document.getElementById('c').toDataURL('image/jpeg',0.95)},i);
 const buf=Buffer.from(d.split(',')[1],'base64'); if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r));
 if(i%300===0) console.log(`frame ${i}/${n} ${((Date.now()-t0)/1000).toFixed(0)}s`);}
ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await b.close(); console.log('done',dur);})();
