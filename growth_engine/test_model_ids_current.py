"""Model ids that leave their provider stay out of the growth engine (2026-11-25).

OpenRouter listed google/gemini-2.5-flash with expiration 2026-12-01; google/gemini-3.8-flash was on
its live list with none. claude-3-5-haiku-latest already 404s on Anthropic. No network.
Run: python3 -m pytest growth_engine/test_model_ids_current.py
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
GONE = ("google/gemini-2.5-flash", "claude-3-5-haiku", "claude-3-", "claude-sonnet-4-5")


def _code(name):
    lines = (HERE / name).read_text(encoding="utf-8").splitlines()
    return "\n".join(ln for ln in lines if not ln.lstrip().startswith("#"))


def test_no_gone_ids():
    for name in ("seo_measure.py", "actioner_llm.py", "reply_agent.py", "sensors/ai_visibility.py"):
        code = _code(name)
        for gone in GONE:
            assert gone not in code, f"{name} still calls {gone}"


def test_gemini_is_the_current_flash_with_live_web():
    assert '"google/gemini-3.8-flash:online"' in _code("seo_measure.py")
