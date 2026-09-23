# Add overlays to a recording

> Read AGENTS.md and docs/WORKFLOW.md. Use assets/my-recording.mp4 with scripts/my-feature.md. Add captions and a lower-third, and position callouts or a spotlight only where they help explain the recording. Build the overlay composition, inspect and tune its timing against the narration, render it, and verify the result.

The advanced builder is available from either assistant:

```sh
node tooling/run-python.cjs _engine/overlay/generate.py --video assets/my-recording.mp4 --script scripts/my-feature.md --out compositions/my-feature --tts
npm run studio -- render compositions/my-feature --output output/my-feature.mp4
```

Optional flags: `--voice bf_emma`, `--video-start 2`, `--video-volume 0.15`, `--no-intro`, `--no-outro`. This builder regenerates `index.html`; preserve manual edits before rerunning. The recording must cover the narrated content after trimming. Default captions use evenly spaced slots; tune them by listening. Callout/spotlight positions are starting values, not automatic UI recognition.
