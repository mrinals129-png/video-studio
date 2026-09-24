# Verification

Local checks on 23 September 2026, Windows x64, Node 24.15.0, Python 3.11.9:

- Project-local dependency installation completed; npm reported no known vulnerabilities.
- Local Kokoro narration generated from the neutral sample script.
- Sample MP4 rendered at 1920 × 1080, 30 fps, approximately 12.47 seconds.
- Export contained H.264 video and AAC audio; full FFmpeg decoding passed.
- Title, middle, closing, and transition frames inspected.
- HyperFrames browser preview loaded with scene and narration tracks; playback and seeking worked.
- Full-frame recording overlays rendered with a one-second source trim, title/closing cards, captions, callout, spotlight, and lower-third. The MP4 passed audio/video and full-decode checks; overlay lint had no errors or warnings.
- Unit tests cover narration-only parsing, Unicode/Windows newlines, missing narration, empty speech, bounded timing, HTML escaping, portable media paths, recording trim/length checks, and matching assistant skills.

The feature template uses three inline sub-compositions with local animation timing. Both feature and overlay compositions pass HyperFrames lint with zero errors and zero warnings; the browser editor's stricter checks also accept the sample.

The project supplies native discovery files for both assistants. This run verified the shared workflow from Codex, not a separate interactive Claude Code session. macOS/Linux end-to-end rendering has not been exercised locally. GitHub Actions source tests passed on Windows, macOS, and Linux.

Speech timing is estimated, not forced alignment. A real project's narration, caption placement, and long titles need an editorial review after rendering.

## GitHub rendering and Pages, 24 September 2026

- [Run 36059719534](https://github.com/mrinals129-png/video-studio/actions/runs/36059719534) installed dependencies and narration models on Ubuntu, passed all 18 tests, rendered the sample, and deployed Pages successfully.
- The online export is 1920 × 1080, approximately 12.50 seconds, with video and audio. Composition lint and a full FFmpeg decode passed. The downloaded artifact's title, middle, and closing frames were visually inspected.
- The public playback page loaded, video playback progressed in Chrome without a media error, and the narration disclosure worked. Codex's in-app browser crashed when playback was attempted; its cause is unconfirmed. Use Chrome for the published player if this occurs.
- Source checks for commit `892f799` passed on Windows, macOS, and Ubuntu.
- A local recording-in-scene render also passed verification after explicitly anchoring its media start to the global timeline; the middle frame showed the recording correctly.

The localhost preview is the local editing interface. Pages hosts the selected finished video; on-demand GitHub Actions performs remote rendering without an always-on application server.
