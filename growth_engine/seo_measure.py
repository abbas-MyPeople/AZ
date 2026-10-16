"""
growth_engine.seo_measure - the WEEKLY measure step (owner approved 2026-10-15).

The daily engine proposes and ships page changes. This step closes the loop once a week by asking
two questions of the outside world, then naming the pages most worth rewriting next:

  a. SEARCH CONSOLE - for azrestaurantpartners.com, last 28 days, by page and by query: impressions,
     clicks, CTR, average position. Read-only (webmasters.readonly). If the service account has not
     been added as a user on the property, we record {"gsc": "no_access", "sa": <client_email>} and
     carry on. Never crashes, never fakes rows.
  b. AEO PROBE - a fixed panel of owner questions, asked to every AI engine we hold a key for, and we
     record whether "AZ Restaurant Partners" / azrestaurantpartners.com is NAMED in the answer and
     which of OUR URLs is cited.
  c. WEAKEST - up to 3 existing guide/compare pages to rewrite, by rule:
       1) high impressions + low CTR in Search Console (people see it, nobody clicks), then
       2) panel topics where engines name competitors but never us.
     Each carries the reason and the queries it should win.

HONESTY RULES (copied from the Wok & Karahi probe, analytics/aeo.py, where each one was learned the hard way):
  - AI answers are non-deterministic and personalised. This is an INDICATIVE sampled panel, never a
    hard metric. One week's move of one question is noise; the trend over weeks is the signal.
  - NO PANEL QUESTION MAY CONTAIN OUR NAME. A question that says "AZ" gets answered by reading the
    name back out of the question - free points that can never move (W&K ran 19 weeks at exactly
    8/25 from that alone). Enforced at import by _assert_panel_is_discovery().
  - Every engine is labelled with its MODE. Live-web engines answer with retrieval, the way the
    consumer apps do. Groq (llama-3.3-70b) is the lone MODEL-MEMORY control so the split has a
    baseline; it is not a measure of the web.
  - Modes are compared with ==, never `in` ("live web" is a substring of the memory label).
  - No key -> the engine is not probed and is listed under "skipped". Nothing is faked.
  - Google AI Overviews exposes no answer API and is not probed.
  - Errors are recorded per engine with a secret-free reason (401 / 402 / 404 / 429 / network).

Keys arrive ONLY from env (this repo is PUBLIC): GA4_SA_JSON (same SA as the GA4 sensor),
ANTHROPIC_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY. Stdlib urllib for every HTTP call; google-auth
(already in requirements.txt) only to mint the Search Console token.

Run: python -m growth_engine.seo_measure            (writes state/seo-weekly.json + appends seo-history.jsonl)
     python -m growth_engine.seo_measure --no-aeo   (Search Console only)
"""
from __future__ import annotations
import os, sys, json, re, time, datetime, argparse, urllib.request, urllib.parse, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import model

REPO = Path(__file__).resolve().parent.parent
STATE = model.STATE
WEEKLY = STATE / "seo-weekly.json"
HISTORY = STATE / "seo-history.jsonl"
DOMAIN = "azrestaurantpartners.com"
GSC_PROPERTIES = ["https://azrestaurantpartners.com/", "sc-domain:azrestaurantpartners.com"]   # URL-prefix is the granted one
GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
GSC_DAYS = 28
TIMEOUT = 60

# Weakest-page rule thresholds. A page needs real impressions before "low CTR" means anything.
WEAK_MIN_IMPRESSIONS = 50
WEAK_MAX_CTR = 0.02             # under 2% clicks per impression
WEAK_MAX = 3

# ── THE PANEL ────────────────────────────────────────────────────────────────────────────────
# Owner questions, in an owner's words. NONE contains our name (see honesty rules). Each maps to the
# existing page that should win it, so a lost question points at a page to rewrite. `geo` is where
# the asker is; Houston is where AZ sells.
PANEL = [
    {"q": "best AI phone answering for restaurants that speaks Urdu", "page": "guide-multilingual-phone-ordering.html"},
    {"q": "AI phone ordering for a restaurant that can take orders in Spanish and Hindi", "page": "guide-multilingual-phone-ordering.html"},
    {"q": "who can automate my restaurant's back office in Houston", "page": "smb-back-office-automation-cost.html"},
    {"q": "Maple alternatives for restaurants", "page": "vs-maple-alternatives.html"},
    {"q": "forward deployed engineer for small restaurants", "page": "smb-forward-deployed-engineer-vs-agency-vs-saas.html"},
    {"q": "best AI phone answering service for restaurants", "page": "vs-best-ai-phone-answering-restaurants.html"},
    {"q": "how much does AI phone answering cost for a restaurant", "page": "ai-phone-answering-cost.html"},
    {"q": "restaurant technology consultant in Houston", "page": "restaurant-technology-consultant-houston.html"},
    {"q": "Owner.com alternatives for an independent restaurant", "page": "vs-owner-com-alternatives.html"},
    {"q": "Popmenu alternatives for a small restaurant", "page": "vs-popmenu-alternatives.html"},
    {"q": "Slang AI vs Loman for restaurant phone calls", "page": "vs-slang-ai-vs-loman.html"},
    {"q": "commission-free online ordering for restaurants in Houston", "page": "commission-free-online-ordering-houston.html"},
    {"q": "how do I get my restaurant recommended by ChatGPT", "page": "get-your-restaurant-recommended-by-ai.html"},
    {"q": "who can set up QR code table ordering for my restaurant", "page": "compare-table-ordering.html"},
    {"q": "done-for-you restaurant technology setup for a small restaurant", "page": "compare-done-for-you.html"},
    {"q": "how can my restaurant get catering orders from offices and churches", "page": "how-to-get-catering-orders-from-offices-churches-schools.html"},
    {"q": "ezCater alternatives for restaurants", "page": "vs-ezcater-alternatives.html"},
    {"q": "AI receptionist for a food truck or bakery", "page": "smb-ai-phone-answering-food-trucks-bakeries-cafes.html"},
    {"q": "how to roll out AI in a small restaurant", "page": "smb-ai-rollout-90-days.html"},
    {"q": "who helps independent restaurants cut DoorDash commission costs", "page": "cut-delivery-commissions.html"},
]
GEO = "Houston, Texas"

_NAME_RE = re.compile(r"\bAZ\s+Restaurant\s+Partners\b|azrestaurantpartners\.com|\bAZRP\b", re.I)


def _assert_panel_is_discovery():
    bad = [p["q"] for p in PANEL if re.search(r"\bAZ\b|azrestaurant|AZ Restaurant", p["q"], re.I)]
    if bad:
        raise ValueError(f"panel questions must never contain our name: {bad}")


_assert_panel_is_discovery()

# Named competitors we recognise. Anything else the engine lists still counts via the list parser.
_COMPETITORS = [
    "Maple", "Slang", "Loman", "Owner.com", "Popmenu", "Toast", "Square", "Clover", "ChowNow", "BentoBox",
    "Restaurant365", "MarginEdge", "Olo", "SoundHound", "ConverseNow", "VoicePlug", "Revmo", "Bite",
    "Sauce", "Deliverect", "Otter", "7shifts", "Homebase", "ezCater", "Sunday", "Presto", "Incentivio",
    "Thanx", "Paytronix", "OpenTable", "Resy", "Lunchbox", "Craver", "TouchBistro", "SpotOn", "Rezku",
    "Smith.ai", "Ruby", "Upmenu", "Menufy", "Grubhub", "Uber Eats", "DoorDash", "Yelp", "Hostie", "Kea",
]
_COMP_RE = re.compile(r"(?<![\w.])(" + "|".join(re.escape(c) for c in _COMPETITORS) + r")(?![\w])", re.I)
_LIST_RE = re.compile(r"^\s*(?:\d+[\.\)]|[-*•])\s*\**([^\n:*—–]{2,60}?)\**\s*(?:[—–:]|\s-\s|$)", re.M)

# ── ENGINES ──────────────────────────────────────────────────────────────────────────────────
LIVE_WEB = "live web answer"
MODEL_MEMORY = "model knowledge (no live web)"
_OR = "https://openrouter.ai/api/v1/chat/completions"
_ANTHROPIC = "https://api.anthropic.com/v1/messages"
_GROQ = "https://api.groq.com/openai/v1/chat/completions"
# Current Claude model + the dynamic-filtering web search server tool (claude-api skill, 2026-10).
CLAUDE_MODEL = os.environ.get("AZ_AEO_CLAUDE_MODEL", "claude-haiku-5-5")  # a sampled panel; cents a week
CLAUDE_SEARCH_TOOL = "web_search_20260209"

ENGINES = [
    # key, display, env var, kind, endpoint, model, mode
    ("sonar", "Perplexity Sonar", "OPENROUTER_API_KEY", "openai", _OR, "perplexity/sonar", LIVE_WEB),
    ("gpt_web", "ChatGPT (GPT-4o mini + live web)", "OPENROUTER_API_KEY", "openai", _OR, "openai/gpt-4o-mini:online", LIVE_WEB),
    ("gemini_web", "Gemini 2.5 Flash (+ live web)", "OPENROUTER_API_KEY", "openai", _OR, "google/gemini-2.5-flash:online", LIVE_WEB),
    ("claude_web", f"Claude ({CLAUDE_MODEL}, Anthropic direct, live web)", "ANTHROPIC_API_KEY", "anthropic", _ANTHROPIC, CLAUDE_MODEL, LIVE_WEB),
    ("groq", "Llama 3.3 70B (Groq) - memory control", "GROQ_API_KEY", "openai", _GROQ, "llama-3.3-70b-versatile", MODEL_MEMORY),
]


def _prompt(q):
    return (f"A restaurant owner near {GEO} asks: \"{q}\". Answer the way an AI assistant would: list up to 5 "
            "specific companies, services or products you would recommend, BEST FIRST, one per line in the "
            "exact format 'N. Name - one-line reason'. Only name ones you actually believe exist.")


def _ask_openai_style(url, key, model_id, q):
    body = json.dumps({"model": model_id, "messages": [{"role": "user", "content": _prompt(q)}],
                       "temperature": 0.2, "max_tokens": 600}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        d = json.loads(r.read().decode())
    msg = (d.get("choices") or [{}])[0].get("message", {}) or {}
    cites = list(d.get("citations") or [])
    if not cites:
        for a in (msg.get("annotations") or []):
            u = ((a.get("url_citation") or {}).get("url")) if isinstance(a, dict) else None
            if u:
                cites.append(u)
    return (msg.get("content") or ""), [c for c in cites if isinstance(c, str)]


def _ask_anthropic(url, key, model_id, q):
    """Messages API with the web_search SERVER tool (search runs on Anthropic's side, results come back
    in the same response). Effort low + a small search budget keeps the weekly cost to cents."""
    body = json.dumps({
        "model": model_id,
        "max_tokens": 4000,
        "output_config": {"effort": "low"},
        "fallbacks": "default",
        "messages": [{"role": "user", "content": _prompt(q)}],
        "tools": [{"type": CLAUDE_SEARCH_TOOL, "name": "web_search", "max_uses": 3}],
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01",
        "anthropic-beta": "server-side-fallback-2026-07-01"})
    with urllib.request.urlopen(req, timeout=TIMEOUT * 2) as r:
        d = json.loads(r.read().decode())
    if d.get("stop_reason") == "refusal":
        return "", []
    text, cites = [], []
    for block in (d.get("content") or []):
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text.append(block.get("text") or "")
            for c in (block.get("citations") or []):
                u = c.get("url") if isinstance(c, dict) else None
                if u:
                    cites.append(u)
        elif block.get("type") == "web_search_tool_result":
            inner = block.get("content")          # a list on success, an error object on failure
            for item in (inner if isinstance(inner, list) else []):
                u = item.get("url") if isinstance(item, dict) else None
                if u:
                    cites.append(u)
    seen, out = set(), []
    for u in cites:
        if u not in seen:
            seen.add(u); out.append(u)
    return "".join(text), out


def _err_word(e, provider):
    code = getattr(e, "code", None)
    if code in (401, 403):
        return f"key rejected ({code}) - the {provider} key is invalid or expired"
    if code == 402:
        return f"out of credit (402) - the {provider} account needs a top-up"
    if code == 404:
        return "model not found (404) - the model id needs updating"
    if code == 400:
        return "bad request (400) - request shape or model id rejected"
    if code == 429:
        return "rate limited (429)"
    if code:
        return f"provider error (HTTP {code})"
    return f"network: {type(e).__name__}"


def _our_urls(cites):
    return sorted({u.split("#")[0] for u in cites if DOMAIN in (u or "")})


def _named_others(text):
    names = {m.group(1).strip() for m in _COMP_RE.finditer(text or "")}
    for m in _LIST_RE.finditer(text or ""):
        n = m.group(1).strip().strip("*").strip()
        if n and not _NAME_RE.search(n):
            names.add(n)
    return sorted(names, key=str.lower)[:8]


def _probe_engine(eng):
    key_id, display, env, kind, url, model_id, mode = eng
    key = os.environ.get(env, "").strip()
    out = {"engine": key_id, "display": display, "mode": mode, "results": [], "errors": 0, "error": None}
    provider = {"OPENROUTER_API_KEY": "OpenRouter", "ANTHROPIC_API_KEY": "Anthropic", "GROQ_API_KEY": "Groq"}[env]
    for p in PANEL:
        rec = {"q": p["q"], "page": p["page"]}
        try:
            if kind == "anthropic":
                text, cites = _ask_anthropic(url, key, model_id, p["q"])
            else:
                text, cites = _ask_openai_style(url, key, model_id, p["q"])
            rec.update({
                "answered": bool(text.strip()),
                "named": bool(_NAME_RE.search(text) or _our_urls(cites)),
                "our_urls": _our_urls(cites),
                "others": _named_others(text),
                "cited_domains": sorted({re.sub(r"^www\.", "", (re.match(r"https?://([^/?#]+)", u) or [None, ""])[1])
                                         for u in cites if u})[:10],
            })
        except Exception as e:                # one bad call costs one row, never the run
            out["errors"] += 1
            out["error"] = _err_word(e, provider)
            rec.update({"answered": False, "named": None, "error": out["error"]})
            if getattr(e, "code", None) in (401, 402, 403, 404):
                out["results"].append(rec)
                break                         # the key or model is dead; do not burn 19 more calls
        out["results"].append(rec)
    answered = [r for r in out["results"] if r.get("answered")]
    out["answered"] = len(answered)
    out["named"] = sum(1 for r in answered if r.get("named"))
    out["named_pct"] = round(100 * out["named"] / len(answered), 1) if answered else None
    return out


def run_aeo():
    active, skipped = [], []
    for eng in ENGINES:
        (active if os.environ.get(eng[2], "").strip() else skipped).append(eng)
    res = {"panel_size": len(PANEL), "geo": GEO, "engines": {},
           "skipped": [{"engine": e[0], "reason": f"no {e[2]}"} for e in skipped],
           "not_probed": "Google AI Overviews (no answer API)"}
    if not active:
        res["status"] = "no_keys"
        return res
    with ThreadPoolExecutor(max_workers=min(4, len(active))) as ex:
        for out in ex.map(_probe_engine, active):
            res["engines"][out["engine"]] = out
    live = [e for e in res["engines"].values() if e["mode"] == LIVE_WEB and e.get("answered")]
    tot_a = sum(e["answered"] for e in live)
    tot_n = sum(e["named"] for e in live)
    res["live_named_pct"] = round(100 * tot_n / tot_a, 1) if tot_a else None
    res["status"] = "ok"
    return res


# ── SEARCH CONSOLE ───────────────────────────────────────────────────────────────────────────
def _sa_info():
    """Same SA key the GA4 sensor uses: analytics/ga4.py reads GA4_SA_JSON (raw or base64)."""
    sys.path.insert(0, str(REPO / "analytics"))
    try:
        import ga4
        return ga4._sa_info()
    except Exception:
        return None


def _gsc_token(info):
    try:
        from google.oauth2 import service_account
        import google.auth.transport.requests as gar
    except ImportError:                       # same stdlib JWT fallback the GA4 client has, other scope
        import ga4
        old, ga4.SCOPE = ga4.SCOPE, GSC_SCOPE
        try:
            return ga4._token_via_stdlib(info)
        finally:
            ga4.SCOPE = old
    creds = service_account.Credentials.from_service_account_info(info, scopes=[GSC_SCOPE])
    creds.refresh(gar.Request())
    return creds.token


def _gsc_query(token, prop, dims, start, end, limit=250):
    url = ("https://searchconsole.googleapis.com/webmasters/v3/sites/"
           + urllib.parse.quote(prop, safe="") + "/searchAnalytics/query")
    body = json.dumps({"startDate": start, "endDate": end, "dimensions": dims, "rowLimit": limit}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode()).get("rows") or []


def _row(r, key_names):
    d = dict(zip(key_names, r.get("keys") or []))
    d.update({"impressions": int(r.get("impressions", 0)), "clicks": int(r.get("clicks", 0)),
              "ctr": round(float(r.get("ctr", 0)), 4), "position": round(float(r.get("position", 0)), 1)})
    return d


def run_gsc():
    info = _sa_info()
    if not info:
        return {"gsc": "no_key", "reason": "GA4_SA_JSON not set"}
    sa = info.get("client_email")
    try:
        token = _gsc_token(info)
    except Exception as e:
        return {"gsc": "token_error", "sa": sa, "reason": type(e).__name__}
    end = datetime.date.today() - datetime.timedelta(days=2)       # GSC lags ~2 days
    start = end - datetime.timedelta(days=GSC_DAYS - 1)
    tried = []
    for prop in GSC_PROPERTIES:
        try:
            pages = [_row(r, ["page"]) for r in _gsc_query(token, prop, ["page"], start.isoformat(), end.isoformat())]
            queries = [_row(r, ["query"]) for r in _gsc_query(token, prop, ["query"], start.isoformat(), end.isoformat())]
            pq = [_row(r, ["page", "query"]) for r in
                  _gsc_query(token, prop, ["page", "query"], start.isoformat(), end.isoformat(), 1000)]
            tot_i = sum(p["impressions"] for p in pages)
            tot_c = sum(p["clicks"] for p in pages)
            return {"gsc": "ok", "sa": sa, "property": prop, "start": start.isoformat(), "end": end.isoformat(),
                    "totals": {"impressions": tot_i, "clicks": tot_c,
                               "ctr": round(tot_c / tot_i, 4) if tot_i else None},
                    "pages": pages, "queries": queries[:100], "page_queries": pq}
        except urllib.error.HTTPError as e:
            tried.append({"property": prop, "http": e.code})
        except Exception as e:
            tried.append({"property": prop, "error": type(e).__name__})
    if all(t.get("http") in (401, 403, 404) for t in tried):
        return {"gsc": "no_access", "sa": sa, "tried": tried,
                "fix": f"add {sa} as a (restricted) user on the Search Console property"}
    return {"gsc": "error", "sa": sa, "tried": tried}


# ── WEAKEST PAGES ────────────────────────────────────────────────────────────────────────────
_NOT_REWRITABLE = {"index.html", "investors.html", "onepager.html", "demo.html", "case-study.html",
                   "v2-home.html", "details.html", "toolbox.html", "guides.html", "glossary.html"}


def _page_file(url):
    path = urllib.parse.urlparse(url).path.lstrip("/")
    if not path or path.endswith("/"):
        path += "index.html"
    elif not path.endswith(".html"):
        path += ".html"
    return path


def _rewritable(f):
    return "/" not in f and f not in _NOT_REWRITABLE and (REPO / f).exists()


def pick_weakest(gsc, aeo):
    picks, seen = [], set()
    if gsc.get("gsc") == "ok":
        pq = gsc.get("page_queries") or []
        cands = [p for p in gsc.get("pages") or []
                 if p["impressions"] >= WEAK_MIN_IMPRESSIONS and p["ctr"] < WEAK_MAX_CTR]
        cands.sort(key=lambda p: p["impressions"] * (1 - p["ctr"]), reverse=True)
        for p in cands:
            f = _page_file(p["page"])
            if f in seen or not _rewritable(f):
                continue
            qs = sorted((r for r in pq if r["page"] == p["page"]), key=lambda r: r["impressions"], reverse=True)
            picks.append({"page": f, "rule": "high_impressions_low_ctr",
                          "reason": (f"{p['impressions']} impressions, {p['clicks']} clicks "
                                     f"(CTR {p['ctr']*100:.1f}%) at avg position {p['position']} over {GSC_DAYS} days"),
                          "win_queries": [r["query"] for r in qs[:5]]})
            seen.add(f)
            if len(picks) >= WEAK_MAX:
                return picks
    # Rule 2: panel questions where at least one engine answered, named others, and never named us.
    losses = {}
    for eng in (aeo.get("engines") or {}).values():
        if eng["mode"] != LIVE_WEB:          # the memory control does not measure the web
            continue
        for r in eng["results"]:
            if r.get("answered") and not r.get("named") and r.get("others"):
                L = losses.setdefault(r["page"], {"qs": set(), "engines": set(), "others": {}})
                L["qs"].add(r["q"]); L["engines"].add(eng["engine"])
                for o in r["others"]:
                    L["others"][o] = L["others"].get(o, 0) + 1
            elif r.get("named"):
                losses.setdefault(r["page"], {"qs": set(), "engines": set(), "others": {}, }).setdefault("won", True)
    ranked = sorted(((f, L) for f, L in losses.items() if L["qs"] and not L.get("won")),
                    key=lambda x: (len(x[1]["engines"]), len(x[1]["qs"])), reverse=True)
    for f, L in ranked:
        if f in seen or not _rewritable(f):
            continue
        top = sorted(L["others"], key=lambda o: -L["others"][o])[:4]
        picks.append({"page": f, "rule": "engines_name_competitors_not_us",
                      "reason": (f"{len(L['engines'])} live engine(s) answered without naming us; "
                                 f"they named {', '.join(top)}"),
                      "win_queries": sorted(L["qs"])})
        seen.add(f)
        if len(picks) >= WEAK_MAX:
            break
    return picks


# ── RUN ──────────────────────────────────────────────────────────────────────────────────────
def score_line(w=None):
    """One short line for the daily brief. None if no weekly file yet."""
    if w is None:
        try:
            w = json.loads(WEEKLY.read_text())
        except Exception:
            return None
    g, a = w.get("gsc") or {}, w.get("aeo") or {}
    parts = []
    if g.get("gsc") == "ok":
        t = g["totals"]
        parts.append(f"Google {t['impressions']} impressions / {t['clicks']} clicks (28d)")
    elif g.get("gsc"):
        parts.append(f"Search Console {g['gsc'].replace('_', ' ')}")
    if a.get("live_named_pct") is not None:
        n = sum(e["named"] for e in a["engines"].values() if e["mode"] == LIVE_WEB)
        d = sum(e["answered"] for e in a["engines"].values() if e["mode"] == LIVE_WEB)
        parts.append(f"AI engines name us in {n}/{d} answers")
    elif a.get("status") == "no_keys":
        parts.append("AI probe skipped (no keys)")
    if w.get("weakest"):
        parts.append("next rewrites: " + ", ".join(p["page"].replace(".html", "") for p in w["weakest"]))
    return f"Weekly score ({w.get('date')}): " + "; ".join(parts) if parts else None


def run(do_aeo=True):
    gsc = run_gsc()
    aeo = run_aeo() if do_aeo else {"status": "skipped_by_flag"}
    weakest = pick_weakest(gsc, aeo)
    now = model.now()
    w = {"date": datetime.date.today().isoformat(), "generated_at": now, "gsc": gsc, "aeo": aeo, "weakest": weakest,
         "honesty": ("Indicative sampled panel; AI answers vary run to run. No panel question contains our name. "
                     "Groq is a model-memory control, not a web measure. Google AI Overviews is not probed.")}
    STATE.mkdir(parents=True, exist_ok=True)
    WEEKLY.write_text(json.dumps(w, indent=2, ensure_ascii=False) + "\n")
    hist = {"date": w["date"], "gsc": gsc.get("gsc"),
            "gsc_totals": gsc.get("totals"),
            "aeo": {k: {"answered": e["answered"], "named": e["named"], "named_pct": e["named_pct"],
                        "mode": e["mode"], "error": e["error"]} for k, e in (aeo.get("engines") or {}).items()},
            "aeo_skipped": [s["engine"] for s in aeo.get("skipped") or []],
            "live_named_pct": aeo.get("live_named_pct"),
            "weakest": [p["page"] for p in weakest]}
    with HISTORY.open("a") as fh:
        fh.write(json.dumps(hist, ensure_ascii=False) + "\n")
    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-aeo", action="store_true")
    args = ap.parse_args()
    w = run(do_aeo=not args.no_aeo)
    g, a = w["gsc"], w["aeo"]
    print(f"[seo_measure] gsc={g.get('gsc')} sa={g.get('sa')} property={g.get('property')}")
    print(f"[seo_measure] aeo status={a.get('status')} engines={list((a.get('engines') or {}).keys())} "
          f"skipped={[s['engine'] for s in a.get('skipped') or []]}")
    for e in (a.get("engines") or {}).values():
        print(f"  {e['engine']}: named {e['named']}/{e['answered']} errors={e['errors']} {e['error'] or ''}")
    print(f"[seo_measure] weakest={[p['page'] for p in w['weakest']]}")
    print(f"[seo_measure] {score_line(w)}")


if __name__ == "__main__":
    main()
