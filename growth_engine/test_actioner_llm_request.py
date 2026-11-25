"""The actioner's Claude request must be one the API accepts (2026-11-25).

Opus 4.8 and Haiku 5.5 both answer 400 "temperature is deprecated for this model", so a request with
`temperature` failed on the primary AND the fallback. No network here.
Run: python3 -m pytest growth_engine/test_actioner_llm_request.py  (or python3 this file)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from growth_engine import actioner_llm as A  # noqa: E402

RETIRED = ("claude-3", "claude-sonnet-4-5", "claude-2")


def test_no_retired_model_ids():
    for m in (A.MODEL, A.FALLBACK_MODEL):
        assert not any(r in m for r in RETIRED), m
    assert A.FALLBACK_MODEL == "claude-haiku-5-5"


def test_no_temperature_on_either_model():
    for m in (A.MODEL, A.FALLBACK_MODEL):
        b = A.request_body(m, "sys", "user")
        assert "temperature" not in b and "top_p" not in b and "top_k" not in b, b
        assert b["model"] == m and b["max_tokens"] == A.MAX_TOKENS


def test_haiku_5_5_spends_its_budget_on_the_answer():
    assert A.request_body("claude-haiku-5-5", "s", "u")["thinking"] == {"type": "disabled"}
    assert "thinking" not in A.request_body("claude-opus-4-8", "s", "u")


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f()
            print("ok", n)
