#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

npm ci
npm run setup
npm run doctor
npm test

# Rebuilds must preserve any manual edits to an existing composition.
if [ ! -d compositions/hello-studio ]; then
  npm run studio -- make --script scripts/hello-studio.md --build-only
fi
