# Use the studio through GitHub

For the **full interactive editor** online, use [GitHub Codespaces](CODESPACES.md). The workflow below is for rendering a committed script without an interactive editor.

Codex and Claude Code can run this studio on GitHub Actions. No always-on server or separate app account is needed. GitHub Pages serves the latest video you explicitly publish.

Tell either assistant:

> Make a video from my script using the Video Studio GitHub workflow. Download the finished MP4 and verify it. Publish it to Pages only if I ask you to share it.

## Assistant workflow

1. Prepare the approved script under `scripts/lowercase-name.md`, following `SCRIPT-TEMPLATE.md`. Review the exact file, commit it, and push it to `main` when the user has authorized uploading it. This is a **public repository**: source scripts, workflow logs, and artifacts are not a private workspace. Use the local workflow for work that must remain private.
2. Start the workflow using the authenticated GitHub CLI. No new token needs to be created or stored in this repository:

```sh
gh workflow run render.yml --repo mrinals129-png/video-studio --ref main -f script_path=scripts/hello-studio.md -f voice=af_heart -f publish=false -f request_id=unique-request-label
```

3. Find the run whose `displayTitle` matches `Render unique-request-label`. Do not assume the newest run belongs to you:

```sh
gh run list --repo mrinals129-png/video-studio --workflow render.yml --json databaseId,displayTitle,status,conclusion,url
gh run view RUN_ID --repo mrinals129-png/video-studio
gh run download RUN_ID --repo mrinals129-png/video-studio --name video-hello-studio-RUN_ID --dir output/cloud-RUN_ID
```

4. Wait for success, download the artifact, and inspect the video before reporting completion. The job already runs unit tests, composition lint, rendering, audio/video stream checks, and a full decode. The artifact includes the MP4 and editable composition, and expires after seven days. Save finished videos locally.
5. When publication is requested, set `publish=true` on a run from `main`. This replaces the current public playback page at [mrinals129-png.github.io/video-studio](https://mrinals129-png.github.io/video-studio/). An ordinary render with `publish=false` leaves Pages unchanged. There is no automatic render on every code push.

The online command produces the standard narrated scene layout. For custom recordings, advanced overlays, or detailed visual editing, both assistants can use the full local studio. The public page is a video player and download link; it is not a second editing application.

## Compute and storage

The workflow uses a standard Ubuntu runner and has a 20-minute timeout. GitHub documents standard hosted runner use for public repositories as free; artifacts and caches have separate storage rules. This setup does not change spending limits or provision paid runners. See [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

Publishing uses GitHub's official Pages workflow actions. No credentials are exposed in the playback page. See [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
