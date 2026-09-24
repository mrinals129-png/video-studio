#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f compositions/hello-studio/index.html ]; then
  echo "Sample is not ready. Run bash .devcontainer/setup.sh, then bash .devcontainer/start.sh."
  exit 1
fi

# HyperFrames reuses the managed preview when it is already running.
node node_modules/hyperframes/bin/hyperframes.mjs preview compositions/hello-studio \
  --port 3002 --background --no-open
echo "Open Video Studio editor (port 3002) in the Ports panel. Keep its visibility Private."
