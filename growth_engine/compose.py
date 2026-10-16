"""
growth_engine.compose — build the DAILY brief email (ported from seo_engine.compose, retargeted to AZ).

Two parts:
  1. "HOW THE SITE PERFORMED" — a short, honest read from the latest GA4 signals (traffic + conversion).
  2. up to 3 concrete PROPOSALS — each with WHY, the exact PAGE/SECTION it touches, and a reply handle.

Renders BOTH a branded HTML email (the primary, visual presentation) and a plain-text fallback with the
same content + the exact reply protocol. COMPOSE only — sending is notify.py. A quiet day produces an
honest short "nothing to change, here's what I'm watching" note. Even with GA4 empty (brand-new property,
no rows) it renders a valid brief.
"""
from __future__ import annotations
import datetime, json, pathlib
from html import escape as _esc
from . import model

_REPO = pathlib.Path(__file__).resolve().parent.parent   # AZ repo root (holds command/worklog.json)


def _worklog(limit_shipped: int = 5, limit_next: int = 3) -> dict:
    """Read command/worklog.json → the REAL work (recently shipped + what's building/queued).
    This is what makes the brief a growth update instead of a maintenance log. Never raises."""
    try:
        items = json.loads((_REPO / "command" / "worklog.json").read_text(encoding="utf-8")).get("items", [])
    except Exception:
        return {"shipped": [], "next": []}
    def _clip(s, n=118):
        s = (s or "").strip()
        return s if len(s) <= n else s[: n - 1].rstrip() + "…"
    shipped = [{"title": i.get("title", ""), "detail": _clip(i.get("detail", "")), "area": i.get("area", "")}
               for i in items if i.get("status") == "shipped"][:limit_shipped]
    nxt = [{"title": i.get("title", ""), "detail": _clip(i.get("detail", "")), "status": i.get("status", "")}
           for i in items if i.get("status") in ("building", "queued")][:limit_next]
    return {"shipped": shipped, "next": nxt}


def _worklog_html(wl) -> str:
    shipped = wl.get("shipped") or []
    if not shipped:
        return ""
    rows = "".join(
        f'<div style="padding:8px 0;border-bottom:1px solid {_LINE};">'
        f'<div><span style="color:{_GREEN};font-size:11px;font-weight:700;letter-spacing:.04em;">● LIVE</span>'
        f'&nbsp; <b style="color:{_INK};font-size:14px;">{_esc(i["title"])}</b></div>'
        f'<div style="color:{_BODY};font-size:12px;margin-top:3px;line-height:1.45;">{_esc(i["detail"])}</div></div>'
        for i in shipped)
    return (f'<tr><td style="padding:18px 24px 2px;"><div style="font-family:{_SERIF};color:{_INK};font-size:13px;'
            f'font-weight:700;letter-spacing:.08em;text-transform:uppercase;">What went live</div>'
            f'<div style="color:{_MUTED};font-size:12px;margin-top:2px;">Real work shipped to the site — the growth engine + build team.</div>'
            f'<div style="margin-top:6px;">{rows}</div></td></tr>')


def _next_html(wl) -> str:
    nxt = wl.get("next") or []
    if not nxt:
        return ""
    rows = "".join(
        f'<div style="padding:5px 0;"><span style="color:{_EMBER};font-size:11px;font-weight:700;">'
        f'{_esc((i.get("status") or "next").upper())}</span>&nbsp; '
        f'<b style="color:{_INK};font-size:13px;">{_esc(i["title"])}</b>'
        f'<div style="color:{_MUTED};font-size:12px;margin-top:1px;">{_esc(i["detail"])}</div></div>'
        for i in nxt)
    return (f'<tr><td style="padding:14px 24px 4px;"><div style="font-family:{_SERIF};color:{_INK};font-size:13px;'
            f'font-weight:700;letter-spacing:.08em;text-transform:uppercase;">What I\'m building next</div>'
            f'<div style="margin-top:6px;">{rows}</div></td></tr>')

FROM_NAME = "AZ site growth engine"
# rule_id → the single KPI each proposal is trying to move (keeps IMPACT honest + specific).
_IMPACT = {
    "G3_underperf_page": "turn page traffic into leads (lead_submit / call_click)",
    "G4_conversion": "primary conversions (book-a-call / lead form)",
    "G5_funnel_dropoff": "keep visitors reaching the offer",
    "G6_dead_cta": "CTA click-through",
    "G0_site_guard": "site integrity → AI/organic discovery",
    "G7_lead_rate": "lead RATE — a higher share of visits converting (right audience)",
}
_DEFAULT_IMPACT = "leads + discovery"

# ── brand palette (mirrors the site: cream / ink / ember) ─────────────────────────────────────
_PAPER, _CARD, _INK, _BODY, _MUTED = "#f4eee2", "#fbf7ee", "#1b1a17", "#4f4a40", "#8a8275"
_EMBER, _LINE, _GREEN, _RED = "#c0492b", "#e5dcc9", "#2f7a3f", "#b23b2e"
_SERIF = "Georgia, 'Times New Roman', serif"
_SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def _dedupe(findings):
    latest = {}
    for f in findings:
        key = f.get("dedupe_key") or f"{f.get('rule_id')}:{f.get('subject')}"
        latest[key] = f              # later record wins (most recent run)
    return list(latest.values())


def _blocks(findings):
    findings = _dedupe(findings)
    alerts = [f for f in findings if f.get("severity") == "alert"]
    proposals = [f for f in findings if f.get("severity") == "opportunity" and f.get("read") == "good"]
    watching = [f for f in findings if f.get("severity") == "opportunity" and f.get("read") == "watch"]
    return alerts, proposals, watching


def _fmt_pct(v):
    return "n/a" if v is None else f"{v:+.0f}%"


def _performance_data(signals) -> dict:
    """Structured performance read used by BOTH the HTML scorecard and the text summary."""
    avail = model.latest(signals, "traffic_available", "site")
    if not avail:
        return {"available": False}
    if not avail.get("value"):
        return {"available": True, "has_rows": False}
    d = {"available": True, "has_rows": True}
    sd = model.latest(signals, "sessions_delta_pct", "site")
    if sd:
        m = sd.get("meta", {})
        d["sessions"] = {"prev": m.get("prev"), "cur": m.get("cur"), "delta": sd.get("value")}
    ct = model.latest(signals, "conv_total_delta_pct", "site")
    if ct:
        m = ct.get("meta", {})
        bd = {}
        for e in ("finder_capture", "call_click", "lead_submit"):
            s = model.latest(signals, f"conv_{e}", "site")
            if s:
                bd[e] = s.get("value")
        d["conversions"] = {"prev": m.get("prev"), "cur": m.get("cur"), "delta": ct.get("value"), "breakdown": bd}
    lr = model.latest(signals, "lead_rate_per_100", "site")
    if lr:
        m = lr.get("meta", {})
        d["lead_rate"] = {"cur": m.get("cur"), "prev": m.get("prev"), "delta": m.get("delta_pct")}
    return d


def _seo_weekly_line():
    """One short line from the weekly measure step (seo_measure.py). Never raises."""
    try:
        from . import seo_measure
        return seo_measure.score_line()
    except Exception:
        return None


def _performance(signals) -> list[str]:
    """The 'how the site performed' summary as plain-text lines (fallback)."""
    d = _performance_data(signals)
    if not d.get("available"):
        return []
    if not d.get("has_rows"):
        return ["• GA4 is connected but has no rows yet — the property is still gathering data."]
    lines = []
    s = d.get("sessions")
    if s:
        lines.append(f"• Traffic: {s.get('prev','?')} → {s.get('cur','?')} sessions "
                     f"({_fmt_pct(s.get('delta'))} vs the prior week).")
    c = d.get("conversions")
    if c:
        parts = [f"{k}={v}" for k, v in (c.get("breakdown") or {}).items()]
        lines.append(f"• Conversions: {c.get('prev','?')} → {c.get('cur','?')} "
                     f"({_fmt_pct(c.get('delta'))} WoW)" + (" — " + ", ".join(parts) if parts else "") + ".")
    return lines


# ══════════════════════════════════════ EXPERIMENTS (A/B) ═══════════════════════════════════════
def _experiments_data() -> dict:
    """Deterministic read of the A/B lifecycle for the brief (running tests + today's decisions).
    Never raises — a missing module / empty experiments.json just yields empty lists."""
    try:
        from . import experiments
        return experiments.brief_data()
    except Exception:
        return {"running": [], "decisions_today": []}


def _rate_str(v):
    return "—" if v is None else f"{v:.1f}"


def _experiments_text(exp) -> list[str]:
    running, decided = exp.get("running") or [], exp.get("decisions_today") or []
    if not running and not decided:
        return []
    out = ["═══ EXPERIMENTS (A/B) ═══"]
    for r in running:
        out.append(f"• {r['id']} on {r.get('page','?')} · day {r.get('days',0)}/{r.get('max_days','?')} — "
                   f"A {_rate_str(r.get('a_rate'))} vs B {_rate_str(r.get('b_rate'))} leads/100 "
                   f"(A {r.get('a_sessions') or 0} / B {r.get('b_sessions') or 0} sessions)")
    for d in decided:
        verb = "PROMOTED B" if d.get("action") == "promote" else "REVERTED to control"
        lift = f", +{d['lift_pct']:.0f}%" if d.get("lift_pct") is not None else ""
        pv = f", p={d['p']}" if d.get("p") is not None else ""
        out.append(f"• DECIDED {d.get('id')}: {verb}{lift}{pv} — {d.get('reason','')}")
    out.append("")
    return out


def _experiments_html(exp) -> str:
    running, decided = exp.get("running") or [], exp.get("decisions_today") or []
    if not running and not decided:
        return ""
    rows = []
    for r in running:
        rows.append(
            f'<div style="background:{_PAPER};border:1px solid {_LINE};border-radius:10px;padding:12px 14px;margin-top:8px;">'
            f'<div style="font-family:{_SANS};color:{_INK};font-size:14px;font-weight:600;">{_esc(r["id"])}'
            f'<span style="color:{_MUTED};font-weight:400;font-size:12px;"> · {_esc(str(r.get("page","")))} · '
            f'day {r.get("days",0)}/{r.get("max_days","?")}</span></div>'
            f'<div style="margin-top:6px;font-size:13px;color:{_BODY};">'
            f'<b>A</b> {_rate_str(r.get("a_rate"))} &nbsp;vs&nbsp; <b>B</b> {_rate_str(r.get("b_rate"))} '
            f'<span style="color:{_MUTED};">leads / 100 visits</span>'
            f'<span style="color:{_MUTED};font-size:12px;"> &nbsp;(A {r.get("a_sessions") or 0} / B {r.get("b_sessions") or 0} sessions)</span></div></div>')
    for d in decided:
        promoted = d.get("action") == "promote"
        color = _GREEN if promoted else _RED
        verb = "Promoted B — winner baked in" if promoted else "Reverted to control"
        lift = f' &nbsp;+{d["lift_pct"]:.0f}%' if d.get("lift_pct") is not None else ""
        pv = f' &nbsp;p={d["p"]}' if d.get("p") is not None else ""
        rows.append(
            f'<div style="border-left:3px solid {color};background:{_CARD};border-radius:0 8px 8px 0;'
            f'padding:8px 12px;margin-top:8px;"><b style="color:{color};font-size:13px;">{_esc(str(d.get("id")))} — {verb}</b>'
            f'<span style="color:{_INK};font-size:13px;font-weight:700;">{lift}{pv}</span>'
            f'<div style="color:{_BODY};font-size:12px;margin-top:2px;">{_esc(str(d.get("reason","")))}</div></div>')
    return (f'<tr><td style="padding:16px 24px 2px;"><div style="font-family:{_SERIF};color:{_INK};font-size:13px;'
            f'font-weight:700;letter-spacing:.08em;text-transform:uppercase;">Experiments (A/B)</div>'
            f'<div style="color:{_MUTED};font-size:12px;margin-top:2px;">Every change proven on real traffic — '
            f'auto-promote winners, auto-revert losers.</div><div>{"".join(rows)}</div></td></tr>')


# ══════════════════════════════════════ HTML EMAIL ══════════════════════════════════════════════
def _delta_html(v):
    if v is None:
        return f'<span style="color:{_MUTED};font-size:13px;">— no prior week</span>'
    color = _GREEN if v >= 0 else _RED
    arrow = "▲" if v >= 0 else "▼"
    return f'<span style="color:{color};font-weight:700;font-size:14px;">{arrow} {abs(v):.0f}%</span>'


def _metric_cell(label, cur, delta, sub=""):
    cur = "—" if cur in (None, "?") else cur
    subline = f'<div style="color:{_MUTED};font-size:12px;margin-top:4px;">{_esc(sub)}</div>' if sub else ""
    return (
        f'<td width="50%" style="padding:6px;" valign="top">'
        f'<div style="background:{_PAPER};border:1px solid {_LINE};border-radius:12px;padding:16px 18px;">'
        f'<div style="color:{_MUTED};font-size:11px;letter-spacing:.12em;text-transform:uppercase;">{_esc(label)}</div>'
        f'<div style="font-family:{_SERIF};color:{_INK};font-size:30px;font-weight:700;line-height:1.1;margin:6px 0 4px;">{_esc(str(cur))}</div>'
        f'{_delta_html(delta)}{subline}</div></td>'
    )


def _scorecard_html(perf) -> str:
    if not perf.get("available"):
        return (f'<tr><td style="padding:4px 24px 8px;"><div style="background:{_PAPER};border:1px dashed {_LINE};'
                f'border-radius:12px;padding:16px 18px;color:{_MUTED};font-size:14px;">GA4 will populate here once '
                f'the property is granted read access.</div></td></tr>')
    if not perf.get("has_rows"):
        return (f'<tr><td style="padding:4px 24px 8px;"><div style="background:{_PAPER};border:1px dashed {_LINE};'
                f'border-radius:12px;padding:16px 18px;color:{_MUTED};font-size:14px;">📊 GA4 is connected — the '
                f'property is new and still gathering its first data. Metrics appear here as traffic builds.</div></td></tr>')
    s = perf.get("sessions") or {}
    c = perf.get("conversions") or {}
    conv_sub = " · ".join(f"{k.replace('_',' ')} {v}" for k, v in (c.get("breakdown") or {}).items())
    cells = _metric_cell("Sessions (7d)", s.get("cur"), s.get("delta"),
                         f"was {s.get('prev','—')} prior week" if s else "")
    cells += _metric_cell("Conversions (7d)", c.get("cur"), c.get("delta"), conv_sub)
    row1 = f'<tr><td style="padding:0 18px 6px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{cells}</tr></table></td></tr>'
    # Lead rate = THE objective (leads per 100 visits). Emphasized on the ink card.
    lr = perf.get("lead_rate") or {}
    lr_row = ""
    if lr.get("cur") is not None:
        lr_row = (
            f'<tr><td style="padding:0 24px 8px;"><div style="background:{_INK};border-radius:12px;padding:14px 18px;">'
            f'<span style="color:#a89f90;font-size:11px;letter-spacing:.12em;text-transform:uppercase;">Lead rate · the number we\'re growing</span>'
            f'<div style="margin-top:5px;"><span style="font-family:{_SERIF};color:#fff;font-size:26px;font-weight:700;">{lr["cur"]:.1f}</span>'
            f'<span style="color:#cfc8ba;font-size:13px;"> leads per 100 visits</span>&nbsp;&nbsp;{_delta_html(lr.get("delta"))}</div>'
            f'<div style="color:#8a8275;font-size:12px;margin-top:5px;">Goal: grow this — more of the right visitors converting, not just more traffic.</div>'
            f'</div></td></tr>')
    return row1 + lr_row


def _proposal_card_html(i, p) -> str:
    impact = _IMPACT.get(p.get("rule_id"), _DEFAULT_IMPACT)
    tgt = p.get("target") or {}
    where = ""
    if tgt.get("page_file"):
        where = tgt["page_file"] + (f" · {tgt['section']}" if tgt.get("section") else "")
    rows = ""
    if p.get("detail"):
        rows += f'<tr><td style="color:{_MUTED};font-size:12px;width:64px;padding:3px 0;" valign="top">Why</td><td style="color:{_BODY};font-size:14px;padding:3px 0;">{_esc(p["detail"])}</td></tr>'
    if where:
        rows += f'<tr><td style="color:{_MUTED};font-size:12px;padding:3px 0;" valign="top">Where</td><td style="color:{_BODY};font-size:14px;padding:3px 0;"><code style="background:{_PAPER};padding:1px 5px;border-radius:4px;">{_esc(where)}</code></td></tr>'
    rows += f'<tr><td style="color:{_MUTED};font-size:12px;padding:3px 0;" valign="top">Impact</td><td style="color:{_BODY};font-size:14px;padding:3px 0;">{_esc(impact)}</td></tr>'
    reply = (f'<div style="background:{_PAPER};border-radius:8px;padding:10px 12px;margin-top:12px;font-family:{_SANS};font-size:13px;color:{_INK};">'
             f'Reply&nbsp; <b style="color:{_GREEN};">"{i} approve"</b> &nbsp;·&nbsp; <b style="color:{_RED};">"{i} reject"</b> '
             f'&nbsp;·&nbsp; <b>"{i} &lt;your tweak&gt;"</b></div>')
    badge = (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
             f'<td style="background:{_EMBER};color:#fff;font-family:{_SERIF};font-weight:700;font-size:15px;'
             f'width:28px;height:28px;text-align:center;border-radius:50%;">{i}</td></tr></table>')
    return (
        f'<tr><td style="padding:8px 24px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:{_CARD};border:1px solid {_LINE};border-radius:12px;"><tr><td style="padding:16px 18px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td width="34" valign="top">{badge}</td>'
        f'<td valign="top" style="padding-left:8px;"><div style="font-family:{_SERIF};color:{_INK};font-size:17px;'
        f'font-weight:700;line-height:1.25;">{_esc(p["headline"])}</div>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;">{rows}</table>'
        f'{reply}</td></tr></table></td></tr></table></td></tr>'
    )


def _continuity(html=False):
    """Recap of what the owner recently asked for + how it turned out (from actions.jsonl)."""
    acts = model.load_actions()[-4:][::-1]
    if not acts:
        return "" if html else []
    labels = {"shipped": "shipped", "running": "running", "done": "done", "reverted": "reverted"}
    if not html:
        out = ["═══ SINCE YOUR LAST REPLY ═══"]
        for a in acts:
            tgt = (a.get("target") or {}).get("page_file") or ""
            st = labels.get(a.get("status"), a.get("status", ""))
            r = f" — {a['result']}" if a.get("result") else ""
            out.append(f"• {a.get('summary','(action)')}" + (f" · {tgt}" if tgt else "") + f"  [{st}]{r}")
        return out
    rows = ""
    for a in acts:
        tgt = (a.get("target") or {}).get("page_file") or ""
        st = labels.get(a.get("status"), a.get("status", ""))
        r = f' — {_esc(a["result"])}' if a.get("result") else ""
        rows += (f'<div style="color:{_BODY};font-size:13px;padding:3px 0;">'
                 f'<b style="color:{_INK};">{_esc(a.get("summary","action"))}</b>'
                 + (f' <span style="color:{_MUTED};">· {_esc(tgt)}</span>' if tgt else "")
                 + f' <span style="color:{_MUTED};">[{_esc(st)}]{r}</span></div>')
    return (f'<tr><td style="padding:14px 24px 4px;"><div style="font-family:{_SERIF};color:{_INK};font-size:13px;'
            f'font-weight:700;letter-spacing:.08em;text-transform:uppercase;">Since your last reply</div>'
            f'<div style="margin-top:6px;">{rows}</div></td></tr>')


def _build_html(subject, kind, perf, alerts, surface, watching, overflow, exp_data=None, wl=None) -> str:
    date_str = datetime.date.today().strftime("%A, %B %-d")
    wl = wl or {"shipped": [], "next": []}
    band = {"alert": _RED, "propose": _EMBER, "holding": _GREEN}.get(kind, _EMBER)
    if kind == "alert":
        verdict = f"{len(alerts)} thing(s) need a look" + (f" · {len(surface)} for your call" if surface else "")
    elif kind == "propose":
        verdict = f"Growth update · {len(surface)} quick call{'s' if len(surface)!=1 else ''} for you"
    else:
        verdict = "Growth update · nothing needs your input today"

    parts = []
    parts.append(f'<div style="background:{band};color:#fff;font-family:{_SANS};font-size:15px;font-weight:600;'
                 f'padding:14px 24px;">{_esc(verdict)}</div>')
    parts.append('<table role="presentation" width="100%" cellpadding="0" cellspacing="0">')
    # LEAD with the real work shipped (the brief's connection to reality)
    parts.append(_worklog_html(wl))
    # performance — honest read of the trajectory
    parts.append(f'<tr><td style="padding:18px 24px 6px;"><div style="font-family:{_SERIF};color:{_INK};font-size:13px;'
                 f'font-weight:700;letter-spacing:.08em;text-transform:uppercase;">How we\'re doing</div></td></tr>')
    parts.append(_scorecard_html(perf))
    _seo = _seo_weekly_line()
    if _seo:
        parts.append(f'<tr><td style="padding:2px 24px 8px;color:{_BODY};font-size:13px;font-family:{_SANS};">{_esc(_seo)}</td></tr>')
    parts.append(_next_html(wl))       # what's building next
    parts.append(_continuity(True))    # "Since your last reply" recap
    # alerts
    if alerts:
        parts.append(f'<tr><td style="padding:14px 24px 4px;"><div style="font-family:{_SERIF};color:{_RED};font-size:13px;'
                     f'font-weight:700;letter-spacing:.08em;text-transform:uppercase;">Needs attention</div></td></tr>')
        for a in alerts:
            d = f'<div style="color:{_BODY};font-size:13px;margin-top:3px;">{_esc(a["detail"])}</div>' if a.get("detail") else ""
            parts.append(f'<tr><td style="padding:2px 24px 8px;"><div style="border-left:3px solid {_RED};padding:6px 12px;'
                         f'background:{_CARD};border-radius:0 8px 8px 0;"><b style="color:{_INK};font-size:14px;">{_esc(a["headline"])}</b>{d}</div></td></tr>')
    # proposals
    if surface:
        parts.append(f'<tr><td style="padding:16px 24px 2px;"><div style="font-family:{_SERIF};color:{_INK};font-size:13px;'
                     f'font-weight:700;letter-spacing:.08em;text-transform:uppercase;">For your call</div>'
                     f'<div style="color:{_MUTED};font-size:12px;margin-top:2px;">Optional — nothing ships until you reply. Reply in plain words; I\'ll understand it.</div></td></tr>')
        for i, p in enumerate(surface, 1):
            parts.append(_proposal_card_html(i, p))
    # experiments (A/B) — running tests + today's decisions
    exp_html = _experiments_html(exp_data or {})
    if exp_html:
        parts.append(exp_html)
    # also today
    also = [f"• {w['headline']}" for w in watching] + [f"• (queued) {o['headline']}" for o in overflow]
    if not surface and not alerts:
        also.append("• Live-site guard (proof bar, platform section, canonical, JSON-LD): all holding.")
    if also:
        items = "".join(f'<div style="color:{_BODY};font-size:13px;padding:2px 0;">{_esc(x)}</div>' for x in also)
        parts.append(f'<tr><td style="padding:14px 24px 6px;"><div style="font-family:{_SERIF};color:{_MUTED};font-size:12px;'
                     f'font-weight:700;letter-spacing:.08em;text-transform:uppercase;">Also today — no action needed</div>'
                     f'<div style="margin-top:6px;">{items}</div></td></tr>')
    parts.append('</table>')

    # reply footer — plain-English, conversational (the loop now understands freeform replies)
    proto = ('<b>Just reply in plain English</b> — a question, a new direction ("focus more on catering"), '
             'an approval, or a tweak. I read every word, reply back with exactly what I understood and what '
             'I\'ll do, and log anything for the team. Nothing changes on the site without your say-so.')
    footer = (f'<div style="border-top:1px solid {_LINE};margin:8px 24px 0;"></div>'
              f'<div style="padding:14px 24px 22px;color:{_BODY};font-size:13px;line-height:1.55;">{proto}'
              f'<div style="color:{_MUTED};font-size:12px;margin-top:10px;">— {FROM_NAME}</div></div>')

    return (
        f'<!doctype html><html><body style="margin:0;padding:0;background:{_PAPER};">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_PAPER};padding:20px 0;"><tr><td align="center">'
        f'<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;'
        f'background:{_CARD};border:1px solid {_LINE};border-radius:14px;overflow:hidden;">'
        f'<tr><td style="height:4px;background:{_EMBER};"></td></tr>'
        f'<tr><td style="padding:20px 24px 4px;"><div style="font-family:{_SERIF};color:{_INK};font-size:20px;font-weight:700;">'
        f'AZ&nbsp;Restaurant&nbsp;Partners</div><div style="color:{_MUTED};font-size:13px;margin-top:2px;">Growth update · {date_str}</div></td></tr>'
        f'<tr><td style="padding:12px 0 0;">{"".join(parts)}</td></tr>'
        f'<tr><td>{footer}</td></tr>'
        f'</table>'
        f'<div style="color:{_MUTED};font-size:11px;font-family:{_SANS};padding:14px 0;">Private brief · azrestaurantpartners.com</div>'
        f'</td></tr></table></body></html>'
    )


def render_email(findings, signals=None) -> dict:
    signals = signals if signals is not None else []
    alerts, proposals, watching = _blocks(findings)
    surface = proposals[:3]
    overflow = proposals[3:]
    perf = _performance(signals)
    seo_line = _seo_weekly_line()
    if seo_line:
        perf = perf + [f"• {seo_line}"]
    perf_data = _performance_data(signals)
    exp_data = _experiments_data()
    wl = _worklog()
    kind = "alert" if alerts else ("propose" if surface else "holding")

    lines = []
    if alerts:
        verdict = f"⚠ {len(alerts)} thing(s) need a look" + (f", plus {len(surface)} for your call." if surface else ".")
    elif surface:
        verdict = f"Growth update — {len(surface)} quick call(s) for you, reply in plain words."
    else:
        verdict = "Growth update — here's what shipped, how we're doing, and what's next. Nothing needs your input today."
    lines.append(verdict)
    lines.append("")

    if wl.get("shipped"):
        lines.append("═══ RECENTLY SHIPPED ═══")
        for i in wl["shipped"]:
            lines.append(f"• {i['title']}")
            if i.get("detail"):
                lines.append(f"  {i['detail']}")
        lines.append("")
    if perf:
        lines.append("═══ HOW WE'RE DOING ═══")
        lines.extend(perf)
        lines.append("")
    if wl.get("next"):
        lines.append("═══ BUILDING NEXT ═══")
        for i in wl["next"]:
            lines.append(f"• [{(i.get('status') or 'next').upper()}] {i['title']}")
        lines.append("")
    _cont = _continuity(False)
    if _cont:
        lines.extend(_cont)
        lines.append("")
    if alerts:
        lines.append("═══ NEEDS ATTENTION ═══")
        for a in alerts:
            lines.append(f"• {a['headline']}")
            if a.get("detail"):
                lines.append(f"  {a['detail']}")
        lines.append("")
    if surface:
        lines.append("═══ PROPOSED CHANGES (reply to approve) ═══")
        lines.append("")
        for i, p in enumerate(surface, 1):
            impact = _IMPACT.get(p.get("rule_id"), _DEFAULT_IMPACT)
            tgt = p.get("target") or {}
            where = ""
            if tgt.get("page_file"):
                where = f"{tgt['page_file']}" + (f" · {tgt['section']}" if tgt.get("section") else "")
            lines.append(f"{i}) {p['headline']}")
            if p.get("detail"):
                lines.append(f"   Why:    {p['detail']}")
            if where:
                lines.append(f"   Where:  {where}")
            lines.append(f"   Impact: {impact}")
            lines.append(f'   Reply:  "{i} approve"  ·  "{i} reject"  ·  "{i} <your exact instruction>"')
            lines.append("")

    lines.extend(_experiments_text(exp_data))

    also = [f"• {w['headline']}" for w in watching] + [f"• (queued) {o['headline']}" for o in overflow]
    if not surface and not alerts:
        also.append("• Live-site guard (proof bar, platform section, canonical, JSON-LD): all holding.")
    if also:
        lines.append("═══ ALSO TODAY (no action needed) ═══")
        lines.extend(also)
        lines.append("")

    lines.append("──")
    lines.append('Just reply in plain English — a question, a new direction ("focus more on catering"), an '
                 'approval, or a tweak. I read every word, reply back with what I understood + what I\'ll do, '
                 'and log anything for the team. Nothing changes on the site without your say-so.')
    lines.append(f"— {FROM_NAME}")

    n_ship = len(wl.get("shipped") or [])
    subj_tag = (f"{len(surface)} for your call" if surface else
                (f"{n_ship} shipped recently" if n_ship else "all holding"))
    if alerts:
        subj_tag = f"{len(alerts)} to review · " + subj_tag
    subject = f"AZ Restaurant Partners — growth update: {subj_tag}"

    surfaced = [{"n": i + 1, "rule_id": p.get("rule_id"), "subject": p.get("subject"),
                 "headline": p.get("headline"), "target": p.get("target") or {}}
                for i, p in enumerate(surface)]
    html = _build_html(subject, kind, perf_data, alerts, surface, watching, overflow, exp_data, wl)
    return {"subject": subject, "body": "\n".join(lines), "html": html, "surfaced": surfaced,
            "counts": {"alerts": len(alerts), "proposals": len(proposals), "watching": len(watching)}}


def from_state() -> dict:
    return render_email(model.load_findings(), model.load_signals())


if __name__ == "__main__":
    e = from_state()
    print("SUBJECT:", e["subject"])
    print("=" * 64)
    print(e["body"])
    import pathlib
    pathlib.Path("growth_engine/state/_preview.html").parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path("growth_engine/state/_preview.html").write_text(e["html"], encoding="utf-8")
    print("\n[HTML preview written to growth_engine/state/_preview.html]")
