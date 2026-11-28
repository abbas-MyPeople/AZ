#!/usr/bin/env python3
"""Find independent restaurants across Greater Houston from free, open data.

Source: OpenStreetMap through the public Overpass API (free, keyless, open licence,
attribution "OpenStreetMap contributors"). Google Places would be fuller but bills past
its free tier, so it stays off until the owner approves a capped key.

Chains are dropped (OSM `brand` / `brand:wikidata` tags, plus a short name list), because a
franchise cannot change its own menu, site or ordering (ARCHITECTURE.md 13.1).

    python3 -m outreach.intel.discover --area spring --out outreach/intel/targets/spring.json
    python3 -m outreach.intel.discover --bbox 29.5,-95.9,30.2,-95.0 --cuisine indian,pakistani

Every target carries where it came from and when, like every other field in this engine.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

OVERPASS = "https://overpass-api.de/api/interpreter"
UA = "AZRestaurantPartners-intel/1.0 (+https://azrestaurantpartners.com)"

# south, west, north, east
AREAS = {
    "houston": (29.52, -95.80, 30.15, -95.05),
    "spring": (29.98, -95.55, 30.12, -95.33),
    "cypress": (29.90, -95.75, 30.05, -95.55),
    "woodlands": (30.10, -95.60, 30.25, -95.40),
    "katy": (29.70, -95.90, 29.85, -95.70),
    "sugar-land": (29.53, -95.70, 29.66, -95.55),
    "humble": (29.95, -95.30, 30.10, -95.15),
}
CHAINS = {"mcdonald's", "subway", "starbucks", "chick-fil-a", "taco bell", "wendy's",
          "burger king", "domino's", "pizza hut", "panda express", "chipotle", "whataburger",
          "sonic", "jack in the box", "popeyes", "kfc", "wingstop", "dairy queen",
          "little caesars", "papa john's", "raising cane's", "olive garden", "ihop",
          "denny's", "applebee's", "chili's", "buffalo wild wings", "five guys", "jersey mike's"}


def query(bbox, cuisines=None) -> str:
    s, w, n, e = bbox
    flt = ""
    if cuisines:
        flt = '["cuisine"~"' + "|".join(cuisines) + '",i]'
    return (f'[out:json][timeout:90];('
            f'nwr["amenity"~"^(restaurant|fast_food|cafe)$"]{flt}({s},{w},{n},{e});'
            f');out center tags;')


def fetch(q: str) -> dict:
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(OVERPASS, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def is_chain(tags: dict) -> bool:
    if tags.get("brand") or tags.get("brand:wikidata"):
        return True
    return (tags.get("name") or "").strip().lower() in CHAINS


def to_target(el: dict, seen_at: str) -> dict | None:
    t = el.get("tags", {})
    name = t.get("name")
    if not name or is_chain(t):
        return None
    lat = el.get("lat") or (el.get("center") or {}).get("lat")
    lon = el.get("lon") or (el.get("center") or {}).get("lon")
    addr = " ".join(x for x in (t.get("addr:housenumber"), t.get("addr:street"),
                                t.get("addr:city"), t.get("addr:postcode")) if x)
    return {
        "name": name,
        "slug": slugify(f"{name} {t.get('addr:city') or ''}"),
        "cuisine": [c.strip() for c in (t.get("cuisine") or "").split(";") if c.strip()],
        "address": addr or None,
        "phone": t.get("phone") or t.get("contact:phone"),
        "website": t.get("website") or t.get("contact:website"),
        "lat": lat, "lon": lon,
        "diet_halal": t.get("diet:halal"),
        "source": {"url": f"https://www.openstreetmap.org/{el['type']}/{el['id']}",
                   "title": "OpenStreetMap contributors", "observed_at": seen_at},
    }


def slugify(s: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in s)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def dedupe(targets: list[dict]) -> list[dict]:
    """Same name within ~150 m is the same place mapped twice."""
    keep: list[dict] = []
    for t in targets:
        dup = next((k for k in keep if k["name"].lower() == t["name"].lower()
                    and t["lat"] and k["lat"]
                    and abs(k["lat"] - t["lat"]) < 0.0015 and abs(k["lon"] - t["lon"]) < 0.0015), None)
        if dup is None:
            keep.append(t)
        else:
            for f in ("website", "phone", "address"):
                dup[f] = dup[f] or t[f]
    return keep


def discover(bbox, cuisines=None, fetcher=fetch) -> list[dict]:
    seen_at = datetime.now(timezone.utc).date().isoformat()
    raw = fetcher(query(bbox, cuisines))
    out = [t for t in (to_target(e, seen_at) for e in raw.get("elements", [])) if t]
    out = dedupe(out)
    # the ones we can research deepest first: a website, then a phone
    out.sort(key=lambda t: (not t["website"], not t["phone"], t["name"].lower()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", choices=sorted(AREAS))
    ap.add_argument("--bbox", help="south,west,north,east")
    ap.add_argument("--cuisine", help="comma list, e.g. indian,pakistani,chinese")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    bbox = tuple(float(x) for x in a.bbox.split(",")) if a.bbox else AREAS[a.area or "houston"]
    cuisines = [c.strip() for c in a.cuisine.split(",")] if a.cuisine else None
    t0 = time.time()
    found = discover(bbox, cuisines)
    path = pathlib.Path(a.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"bbox": bbox, "cuisines": cuisines, "count": len(found),
                                "licence": "Data (c) OpenStreetMap contributors, ODbL",
                                "targets": found}, indent=1, ensure_ascii=False))
    print(f"{len(found)} independent restaurants in {time.time() - t0:.1f}s -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
