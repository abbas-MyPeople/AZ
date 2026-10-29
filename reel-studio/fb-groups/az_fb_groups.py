"""az_fb_groups - one AZ post a day into a restaurant-owner Facebook group, and a daily watch on the replies.

Owner, 2026-10-29: "for the Facebook ones, can you do an automated thing where you keep going automatically
every single day and keep track of replies and tell me if there's any lead ... don't cost me, but make sure
this is resilient and always trustable."

HOW IT RUNS
  * On the owner's Mac from launchd (com.az.fb-groups.plist): at login and at 10:05 and 16:05. Once a day it
    posts; every run it reads replies. Facebook has no API for groups, so this uses a browser profile kept
    only for this job (~/.az-fb-browser), signed in once by the owner (`--login`). Same machine and network
    as his normal Facebook, so it never looks like a strange login.
  * Posting: one post a day, the next approved text + its short video, into the group that has waited
    longest. Each group gets each post at most once, and no group gets two posts within 6 days.
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
PROFILE = os.path.expanduser("~/.az-fb-browser")
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

def browser(p, headless=True):
    return p.chromium.launch_persistent_context(PROFILE, channel="chrome", headless=headless,
        args=["--disable-blink-features=AutomationControlled"], ignore_default_args=["--use-mock-keychain", "--enable-automation"],
        viewport={"width": 1280, "height": 1600}, locale="en-US")

def signed_in(pg):
    pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(5000)
    return "login" not in pg.url and pg.locator('[aria-label="Your profile"], [aria-label="Account controls and settings"]').count() > 0

def next_pair(conf, st, today):
    """The approved post each group has not had yet, into the group that waited longest (6+ days)."""
    done = {(x["group"], x["post"]) for x in st.get("posts", [])}
    last = {}
    for x in st.get("posts", []): last[x["group"]] = max(last.get(x["group"], ""), x["at"][:10])
    gap = lambda g: (today - dt.date.fromisoformat(last[g])).days if g in last else 999
    for g in sorted([g["url"] for g in conf["groups"]], key=gap, reverse=True):
        if gap(g) < 6: continue
        for i, post in enumerate(conf["posts"]):
            if (g, i) not in done: return g, i
    return None

def post_one(pg, group, post):
    pg.goto(group, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(6000)
    pg.get_by_role("button", name=re.compile(r"^Write something", re.I)).first.click(timeout=20000)
    dlg = pg.locator('div[role="dialog"]').filter(has=pg.locator('[contenteditable="true"]')).last
    dlg.wait_for(timeout=20000); pg.wait_for_timeout(1500)
    box = dlg.locator('[contenteditable="true"]').first; box.click()
    for k, line in enumerate(post["text"].split("\n")):
        if k: pg.keyboard.press("Shift+Enter")
        if line: pg.keyboard.insert_text(line)
    pg.wait_for_timeout(1000)
    if post.get("video"):
        inp = dlg.locator('input[type="file"]')
        if not inp.count():
            dlg.get_by_role("button", name=re.compile(r"Photo/video|photo or video", re.I)).first.click(); pg.wait_for_timeout(1500)
            inp = dlg.locator('input[type="file"]')
        inp.first.set_input_files(os.path.join(HOME, post["video"])); pg.wait_for_timeout(8000)
    btn = dlg.get_by_role("button", name=re.compile(r"^Post$", re.I)).last
    for _ in range(90):  # the Post button wakes up once the video has uploaded
        if btn.is_enabled() and btn.get_attribute("aria-disabled") != "true": break
        pg.wait_for_timeout(2000)
    btn.click(); pg.wait_for_timeout(12000)
    body = pg.inner_text("body")
    pending = bool(re.search(r"pending|admin approval|will be reviewed|submitted for review", body, re.I))
    return {"pending": pending, "url": find_post(pg, group, post["text"])}

def find_post(pg, group, txt):
    """The permalink of our post in the group feed, newest first; None while it waits for an admin."""
    key = txt.split("\n")[0][:50]
    pg.goto(group.rstrip("/") + "/?sorting_setting=CHRONOLOGICAL", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(7000)
    for a in pg.locator('div[role="article"], div[aria-posinset]').all()[:12]:
        try:
            if key[:30] in a.inner_text():
                for h in a.locator('a[href*="/posts/"], a[href*="/permalink/"]').all():
                    u = h.get_attribute("href") or ""
                    if "/groups/" in u: return u.split("?")[0]
        except Exception: continue
    return None

def read_comments(pg, url):
    pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(6000)
    for _ in range(4):  # open "View more comments" / "most relevant" collapses
        more = pg.get_by_role("button", name=re.compile(r"View (more|all|\d+ more) (comments|replies)", re.I))
        if not more.count(): break
        try: more.first.click(); pg.wait_for_timeout(2500)
        except Exception: break
    out = []
    for c in pg.locator('div[role="article"][aria-label^="Comment by"], div[role="article"][aria-label^="Reply by"]').all():
        try:
            who = re.sub(r"^(Comment|Reply) by\s+", "", c.get_attribute("aria-label") or "").split(" ")[0:3]
            body = c.inner_text().strip()
            out.append({"who": " ".join(who).strip(), "text": body[:400]})
        except Exception: continue
    return out

def run(force_post=False):
    from playwright.sync_api import sync_playwright
    os.makedirs(HOME, exist_ok=True)
    conf = load(CONF, None); st = load(STATE, {"posts": [], "seen": {}, "status": "new"})
    if not conf: log("no config.json"); return
    today = dt.date.today(); now = dt.datetime.now().isoformat(timespec="seconds")
    with sync_playwright() as p:
        ctx = browser(p); pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            if not signed_in(pg):
                st["status"] = "signed_out"; save(st); log("signed out")
                if st.get("signed_out_noted") != str(today):
                    note("Facebook groups paused: sign-in needed", ["The daily Facebook group posts are paused because Facebook signed this job out.",
                         "On your Mac run: python3 ~/Library/Application\\ Support/az-fb-groups/az_fb_groups.py --login", "Sign in once in the window that opens, then close it."], urgent=True)
                    st["signed_out_noted"] = str(today); save(st)
                return
            st["status"] = "ok"
            # 1. one post a day
            if (force_post or st.get("posted_day") != str(today)) and dt.datetime.now().hour >= 10:
                pair = next_pair(conf, st, today)
                if pair:
                    g, i = pair; name = next((x["name"] for x in conf["groups"] if x["url"] == g), g)
                    try:
                        r = post_one(pg, g, conf["posts"][i])
                        st["posts"].append({"group": g, "name": name, "post": i, "at": now, "url": r["url"], "pending": r["pending"]})
                        st["posted_day"] = str(today); save(st)
                        log("posted", name, "post", i, r)
                    except Exception as e:
                        shot = os.path.join(HOME, f"fail-{today}.png")
                        try: pg.screenshot(path=shot)
                        except Exception: pass
                        log("POST FAIL", name, str(e)[:300]); st["posted_day"] = str(today); save(st)
                        note("Facebook group post did not go out", [f"Group: {name}", f"What happened: {str(e)[:150]}", "Tomorrow's run tries again. Nothing else changed."])
                else: log("nothing to post today (every group had a post in the last 6 days or all posts used)")
            # 2. find permalinks still missing (held for admin approval), then read replies
            leads, fresh = [], []
            for x in st["posts"]:
                if dt.date.fromisoformat(x["at"][:10]) < today - dt.timedelta(days=30): continue
                if not x.get("url"):
                    x["url"] = find_post(pg, x["group"], conf["posts"][x["post"]]["text"])
                    if x["url"]: x["pending"] = False; log("now live", x["name"])
                    continue
                for c in read_comments(pg, x["url"]):
                    h = hashlib.sha1((x["url"] + c["who"] + c["text"]).encode()).hexdigest()[:16]
                    if h in st["seen"]: continue
                    st["seen"][h] = now; item = {**c, "group": x["name"], "url": x["url"]}
                    (leads if LEAD.search(c["text"]) else fresh).append(item)
            save(st)
            for l in leads:
                text(f"Possible lead in FB group {l['group'][:40]}: {l['who']} said \"{l['text'][:150]}\" {l['url']}")
                log("LEAD", l["group"], l["who"], l["text"][:80])
            if st.get("noted_day") != str(today) and dt.datetime.now().hour >= 16:
                todays = [x for x in st["posts"] if x["at"][:10] == str(today)]
                lines = [f"Posted in {x['name']}" + (" (waiting for the group admin)" if not x.get("url") else "") for x in todays] or ["No new group post today."]
                lines += [f"{c['who']} in {c['group'][:30]}: {c['text'][:120]}" for c in (leads + fresh)[:12]]
                lines.append(f"Groups posted so far: {len(st['posts'])}. Leads texted today: {len(leads)}.")
                note("Facebook groups today", lines); st["noted_day"] = str(today); save(st)
        except Exception:
            log("RUN FAIL", traceback.format_exc()[-600:]); st["status"] = "error"; save(st)
            if st.get("error_noted") != str(today):
                note("Facebook groups job hit an error", ["It will retry at its next run.", traceback.format_exc()[-180:]]); st["error_noted"] = str(today); save(st)
        finally:
            ctx.close(); heartbeat(st)

def login():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = browser(p, headless=False); pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        pg.goto("https://www.facebook.com/login")
        print("Sign in to Facebook in this window, then close the window.")
        while ctx.pages: time.sleep(2)

if __name__ == "__main__":
    if "--login" in sys.argv: login()
    else: run(force_post="--post-now" in sys.argv)
