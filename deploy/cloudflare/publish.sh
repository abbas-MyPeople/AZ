#!/bin/sh
# Publish main of this repo to the Cloudflare Worker "azrestaurantpartners" (docs/49 in the Wok repo).
# Same files GitHub Pages serves: a clean export of main, never the working tree, never .github.
# Needs CLOUDFLARE_API_TOKEN (or a wrangler login) and CLOUDFLARE_ACCOUNT_ID.
set -eu
cd "$(dirname "$0")/../.."
rm -rf _site && mkdir _site
git archive "${1:-origin/main}" | tar -x -C _site
rm -rf _site/.github
cd deploy/cloudflare && npx -y wrangler@4 deploy
