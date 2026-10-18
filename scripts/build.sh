#!/usr/bin/env bash
# Builds the site into _site/. Replace the body with your generator's build; keep the output folder.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf _site
cp -r site _site
echo "built _site/"
