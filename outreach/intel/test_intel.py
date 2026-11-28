"""python3 -m pytest outreach/intel/test_intel.py -q   (or: python3 -m outreach.intel.test_intel)"""
import copy
import json
import pathlib
import tempfile
from datetime import date

from outreach.intel import discover, model, render

SLUG = "wok-and-karahi-spring"
BASE = json.loads((model.PROFILES / f"{SLUG}.json").read_text())


def test_seed_profile_is_fit_to_show():
    assert model.validate(BASE) == []


def test_a_fact_without_a_source_is_refused():
    p = copy.deepcopy(BASE)
    p["findings"][0]["evidence"] = []
    assert any("needs evidence" in e for e in model.validate(p))


def test_a_guess_must_say_what_only_the_owner_knows():
    p = copy.deepcopy(BASE)
    g = next(f for f in p["findings"] if f["kind"] == "hypothesis")
    g.pop("open_question")
    g["confidence"] = 1.0
    errs = model.validate(p)
    assert any("confidence below 1" in e for e in errs)
    assert any("open question" in e for e in errs)


def test_a_pattern_must_cross_two_dimensions():
    p = copy.deepcopy(BASE)
    p["patterns"][0]["finding_ids"] = ["f-cuisine"]
    assert any("two dimensions" in e for e in model.validate(p))


def test_scenarios_never_guarantee_and_label_every_number():
    p = copy.deepcopy(BASE)
    o = next(o for o in p["opportunities"] if o.get("scenario"))
    o["scenario"]["assumptions"].append({"label": "Avg ticket", "value": 30})
    o["scenario"]["result_text"] = "Guaranteed $3,000 more"
    errs = model.validate(p)
    assert any("needs a source" in e for e in errs)
    assert any("never guarantee" in e for e in errs)


def test_em_dashes_are_refused():
    p = copy.deepcopy(BASE)
    p["headline"]["insight"] = "Rare combo — halal"
    assert any("dash" in e for e in model.validate(p))


def test_recency_weighting():
    now = date(2026, 11, 28)
    assert model.recency_weight("2026-10-01", now) == 1.0
    assert model.recency_weight("2026-02-01", now) == 0.6
    assert model.recency_weight("2024-06-01", now) == 0.25
    assert model.is_stale("2024-06-01", now)


def test_owner_events_replay_and_ripple():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / f"{SLUG}.json").write_text(json.dumps(BASE))
        evs = [
            {"id": "e1", "target": "f-cuisine", "action": "confirm", "by": "owner", "at": "2026-11-28T20:00:00Z"},
            {"id": "e2", "target": "f-group-demand", "action": "challenge", "note": "Mostly walk-ins, few groups",
             "by": "owner", "at": "2026-11-28T20:01:00Z"},
            {"id": "e3", "target": "f-crispy-beef", "action": "correct", "note": "Chilli chicken outsells it now",
             "by": "owner", "at": "2026-11-28T20:02:00Z"},
            {"id": "e4", "target": "u-trays", "action": "answer", "note": "About 6", "by": "owner",
             "at": "2026-11-28T20:03:00Z"},
        ]
        assert model.ingest(SLUG, evs, root) == 4
        assert model.ingest(SLUG, evs, root) == 0            # same ids are never applied twice
        p = model.load(SLUG, root)
        f = {x["id"]: x for x in p["findings"]}
        assert f["f-cuisine"]["status"] == "confirmed" and f["f-cuisine"]["weight"] == 1.0
        assert f["f-group-demand"]["status"] == "challenged" and f["f-group-demand"]["confidence"] == 0.25
        assert f["f-crispy-beef"]["claim"] == "Chilli chicken outsells it now"
        assert f["f-crispy-beef"]["was"][0]["claim"].startswith("The restaurant leads")
        assert f["f-group-demand"]["evidence"][-1]["url"] == "owner"
        assert next(u for u in p["unknowns"] if u["id"] == "u-trays")["answer"] == "About 6"
        pats = {x["id"]: x for x in p["patterns"]}
        assert pats["p-one-order-everyone"]["on_hold"] is True
        # the base file is never rewritten; the history is all in the events
        assert json.loads((root / f"{SLUG}.json").read_text()) == BASE


def test_a_bad_event_writes_nothing():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / f"{SLUG}.json").write_text(json.dumps(BASE))
        try:
            model.ingest(SLUG, [{"id": "x", "target": "nope", "action": "confirm"}], root)
        except KeyError:
            pass
        assert not (root / f"{SLUG}.events.jsonl").exists() or \
            (root / f"{SLUG}.events.jsonl").read_text() == ""


def test_page_has_every_layer_and_no_internal_words():
    page = render.render(model.load(SLUG))
    for sid in ('id="l2"', 'id="l3"', 'id="l4"', 'id="l5"', "noindex"):
        assert sid in page
    assert BASE["headline"]["insight"].split(".")[0] in page
    low = page.lower()
    for word in ("confidence", "hypothesis", "inference", "dimension", "tier"):
        assert word not in low.split("<script>")[0].replace('class="', ""), word
    assert "—" not in page and "–" not in page


def test_discovery_drops_chains_and_duplicates():
    raw = {"elements": [
        {"type": "node", "id": 1, "lat": 30.07, "lon": -95.47,
         "tags": {"amenity": "restaurant", "name": "Wok & Karahi", "cuisine": "chinese;pakistani",
                  "addr:city": "Spring", "website": "https://wokandkarahitexas.com"}},
        {"type": "way", "id": 2, "center": {"lat": 30.0705, "lon": -95.4705},
         "tags": {"amenity": "restaurant", "name": "Wok & Karahi", "phone": "+1 281 362 5354"}},
        {"type": "node", "id": 3, "lat": 30.0, "lon": -95.4,
         "tags": {"amenity": "fast_food", "name": "Subway"}},
        {"type": "node", "id": 4, "lat": 30.0, "lon": -95.4,
         "tags": {"amenity": "fast_food", "name": "Some Burger", "brand": "Some Burger"}},
    ]}
    got = discover.discover((29, -96, 31, -95), fetcher=lambda q: raw)
    assert [t["name"] for t in got] == ["Wok & Karahi"]
    assert got[0]["phone"] == "+1 281 362 5354" and got[0]["cuisine"] == ["chinese", "pakistani"]
    assert got[0]["source"]["url"].startswith("https://www.openstreetmap.org/")


if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("ok  ", name)
            except Exception as e:  # noqa: BLE001
                fails += 1
                print("FAIL", name, repr(e))
    sys.exit(1 if fails else 0)
