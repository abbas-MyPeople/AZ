#!/usr/bin/env python3
"""Build the v3 home page: inject the shared tracking script and write index.html."""
import pathlib
HERE=pathlib.Path(__file__).parent; REPO=HERE.parent
src=(HERE/"home-src.html").read_text()
track=(REPO/"v2/track.js").read_text().replace("__PAGEID__","home_v3")
(REPO/"index.html").write_text(src.replace("__TRACKING__",track))
print("index.html written")
