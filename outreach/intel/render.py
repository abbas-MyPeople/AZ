#!/usr/bin/env python3
"""Render a restaurant profile as the page an owner sees on a phone, in person.

Five layers, each one tap deeper than the last:
  5 seconds   one insight about THEIR restaurant, in big type, and "Is this right?"
  30 seconds  three proofs, each with the source and the date we saw it
  2 minutes   opportunities, each tied to the findings it rests on
  10 minutes  everything we found, by topic, each one they can confirm or correct
  unlimited   every source, date and confidence, plus the questions only they can answer

Every Right / Not quite / Add detail tap becomes an owner event (see model.apply_event).
It is kept on the phone first, so a weak signal in a restaurant never loses an answer, and
sent to ENDPOINT when one is configured. The page is noindex and lives under /intel/.

    python3 -m outreach.intel.render wok-and-karahi-spring [--out intel/<slug>/index.html]
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib

from outreach.intel import model

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENDPOINT = "https://wok-voice.fly.dev/gateway/az-intel/answer"   # voice-agent/src/az_intel.py

LABELS = {
    "fact": "We saw this", "derived": "Worked out from what we saw",
    "inference": "Our read, please check", "hypothesis": "A guess, only you know",
}
DIM_NAMES = {
    "identity": "Who you are", "history": "Your story", "cuisine": "Your food", "menu": "Your menu",
    "pricing": "Prices", "reputation": "Reputation", "sentiment": "What guests say",
    "website": "Website", "ordering": "Ordering", "marketing": "Marketing", "social": "Social media",
    "competition": "Competition", "geography": "Location", "catering": "Catering",
    "community": "Community", "technology": "Technology", "operations": "How you run",
    "people": "Team",
}

CSS = """
:root{--ink:oklch(23% .012 60);--ink-2:oklch(45% .01 60);--ink-3:oklch(60% .008 60);
--paper:oklch(97% .006 75);--surface:#fff;--surface-2:oklch(93.5% .007 75);--rule:oklch(88% .008 70);
--deep:oklch(38% .07 160);--ticket:oklch(53% .15 32);--ticket-soft:oklch(95% .022 32);
--brand:#1c4739;--on-brand:#fff;--slab:#1a1714;--on-slab:#f2ede7;--on-slab-2:#c8c0b6;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,sans-serif;--serif:Georgia,"Iowan Old Style",serif;
--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.55 var(--sans);-webkit-font-smoothing:antialiased}
.w{max-width:560px;margin:0 auto;padding:0 20px}
.hero{min-height:100svh;background:var(--slab);color:var(--on-slab);display:flex;flex-direction:column;justify-content:center;padding:40px 0}
.kick{font:600 11px/1 var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--ticket);margin:0 0 18px}
.hero .kick{color:oklch(75% .12 40)}
h1{font-size:clamp(2rem,8.4vw,2.9rem);line-height:1.06;letter-spacing:-.035em;font-weight:820;margin:0 0 18px;text-wrap:balance}
.proof{font:1.1rem/1.5 var(--serif);color:var(--on-slab-2);margin:0 0 30px}
h2{font-size:1.55rem;line-height:1.15;letter-spacing:-.025em;margin:0 0 6px}
.sub{color:var(--ink-2);margin:0 0 20px}
section{padding:48px 0;border-top:1px solid var(--rule)}
.btn{font:650 16px var(--sans);padding:14px 20px;border-radius:6px;border:1px solid transparent;cursor:pointer;min-height:48px}
.btn-p{background:var(--brand);color:var(--on-brand)}
.btn-g{background:transparent;border-color:var(--rule);color:inherit}
.hero .btn-g{border-color:oklch(45% .01 60);color:var(--on-slab)}
.row{display:flex;gap:10px;flex-wrap:wrap}
.card{background:var(--surface);border:1px solid var(--rule);border-radius:8px;padding:18px;margin:0 0 14px}
.card h3{font-size:1.08rem;margin:0 0 6px;letter-spacing:-.01em}
.tag{display:inline-block;font:600 11px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;padding:5px 7px;border-radius:4px;background:var(--surface-2);color:var(--ink-2);margin:0 0 10px}
.tag.guess{background:var(--ticket-soft);color:var(--ticket)}
.src{font-size:14px;color:var(--ink-3);margin:8px 0 0}
.src a{color:var(--deep)}
q{font-family:var(--serif);font-style:italic}
.ask{margin:14px 0 0;padding:12px 0 0;border-top:1px dashed var(--rule)}
.ask p{font-size:15px;color:var(--ink-2);margin:0 0 10px}
.ask .btn{font-size:14px;padding:10px 14px;min-height:44px}
.done{font-size:14px;color:var(--deep);font-weight:650;margin:10px 0 0}
textarea{width:100%;font:16px var(--sans);padding:10px;border:1px solid var(--rule);border-radius:6px;margin:10px 0 0;min-height:76px}
.more{display:none}.more.open{display:block}
details{border-top:1px solid var(--rule);padding:12px 0}summary{font-weight:700;cursor:pointer;min-height:44px;display:flex;align-items:center}
.why{font-size:15px;color:var(--ink-2)}
.hold{opacity:.55}
footer{padding:30px 0 60px;font-size:13px;color:var(--ink-3)}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def evidence_line(f: dict) -> str:
    bits = []
    for e in f.get("evidence", []):
        when = e.get("published_at") or e.get("observed_at")
        q = f' <q>{esc(e["quote"])}</q>' if e.get("quote") else ""
        if e.get("url") == "owner":
            bits.append(f"You told us{', ' + esc(when) if when else ''}.{q}")
        else:
            bits.append(f'<a href="{esc(e["url"])}" rel="noopener nofollow" target="_blank">{esc(e.get("title") or e["url"])}</a>, seen {esc(when)}.{q}')
    if not bits:
        return '<p class="src">Nothing public shows this yet. That is why we ask you.</p>'
    stale = ' <strong>This is over a year old, so it counts for less.</strong>' if f.get("stale") else ""
    return '<p class="src">' + "<br>".join(bits) + stale + "</p>"


def ask_block(target: str, question: str | None = None) -> str:
    q = f"<p>{esc(question)}</p>" if question else ""
    return (f'<div class="ask" data-target="{esc(target)}">{q}<div class="row">'
            f'<button class="btn btn-p" data-act="confirm">Right</button>'
            f'<button class="btn btn-g" data-act="challenge">Not quite</button>'
            f'<button class="btn btn-g" data-act="elaborate">Add detail</button></div></div>')


def finding_card(f: dict) -> str:
    guess = f["kind"] in ("inference", "hypothesis")
    status = {"confirmed": "You confirmed this", "corrected": "You corrected this",
              "challenged": "You said this is not quite right"}.get(f.get("status") or "")
    return (f'<div class="card" id="{esc(f["id"])}">'
            f'<span class="tag{" guess" if guess else ""}">{esc(LABELS[f["kind"]])}</span>'
            f'<h3>{esc(f["claim"])}</h3>{evidence_line(f)}'
            + (f'<p class="done">{esc(status)}</p>' if status else ask_block(f["id"], f.get("open_question")))
            + "</div>")


def render(p: dict) -> str:
    fids = {f["id"]: f for f in p["findings"]}
    h = p["headline"]
    hero = (f'<header class="hero"><div class="w"><p class="kick">{esc(p["name"])} · {esc(p["area"])}</p>'
            f'<h1>{esc(h["insight"])}</h1><p class="proof">{esc(h.get("plain_proof", ""))}</p>'
            f'<div class="row" data-target="{esc(h["finding_ids"][0])}" data-headline="1">'
            f'<button class="btn btn-p" data-act="confirm">That\'s right</button>'
            f'<button class="btn btn-g" data-go="l2">How do you know?</button></div></div></header>')

    proofs = "".join(finding_card(fids[i]) for i in p.get("credibility", []) if i in fids)
    l2 = (f'<section id="l2"><div class="w"><p class="kick">How we know</p>'
          f'<h2>Three things we checked before we came</h2><p class="sub">Each one shows where we saw it and when.</p>'
          f'{proofs}<button class="btn btn-g" data-go="l3">What this could mean for you</button></div></section>')

    opp_cards = []
    for o in p.get("opportunities", []):
        rests = ", ".join(esc(fids[i]["claim"].rstrip(".")) for i in o["finding_ids"] if i in fids)
        sc = o.get("scenario")
        sc_html = ""
        if sc:
            rows = "".join(f'<li>{esc(a["label"])}: {esc(a["value"]) if a.get("value") is not None else "<em>your number</em>"}'
                           f'{" (" + esc(a["note"]) + ")" if a.get("note") else ""}</li>' for a in sc["assumptions"])
            sc_html = (f'<p class="why"><strong>The maths:</strong> {esc(sc["formula"])}</p><ul class="why">{rows}</ul>'
                       f'<p class="why">{esc(sc.get("result_text", ""))}</p>')
        opp_cards.append(
            f'<div class="card{" hold" if o.get("on_hold") else ""}"><span class="tag">{esc(o["kind"].replace("_", " "))}</span>'
            f'<h3>{esc(o["title"])}</h3><p class="why">{esc(o.get("why", ""))}</p>{sc_html}'
            f'<p class="src">Based on: {rests}.</p>'
            + ('<p class="done">On hold: you told us part of this is not right.</p>' if o.get("on_hold") else "")
            + "</div>")
    pats = "".join(
        f'<div class="card{" hold" if pt.get("on_hold") else ""}"><span class="tag">Connected</span><h3>{esc(pt["title"])}</h3>'
        f'<p class="why">{esc(pt["explanation"])}</p></div>' for pt in p.get("patterns", []))
    l3 = (f'<section id="l3"><div class="w"><p class="kick">Opportunities</p>'
          f'<h2>What we would work on with you</h2><p class="sub">Each idea comes from something we found. Nothing here is a promise.</p>'
          f'{pats}{"".join(opp_cards)}<button class="btn btn-g" data-go="l4">Everything we found</button></div></section>')

    groups: dict[str, list] = {}
    for f in p["findings"]:
        groups.setdefault(f["dimension"], []).append(f)
    l4 = ('<section id="l4"><div class="w"><p class="kick">Everything we found</p>'
          '<h2>Tell us what we got right and wrong</h2><p class="sub">Your answers go straight into what we know about you.</p>'
          + "".join(f'<details><summary>{esc(DIM_NAMES.get(d, d))} ({len(fs)})</summary>'
                    + "".join(finding_card(f) for f in fs) + "</details>" for d, fs in groups.items())
          + "</div></section>")

    unknowns = "".join(
        f'<div class="card"><h3>{esc(u["question"])}</h3><p class="why">{esc(u["why_it_matters"])}</p>'
        + (f'<p class="done">You said: {esc(u["answer"])}</p>' if u.get("answer") else
           f'<div class="ask" data-target="{esc(u["id"])}"><div class="row"><button class="btn btn-g" data-act="answer">Answer</button></div></div>')
        + "</div>" for u in p.get("unknowns", []))
    l5 = (f'<section id="l5"><div class="w"><p class="kick">Only you know</p>'
          f'<h2>What public information can\'t tell us</h2><p class="sub">Sales, costs and how busy you are never show up online. We never guess them.</p>'
          f'{unknowns}</div></section>')

    data = json.dumps({"slug": p["slug"], "endpoint": ENDPOINT}).replace("</", "<\\/")
    js = JS.replace("__DATA__", data)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f'<meta name="robots" content="noindex,nofollow"><title>{esc(p["name"])}</title>'
            f'<style>{CSS}</style></head><body>{hero}{l2}{l3}{l4}{l5}'
            f'<footer class="w">Built from public information, each item dated. Prepared {esc(p.get("built_at", ""))}.</footer>'
            f'<script>{js}</script></body></html>')


JS = r"""
(()=>{const D=__DATA__,K='intel:'+D.slug;
const load=()=>{try{return JSON.parse(localStorage.getItem(K)||'[]')}catch(e){return[]}};
const save=a=>{try{localStorage.setItem(K,JSON.stringify(a))}catch(e){}};
function send(ev){const all=load();all.push(ev);save(all);
 if(!D.endpoint)return;
 fetch(D.endpoint,{method:'POST',headers:{'Content-Type':'text/plain;charset=UTF-8'},body:JSON.stringify({slug:D.slug,event:ev})})
  .then(r=>{if(r.ok){ev.sent=1;save(load().map(x=>x.id===ev.id?ev:x))}}).catch(()=>{});}
function mark(box,text){const p=document.createElement('p');p.className='done';p.textContent=text;box.replaceWith(p);}
document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
 if(b.dataset.go){document.getElementById(b.dataset.go).scrollIntoView();return;}
 const box=b.closest('[data-target]');if(!box)return;const act=b.dataset.act,target=box.dataset.target;
 const ev={id:Date.now().toString(36)+Math.random().toString(36).slice(2,6),target,action:act,by:'owner',at:new Date().toISOString()};
 if(act==='confirm'){send(ev);mark(box,'Thank you. Noted as right.');return;}
 if(box.querySelector('textarea'))return;
 const t=document.createElement('textarea');
 t.placeholder=act==='challenge'?'What is it really like?':act==='answer'?'Your answer':'Tell us more';
 const ok=document.createElement('button');ok.className='btn btn-p';ok.textContent='Save';ok.style.marginTop='10px';
 box.append(t,ok);t.focus();
 ok.onclick=ev2=>{ev2.stopPropagation();const note=t.value.trim();if(!note){t.focus();return;}
  ev.note=note;send(ev);mark(box,'Thank you. We have updated this.');};
});
})();
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--out")
    a = ap.parse_args()
    p = model.load(a.slug)
    errs = model.validate(json.loads((model.PROFILES / f"{a.slug}.json").read_text()))
    if errs:
        print("not fit to show:\n" + "\n".join(errs))
        return 1
    out = pathlib.Path(a.out) if a.out else ROOT / "intel" / a.slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(p))
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
