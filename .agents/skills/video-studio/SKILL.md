---
name: video-studio
description: Create, narrate, preview, edit, and render local product videos from Markdown scripts or recordings in this Video Studio repository.
---

# Video Studio

Read `AGENTS.md` and `docs/WORKFLOW.md` from the repository root. Follow the script → voice → scenes → lint → render → verify workflow there.

For setup, use `npm ci` and `npm run setup`. For a first video, use `npm run demo`. For a user script, use `npm run studio -- make --script scripts/<name>.md`. Inspect the generated composition and narration before describing the result as complete.

Keep assistant-specific configuration out of the engine. Preserve manual composition edits by using `render` rather than regenerating. Explain any actual missing dependency or failed check plainly.

For online rendering or GitHub Pages, read `docs/ONLINE.md`. Dispatch `render.yml` with a unique request label, verify that exact run, and download its artifact. Publishing is opt-in; this public repository is not suitable for confidential scripts or media.
