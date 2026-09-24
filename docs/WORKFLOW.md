# Making a video

Open this repository in Codex or Claude Code. Codex reads `AGENTS.md` and discovers `.agents/skills/video-studio`; Claude Code reads `CLAUDE.md` and exposes `/video-studio` from `.claude/skills/video-studio`. Both use this workflow.

To use GitHub's compute instead of the local renderer, follow [ONLINE.md](ONLINE.md). The optional Pages deployment publishes a playable MP4 after a successful render.

1. Copy `SCRIPT-TEMPLATE.md` into `scripts/your-feature.md`. Fill in the title, product, tagline, and narration. Animation notes guide the assistant; the command-line generator does not interpret them automatically.
2. Run `npm run studio -- make --script scripts/your-feature.md`. This generates local speech, builds three animated scenes, checks the HTML, renders an MP4, and verifies its audio/video streams and decoding.
3. Open `output/your-feature.mp4`. Use `npm run studio -- preview compositions/your-feature` to inspect the timeline in your browser.
4. Ask your assistant to refine the HTML, timing, or colors. Rerender with `npm run studio -- render compositions/your-feature --output output/your-feature.mp4`.

`--build-only` creates the composition without rendering. To deliberately rebuild after changing narration or voice, add `--force`; this replaces the generated HTML, so preserve any manual scene edits first.

## Screenshots and recordings

Place assets in `assets/` (ignored by Git). Add one of:

```text
npm run studio -- make --script scripts/your-feature.md --image assets/screenshot.png
npm run studio -- make --script scripts/your-feature.md --video assets/recording.mp4 --video-start 2 --video-volume 0.1
```

The recording appears in the middle scene; title and closing scenes surround it. The trim value is seconds into the source video. The recording must cover the whole middle scene; the command reports a clear error if it is too short. The original sound is muted unless `--video-volume` is set (0–1). Assets are copied into the composition so paths work on all supported platforms.

For full-frame recordings with captions, callouts, spotlight, intro/outro, and lower-third, use `_engine/overlay/generate.py` through `node tooling/run-python.cjs`. See `prompts/overlay-a-video.md`.

## Voice and timing

Choose `--voice af_heart` (default), `am_adam`, `bf_emma`, or `bm_george`. British voices use British English phonemization. Kokoro runs locally after initial setup. The generated `transcript.json` uses character-proportional word timing: these are estimates, not exact word alignment. Listen to the narration when adjusting captions and scene boundaries.

The default layout suits short scripts (roughly 30–80 words) and needs at least six seconds of narration. Longer scripts need extra scenes or shorter on-screen summaries, authored by the assistant.

## Quality checks

Run `npm test` after changing code. For each deliverable, lint and render, verify video and audio exist, decode the entire export, then inspect frames from the title, middle, closing, and transitions. Check text fit and narration timing; a successful render alone does not prove visual quality.

HyperFrames captures paused GSAP timelines. Register the timeline on `window.__timelines` using the composition ID, specify duration, and keep animations deterministic under seeks. The generated scenes use local GSAP and system fonts, with no font/CDN dependency.

## Troubleshooting

- Run `npm run setup` for missing Python libraries or models; it is safe to rerun.
- `npm run doctor` reports project dependencies. Rendering needs working Chrome/Chromium; HyperFrames can install its browser with `npx hyperframes browser ensure`.
- Close memory-heavy applications if rendering fails with low available RAM. The studio uses one render worker.
- On Windows, use `npm.cmd` if PowerShell blocks `npm.ps1`.
- HyperFrames' own optional cloud/music/transcription checks are separate from this studio's local voice engine.
- No API key is needed for this workflow. Assistant subscriptions, if applicable, are separate.
