# Video Studio

Turn a Markdown script into a narrated product video with **Codex or Claude Code**. Bring screenshots or a screen recording, refine the scenes with your assistant, and export an MP4 on your own computer.

This is a local video-making toolkit with a browser preview, not a hosted service. It uses HyperFrames for HTML animation and rendering, and Kokoro for local speech. No video-generation API key is required.

![Frame from the generated sample video](docs/preview.png)

## Get started

Install [Node.js 22+](https://nodejs.org/) and [Python 3.10–3.12](https://www.python.org/downloads/), then open this folder in Codex or Claude Code and ask:

> Set up Video Studio and make the sample video. Verify the export and show me the result.

Or run:

```sh
npm ci
npm run setup
npm run demo
npm run preview
```

The sample is saved to `output/hello-studio.mp4`. The preview command prints a local browser address. Initial setup downloads the speech libraries and roughly 120 MB of model files; rendering may also download a Chromium browser. Dependencies stay local to this project.

On Windows, use `npm.cmd` if PowerShell blocks `npm`. The same commands are intended for Windows, macOS, and Linux; see [verification notes](docs/VERIFICATION.md) for platforms actually tested.

## Make your own

Copy [SCRIPT-TEMPLATE.md](SCRIPT-TEMPLATE.md) to `scripts/my-feature.md`, fill it in, then ask your assistant:

> Make a video from scripts/my-feature.md. Use my screenshot in assets/screenshot.png, check the narration and scenes, and export an MP4.

See the [workflow](docs/WORKFLOW.md) for recordings, voice selection, editing, and troubleshooting. [Ready-to-use prompts](prompts/start-a-video.md) are included.

## What is included

- Native project instructions and video skills for Codex and Claude Code.
- Local narration, reusable HTML scenes, and editable brand colors.
- Screenshot and recording support, plus an advanced overlay template.
- A browser timeline preview and MP4 export.
- Repeatable setup, automated checks, and export verification.

Scripts live in `scripts/`, personal media in `assets/`, editable scenes in `compositions/`, and exports in `output/`. Models and generated/personal media are ignored by Git. Change `_engine/templates/brand.css` to set your visual identity.

Word timestamps are estimated, so captions and scene timing need listening review. Complex animation requests are implemented by the assistant in HTML; the generator itself provides a starting composition.

## Development

```sh
npm test
npm run doctor
npm run studio -- --help
```

Read [AGENTS.md](AGENTS.md) for contributor guidance. The studio source is [MIT licensed](LICENSE). Dependencies have their own licenses; see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). The original work-specific examples and conversation exports are not part of this repository.
