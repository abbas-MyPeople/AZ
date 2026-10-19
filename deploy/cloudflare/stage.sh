#!/bin/sh
# Stage the site into _site: a clean export of one commit (default: origin/main when it exists, else HEAD),
# minus .github. The same files GitHub Pages serves from main. Cloudflare Workers Builds runs this as the
# build command on every push to main; publish.sh runs it for a manual publish.
set -eu
cd "$(dirname "$0")/../.."
ref="${1:-}"
if [ -z "$ref" ]; then
  if git rev-parse -q --verify origin/main >/dev/null; then ref=origin/main; else ref=HEAD; fi
fi
rm -rf _site && mkdir _site
git archive "$ref" | tar -x -C _site
rm -rf _site/.github
echo "staged $(find _site -type f | wc -l | tr -d ' ') files from $ref"
