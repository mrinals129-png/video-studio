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

The feature template has three advisory HyperFrames lint findings recommending separate sub-composition files. It has no lint errors, and it renders and plays in Studio. The current layout deliberately keeps the three scenes in one editable file.

The project supplies native discovery files for both assistants. This run verified the shared workflow from Codex, not a separate interactive Claude Code session. macOS/Linux end-to-end rendering has not been exercised locally. GitHub Actions runs the source tests on Windows, macOS, and Linux.

Speech timing is estimated, not forced alignment. A real project's narration, caption placement, and long titles need an editorial review after rendering.
