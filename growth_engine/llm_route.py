"""Copied from WokAndKarahiTexas.com voice-agent/src/llm_route.py - keep the two in step.

NOTHING STOPS IF THE ANTHROPIC ACCOUNT STOPS (owner, 2026-10-24: "make sure that the website, all
services, Haniya app, every single thing works, even if this account is gone for days").

Every Claude call in this repo is a plain POST to api.anthropic.com/v1/messages. OpenRouter serves the same
request body, the same model names and the same answer shape at openrouter.ai/api/v1/messages (verified live
2026-10-24 for claude-haiku-5-5, claude-sonnet-5-5, anthropic/claude-opus-5.5, claude-haiku-4-5-20251001).
So the backup is a different door to the same models, not a different brain.

`install()` puts one opener in front of urllib for the whole process. Any request to api.anthropic.com:
  - goes to Anthropic first, as today;
  - on an account failure (401/403, or 400/402/429 naming billing, credit or usage limits) it is sent again,
    unchanged, to OpenRouter, and Anthropic is skipped for HARD_HOLD (the account is likely gone);
  - on an outage (5xx, 529, connection error, timeout) it is sent again to OpenRouter, and Anthropic is skipped
    for SOFT_HOLD;
  - any other error (a bad request) is handed back as it came, since a second door would fail the same way.
Every other URL passes through untouched.

LLM_ROUTE=openrouter sends everything to OpenRouter; LLM_ROUTE=anthropic turns the backup off.
Key: OPENROUTER_API_KEY, else RELAY_BACKUP_OPENROUTER_KEY. With no key, behaviour is exactly as before.
"""
from __future__ import annotations

import io
import os
import socket
import threading
import time
import urllib.error
import urllib.request

ANTHROPIC_HOST = "api.anthropic.com"
BACKUP_URL = "https://openrouter.ai/api/v1/messages"
HARD_HOLD = 30 * 60
SOFT_HOLD = 3 * 60
_HARD_WORDS = ("credit balance", "billing", "usage limit", "insufficient", "quota", "disabled",
               "suspended", "permission", "invalid x-api-key", "authentication")

_lock = threading.Lock()
_st = {"skip_until": 0.0, "why": "", "backup_calls": 0, "last_switch": 0.0}


def backup_key() -> str:
    return (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("RELAY_BACKUP_OPENROUTER_KEY") or "").strip()


def _mode() -> str:
    return os.environ.get("LLM_ROUTE", "").strip().lower()


def state() -> dict:
    """For health pages: which door Claude calls use right now, and why."""
    with _lock:
        s = dict(_st)
    s["using"] = "openrouter" if (_mode() == "openrouter" or time.time() < s["skip_until"]) else "anthropic"
    s["backup_ready"] = bool(backup_key())
    return s


def _note(why: str, hold: float) -> None:
    with _lock:
        first = time.time() >= _st["skip_until"]
        _st["skip_until"] = time.time() + hold
        _st["why"] = why
        if first:
            _st["last_switch"] = time.time()
    if first:
        try:
            import obslog
            obslog.record("llm_route.switch", f"Anthropic -> OpenRouter for {int(hold / 60)} min: {why}")
        except Exception:                                            # noqa: BLE001
            pass


def is_hard(code: int, body: str) -> bool:
    b = str(body or "").lower()
    return code in (401, 403) or (code in (400, 402, 429) and any(w in b for w in _HARD_WORDS))


def is_outage(code: int) -> bool:
    return code >= 500


def _to_backup(req: urllib.request.Request) -> urllib.request.Request:
    """The same request, sent to OpenRouter with the backup key. Body untouched."""
    hdrs = {k: v for k, v in req.header_items() if k.lower() not in ("x-api-key", "authorization", "host")}
    hdrs["x-api-key"] = backup_key()
    return urllib.request.Request(BACKUP_URL, data=req.data, headers=hdrs, method=req.get_method())


def _replay(e: urllib.error.HTTPError, body: bytes) -> urllib.error.HTTPError:
    """An HTTPError whose body can still be read by the caller (we read it to decide)."""
    return urllib.error.HTTPError(e.url, e.code, e.msg, e.hdrs, io.BytesIO(body))


class FailoverOpener(urllib.request.OpenerDirector):
    """urllib's default opener plus the Anthropic -> OpenRouter backup."""

    def open(self, fullurl, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):  # noqa: D401
        req = fullurl if isinstance(fullurl, urllib.request.Request) else urllib.request.Request(fullurl, data)
        if data is not None and isinstance(fullurl, urllib.request.Request):
            req.data = data
        if req.host != ANTHROPIC_HOST or _mode() == "anthropic" or not backup_key():
            return super().open(req, timeout=timeout)
        if _mode() == "openrouter" or time.time() < _st["skip_until"]:
            with _lock:
                _st["backup_calls"] += 1
            return super().open(_to_backup(req), timeout=timeout)
        try:
            return super().open(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read()
            except Exception:                                        # noqa: BLE001
                pass
            text = body.decode("utf-8", "replace")
            if is_hard(e.code, text):
                _note(f"http {e.code} {text[:120]}", HARD_HOLD)
            elif is_outage(e.code):
                _note(f"http {e.code}", SOFT_HOLD)
            else:
                raise _replay(e, body) from None
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            _note(f"{type(e).__name__}: {str(e)[:120]}", SOFT_HOLD)
        with _lock:
            _st["backup_calls"] += 1
        return super().open(_to_backup(req), timeout=timeout)


_installed = False


def install() -> None:
    """Put the backup in front of urllib.request.urlopen for this whole process. Safe to call twice."""
    global _installed
    if _installed:
        return
    base = urllib.request.build_opener()
    op = FailoverOpener()
    for h in base.handlers:
        op.add_handler(h)
    urllib.request.install_opener(op)
    _installed = True
