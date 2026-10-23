#!/usr/bin/env python3
"""Build the v3 pages: inject the shared tracking script and write index.html and start/index.html."""
import pathlib
HERE=pathlib.Path(__file__).parent; REPO=HERE.parent
track=(REPO/"v2/track.js").read_text()
pages={"home-min-src.html":("index.html","home_v4"),"start-src.html":("start/index.html","start_v1")}
for src,(out,pid) in pages.items():
    html=(HERE/src).read_text().replace("__TRACKING__",track.replace("__PAGEID__",pid))
    (REPO/out).parent.mkdir(parents=True,exist_ok=True)
    (REPO/out).write_text(html)
    print(out,"written")
