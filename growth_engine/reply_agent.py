"""
growth_engine.reply_agent — THE AGENTIC BUILD WORKER.

Takes a freeform owner directive ("write a page on halal office catering", "add a Square-vs-Clover FAQ",
"tighten the About copy") and IMPLEMENTS it against the static site by creating/editing files through a
bounded Anthropic tool-use loop. It matches the existing design system by reading a close existing page,
and wires new pages into the sitemap + guides hub.

SAFETY (defense in depth):
  • Writes are SCOPED: only inside the repo, only .html/.xml/.json/.txt/.css/.md, and NEVER
    growth_engine/ · .github/ · .git/ · scripts/ · credentials/ · command/ (protected). No shell, no python.
  • It only ever writes to a THROWAWAY branch; run.py opens a PR — nothing reaches the live site until the
    owner replies "merge". So even an imperfect build is fully gated + revertible.
  • Bounded: MAX_STEPS tool iterations, capped tokens, capped read size.
  • No API key / ENGINE_DISABLED=1 → clean no-op.
"""
from __future__ import annotations
import os, json, re, urllib.request
from .executors import REPO

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



def validate(changed) -> tuple:
    """Automated safety gate for auto-merge: every changed .html has valid JSON-LD + basic structure,
    and sitemap.xml stays well-formed XML. Returns (ok, reason). A failure keeps the task PR-gated."""
    for f in changed:
        p = REPO / f
        if not p.is_file():
            return False, f"{f}: missing after build"
        if f.endswith(".html"):
            html = p.read_text(encoding="utf-8", errors="replace")
            for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
                try:
                    json.loads(b)
                except Exception:
                    return False, f"{f}: invalid JSON-LD"
            low = html.lower()
            if "<head" not in low or "</html>" not in low or "</body>" not in low:
                return False, f"{f}: incomplete HTML document"
        if f == "sitemap.xml":
            import xml.dom.minidom as _m
            try:
                _m.parse(str(p))
            except Exception:
                return False, "sitemap.xml not well-formed"
    return True, "ok"

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("REPLY_AGENT_MODEL", "claude-opus-4-8")
MAX_STEPS = 26
MAX_TOKENS = 4096
READ_CAP = 42000

_WRITE_EXT = {".html", ".xml", ".json", ".txt", ".css", ".md"}
_DENY_PREFIX = ("growth_engine", ".github", ".git", "scripts", "credentials", "command")


def _rel(path: str):
    try:
        return (REPO / path).resolve().relative_to(REPO)
    except Exception:
        return None


def _can_write(path: str):
    rel = _rel(path)
    if rel is None:
        return False, "outside the repo"
    if str(rel).startswith(_DENY_PREFIX):
        return False, "protected path (engine/workflow/queue)"
    if rel.suffix.lower() not in _WRITE_EXT:
        return False, f"extension {rel.suffix or '(none)'} not allowed"
    return True, str(rel)


TOOLS = [
    {"name": "list_dir", "description": "List files/dirs under a repo-relative path (default = repo root).",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
    {"name": "read_file", "description": "Read a repo file's text (truncated).",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Create or overwrite a repo file. Allowed: .html/.xml/.json/.txt/.css/.md. "
                                          "Forbidden: engine, workflow, python, or queue files.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                      "required": ["path", "content"]}},
    {"name": "finish", "description": "Finish; give a 1-2 sentence summary of what you built/changed.",
     "input_schema": {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}},
]


def _exec_tool(name, inp, changed) -> str:
    if name == "list_dir":
        rel = _rel(inp.get("path", ".") or ".")
        if rel is None:
            return "error: outside repo"
        d = REPO / rel
        if not d.exists():
            return "error: not found"
        if d.is_file():
            return f"(file) {rel}"
        return "\n".join(sorted(p.name + ("/" if p.is_dir() else "") for p in d.iterdir()))[:4000]
    if name == "read_file":
        rel = _rel(inp.get("path", ""))
        if rel is None or not (REPO / rel).is_file():
            return "error: not found"
        return (REPO / rel).read_text(encoding="utf-8", errors="replace")[:READ_CAP]
    if name == "write_file":
        ok, info = _can_write(inp.get("path", ""))
        if not ok:
            return f"refused: {info}"
        p = REPO / info
        p.parent.mkdir(parents=True, exist_ok=True)
        content = inp.get("content", "")
        p.write_text(content, encoding="utf-8")
        changed.add(info)
        return f"wrote {info} ({len(content)} bytes)"
    return "error: unknown tool"


_SYSTEM = (
    "You are the build agent for AZ Restaurant Partners' static website — hand-coded HTML with a shared "
    "styles.css (no framework), deployed via GitHub Pages. AZ is a done-for-you restaurant technology & "
    "growth team for independent, family-run restaurants (Greater Houston), run by Abbas Zoeb, an ex-Google "
    "engineer who owns an award-winning halal restaurant (Wok & Karahi, 4.6★/872 Google reviews).\n\n"
    "Implement the owner's directive by creating/editing files with your tools. RULES:\n"
    "1. Match the existing design system EXACTLY. BEFORE creating a page, read a close existing one and mirror "
    "its <head>, nav, body classes, footer and <script> tags: a guide → get-restaurant-on-google-maps.html; a "
    "comparison → chownow-vs-owner.html (use the .cmp table); a definition → glossary/restaurant-pos.html "
    "(note the ../ prefixes for files in a subdir). Use ONLY existing CSS classes.\n"
    "2. Ground every fact. NEVER invent statistics, prices, or client results. Hedge any pricing with "
    "'confirm on a live quote (2026)'. Keep AZ's vendor-neutral, 'you only pay once you're saving' voice.\n"
    "3. For a NEW page, wire it in: add a <url> to sitemap.xml and a matching card (and ItemList entry) to "
    "guides.html where it fits. Add valid JSON-LD (Article/FAQPage/BreadcrumbList or DefinedTerm as appropriate).\n"
    "4. Production-quality only — an owner should be proud to ship it. Prefer editing/adding over restructuring.\n"
    "5. You CANNOT edit engine, workflow, python, or the task-queue files — don't try.\n"
    "When finished, call finish with a short summary. Work efficiently; don't over-read."
)


def build(directive: str, verbose: bool = True) -> dict:
    """Run the bounded build loop. Returns {available, changed_files, summary}."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or os.environ.get("ENGINE_DISABLED") == "1":
        return {"available": False, "changed_files": [], "summary": "no API key / disabled"}
    changed: set = set()
    messages = [{"role": "user", "content":
                 f"OWNER DIRECTIVE (from an email reply):\n{directive}\n\n"
                 f"Implement it now. Start by reading a close existing page to match the design system, "
                 f"then create/edit the files and wire any new page into sitemap.xml + guides.html."}]
    summary = ""
    for _ in range(MAX_STEPS):
        body = json.dumps({"model": MODEL, "max_tokens": MAX_TOKENS, "system": _SYSTEM,
                           "tools": TOOLS, "messages": messages}).encode()
        req = urllib.request.Request(API_URL, data=body, headers={
            "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=200) as r:
                data = json.loads(r.read().decode())
        except Exception as e:
            if verbose:
                print(f"reply_agent: API error {type(e).__name__} — stopping.")
            break
        content = data.get("content", []) or []
        messages.append({"role": "assistant", "content": content})
        results, stop = [], False
        for block in content:
            if block.get("type") == "tool_use":
                name, inp, tuid = block.get("name"), block.get("input", {}) or {}, block.get("id")
                if name == "finish":
                    summary = (inp.get("summary") or "").strip()
                    stop = True
                    results.append({"type": "tool_result", "tool_use_id": tuid, "content": "done"})
                    continue
                out = _exec_tool(name, inp, changed)
                if verbose:
                    print(f"  [{name}] {str(inp.get('path', ''))[:56]} -> {out[:56]}")
                results.append({"type": "tool_result", "tool_use_id": tuid, "content": out[:6000]})
        if stop:
            break
        if not results:            # model replied with text but no tool call → nothing more to do
            break
        messages.append({"role": "user", "content": results})
    return {"available": True, "changed_files": sorted(changed),
            "summary": summary or (f"Built/edited {len(changed)} file(s)." if changed else "No changes produced.")}
