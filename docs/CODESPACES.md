# Open the full editor online

[Create a Video Studio Codespace](https://codespaces.new/mrinals129-png/video-studio)

Codespaces runs the existing studio on a GitHub-hosted development computer. You get the full editing interface, project files, narration, and rendering. GitHub Pages remains the public player for finished videos.

## Start

1. Open the link above and choose a **2-core** machine on `main`.
2. Create the Codespace. First setup installs Node 22, Python 3.11, media tools, the voice models, and Chromium; allow several minutes. It builds the sample composition without rendering an MP4.
3. Open the **Ports** panel, find **Video Studio editor / 3002**, and click **Open in Browser**. Leave visibility **Private**: the editor can change project files. The browser address ends in `-3002.app.github.dev` and requires your GitHub sign-in.
4. Use the editor as you would the localhost version. The preview restarts when the Codespace starts again.

If initial setup fails, inspect its terminal output, then run `bash .devcontainer/setup.sh`. To restart the editor, run `bash .devcontainer/start.sh`. Setup preserves an existing sample composition rather than overwriting edits.

## Use an assistant

Open this repository with Codex or Claude Code **in the Codespace**, or connect an assistant with remote terminal access. The local Codex desktop session does not automatically move to the remote machine. Install/sign in to your chosen assistant separately; Codespaces does not include its subscription or credentials. Repository instructions and skills are already included for both assistants.

Ask:

> Read AGENTS.md (Codex) or CLAUDE.md (Claude Code), then help me edit the video in this Codespace. Preserve my manual scene edits and verify the exported MP4.

Render the sample's current edits with:

```sh
npm run studio -- render compositions/hello-studio --output output/hello-studio.mp4
```

Download the MP4 from the Codespace file explorer. Scripts and code can be committed to the public repository after review. Generated compositions, exports, voice models, and personal media are ignored by Git: download anything you want to keep before deleting the Codespace. They persist across stops, but not deletion.

## Stop when finished

Use **Stop Codespace** when you are done; closing the editor tab alone is not a reliable way to stop compute. Set the idle timeout to 15 minutes in your Codespaces settings. Stopped Codespaces still use storage until deleted; save your work first.

GitHub Pro currently includes **180 core-hours** and **20 GB-month of storage** per month. A two-core Codespace uses two core-hours per running hour (about 90 running hours if no other Codespaces use your allowance). Excess usage can incur charges depending on your billing settings. This repository does not change your spending limits, auto-deletion settings, or install assistant credentials.

Sources: [Codespaces billing](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces), [port forwarding](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace).

## Verification status

The studio's Ubuntu rendering workflow has passed on GitHub Actions. The Codespaces configuration is prepared, but a fresh Codespace build and its authenticated editor connection still need to be verified; an Actions run does not establish that those work.
