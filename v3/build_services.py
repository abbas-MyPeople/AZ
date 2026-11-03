#!/usr/bin/env python3
"""Build /services/ alone. build.py also rewrites the home and /start, whose outputs have newer hand edits."""
import pathlib
HERE=pathlib.Path(__file__).parent; REPO=HERE.parent
track=(REPO/"v2/track.js").read_text().replace("__PAGEID__","services_v1")
(REPO/"services/index.html").write_text((HERE/"services-src.html").read_text().replace("__TRACKING__",track))
print("services/index.html written")
