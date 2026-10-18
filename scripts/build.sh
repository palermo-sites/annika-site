#!/usr/bin/env bash
# Builds the Astro site into _site/ (astro.config.mjs outDir). BASE_PATH sets the base path when served under one.
set -euo pipefail
cd "$(dirname "$0")/.."
npm ci --no-audit --no-fund
npx astro build
echo "built _site/"
