#!/bin/sh
# Manual publish of this repo to the Cloudflare Worker "azrestaurantpartners" (docs/49 in the Wok repo).
# Normally Cloudflare Workers Builds does this on every push to main: build command
# `sh deploy/cloudflare/stage.sh`, deploy command `npx wrangler deploy -c deploy/cloudflare/wrangler.toml`.
# Needs a wrangler login on this machine.
set -eu
cd "$(dirname "$0")"
sh ./stage.sh "${1:-}"
npx -y wrangler@4 deploy -c wrangler.toml
