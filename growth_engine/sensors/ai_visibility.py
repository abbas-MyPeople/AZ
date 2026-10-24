"""
growth_engine.sensors.ai_visibility — AI-recommendation rank tracker.

For each target buyer query, asks a web-grounded LLM (Anthropic Messages API + the web_search tool)
"who/what would you recommend?" and records whether azrestaurantpartners.com is cited/mentioned, plus
which competitor domains the AI keeps citing (that's the content-gap target list). Emits findings for the
brief. A proxy for "what AI answer engines recommend" — Claude's web-grounded answer stands in for the
broader AI-answer shape.

SAFETY: this hits an EXTERNAL, PAID API, so it is OPT-IN and cost-capped:
  • runs only when AI_VISIBILITY_ENABLED=1 (and ANTHROPIC_API_KEY present),
  • at most WEEKLY (a timestamp in state gates it),
  • at most MAX_QUERIES per run, small model, low max_tokens.
Never breaks the loop: any error → clean no-op. Kill switch ENGINE_DISABLED=1 also no-ops.
Run manually to test: `AI_VISIBILITY_ENABLED=1 python -m growth_engine.run --mode aivis --force`.
"""
from __future__ import annotations
import os, json, re, time, urllib.request, urllib.error
from .. import model

def _llm_backup():
    """If the Anthropic account stops, Claude calls go to OpenRouter instead (growth_engine/llm_route.py)."""
    import importlib.util as _iu
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d) and not os.path.exists(os.path.join(d, "growth_engine", "llm_route.py")):
        d = os.path.dirname(d)
    try:
        spec = _iu.spec_from_file_location("llm_route", os.path.join(d, "growth_engine", "llm_route.py"))
        mod = _iu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.install()
    except Exception:                                                # noqa: BLE001
        pass


_llm_backup()


API = "https://api.anthropic.com/v1/messages"
STATE_TS = model.STATE / "ai_visibility_last.json"
MAX_QUERIES = 10
MODEL = os.environ.get("AI_VIS_MODEL", "claude-haiku-4-5")
DOMAIN = "azrestaurantpartners.com"

TARGET_QUERIES = [
    "best restaurant POS for a small independent restaurant",
    "how to cut DoorDash commission fees for a restaurant",
    "how much does AI phone answering cost for a restaurant",
    "should a restaurant leave DoorDash for its own online ordering",
    "how much does a restaurant POS system really cost",
    "commission-free online ordering systems for restaurants",
    "restaurant technology consultant in Houston",
    "how to get my restaurant recommended by ChatGPT",
    "do restaurants lose money on DoorDash",
    "best AI phone answering service for restaurants",
]


def _enabled() -> bool:
    return os.environ.get("AI_VISIBILITY_ENABLED") == "1" and bool(os.environ.get("ANTHROPIC_API_KEY")) \
        and os.environ.get("ENGINE_DISABLED") != "1"


def _due(force: bool) -> bool:
    if force:
        return True
    try:
        last = json.loads(STATE_TS.read_text()).get("ts", 0)
    except Exception:
        last = 0
    return (time.time() - last) > 6 * 86400   # weekly


def _ask(query: str) -> tuple[str, list[str]]:
    """Return (answer_text, cited_domains) for a web-grounded recommendation answer."""
    body = {
        "model": MODEL, "max_tokens": 700,
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
        "messages": [{"role": "user", "content":
            f"A restaurant owner asks: \"{query}\". Search the web and answer with your honest, specific "
            f"recommendation — name the actual businesses, tools, or sites you'd point them to. Be concise."}],
    }
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST", headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
        "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    text, urls = [], []
    for block in data.get("content", []):
        if block.get("type") == "text":
            text.append(block.get("text", ""))
            for c in block.get("citations", []) or []:
                if c.get("url"):
                    urls.append(c["url"])
        elif block.get("type") == "web_search_tool_result":
            for item in block.get("content", []) or []:
                if isinstance(item, dict) and item.get("url"):
                    urls.append(item["url"])
    return "\n".join(text), urls


def _domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url or "")
    return (m.group(1).lower().replace("www.", "") if m else "").strip()


def run(verbose: bool = True, force: bool = False) -> dict:
    if not _enabled():
        if verbose:
            print("ai_visibility: disabled (set AI_VISIBILITY_ENABLED=1 + ANTHROPIC_API_KEY) — skipping.")
        return {"available": False}
    if not _due(force):
        if verbose:
            print("ai_visibility: ran within the last week — skipping (weekly cadence).")
        return {"available": False, "reason": "cadence"}

    cited, comp = 0, {}
    misses = []
    for q in TARGET_QUERIES[:MAX_QUERIES]:
        try:
            text, urls = _ask(q)
        except Exception as e:
            if verbose:
                print(f"ai_visibility: query failed ({type(e).__name__}) — continuing.")
            continue
        doms = {_domain(u) for u in urls if _domain(u)}
        hit = DOMAIN in doms or DOMAIN.split(".")[0] in (text or "").lower().replace(" ", "")
        if hit:
            cited += 1
        else:
            misses.append(q)
        for d in doms:
            if d and DOMAIN not in d:
                comp[d] = comp.get(d, 0) + 1

    n = len(TARGET_QUERIES[:MAX_QUERIES])
    top_comp = sorted(comp, key=lambda k: -comp[k])[:6]
    model.signal("aivis", "queries_cited", "site", cited, unit="count", period="point",
                 meta={"of": n, "top_competitors": top_comp})
    read = "good" if cited < n else "watch"
    model.finding("V1_ai_visibility", "site", "opportunity", read,
                  f"AI-visibility: AZ recommended for {cited}/{n} target queries",
                  detail=("Not yet cited for: " + "; ".join(misses[:4]) + ". " if misses else "")
                         + ("AI keeps citing: " + ", ".join(top_comp) + " — the domains to out-publish." if top_comp else ""))
    STATE_TS.parent.mkdir(parents=True, exist_ok=True)
    STATE_TS.write_text(json.dumps({"ts": time.time(), "cited": cited, "of": n, "top": top_comp}))
    if verbose:
        print(f"ai_visibility: {cited}/{n} cited. Top competitors: {top_comp}")
    return {"available": True, "cited": cited, "of": n, "competitors": top_comp}
