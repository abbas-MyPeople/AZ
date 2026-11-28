#!/usr/bin/env python3
"""The restaurant intelligence model - one living profile per restaurant.

Builds on outreach/ARCHITECTURE.md (the evidence envelope and the four tiers). What this
adds is the part a dossier never had: the profile keeps learning. Every owner reaction in
the room (confirm, challenge, correct, add detail, answer a question) is an event appended
to <slug>.events.jsonl, and the live profile is always base + every event replayed in order.
Nothing is overwritten, so we can always show what we believed before the owner spoke.

    python3 -m outreach.intel.model check  <slug>      # validate the base profile
    python3 -m outreach.intel.model ingest <slug> <events.json>
    python3 -m outreach.intel.model show   <slug>      # the profile as it stands now

Rules enforced here, not in prose:
- every fact or derived finding names a source URL and the date we saw it
- an inference or hypothesis carries a confidence below 1 and an open question
- a pattern must join findings from at least two different dimensions (cross-domain)
- every number in a money scenario is a labelled assumption with its source
- old evidence counts for less: a review over 12 months old is flagged stale
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys
from datetime import date, datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
PROFILES = HERE / "profiles"

DIMENSIONS = (
    "identity", "history", "cuisine", "menu", "pricing", "reputation", "sentiment",
    "website", "ordering", "marketing", "social", "competition", "geography",
    "catering", "community", "technology", "operations", "people",
)
KINDS = ("fact", "derived", "inference", "hypothesis")
ACTIONS = ("confirm", "challenge", "correct", "elaborate", "answer")
OPPORTUNITY_KINDS = (
    "business", "revenue", "marketing", "signature_dish", "catering", "guest_experience",
    "ordering", "operations", "differentiation", "automation", "haniya_demo",
)
ASSUMPTION_SOURCES = ("public", "industry", "owner", "ours")
DASHES = re.compile("[–—]")


def today() -> date:
    return datetime.now(timezone.utc).date()


def _d(s: str | None) -> date | None:
    try:
        return date.fromisoformat(s[:10]) if s else None
    except ValueError:
        return None


def recency_weight(published: str | None, now: date | None = None) -> float:
    """How much a dated piece of evidence should count today.

    The owner's rule (2026-11-24): "2 years is a long time ... treat things with correct
    weight". Under 6 months counts in full, 6-12 months at 0.6, older at 0.25 and stale."""
    d = _d(published)
    if d is None:
        return 0.8          # undated pages (a menu, a homepage) are current as observed
    age = ((now or today()) - d).days
    if age <= 183:
        return 1.0
    if age <= 365:
        return 0.6
    return 0.25


def is_stale(published: str | None, now: date | None = None) -> bool:
    return recency_weight(published, now) < 0.5


def finding_weight(f: dict, now: date | None = None) -> float:
    """Evidence strength now: best recency among its sources times confidence."""
    if f.get("status") == "confirmed":
        return 1.0
    ws = [recency_weight(e.get("published_at"), now) for e in f.get("evidence", [])] or [0.5]
    return round(max(ws) * float(f.get("confidence", 0.5)), 3)


# ── validation ─────────────────────────────────────────────────────────────────

def _texts(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _texts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _texts(v)


def validate(p: dict) -> list[str]:
    """Every rule from the docstring. Returns problems; empty means fit to show an owner."""
    errs: list[str] = []
    fids = {}
    for f in p.get("findings", []):
        fid = f.get("id", "?")
        if fid in fids:
            errs.append(f"{fid}: duplicate id")
        fids[fid] = f
        if f.get("dimension") not in DIMENSIONS:
            errs.append(f"{fid}: unknown dimension {f.get('dimension')!r}")
        if f.get("kind") not in KINDS:
            errs.append(f"{fid}: kind must be one of {KINDS}")
        if not f.get("claim"):
            errs.append(f"{fid}: no claim")
        ev = f.get("evidence") or []
        if f.get("kind") in ("fact", "derived"):
            if not ev:
                errs.append(f"{fid}: a {f.get('kind')} needs evidence")
            for e in ev:
                if not e.get("url") or not _d(e.get("observed_at")):
                    errs.append(f"{fid}: evidence needs a url and observed_at date")
        else:
            if float(f.get("confidence", 1)) >= 1:
                errs.append(f"{fid}: an {f.get('kind')} must carry confidence below 1")
            if not f.get("open_question"):
                errs.append(f"{fid}: an {f.get('kind')} needs the open question only the owner can answer")
    for pat in p.get("patterns", []):
        ids = pat.get("finding_ids", [])
        missing = [i for i in ids if i not in fids]
        if missing:
            errs.append(f"pattern {pat.get('id')}: unknown findings {missing}")
        dims = {fids[i]["dimension"] for i in ids if i in fids}
        if len(dims) < 2:
            errs.append(f"pattern {pat.get('id')}: must join at least two dimensions, has {sorted(dims)}")
    for o in p.get("opportunities", []):
        oid = o.get("id", "?")
        if o.get("kind") not in OPPORTUNITY_KINDS:
            errs.append(f"{oid}: unknown opportunity kind {o.get('kind')!r}")
        if not [i for i in o.get("finding_ids", []) if i in fids]:
            errs.append(f"{oid}: an opportunity must rest on at least one finding")
        sc = o.get("scenario")
        if sc:
            for a in sc.get("assumptions", []):
                if a.get("source") not in ASSUMPTION_SOURCES:
                    errs.append(f"{oid}: assumption {a.get('label')!r} needs a source {ASSUMPTION_SOURCES}")
            if "guarantee" in json.dumps(sc).lower():
                errs.append(f"{oid}: scenarios never guarantee an outcome")
    h = p.get("headline") or {}
    if not h.get("insight") or not [i for i in h.get("finding_ids", []) if i in fids]:
        errs.append("headline: needs one insight resting on real findings")
    for i in p.get("credibility", []):
        if i not in fids:
            errs.append(f"credibility: unknown finding {i}")
    for t in _texts({k: v for k, v in p.items() if k != "sources_note"}):
        if DASHES.search(t):
            errs.append(f"em or en dash in: {t[:60]!r}")
            break
    return errs


# ── the learning loop ──────────────────────────────────────────────────────────

def apply_event(p: dict, ev: dict) -> dict:
    """One owner reaction becomes evidence. Returns the same profile, changed in place."""
    act = ev.get("action")
    if act not in ACTIONS:
        raise ValueError(f"unknown action {act!r}")
    at = ev.get("at") or datetime.now(timezone.utc).isoformat(timespec="seconds")
    owner_ev = {"url": "owner", "title": f"Owner, in person ({ev.get('by') or 'owner'})",
                "quote": ev.get("note", ""), "observed_at": at[:10], "published_at": at[:10]}
    if act == "answer":
        for u in p.get("unknowns", []):
            if u.get("id") == ev.get("target"):
                u["answer"] = ev.get("note", "")
                u["answered_at"] = at
        p.setdefault("history", []).append({"at": at, **ev})
        return p
    f = next((f for f in p.get("findings", []) if f.get("id") == ev.get("target")), None)
    if f is None:
        raise KeyError(f"no finding {ev.get('target')!r}")
    if act == "confirm":
        f["status"] = "confirmed"
        f["confidence"] = 1.0
    elif act == "challenge":
        f["status"] = "challenged"
        f["confidence"] = round(float(f.get("confidence", 0.5)) / 2, 3)
    elif act == "correct":
        f.setdefault("was", []).append({"claim": f["claim"], "until": at})
        f["claim"] = ev.get("note") or f["claim"]
        f["status"] = "corrected"
        f["confidence"] = 1.0
    elif act == "elaborate":
        f["status"] = f.get("status") or "unconfirmed"
    if ev.get("note") or act in ("confirm", "correct"):
        f.setdefault("evidence", []).append(owner_ev)
    _ripple(p)
    p.setdefault("history", []).append({"at": at, **ev})
    return p


def _ripple(p: dict) -> None:
    """An opportunity built only on findings the owner pushed back on is put on hold,
    so we never keep pitching something he told us is wrong."""
    weak = {f["id"] for f in p.get("findings", []) if f.get("status") == "challenged"}
    for o in p.get("opportunities", []):
        ids = set(o.get("finding_ids", []))
        o["on_hold"] = bool(ids) and ids <= weak
    for pat in p.get("patterns", []):
        pat["on_hold"] = bool(set(pat.get("finding_ids", [])) & weak)


def load(slug: str, root: pathlib.Path = PROFILES) -> dict:
    base = json.loads((root / f"{slug}.json").read_text())
    p = copy.deepcopy(base)
    evp = root / f"{slug}.events.jsonl"
    if evp.exists():
        for line in evp.read_text().splitlines():
            if line.strip():
                apply_event(p, json.loads(line))
    _ripple(p)
    now = today()
    for f in p.get("findings", []):
        f["weight"] = finding_weight(f, now)
        f["stale"] = bool(f.get("evidence")) and all(
            is_stale(e.get("published_at"), now) for e in f["evidence"] if e.get("published_at"))\
            and any(e.get("published_at") for e in f["evidence"])
    return p


def ingest(slug: str, events: list[dict], root: pathlib.Path = PROFILES) -> int:
    """Append owner events, skipping any we already hold (same id), after checking each applies."""
    evp = root / f"{slug}.events.jsonl"
    seen = set()
    if evp.exists():
        seen = {json.loads(l).get("id") for l in evp.read_text().splitlines() if l.strip()}
    probe = load(slug, root)
    new = []
    for e in events:
        if e.get("id") and e["id"] in seen:
            continue
        apply_event(probe, e)          # raises on a bad target before anything is written
        new.append(e)
    with evp.open("a") as fh:
        for e in new:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    return len(new)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, slug = argv[0], argv[1]
    if cmd == "check":
        errs = validate(json.loads((PROFILES / f"{slug}.json").read_text()))
        print("\n".join(errs) or "ok")
        return 1 if errs else 0
    if cmd == "ingest":
        print(ingest(slug, json.loads(pathlib.Path(argv[2]).read_text())), "new events")
        return 0
    if cmd == "show":
        print(json.dumps(load(slug), indent=2, ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
