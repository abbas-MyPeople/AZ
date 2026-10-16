#!/usr/bin/env python3
"""Build the secondary pages in the new home's style (investors, case study, demo, details).

The home itself is built by v3/build.py and is not touched here. These pages share:
  base.css      a copy of the home's styles (v3/home-src.html) - keep in step with the home
  lead-form.js  the home's inquiry form code, same gateway endpoint (az-lead)
Placeholders: __BASECSS__, __LEADFORM__, __TRACKING__ (v2/track.js with the page id).
"""
import pathlib
HERE = pathlib.Path(__file__).parent
REPO = HERE.parent
TRACK = (REPO / "v2/track.js").read_text()
BASE = (HERE / "base.css").read_text()
FORM = (HERE / "lead-form.js").read_text()

PAGES = [
    ("investors-src.html", "investors.html", "investors_v3"),
    ("case-study-src.html", "case-study.html", "case_study_v3"),
    ("demo-src.html", "demo.html", "demo_v3"),
    ("details-src.html", "details.html", "details_v3"),
]

for src, out, page in PAGES:
    s = (HERE / src).read_text()
    s = (s.replace("__BASECSS__", BASE)
          .replace("__LEADFORM__", FORM)
          .replace("__TRACKING__", TRACK.replace("__PAGEID__", page)))
    for ph in ("BASECSS", "LEADFORM", "TRACKING"):
        assert "__%s__" % ph not in s, (out, ph)
    (REPO / out).write_text(s)
    print(out, "written")
