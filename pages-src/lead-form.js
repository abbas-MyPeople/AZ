/* The inquiry form, same code and endpoint as the home page (v3/home-src.html).
   Posts to the gateway az-lead door with interests + role. Injected by build.py into pages that carry the form.
   The form needs id="leadForm", a button id="leadSend" and a note id="leadNote". */
(function(){
  var bar=document.getElementById("sticky"), target=document.getElementById("start");
  if(bar&&target){
    var check=function(){ var r=target.getBoundingClientRect(); bar.classList.toggle("away", r.top<innerHeight*0.95 && r.bottom>0); };
    addEventListener("scroll",check,{passive:true}); check();
  }
})();
(function(){
  var f=document.getElementById("leadForm"), btn=document.getElementById("leadSend"), note=document.getElementById("leadNote");
  if(!f) return;
  var formName=f.getAttribute("data-form")||"inquiry";
  function track(n,p){ try{ window.azTrack && window.azTrack(n,p); }catch(e){} }
  f.addEventListener("submit",function(e){
    e.preventDefault();
    var fd=new FormData(f), d={};
    fd.forEach(function(v,k){ if(k!=="interest") d[k]=v; });
    var picks=fd.getAll("interest");
    if(!d.name||!d.email||!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)){
      note.className="formnote err"; note.textContent="Add your name and a valid email so we can reply."; return;
    }
    d.interests=picks.length?picks.join(", "):"General enquiry";
    d._website=d._honey||""; delete d._honey;
    d._subject="AZ enquiry - "+(d.role||"")+" - "+(d.restaurant||d.name);
    d.source=(window.azSource&&window.azSource())||"direct / none";
    d.page=location.pathname;
    d._template="table"; d._captcha="false";
    btn.disabled=true; btn.textContent="Sending...";
    track("form_submit",{form:formName,interests:d.interests,role:d.role});
    fetch("https://wok-voice.fly.dev/gateway/form/az-lead",{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify(d)})
      .then(function(r){ if(!r.ok) throw 0; return r.json(); })
      .then(function(b){ if(!b||b.received!==true) throw 0;
        f.reset(); btn.textContent="Sent"; note.className="formnote ok"; note.textContent="Got it. We'll come back to you today.";
        track("form_success",{form:formName}); })
      .catch(function(){ btn.disabled=false; btn.textContent="Send"; note.className="formnote err";
        note.innerHTML='That didn’t send. Email <a href="mailto:abbas@azrestaurantpartners.com">abbas@azrestaurantpartners.com</a> or call (408) 393-6716.';
        track("form_error",{form:formName}); });
  });
})();
