"""az_fb_groups - one AZ post a day into a restaurant-owner Facebook group, and a daily watch on the replies.

Owner, 2026-10-29: "for the Facebook ones, can you do an automated thing where you keep going automatically
every single day and keep track of replies and tell me if there's any lead ... don't cost me, but make sure
this is resilient and always trustable."

HOW IT RUNS
  * On the owner's Mac from launchd (com.az.fb-groups.plist): at login, on wake, and every 2 hours 9 AM-11 PM.
    Two posts a day (one after 10 AM, one after 3 PM, 3+ hours apart); a run that was missed while the Mac
    was shut catches up at the next run. Every run reads replies. Chrome is opened if it is not running. Facebook has no API for groups (Meta removed it in April 2024), so it
    works inside the owner's own Chrome, already signed in (chrome.py, AppleScript), in its own minimized
    window that it closes. Owner, 2026-10-29: a separate browser login "logs out after some time".
  * Posting: two posts a day, the next text + its short video, into the group that has waited longest
    (4+ days since our last post there). Posts are reused once a group has had them all.
  * Replies: every post from the last 30 days is reread. A new comment that reads like interest (price,
    demo, how, DM me, my restaurant ...) is texted to the owner at once; everything else goes in the
    daily note in the Haniya app. It never replies or comments on its own.
  * Trust: every action is logged (~/Library/Logs/az-fb-groups.log); state lives in state.json; any failure
    (signed out, composer changed, post held for admin approval) sends one note saying what happened and
    what to do. A heartbeat goes to the AZ server, which warns the owner if this job goes quiet for 2 days.
"""
from __future__ import annotations
import base64, datetime as dt, hashlib, json, os, re, subprocess, sys, time, traceback, urllib.request

HOME = os.path.expanduser("~/Library/Application Support/az-fb-groups")
STATE = os.path.join(HOME, "state.json")
CONF = os.path.join(HOME, "config.json")
LOG = os.path.expanduser("~/Library/Logs/az-fb-groups.log")
AUTH = os.path.join(HOME, "owner-note.auth")           # one line admin:<password>, same as the AZ poster
NOTE_URL = "https://voice.wokandkarahitexas.com/admin/owner-note"
TEXT_URL = "https://voice.wokandkarahitexas.com/admin/owner-text"
SERVER = "root@167.233.155.109"; KEY = os.path.expanduser("~/.ssh/wk_hetzner_ed25519")
LEAD = re.compile(r"\b(price|pricing|cost|how much|demo|interested|info|details|dm|inbox|message me|pm|contact|"
                  r"call me|sign up|signup|how do (i|we)|can you|do you|my restaurant|our restaurant|we have|"
                  r"need this|want this|link|website|setup|set up|works with|clover|toast|square)\b", re.I)

def log(*a):
    line = dt.datetime.now().isoformat(timespec="seconds") + " " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG, "a") as f: f.write(line + "\n")

def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def save(st):
    tmp = STATE + ".tmp"; json.dump(st, open(tmp, "w"), indent=1); os.replace(tmp, STATE)

def _owner(url, body):
    try: cred = open(AUTH).read().strip()
    except OSError: log("no owner credential, message not sent"); return False
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json",
          "User-Agent": "az-fb-groups/1", "Authorization": "Basic " + base64.b64encode(cred.encode()).decode()})
    try: return bool(json.loads(urllib.request.urlopen(req, timeout=20).read() or b"{}").get("sent"))
    except Exception as e: log("owner message FAIL", str(e)[:160]); return False

def note(title, lines, urgent=False): return _owner(NOTE_URL, {"title": title[:80], "lines": lines[:20], "urgent": urgent})
def text(msg): return _owner(TEXT_URL, {"text": msg[:320]})

def heartbeat(st):
    beat = {"at": dt.datetime.now().isoformat(timespec="seconds"), "posts": len(st.get("posts", [])),
            "last_post": (st.get("posts") or [{}])[-1].get("at"), "status": st.get("status")}
    try:
        subprocess.run(["ssh", "-i", KEY, "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", SERVER,
                        "cat > /opt/az-social/fb-groups-heartbeat.json"], input=json.dumps(beat).encode(), timeout=40, check=True)
    except Exception as e: log("heartbeat FAIL", str(e)[:120])

DLG = "const d=[...document.querySelectorAll('[role=dialog]')].find(d=>d.querySelector('[contenteditable=true]'));"

def signed_in(w):
    w.go("https://www.facebook.com/", 8)
    return w.js("return !location.href.includes('login') && !!document.querySelector('[aria-label=\"Your profile\"],[aria-label=\"Account controls and settings\"],[aria-label=\"Create\"]')")

def next_pair(conf, st, today):
    """Next (group, post): the group that has waited longest (at least min_group_gap_days), with a post it
    has not had yet; once every post has run there, the post it has seen least, never the same one twice
    in a row. Owner, 2026-10-29: "every day we need to do 2 posts ... You can reuse posts"."""
    gapmin = conf.get("min_group_gap_days", 4)
    last, used = {}, {}
    for x in st.get("posts", []):
        last[x["group"]] = max(last.get(x["group"], ""), x["at"][:10])
        used.setdefault(x["group"], []).append(x["post"])
    gap = lambda g: (today - dt.date.fromisoformat(last[g])).days if g in last else 999
    for g in sorted([g["url"] for g in conf["groups"]], key=gap, reverse=True):
        if gap(g) < gapmin: continue
        seen = used.get(g, []); n = len(conf["posts"])
        fresh = [i for i in range(n) if i not in seen]
        if fresh: return g, fresh[0]
        prev = seen[-1] if seen else None
        return g, min((i for i in range(n) if i != prev), key=lambda i: (seen.count(i), i))
    return None

def post_one(w, group, post):
    w.go(group, 9)
    if not w.js("const b=[...document.querySelectorAll('[role=button]')].find(b=>/^Write something/i.test((b.innerText||'').trim()));if(!b)return false;b.click();return true"):
        raise RuntimeError("no post box in this group (posting may be off for members)")
    time.sleep(4)
    if not w.js(DLG + "return !!d"): raise RuntimeError("the post window did not open")
    lines = post["text"].split("\n")
    w.js(DLG + "const e=d.querySelector('[contenteditable=true]');e.focus();const L=" + json.dumps(lines) + ";"
         "L.forEach((l,i)=>{if(i)e.dispatchEvent(new InputEvent('beforeinput',{inputType:'insertParagraph',bubbles:true,cancelable:true}));"
         "if(l)document.execCommand('insertText',false,l)});return 1")
    time.sleep(1.5)
    got = w.js(DLG + "return d.querySelector('[contenteditable=true]').innerText")
    if lines[0][:25] not in (got or ""): raise RuntimeError("the text did not land in the post box")
    if post.get("video"):
        w.push_file(os.path.join(HOME, post["video"]))
        r = w.js(DLG + "let i=d.querySelector('input[type=file]');if(!i){const b=[...d.querySelectorAll('[aria-label]')].find(x=>/photo\\/video|photo or video/i.test(x.getAttribute('aria-label')));if(b)b.click();i=d.querySelector('input[type=file]')}"
                 "if(!i)return 'no input';const dt=new DataTransfer();dt.items.add(window.__azFile);i.files=dt.files;i.dispatchEvent(new Event('change',{bubbles:true}));return 'ok'")
        if r != "ok": raise RuntimeError("could not attach the video")
    for _ in range(100):  # the Post button wakes up once the video has uploaded
        time.sleep(3)
        s = w.js(DLG + "if(!d)return {gone:true};const p=[...d.querySelectorAll('[role=button],[aria-label]')].find(b=>/^Post$/i.test((b.getAttribute('aria-label')||b.innerText||'').trim()));"
                 "return {ready:!!p&&p.getAttribute('aria-disabled')!=='true', video:!post_video||!!d.querySelector('video')}".replace("post_video", "false" if not post.get("video") else "true"))
        if s.get("ready") and s.get("video"): break
    else: raise RuntimeError("the video never finished uploading")
    w.js(DLG + "const p=[...d.querySelectorAll('[role=button],[aria-label]')].find(b=>/^Post$/i.test((b.getAttribute('aria-label')||b.innerText||'').trim()));p.click();return 1")
    for _ in range(40):
        time.sleep(3)
        if not w.js(DLG + "return !!d"): break
    else: raise RuntimeError("the post window stayed open after Post")
    body = w.js("return document.body.innerText.slice(0,4000)") or ""
    pending = bool(re.search(r"pending|admin approval|will be reviewed|submitted for review", body, re.I))
    return {"pending": pending, "url": None}

def find_post(w, group, txt):
    """The permalink of our post in the group feed, newest first; None while it waits for an admin."""
    w.go(group.rstrip("/") + "/?sorting_setting=CHRONOLOGICAL", 10)
    key = txt.split("\n")[0][:30]
    return w.js("const k=" + json.dumps(key) + ";for(const a of [...document.querySelectorAll('[role=article],[aria-posinset]')].slice(0,15)){"
                "if(!(a.innerText||'').includes(k))continue;for(const h of a.querySelectorAll('a[href]')){const u=h.href||'';"
                "if(/\\/groups\\/[^/]+\\/(posts|permalink)\\//.test(u))return u.split('?')[0]}}return null")

def read_comments(w, url):
    w.go(url, 8)
    for _ in range(4):
        n = w.js("const b=[...document.querySelectorAll('[role=button]')].filter(b=>/^View (more|all|\\d+ more) (comments|replies)|^View \\d+ repl/i.test((b.innerText||'').trim()));b.forEach(x=>x.click());return b.length")
        if not n: break
        time.sleep(3)
    return w.js("return [...document.querySelectorAll('[role=article][aria-label^=\"Comment by\"],[role=article][aria-label^=\"Reply by\"]')].map(c=>({"
                "who:(c.getAttribute('aria-label')||'').replace(/^(Comment|Reply) by\\s+/,'').replace(/\\s+\\d+\\s+\\w+\\s+ago$/,''),"
                "text:(c.innerText||'').trim().slice(0,400)}))") or []

def run(force_post=False):
    import chrome
    os.makedirs(HOME, exist_ok=True)
    conf = load(CONF, None); st = load(STATE, {"posts": [], "seen": {}, "status": "new"})
    if not conf: log("no config.json"); return
    today = dt.date.today(); now = dt.datetime.now().isoformat(timespec="seconds")
    if True:
        try: w = chrome.Window()
        except Exception as e:  # Chrome closed, or the Mac has not allowed this job to control Chrome yet
            log("CHROME FAIL", str(e)[:200]); st["status"] = "no_chrome"; save(st); heartbeat(st)
            if st.get("chrome_noted") != str(today):
                note("Facebook groups could not reach Chrome", ["The daily Facebook job could not open a Chrome window.",
                     "If your Mac asked whether to let it control Google Chrome, click OK. Otherwise just keep Chrome open; the next run retries."], urgent=True)
                st["chrome_noted"] = str(today); save(st)
            return
        try:
            if not signed_in(w):
                st["status"] = "signed_out"; save(st); log("signed out")
                if st.get("signed_out_noted") != str(today):
                    note("Facebook groups paused: Chrome is signed out of Facebook", ["The daily Facebook group posts need your Chrome to be signed in to Facebook.",
                         "Open facebook.com in Chrome and sign in. The next run picks up by itself."], urgent=True)
                    st["signed_out_noted"] = str(today); save(st)
                return
            st["status"] = "ok"
            # 1. one post a day
            todays = [x for x in st["posts"] if x["at"][:10] == str(today)]
            fails = st.get("fails", {}).get(str(today), 0)
            hour = dt.datetime.now().hour
            slot_open = (len(todays) == 0 and hour >= 10) or (len(todays) == 1 and hour >= 15 and
                         (dt.datetime.now() - dt.datetime.fromisoformat(todays[-1]["at"])).total_seconds() > 3 * 3600)
            if force_post or (slot_open and len(todays) < conf.get("posts_per_day", 2) and fails < 3):
                pair = next_pair(conf, st, today)
                if pair:
                    g, i = pair; name = next((x["name"] for x in conf["groups"] if x["url"] == g), g)
                    try:
                        r = post_one(w, g, conf["posts"][i])
                        if not r["pending"]:  # some groups hold every post for the admin; check the queue
                            w.go(g.rstrip("/") + "/my_pending_content", 10)
                            r["pending"] = bool(w.js("return (document.querySelector('[role=main]')||document.body).innerText.includes(" + json.dumps(conf["posts"][i]["text"].split("\n")[0][:30]) + ")"))
                        st["posts"].append({"group": g, "name": name, "post": i, "at": now, "url": r["url"], "pending": r["pending"]})
                        st["posted_day"] = str(today); save(st)
                        log("posted", name, "post", i, r)
                    except Exception as e:
                        st.setdefault("fails", {})[str(today)] = fails + 1; save(st)
                        log("POST FAIL", name, str(e)[:300])
                        if fails + 1 >= 3: note("Facebook group posts stopped for today", [f"Last try: {name}", f"What happened: {str(e)[:150]}", "Three tries failed today. Tomorrow starts fresh."])
                else: log("nothing to post today (every group had a post in the last 6 days or all posts used)")
            # 2. replies: read each group's "your posts" page once (Facebook hides post links from scripts)
            leads, fresh, counts = [], [], st.setdefault("counts", {})
            recent = [x for x in st["posts"] if dt.date.fromisoformat(x["at"][:10]) >= today - dt.timedelta(days=30)]
            for g in sorted({x["group"] for x in recent}):
                mine = [x for x in recent if x["group"] == g]; gname = mine[0]["name"]
                keys = {x["post"]: conf["posts"][x["post"]]["text"].split("\n")[0][:30] for x in mine}
                for x in mine:
                    if x.get("pending"):
                        w.go(g.rstrip("/") + "/my_pending_content", 10)
                        still = w.js("return (document.querySelector('[role=main]')||document.body).innerText.includes(" + json.dumps(keys[x["post"]]) + ")")
                        if not still: x["pending"] = False; log("now live", gname)
                w.go(g.rstrip("/") + "/my_posted_content", 10)
                for _ in range(3):  # open the comment lists under our posts
                    n = w.js("const b=[...document.querySelectorAll('[role=button]')].filter(b=>/^\\d+ comments?$|^View (more|all|\\d+ more) (comments|replies)/i.test((b.innerText||'').trim()));b.forEach(x=>x.click());return b.length")
                    if not n: break
                    time.sleep(3)
                found = w.js("const K=" + json.dumps(keys) + ";const out={};for(const a of document.querySelectorAll('[role=article],[aria-posinset]')){const t=a.innerText||'';"
                             "for(const [p,k] of Object.entries(K)){if(!t.includes(k)||out[p])continue;const m=t.match(/(\\d+)\\s+comments?/i);"
                             "out[p]={n:m?+m[1]:0,c:[...a.querySelectorAll('[role=article][aria-label^=\"Comment by\"],[role=article][aria-label^=\"Reply by\"]')].map(c=>({"
                             "who:(c.getAttribute('aria-label')||'').replace(/^(Comment|Reply) by\\s+/,'').replace(/\\s+\\d+\\s+\\w+\\s+ago$/,''),text:(c.innerText||'').trim().slice(0,400)}))}}}return out") or {}
                for p, r in found.items():
                    ck = f"{g}|{p}"; before = counts.get(ck, 0); counts[ck] = max(before, r["n"])
                    new = []
                    for c in r["c"]:
                        h = hashlib.sha1((ck + c["who"] + c["text"]).encode()).hexdigest()[:16]
                        if h not in st["seen"]: st["seen"][h] = now; new.append({**c, "group": gname, "url": g.rstrip("/") + "/my_posted_content"})
                    for c in new: (leads if LEAD.search(c["text"]) else fresh).append(c)
                    if r["n"] > before and not new:  # comments we could not read: still tell him, with the link
                        leads.append({"who": f"{r['n'] - before} new comment(s)", "text": "open the post to read them", "group": gname, "url": g.rstrip("/") + "/my_posted_content"})
            save(st)
            log("run ok:", f"posted today={st.get('posted_day') == str(today)}", f"new comments={len(leads) + len(fresh)}", f"leads={len(leads)}")
            for l in leads:
                text(f"Possible lead in FB group {l['group'][:40]}: {l['who']} said \"{l['text'][:150]}\" {l['url']}")
                log("LEAD", l["group"], l["who"], l["text"][:80])
            if st.get("noted_day") != str(today) and dt.datetime.now().hour >= 19:
                todays = [x for x in st["posts"] if x["at"][:10] == str(today)]
                lines = [f"Posted in {x['name']}" + (" (waiting for the group admin)" if x.get("pending") else "") for x in todays] or ["No new group post today."]
                lines += [f"{c['who']} in {c['group'][:30]}: {c['text'][:120]}" for c in (leads + fresh)[:12]]
                lines.append(f"Groups posted so far: {len(st['posts'])}. Leads texted today: {len(leads)}.")
                note("Facebook groups today", lines); st["noted_day"] = str(today); save(st)
        except Exception:
            log("RUN FAIL", traceback.format_exc()[-600:]); st["status"] = "error"; save(st)
            if st.get("error_noted") != str(today):
                note("Facebook groups job hit an error", ["It will retry at its next run.", traceback.format_exc()[-180:]]); st["error_noted"] = str(today); save(st)
        finally:
            w.close(); heartbeat(st)

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    run(force_post="--post-now" in sys.argv)
