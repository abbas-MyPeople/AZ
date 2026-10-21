#!/usr/bin/env python3
"""Render research/content-engine/posts.json into a phone-friendly posting calendar.

Usage: python3 scripts/build-content-calendar.py  ->  research/content-engine/calendar.html
Images are referenced as assets/social/*.jpg and published next to the page.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "research/content-engine/posts.json"
OUT = ROOT / "research/content-engine/calendar.html"

PAGE = r"""<title>Abbas Content Calendar</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Layout: one column of day entries, each = card image + platform tabs with copy-ready text */
:root{
  --ink:oklch(23% 0.012 60);--ink-2:oklch(45% 0.010 60);--ink-3:oklch(60% 0.010 60);
  --paper:oklch(97% 0.006 75);--surface:oklch(100% 0 0);--surface-2:oklch(93.5% 0.007 75);
  --rule:oklch(88% 0.008 70);--deep:oklch(38% 0.070 160);--ticket:oklch(53% 0.150 32);
  --ticket-soft:oklch(95% 0.022 32);--brand:#1c4739;--on-brand:#ffffff;--on-brand-2:#bcd8cc;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--serif:"Iowan Old Style",Georgia,serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;--r:7px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:oklch(94% 0.010 75);--ink-2:oklch(78% 0.010 75);--ink-3:oklch(63% 0.010 75);
  --paper:oklch(16% 0.008 70);--surface:oklch(20% 0.008 70);--surface-2:oklch(25% 0.008 70);
  --rule:oklch(31% 0.009 70);--deep:oklch(76% 0.105 162);--ticket:oklch(70% 0.135 34);
  --ticket-soft:oklch(26% 0.045 32);color-scheme:dark}}
:root[data-theme="dark"]{
  --ink:oklch(94% 0.010 75);--ink-2:oklch(78% 0.010 75);--ink-3:oklch(63% 0.010 75);
  --paper:oklch(16% 0.008 70);--surface:oklch(20% 0.008 70);--surface-2:oklch(25% 0.008 70);
  --rule:oklch(31% 0.009 70);--deep:oklch(76% 0.105 162);--ticket:oklch(70% 0.135 34);
  --ticket-soft:oklch(26% 0.045 32);color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font:16.5px/1.6 var(--sans);margin:0}
.w{max-width:880px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
header{padding-block:40px 28px;border-bottom:1px solid var(--rule)}
.kick{font:600 11px/1.4 var(--mono);letter-spacing:.15em;text-transform:uppercase;color:var(--ticket);margin:0}
h1{font-size:clamp(2rem,5vw,3rem);font-weight:830;letter-spacing:-.04em;line-height:1.03;margin:10px 0 14px;text-wrap:balance}
h2{font-size:clamp(1.3rem,3vw,1.7rem);font-weight:790;letter-spacing:-.03em;line-height:1.15;margin:4px 0 0;text-wrap:balance}
.lede{font-family:var(--serif);color:var(--ink-2);max-width:60ch;margin:0}
.prog{display:flex;gap:18px;flex-wrap:wrap;margin-top:22px;font-size:14px;color:var(--ink-2)}
.prog b{font-variant-numeric:tabular-nums;color:var(--ink);font-size:20px;font-weight:780;display:block}
.needs{margin-block:28px 0;background:var(--ticket-soft);border-radius:var(--r);padding:18px 20px}
.needs h3{margin:0 0 8px;font-size:1rem;font-weight:720}
.needs ul{margin:0;padding-left:18px;display:grid;gap:6px;font-size:15px}
.needs li span{color:var(--ink-3);font-family:var(--mono);font-size:12px}
main{display:grid;gap:0}
.day{padding-block:36px;border-bottom:1px solid var(--rule);scroll-margin-top:12px}
.day.today{background:linear-gradient(var(--surface-2),var(--surface-2)) padding-box}
.dhead{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.date{font:600 13px/1 var(--mono);color:var(--ink-2);font-variant-numeric:tabular-nums}
.pill{font:600 11px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;padding:5px 8px;border-radius:4px;background:var(--surface-2);color:var(--ink-2)}
.today .pill.now{background:var(--brand);color:var(--on-brand)}
.grid{display:grid;grid-template-columns:minmax(0,300px) minmax(0,1fr);gap:28px;margin-top:20px;align-items:start}
@media (max-width:720px){.grid{grid-template-columns:1fr}}
.imgs{display:grid;gap:10px}
.imgs img{width:100%;height:auto;border-radius:var(--r);border:1px solid var(--rule);display:block}
.imgs .more{display:grid;grid-template-columns:repeat(auto-fill,minmax(70px,1fr));gap:8px}
.imgs a{color:var(--deep);font-size:13px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.tab{font:600 14px/1 var(--sans);min-height:40px;padding:0 14px;border-radius:5px;border:1px solid var(--rule);background:var(--surface);color:var(--ink);cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.tab[aria-selected="true"]{background:var(--brand);color:var(--on-brand);border-color:var(--brand)}
.tab .dot{width:7px;height:7px;border-radius:50%;background:var(--deep)}
.tab[aria-selected="true"] .dot{background:var(--on-brand-2)}
.tab:focus-visible,.btn:focus-visible{outline:2.5px solid var(--deep);outline-offset:3px}
.panel{background:var(--surface);border:1px solid var(--rule);border-radius:var(--r);padding:16px 18px;min-width:0}
.panel pre{white-space:pre-wrap;word-wrap:break-word;font:15px/1.55 var(--sans);margin:0;color:var(--ink)}
.panel .sub{margin-top:14px;padding-top:12px;border-top:1px dashed var(--rule)}
.panel .sub .kick{color:var(--ink-3);margin-bottom:6px}
.acts{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:14px}
.btn{font:650 14px/1 var(--sans);min-height:42px;padding:0 16px;border-radius:5px;border:1px solid var(--brand);background:var(--brand);color:var(--on-brand);cursor:pointer}
.btn.g{background:transparent;color:var(--ink);border-color:var(--rule)}
.btn.done{background:transparent;color:var(--deep);border-color:var(--deep)}
.count{font:12px var(--mono);color:var(--ink-3);font-variant-numeric:tabular-nums}
.count.over{color:var(--ticket);font-weight:700}
.need{margin-top:12px;font-size:14px;color:var(--ink-2)}
.need b{color:var(--ticket)}
footer{padding-block:32px 60px;color:var(--ink-3);font-size:14px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>

<header><div class="w">
  <p class="kick">AZ Restaurant Partners - content engine</p>
  <h1>Two weeks of posts, ready to go</h1>
  <p class="lede">Starts with the FOX 26 segment while it is still news. Open today's entry, tap a platform, tap Copy, paste, attach the card. Tick Posted so you know where you left off.</p>
  <div class="prog" id="prog"></div>
  <div class="needs" id="needs"></div>
</div></header>
<main class="w" id="days"></main>
<footer><div class="w">Every number on these posts comes from azrestaurantpartners.com or the capability ledger. Cards are regenerated with scripts/gen-social-cards.py.</div></footer>

<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
var data=JSON.parse(document.getElementById('data').textContent);
var store={get:function(k){try{return JSON.parse(localStorage.getItem('azcal:'+k))}catch(e){return null}},
           set:function(k,v){try{localStorage.setItem('azcal:'+k,JSON.stringify(v))}catch(e){}}};
var done=store.get('done')||{};
var PLAT=[['linkedin','LinkedIn'],['x','X'],['instagram','Instagram'],['facebook','Facebook'],['video','Video script'],['newsletter','Newsletter']];
var today=new Date();var iso=today.getFullYear()+'-'+String(today.getMonth()+1).padStart(2,'0')+'-'+String(today.getDate()).padStart(2,'0');
function el(t,c,txt){var e=document.createElement(t);if(c)e.className=c;if(txt!=null)e.textContent=txt;return e}
function xlen(t){return t.replace(/https?:\/\/\S+/g,'x'.repeat(23)).length}
function fmt(d){var p=d.split('-');return new Date(+p[0],+p[1]-1,+p[2]).toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'})}
function videoText(v){return 'FORMAT: '+v.format+'\n\nHOOK: '+v.hook+'\n\nBEATS:\n'+v.beats.map(function(b){return '- '+b}).join('\n')}
function copy(text,btn){
  var ok=function(){var o=btn.textContent;btn.textContent='Copied';setTimeout(function(){btn.textContent=o},1400)};
  var fallback=function(){var ta=document.createElement('textarea');ta.value=text;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');ok()}catch(e){btn.textContent='Select and copy the text'}document.body.removeChild(ta)};
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(ok,fallback)}else fallback();
}
var needs=[];
var root=document.getElementById('days');var todayEl=null;
data.days.forEach(function(d){
  var s=el('section','day');s.id='day'+d.day;
  var isToday=d.date===iso;if(isToday){s.classList.add('today');todayEl=s}
  var h=el('div','dhead');
  h.appendChild(el('span','date','Day '+d.day+' - '+fmt(d.date)));
  h.appendChild(el('span','pill',d.pillar));
  if(isToday)h.appendChild(el('span','pill now','Today'));
  s.appendChild(h);s.appendChild(el('h2',null,d.title));
  var g=el('div','grid');
  var imgs=el('div','imgs');
  var main=el('img');main.src=d.image;main.alt='Social card for '+d.title;main.loading='lazy';main.width=1080;main.height=1350;
  var a=el('a');a.href=d.image;a.target='_blank';a.rel='noopener';a.appendChild(main);imgs.appendChild(a);
  if(d.also&&d.also.length){var m=el('div','more');d.also.forEach(function(src){var i=el('img');i.src=src;i.alt='Extra card';i.loading='lazy';var l=el('a');l.href=src;l.target='_blank';l.rel='noopener';l.appendChild(i);m.appendChild(l)});imgs.appendChild(m)}
  imgs.appendChild(el('a',null,'Open full-size card to save it'));imgs.lastChild.href=d.image;imgs.lastChild.target='_blank';imgs.lastChild.rel='noopener';
  g.appendChild(imgs);
  var right=el('div');right.style.minWidth='0';
  var tabs=el('div','tabs');tabs.setAttribute('role','tablist');
  var panel=el('div','panel');panel.setAttribute('role','tabpanel');
  var avail=PLAT.filter(function(p){return d[p[0]]});
  function show(key){
    tabs.querySelectorAll('.tab').forEach(function(t){t.setAttribute('aria-selected',t.dataset.k===key?'true':'false')});
    panel.innerHTML='';
    var text=key==='video'?videoText(d.video):d[key];
    panel.appendChild(el('pre',null,text));
    var extra=[];
    if(key==='linkedin'&&d.linkedin_first_comment)extra.push(['First comment',d.linkedin_first_comment]);
    if(key==='x'&&d.x_thread)d.x_thread.forEach(function(t,i){extra.push(['Thread reply '+(i+1),t])});
    if(key==='instagram'&&d.stories)extra.push(['Stories',d.stories]);
    extra.forEach(function(e){var sub=el('div','sub');sub.appendChild(el('p','kick',e[0]));sub.appendChild(el('pre',null,e[1]));var b=el('button','btn g','Copy');b.type='button';b.style.marginTop='8px';b.onclick=function(){copy(e[1],b)};sub.appendChild(b);panel.appendChild(sub)});
    var acts=el('div','acts');
    var c=el('button','btn','Copy');c.type='button';c.onclick=function(){copy(text,c)};acts.appendChild(c);
    var k=d.day+':'+key;var p=el('button','btn g'+(done[k]?' done':''),done[k]?'Posted':'Mark posted');p.type='button';p.setAttribute('aria-pressed',done[k]?'true':'false');
    p.onclick=function(){done[k]=!done[k];store.set('done',done);p.textContent=done[k]?'Posted':'Mark posted';p.classList.toggle('done',!!done[k]);p.setAttribute('aria-pressed',done[k]?'true':'false');renderTabs();renderProg()};
    acts.appendChild(p);
    if(key==='x'){var n=xlen(text);acts.appendChild(el('span','count'+(n>280?' over':''),n+' / 280'))}
    panel.appendChild(acts);
    var need=d.needs||(key==='video'&&d.video.needs);
    if(key==='video'&&d.video.needs)need=d.video.needs;
    if(need){var nd=el('p','need');nd.innerHTML='<b>Needs from you:</b> ';nd.appendChild(document.createTextNode(need.replace('[ABBAS] ','')));panel.appendChild(nd)}
  }
  function renderTabs(){tabs.querySelectorAll('.tab').forEach(function(t){t.querySelector('.dot').hidden=!done[d.day+':'+t.dataset.k]})}
  avail.forEach(function(p){var t=el('button','tab');t.type='button';t.dataset.k=p[0];t.setAttribute('role','tab');var dot=el('i','dot');dot.hidden=true;t.appendChild(dot);t.appendChild(document.createTextNode(p[1]));t.onclick=function(){show(p[0])};tabs.appendChild(t)});
  right.appendChild(tabs);right.appendChild(panel);g.appendChild(right);s.appendChild(g);root.appendChild(s);
  show(avail[0][0]);renderTabs();
  if(d.needs)needs.push([d.day,d.needs]);
  if(d.video&&d.video.needs)needs.push([d.day,d.video.needs]);
});
var nb=document.getElementById('needs');
nb.appendChild(el('h3',null,'What only you can provide ('+needs.length+')'));
var ul=el('ul');needs.forEach(function(n){var li=el('li');li.appendChild(el('span',null,'Day '+n[0]+'  '));li.appendChild(document.createTextNode(n[1].replace('[ABBAS] ','')));ul.appendChild(li)});nb.appendChild(ul);
function renderProg(){
  var total=0,posted=0;data.days.forEach(function(d){PLAT.forEach(function(p){if(d[p[0]]&&p[0]!=='video'){total++;if(done[d.day+':'+p[0]])posted++}})});
  var pr=document.getElementById('prog');pr.innerHTML='';
  [[data.days.length,'days'],[total,'posts to publish'],[posted,'marked posted'],[14,'branded cards']].forEach(function(x){var s=el('div');s.appendChild(el('b',null,String(x[0])));s.appendChild(document.createTextNode(x[1]));pr.appendChild(s)});
}
renderProg();
if(todayEl&&!location.hash)setTimeout(function(){todayEl.scrollIntoView({block:'start'})},50);
})();
</script>
"""


def main():
    data = json.loads(SRC.read_text())
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    OUT.write_text(PAGE.replace("__DATA__", blob))
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
