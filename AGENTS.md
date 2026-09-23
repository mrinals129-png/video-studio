# Video Studio

This repository turns Markdown scripts and optional screenshots or recordings into local narrated MP4s. Explain actions and results in plain language.

## Start here

- Read `docs/WORKFLOW.md` for production steps and supported commands.
- `npm ci`, then `npm run setup` installs project-local dependencies. Node 22+ and Python 3.10–3.12 are required.
- `npm run demo` creates the sample video; `npm run preview` opens its local editing server.
- `npm test` checks parsing, escaping, timing, and media validation.
- Use `npm run studio -- ...` to get the project's Python environment and portable media tools. Do not assume Homebrew, nvm, a global HyperFrames install, or a particular shell.

## Working rules

- Work from the repository root. Preserve the user's source recordings and scripts.
- Read `transcript.json` before editing scene timing. Word timestamps are estimates, not speech alignment. Verify timing against the voice track.
- Regenerating a composition replaces manual edits: use `studio render` to render edits and `make --force` only when regeneration is intended.
- Use local assets, `brand.css` tokens, paused GSAP timelines, and explicit composition duration. Keep assets inside the composition so rendering does not depend on external paths.
- Never report a finished video until lint, rendering, media-stream checks, and a full decode pass. Inspect representative frames for clipped text, missing assets, and transition problems.
- Generated media, models, credentials, and personal source assets are ignored. Stage only reviewed source files. Never publish the original import or its Git history.
- Do not install global assistant settings, auto-approve tool permissions, or add paid cloud services as part of setup.

## Main files

- `studio.py`: make, render, preview, verify, and dependency checks.
- `_engine/tts/generate.py`: local Kokoro narration and estimated transcript timing.
- `_engine/templates/`: reusable scene designs and brand tokens.
- `_engine/overlay/generate.py`: advanced recording overlay builder.
- `tooling/`: cross-platform bootstrap and Python launcher.

After changing generation code, run unit tests and a real sample render. Keep README claims consistent with verified behavior.
