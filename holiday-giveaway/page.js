(function(){
"use strict";
var $=function(id){return document.getElementById(id)};
var EN={},lang="en";
document.querySelectorAll("[data-i]").forEach(function(e){EN[e.dataset.i]=e.innerHTML});
function t(k,v){var s=(T[lang]&&T[lang][k]!=null)?T[lang][k]:(T.en[k]!=null?T.en[k]:(EN[k]||""));
  if(v)Object.keys(v).forEach(function(n){s=s.split("{"+n+"}").join(v[n])});return s}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
var LOC={en:"en-US",hi:"hi-IN-u-nu-latn",ur:"ur-PK-u-nu-latn"};

/* Central Time clock */
function ct(ms){
  var p={};new Intl.DateTimeFormat("en-US",{timeZone:"America/Chicago",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"})
    .formatToParts(new Date(ms)).forEach(function(x){p[x.type]=x.value});
  return {key:p.year+"-"+p.month+"-"+p.day,secs:(+p.hour)*3600+(+p.minute)*60+(+p.second)};
}
function phase(){var n=Date.now();return n<START?"pre":(n>=END?"end":"live")}
function dayKey(){var ph=phase();return ph==="pre"?"2026-12-01":(ph==="live"?ct(Date.now()).key:null)}
function dayNum(k){return k==="2027-01-01"?32:+k.slice(8,10)}
function fmtDate(k,opt){return new Intl.DateTimeFormat(LOC[lang],Object.assign({timeZone:"America/Chicago"},opt)).format(new Date(Date.parse(k+"T12:00:00-06:00")))}
function left(ms){var m=Math.max(0,Math.floor(ms/60000)),d=Math.floor(m/1440),h=Math.floor(m%1440/60),mm=m%60;
  return (d?d+t("u_d")+" ":"")+h+t("u_h")+" "+String(mm).padStart(2,"0")+t("u_m")}
function initial(s){return (s||"?").replace(/[^A-Za-z0-9]/g,"").charAt(0).toUpperCase()||"?"}

/* hero, lockup, follow links */
function drawHero(){
  var ph=phase(),k=dayKey(),pz=k&&PRIZES[k];
  $("tdLabel").textContent=ph==="end"?t("tdEnd"):(ph==="pre"?t("tdFirst"):t("tdToday"));
  $("tdDate").textContent=k?t("dayN",{n:dayNum(k)})+t("sep")+fmtDate(k,{weekday:"short",month:"short",day:"numeric"}):"";
  $("tdPrize").textContent=ph==="end"?t("endMsg"):(pz?(pz.p[lang]||pz.p.en):t("unkPrize"));
  $("tdPrize").style.fontSize=ph==="end"?"1.25rem":"";
  $("tdBiz").textContent=ph==="end"?"":(pz?t("from",{b:pz.s}):t("unkBiz"));
  $("tdBiz").hidden=ph==="end";
  tick();
  var biz=pz?pz.s:null,isWk=biz===WK;
  $("lkx").hidden=$("lkb").hidden=isWk||ph==="end";
  $("lkb").style.display=(isWk||ph==="end")?"none":"";
  $("lkx").style.display=(isWk||ph==="end")?"none":"";
  $("lkbn").textContent=biz||t("todayBiz");
  $("lkbl").textContent=k?t("dayN",{n:dayNum(k)}):"";
  var b2=$("s2b");b2.href=(pz&&pz.post)||"https://www.instagram.com/azrestaurantpartners/";b2.firstChild.innerHTML=bidi(esc((pz&&pz.post)?t("s2post"):t("s2b")));
  var a=$("fo3");
  a.hidden=isWk;a.style.display=isWk?"none":"";$("foNote").hidden=!isWk;
  if(!isWk){
    if(pz&&pz.h){a.href="https://www.instagram.com/"+pz.h+"/";$("fo3h").textContent="@"+pz.h}
    else{a.href="https://www.instagram.com/azrestaurantpartners/";$("fo3h").textContent=t("todayBiz")}
    a.querySelector("small").textContent=pz?pz.s:t("onPost");
    var m=$("fo3m");
    if(pz&&pz.logo){m.outerHTML='<img id="fo3m" src="'+esc(pz.logo)+'" alt="" width="36" height="36">'}
    else if(m.tagName!=="IMG"){m.textContent=pz?initial(pz.s):"?"}
  }
}
function tick(){
  var ph=phase(),el=$("tdCd");
  if(ph==="end"){el.hidden=true;return}
  el.hidden=false;
  var ms=ph==="pre"?START-Date.now():(86400-ct(Date.now()).secs)*1000;
  el.innerHTML=esc(ph==="pre"?t("cdPre"):t("cdLive"))+' <b>'+esc(left(ms))+'</b>';
}

/* calendar */
var MON={en:["Dec","Jan"],hi:["दिसंबर","जनवरी"],ur:["دسمبر","جنوری"]};
function drawCal(){
  var ul=$("cal"),h="",now=phase()==="live"?ct(Date.now()).key:null,last=0;
  Object.keys(PRIZES).forEach(function(k){last=Math.max(last,dayNum(k))});
  var cur=dayKey()?dayNum(dayKey()):32,shown=Math.min(32,Math.max(last,cur)+3);
  $("calMore").hidden=shown>=32||!ul.classList.contains("short");
  for(var i=0;i<32;i++){
    var dec=i<31,dn=dec?i+1:1,key=(dec?"2026-12-":"2027-01-")+String(dn).padStart(2,"0"),pz=PRIZES[key];
    var date=(MON[lang]||MON.en)[dec?0:1]+" "+dn,label=t("day")+" "+(i+1)+", "+date,cls=(key===now?" now":"")+(i>=shown?" later":"");
    if(pz){h+='<li class="lit'+cls+'"><span class="d">'+esc(date)+' <small>'+esc(t("day")+" "+(i+1))+'</small></span><span><span class="p">'+esc(pz.p[lang]||pz.p.en)+'</span><br><span class="s">'+esc(pz.s)+'</span></span></li>';}
    else h+='<li class="'+cls.trim()+'" aria-label="'+esc(label+", "+t("hidden"))+'"><span class="d">'+esc(date)+' <small>'+esc(t("day")+" "+(i+1))+'</small></span><span class="q" aria-hidden="true">?</span><span class="r">'+esc(t("hidden"))+'</span></li>';
  }
  ul.innerHTML=h;
}

/* sponsors */
function drawSp(){
  var h='<li><img src="/assets/brand/logo-180.png" alt="" width="52" height="52" loading="lazy"><div><b>AZ Restaurant Partners</b><small>'+esc(t("spOrg"))+'</small><a href="https://www.instagram.com/azrestaurantpartners/" target="_blank" rel="noopener">@azrestaurantpartners</a></div></li>'
       +'<li><img src="/assets/giveaway/wk-logo.png" alt="" width="52" height="52" loading="lazy"><div><b>Wok &amp; Karahi</b><small>'+esc(t("spWk"))+'</small><a href="https://www.instagram.com/wokandkarahitexas/" target="_blank" rel="noopener">@wokandkarahitexas</a></div></li>';
  Object.keys(PRIZES).sort().forEach(function(k){var p=PRIZES[k];if(p.s===WK)return;
    var pic=p.logo?'<img src="'+esc(p.logo)+'" alt="" width="52" height="52" loading="lazy">':'<span class="mono" aria-hidden="true">'+esc(initial(p.s))+'</span>';
    h+='<li>'+pic+'<div><b>'+esc(p.s)+'</b><small>'+esc(t("spDay",{n:dayNum(k),date:fmtDate(k,{month:"short",day:"numeric"})}))+'</small>'+(p.h?'<a href="https://www.instagram.com/'+esc(p.h)+'/" target="_blank" rel="noopener">@'+esc(p.h)+'</a>':'')+'</div></li>'});
  if(phase()!=="end")h+='<li class="next">'+esc(t("spNext"))+'</li>';
  $("sp").innerHTML=h;
}

/* forms */
function store(n,v){try{if(v===undefined)return localStorage.getItem(n);localStorage.setItem(n,v)}catch(e){return null}}
function doneKey(kind){return "hg_"+kind+"_"+dayKey()}
function fieldErr(id,msg){var i=$(id),e=$(id+"-e");if(!i||!e)return;e.textContent=msg||"";
  if(msg){i.setAttribute("aria-invalid","true");i.setAttribute("aria-describedby",id+"-e")}else{i.removeAttribute("aria-invalid");i.removeAttribute("aria-describedby")}}
function igClean(v){v=(v||"").trim();var m=v.match(/instagram\.com\/([A-Za-z0-9._]+)/i);if(m)v=m[1];return v.replace(/^@+/,"")}
function igOk(v){return /^[A-Za-z0-9._]{1,30}$/.test(v)}
function phoneOk(v){var d=(v||"").replace(/\D/g,"");if(d.length===11&&d[0]==="1")d=d.slice(1);return d.length===10&&/^[2-9]/.test(d)}
var REEL=/^(https?:\/\/)?(www\.|m\.)?instagram\.com\/(reel|reels|p)\/[A-Za-z0-9_-]{5,}/i;
function minDate(){return ct(Date.now()).key}

var JUST={};
function drawForms(){
  var ph=phase(),pre=ph==="pre";
  ["p","r"].forEach(function(x){
    var kind=x==="p"?"party":"reel",f=$(x==="p"?"fParty":"fReel"),done=$(x+"Done"),cl=$(x+"Closed");
    var already=ph!=="end"&&(JUST[kind]||store(doneKey(kind)));
    if(ph==="end"){f.hidden=true;done.hidden=true;cl.hidden=false;cl.textContent=t("closed");return}
    cl.hidden=true;
    if(already){f.hidden=true;done.hidden=false;$(x+"DoneT").textContent=JUST[kind]?t(x==="p"?(pre?"pDone1":"pDone"):(pre?"rDone1":"rDone")):t(x+"Again")}
    else{f.hidden=false;done.hidden=true}
    $(x==="p"?"barP":"barR").classList.toggle("on",!!already);
  });
  $("pDate").min=minDate();
}

function send(form,payload,x,kind){
  var btn=form.querySelector("button[type=submit]"),label=btn.innerHTML,ferr=$(x+"Err");
  ferr.textContent="";btn.disabled=true;btn.textContent=t("sending");
  fetch(API+form.dataset.ep,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)})
  .then(function(r){return r.json().catch(function(){return {ok:false,status:r.status}}).then(function(j){j.status=j.status||r.status;return j})})
  .then(function(j){
    if(j&&j.ok){JUST[kind]=1;store(doneKey(kind),"1");drawForms();$(x+"Done").focus({preventScroll:true});return}
    if(j&&j.reason==="rate_limited"){ferr.textContent=t("eRate");return}
    var fmap={name:"pName",phone:"pPhone",instagram:x==="p"?"pIg":"rIg",event_type:"pType",event_date:"pDate",headcount:"pHead",reel_url:"rUrl"};
    if(j&&j.field&&fmap[j.field]&&$(fmap[j.field])){var id=fmap[j.field];
      var known={pName:"eName",pPhone:"ePhone",pIg:"eIg",rIg:"eIg",pType:"eType",pDate:"eDate",pHead:"eHead",rUrl:"eUrl"};
      fieldErr(id,t(known[id]));$(id).focus();return}
    ferr.textContent=t("eNet");
  })
  .catch(function(){ferr.textContent=t("eNet")})
  .then(function(){btn.disabled=false;btn.innerHTML=label});
}

function firstBad(list){for(var i=0;i<list.length;i++){if(list[i][1]){fieldErr(list[i][0],t(list[i][2]))}else fieldErr(list[i][0],"")}
  for(var j=0;j<list.length;j++)if(list[j][1]){$(list[j][0]).focus();return true}return false}

$("fParty").dataset.ep="az-giveaway-party";$("fReel").dataset.ep="az-giveaway-reel";
$("fParty").addEventListener("submit",function(e){e.preventDefault();
  var name=$("pName").value.trim(),ph=$("pPhone").value.trim(),ig=igClean($("pIg").value),ty=$("pType").value,dt=$("pDate").value,hc=$("pHead").value.trim();
  var n=parseInt(hc,10);
  if(firstBad([["pName",name.length<2,"eName"],["pPhone",!phoneOk(ph),"ePhone"],["pIg",!igOk(ig),"eIg"],["pType",!ty,"eType"],["pDate",!/^\d{4}-\d{2}-\d{2}$/.test(dt)||dt<minDate(),"eDate"],["pHead",!/^\d+$/.test(hc)||n<1||n>5000,"eHead"]]))return;
  send(this,{name:name,phone:ph,instagram:"@"+ig,event_type:ty,event_date:dt,headcount:n,day:dayKey(),_hp:$("pHp").value},"p","party");
});
$("fReel").addEventListener("submit",function(e){e.preventDefault();
  var ig=igClean($("rIg").value),u=$("rUrl").value.trim();
  if(firstBad([["rIg",!igOk(ig),"eIg"],["rUrl",!REEL.test(u),"eUrl"]]))return;
  if(!/^https?:/i.test(u))u="https://"+u;
  send(this,{instagram:"@"+ig,reel_url:u,day:dayKey(),_hp:$("rHp").value},"r","reel");
});
document.querySelectorAll("form input,form select").forEach(function(i){i.addEventListener("input",function(){if(i.getAttribute("aria-invalid"))fieldErr(i.id,"")})});

/* sticky CTA: shows once the hero button is gone, hides while a form is on screen */
var dock=$("dock"),seen=new Set();
if("IntersectionObserver" in window){
  var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting)seen.add(en.target);else seen.delete(en.target)});
    dock.classList.toggle("show",phase()!=="end"&&seen.size===0)},{threshold:0});
  ["heroCta","party","reel","enter"].forEach(function(id){io.observe($(id))});
}

/* language */
function bidi(h){return lang==="ur"?String(h).replace(/(^|[\s(>:،"])(@[A-Za-z0-9._]+[A-Za-z0-9_]|18\+|\$\d[\d,]*)/g,"$1<bdi>$2</bdi>"):h}
function setLang(l){lang=T[l]?l:"en";var h=document.documentElement;h.lang=lang;h.dir=(lang==="ur")?"rtl":"ltr";
  document.querySelectorAll("[data-i]").forEach(function(e){var v=T[lang]&&T[lang][e.dataset.i];e.innerHTML=bidi(lang!=="en"&&v!=null?v:EN[e.dataset.i])});
  document.querySelectorAll(".lang button").forEach(function(b){b.setAttribute("aria-pressed",String(b.dataset.lang===lang))});
  drawAll();store("az_lang",lang)}
function drawAll(){drawHero();drawCal();drawSp();drawForms()}
$("calMore").addEventListener("click",function(){$("cal").classList.remove("short");this.hidden=true;this.setAttribute("aria-expanded","true")});
document.querySelectorAll(".lang button").forEach(function(b){b.addEventListener("click",function(){setLang(b.dataset.lang)})});
var q=new URLSearchParams(location.search).get("lang"),s=q||store("az_lang");
if(s&&s!=="en"&&T[s])setLang(s);else drawAll();
var lastPhase=phase(),lastKey=dayKey();
setInterval(function(){if(phase()!==lastPhase||dayKey()!==lastKey){lastPhase=phase();lastKey=dayKey();drawAll()}else tick()},20000);
})();
