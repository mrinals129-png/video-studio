#!/usr/bin/env python3
"""
Video Studio — overlay generator
=====================================
Ingests a user-supplied video and builds a HyperFrames composition that
adds GSAP overlays (captions, callouts, spotlight, Ken Burns, lower-third,
intro/outro cards) on top of the recording.

Usage
-----
python3 _engine/overlay/generate.py \\
  --video   assets/my-recording.mp4  \\
  --script  scripts/my-feature.md    \\
  --out     compositions/my-feature/ \\
  [--tts]                            \\  # regenerate narration from script
  [--voice  af_heart]                \\  # Kokoro voice flag
  [--video-start  2.5]               \\  # trim: skip first N seconds of video
  [--video-volume 0.15]              \\  # original audio volume (0=mute, 1=full)
  [--no-intro]                       \\  # skip intro title card
  [--no-outro]                       \\  # skip outro CTA card

What it produces
----------------
compositions/<slug>/
  index.html        — filled template ready for `npm run studio -- render`
  brand.css         — copied from _engine/templates/brand.css
  narration.wav     — TTS output (or copied from existing)
  transcript.json   — word-level timestamps from TTS
  narration.txt     — plain text version of narration

The user's video is copied into the composition, so it previews and renders
without depending on a path outside the composition directory.
"""

import argparse
import html as html_lib
import math
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ── Repo root = two levels up from this script ──
REPO_ROOT   = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from studio import probe, metadata, fill_template as safe_fill_template

TEMPLATES   = REPO_ROOT / "_engine" / "templates"
TTS_SCRIPT  = REPO_ROOT / "_engine" / "tts" / "generate.py"


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def die(msg: str):
    print(f"[overlay] ✗ {msg}", file=sys.stderr)
    sys.exit(1)


def info(msg: str):
    print(f"[overlay] {msg}")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def ffprobe_duration(video_path: Path) -> float:
    """Return the duration of a video file in seconds via ffprobe."""
    data = probe(video_path)
    if not any(s.get("codec_type") == "video" for s in data.get("streams", [])):
        die("The input must contain a video stream.")
    return float(data["format"]["duration"])


def parse_script(script_path: Path) -> dict:
    """
    Parse a SCRIPT-TEMPLATE.md file.
    Returns dict with keys: feature_name, tagline, narration, animation_notes.
    """
    data = metadata(script_path)
    return {"feature_name": data.get("feature name", script_path.stem),
            "product_name": data.get("product name", "Video Studio"),
            "tagline": data.get("tagline", ""), "narration": data["narration"],
            "animation_notes": data.get("animation notes", "")}


def sentence_boundaries(transcript: list) -> list:
    """
    Given a list of word dicts [{word, start, end}, ...],
    return a list of sentence end times (float seconds)
    by detecting words ending in . ! ?
    """
    boundaries = []
    for w in transcript:
        word = w.get("word", "").strip()
        if word.endswith((".", "!", "?")):
            boundaries.append(round(w["end"], 3))
    return boundaries


def fill_template(template_text: str, replacements: dict) -> str:
    """Replace all {{KEY}} placeholders. Keys are case-sensitive."""
    safe = {key: html_lib.escape(value, quote=True) if isinstance(value, str) else value
            for key, value in replacements.items()}
    return safe_fill_template(template_text, safe)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Video Studio overlay generator")
    parser.add_argument("--video",        required=True,  help="Path to user's MP4/MOV recording")
    parser.add_argument("--script",       required=True,  help="Path to script .md file")
    parser.add_argument("--out",          required=False, help="Output composition directory (auto-derived from slug if omitted)")
    parser.add_argument("--tts",          action="store_true", help="Regenerate TTS narration from script")
    parser.add_argument("--voice",        default="af_heart", choices=["af_heart", "am_adam", "bf_emma", "bm_george"], help="Kokoro voice (default: af_heart)")
    parser.add_argument("--video-start",  type=float, default=0.0, help="Skip first N seconds of the video (trim)")
    parser.add_argument("--video-volume", type=float, default=0.0, help="Volume of original video audio (0=mute)")
    parser.add_argument("--no-intro",     action="store_true", help="Omit the intro title card")
    parser.add_argument("--no-outro",     action="store_true", help="Omit the outro CTA card")
    args = parser.parse_args()

    video_path  = Path(args.video).resolve()
    script_path = Path(args.script).resolve()

    if not video_path.exists():
        die(f"Video not found: {video_path}")
    if not script_path.exists():
        die(f"Script not found: {script_path}")

    if not math.isfinite(args.video_start) or args.video_start < 0:
        die("--video-start must be finite and non-negative")
    if not math.isfinite(args.video_volume) or not 0 <= args.video_volume <= 1:
        die("--video-volume must be between 0 and 1")

    # ── Parse script ──
    script = parse_script(script_path)
    feature_name = script["feature_name"] or script_path.stem
    slug         = slugify(feature_name) or "video"
    tagline      = script["tagline"] or "Video Studio"

    # ── Derive output path ──
    out_dir = Path(args.out).resolve() if args.out else (REPO_ROOT / "compositions" / slug)
    out_dir.mkdir(parents=True, exist_ok=True)
    info(f"Composition → {out_dir}/")

    shutil.copy2(REPO_ROOT / "node_modules/gsap/dist/gsap.min.js", out_dir / "gsap.min.js")

    # ── Copy brand.css ──
    brand_src = TEMPLATES / "brand.css"
    if brand_src.exists():
        shutil.copy2(brand_src, out_dir / "brand.css")
        info("brand.css copied")

    # ── TTS ──
    narration_wav   = out_dir / "narration.wav"
    transcript_json = out_dir / "transcript.json"
    narration_txt   = out_dir / "narration.txt"

    if args.tts or not narration_wav.exists() or not transcript_json.exists():
        info("Generating TTS narration…")
        if not TTS_SCRIPT.exists():
            die(f"TTS script not found: {TTS_SCRIPT}")
        tts_cmd = [
            sys.executable, str(TTS_SCRIPT),
            "--input",  str(script_path),
            "--out",    str(out_dir),
            "--voice",  args.voice,
        ]
        subprocess.run(tts_cmd, check=True)
        info("TTS done ✅")
    else:
        info("Narration already exists — skipping TTS (pass --tts to regenerate)")

    # ── Read transcript ──
    if not transcript_json.exists():
        die(f"transcript.json not found at {transcript_json}. TTS may have failed.")

    with open(transcript_json, encoding="utf-8") as f:
        transcript_data = json.load(f)

    words          = transcript_data.get("words", transcript_data.get("segments", []))
    total_duration = round(transcript_data.get("duration", words[-1]["end"] if words else 60), 3)
    if not math.isfinite(total_duration) or total_duration < 8:
        die("Use at least eight seconds of narration for an overlay video.")
    boundaries     = sentence_boundaries(words)

    info(f"Narration duration: {total_duration}s, sentence boundaries: {boundaries}")

    # ── Video timing ──
    video_duration_raw = ffprobe_duration(video_path)
    video_start        = args.video_start
    video_duration     = round(video_duration_raw - video_start, 3)
    if video_duration <= 0:
        die("The trim point is past the end of the recording.")
    video_src = "source" + video_path.suffix.lower()
    if video_path != (out_dir / video_src).resolve():
        shutil.copy2(video_path, out_dir / video_src)

    # The video starts after the intro (if any).
    # Intro = 3s, outro = last 4s of total audio duration.
    intro_duration = 0.0 if args.no_intro else 3.0
    outro_start    = total_duration - 4.0 if not args.no_outro else total_duration

    needed = outro_start - intro_duration
    if video_duration < needed:
        die(f"Recording needs {needed:.1f}s after trim; only {video_duration:.1f}s remain.")
    video_duration = needed

    # ── Caption timing from sentence boundaries ──
    # Distribute available boundaries across 3 caption slots.
    # Show up to three captions in non-overlapping intervals, bounded by the video.
    cap_starts = [round(intro_duration + i * needed / 3, 3) for i in range(3)]
    cap_ends = [round(intro_duration + (i + 1) * needed / 3 - .35, 3) for i in range(3)]

    # ── Callout / spotlight (sensible defaults — the assistant will tune) ──
    callout_start     = round(intro_duration + .5, 3)
    callout_end       = round(min(outro_start - .4, callout_start + 4.0), 3)
    spotlight_start   = callout_start
    spotlight_end     = callout_end

    lower_third_start = round(intro_duration + 0.5, 3)
    lower_third_end   = round(outro_start - 0.5, 3)

    # ── Parse narration sentences for captions ──
    narration = script["narration"]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", narration) if s.strip()]

    def caption_text(idx):
        if idx < len(sentences):
            return sentences[idx]
        return ""

    # ── Title card lines ──
    words_in_name = feature_name.split()
    title_line1   = " ".join(words_in_name[:2]) if len(words_in_name) > 2 else feature_name
    title_line2   = " ".join(words_in_name[2:]) if len(words_in_name) > 2 else ""

    # ── Build placeholder map ──
    r = {
        # Meta
        "COMPOSITION_ID":         slug,
        "PRODUCT_NAME":           script["product_name"],
        "FEATURE_TITLE_LINE1":    title_line1,
        "FEATURE_TITLE_LINE2":    title_line2,
        "FEATURE_TAGLINE":        tagline,
        "TOTAL_DURATION":         total_duration,
        # Video
        "VIDEO_SRC":              video_src,
        "VIDEO_START":            intro_duration,
        "VIDEO_MEDIA_START":      video_start,
        "INTRO_DURATION":         intro_duration,
        "VIDEO_DURATION":         video_duration,
        "VIDEO_VOLUME":           args.video_volume,
        # Intro / outro
        "INTRO_EXIT":             round(max(0, intro_duration - 0.4), 3),
        "OUTRO_START":            outro_start,
        "OUTRO_START_PLUS_0_3":   round(outro_start + 0.3, 3),
        "OUTRO_START_PLUS_0_9":   round(outro_start + 0.9, 3),
        "OUTRO_START_PLUS_1_5":   round(outro_start + 1.5, 3),
        "OUTRO_LINE1":            tagline,
        "OUTRO_LINE2":            "",
        # Captions
        "CAPTION_1_TEXT":         caption_text(0),
        "CAPTION_1_START":        cap_starts[0],
        "CAPTION_1_END":          cap_ends[0],
        "CAPTION_2_TEXT":         caption_text(1),
        "CAPTION_2_START":        cap_starts[1],
        "CAPTION_2_END":          cap_ends[1],
        "CAPTION_3_TEXT":         caption_text(2),
        "CAPTION_3_START":        cap_starts[2],
        "CAPTION_3_END":          cap_ends[2],
        # Callout / spotlight (positional defaults — the assistant will override)
        "CALLOUT_1_TEXT":         feature_name,
        "CALLOUT_1_TOP":          80,
        "CALLOUT_1_LEFT":         80,
        "CALLOUT_1_START":        callout_start,
        "CALLOUT_1_END":          callout_end,
        "SPOTLIGHT_1_TOP":        200,
        "SPOTLIGHT_1_LEFT":       200,
        "SPOTLIGHT_1_W":          400,
        "SPOTLIGHT_1_H":          240,
        "SPOTLIGHT_1_START":      spotlight_start,
        "SPOTLIGHT_1_END":        spotlight_end,
        # Lower third
        "LOWER_THIRD_TITLE":      feature_name,
        "LOWER_THIRD_SUB":        tagline,
        "LOWER_THIRD_START":      lower_third_start,
        "LOWER_THIRD_END":        lower_third_end,
    }

    # ── Fill template ──
    template_path = TEMPLATES / "overlay-scene.html"
    if not template_path.exists():
        die(f"Template not found: {template_path}")

    html = template_path.read_text(encoding="utf-8")
    html = fill_template(html, r)

    # Keep valid nested HTML and timeline targets, but hide optional cards.
    if args.no_intro:
        html = html.replace('<div id="intro-card">', '<div id="intro-card" style="display:none">')
    if args.no_outro:
        html = html.replace('<div id="outro-card">', '<div id="outro-card" style="display:none">')
        html = re.sub(r"// ── Outro card ──.*?(?=// ── Initial)", ";\n\n    ", html, flags=re.DOTALL)
    narration_txt.write_text(script["narration"], encoding="utf-8")

    index_path = out_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")

    info(f"index.html written ✅")
    info("")
    info("Next step — render:")
    info(f"  npm run studio -- render \"{out_dir}\" --output output/{out_dir.name}.mp4")
    info("")
    info("After watching the video, tune overlays:")
    info(f"  Edit: {out_dir}/index.html")
    info(f"  Re-render: npm run studio -- render \"{out_dir}\" --output output/{out_dir.name}.mp4")


if __name__ == "__main__":
    main()
