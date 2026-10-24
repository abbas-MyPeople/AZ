#!/usr/bin/env python3
"""
Generate the SPY morning research briefing.

Runs Claude with web search to find the news that has *confidently* moved (or is
set to move) SPY — surfaced AND inferred — then synthesizes bite-sized drivers.
Hard numbers (spot, VIX, expected move, volatility regime) are computed here from
the real market snapshot and stamped OVER the model output, so the figures are
grounded in reality, never hallucinated.

Writes:
  stocks/data/spy/research/latest.json
  stocks/data/spy/research/<YYYY-MM-DD>.json   (archive)

Requires env ANTHROPIC_API_KEY. Stdlib only.
"""
import json, os, sys, math, datetime, urllib.request, urllib.error

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


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.environ.get("STOCKS_RESEARCH_MODEL", "claude-sonnet-5")
API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def now_et():
    return datetime.datetime.utcnow() - datetime.timedelta(hours=4)

def load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

def vol_profile(vix):
    if not vix:
        return {"score": 40, "regime": "normal"}
    score = max(0, min(100, round((vix - 10) / 30 * 100)))
    regime = "low" if vix < 15 else "normal" if vix < 20 else "elevated" if vix < 28 else "high"
    return {"score": score, "regime": regime}

SCHEMA_HINT = """Return ONLY a JSON object (no prose, no code fence) with EXACTLY these keys:
{
 "headline": "punchy < 90 char headline for today's SPY setup",
 "summary": "2-3 sentence synthesis of what is driving SPY right now",
 "bias": {"direction":"bullish|bearish|neutral","confidence":"high|med|low","note":"one line why"},
 "keyLevels": {"support":[num,num],"resistance":[num,num],"pivot":num},
 "watchWindows": [
   {"start":"9:30 ET","end":"10:30 ET","what":"what happens in this window and why it matters",
    "expectVol":"high|med|low","direction":"bullish|bearish|two-way","probabilityPct":60}
 ],
 "drivers": [
   {"title":"short title","type":"bull|bear|macro","impact":"high|med|low",
    "confidence":"high|med|low","inferred":false,
    "direction":"bullish|bearish|neutral",
    "probabilityPct": 65,
    "magnitude":"±0.4%",
    "pricedIn":"yes|partial|no",
    "window":"10:00-11:00 ET or null if all-day",
    "detail":"1-2 sentences, concrete and specific with numbers where possible",
    "tags":["Fed","rates"],"source":"https://..."}
 ],
 "calendar": [{"time":"8:30 ET","event":"...","importance":"high|med|low"}],
 "watch": ["specific thing to watch today", "..."],
 "sources": [{"title":"outlet","url":"https://..."}]
}
Provide 4-7 drivers and 2-5 watchWindows covering the session start to close.
For EVERY driver answer the trader's four questions: which direction does it push,
how big (magnitude as a % move), how likely (probabilityPct that it actually moves
SPY), and is it already priced in (yes/partial/no)? Mark inferred=true for
second-order effects you reason to (not directly reported). Rank by CONFIDENT
price impact. Be concrete; cite real sources."""

def build_prompt(quote):
    d = now_et().strftime("%A, %B %d, %Y")
    spot = quote.get("price")
    vix = quote.get("vix")
    return (
        f"You are a sharp buy-side analyst writing a pre-open briefing for SPY (S&P 500 ETF) "
        f"for {d}. Use web search to find the most important, market-moving news from the last "
        f"24-48 hours that has confidently affected or will affect SPY: macro data, Fed/rates, "
        f"mega-cap earnings & moves, geopolitics, bond yields, oil, USD, and cross-asset signals. "
        f"Go deep — surface the obvious AND infer second-order effects. Synthesize into concise, "
        f"high-signal drivers a busy trader can absorb in seconds.\n\n"
        f"Write it as an ACTION SHEET, not a news recap. The reader wants: watch out from THIS "
        f"time to THIS time; THIS is happening; expect THIS much volatility; it is (not) priced "
        f"in; it leans bullish/bearish with roughly X% probability of actually moving the market. "
        f"Every claim should answer: direction, size, likelihood, priced-in?\n\n"
        f"Current context (grounding): SPY ~{spot}, VIX ~{vix}. Use real, current figures from your search.\n\n"
        + SCHEMA_HINT
    )

def call_claude(prompt):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 4000,
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.loads(r.read().decode())
    text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
    return text

def extract_json(text):
    # Grab the outermost {...}
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("no JSON in model output")
    return json.loads(text[start:end + 1])

def main():
    if not API_KEY:
        print("ANTHROPIC_API_KEY not set — skipping research generation.", file=sys.stderr)
        sys.exit(0)  # don't fail CI; the page shows the last good brief

    # COST GUARD: at most ONE paid API run per day (~$0.10-0.25/run, so the
    # daily API spend stays well under $1 no matter how often the workflow
    # is triggered). FORCE=1 (manual dispatch) overrides for a same-day redo.
    existing = load(os.path.join(ROOT, "data", "spy", "research", "latest.json"), {})
    today = now_et().strftime("%Y-%m-%d")
    if os.environ.get("FORCE") != "1" and existing.get("date") == today and "watchWindows" in existing:
        print(f"brief for {today} already exists — skipping (cost guard: max 1 run/day).")
        sys.exit(0)

    quote = load(os.path.join(ROOT, "data", "spy", "quote", "latest.json"), {})
    spot = quote.get("price")
    vix = quote.get("vix")
    dmp = quote.get("dailyMovePct")

    try:
        raw = call_claude(build_prompt(quote))
        r = extract_json(raw)
    except Exception as e:
        print("research generation failed:", e, file=sys.stderr)
        sys.exit(0)

    # Stamp authoritative numbers computed from the real snapshot
    r["symbol"] = "SPY"
    r["session"] = "pre-open"
    r["date"] = now_et().strftime("%Y-%m-%d")
    # True UTC — the frontend parses this as an instant for "ago" display.
    r["generatedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    vp = vol_profile(vix)
    r["volatility"] = {"vix": vix, "vixChg": quote.get("vixChg"),
                       "ivRank": r.get("volatility", {}).get("ivRank"),
                       "regime": vp["regime"], "score": vp["score"]}
    if spot and dmp:
        dollar = round(spot * dmp / 100, 2)
        r["expectedMove"] = {"pct": dmp, "dollarLow": round(spot - dollar, 2),
                             "dollarHigh": round(spot + dollar, 2), "basis": "options-implied (ATM IV)"}
    r.setdefault("keyLevels", {})

    out_dir = os.path.join(ROOT, "data", "spy", "research")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "latest.json"), "w") as f:
        json.dump(r, f, indent=2)
    with open(os.path.join(out_dir, f"{r['date']}.json"), "w") as f:
        json.dump(r, f, indent=2)
    print(f"OK: briefing for {r['date']} with {len(r.get('drivers', []))} drivers.")

if __name__ == "__main__":
    main()
