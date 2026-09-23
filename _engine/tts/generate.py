"""
Video Studio — Kokoro TTS engine
Converts a script .md file into narration.wav + transcript.json

Usage:
  python3 _engine/tts/generate.py --input scripts/my-feature.md --out compositions/my-feature/
  python3 _engine/tts/generate.py --input scripts/my-feature.md --out compositions/my-feature/ --voice am_adam
"""

import argparse
import json
import os
import re
import sys


# ── Voice options ──────────────────────────────────────────────────────────────
VOICES = {
    "af_heart":  "American female — warm (default)",
    "am_adam":   "American male",
    "bf_emma":   "British female",
    "bm_george": "British male",
}

# ── Model file paths (relative to repo root) ──────────────────────────────────
REPO_ROOT   = os.path.join(os.path.dirname(__file__), "..", "..")
MODEL_PATH  = os.path.join(REPO_ROOT, "kokoro-v1.0.int8.onnx")
VOICES_PATH = os.path.join(REPO_ROOT, "voices-v1.0.bin")


def read_script(path: str) -> str:
    """Read a markdown script file and strip markdown syntax, keeping narration only."""
    with open(path, "r", encoding="utf-8-sig") as f:
        text = f.read()

    # A structured script must have narration; never read metadata aloud.
    narration_match = re.search(r"^##\s+Narration\s*$\n(.*?)(?=^##\s|\Z)", text, re.DOTALL | re.MULTILINE | re.IGNORECASE)
    if narration_match:
        text = narration_match.group(1).strip()
    elif re.search(r"^##\s", text, re.MULTILINE):
        return ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^#+\s.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*|__|\*|_|`", "", text)
    return re.sub(r"\s+", " ", text).strip()


def generate_voice(text: str, output_dir: str, voice: str = "af_heart"):
    """Generate narration.wav using Kokoro-ONNX (fully offline, Apache 2.0)."""
    if not text.strip():
        raise ValueError("Narration must not be empty")
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf
    except ImportError:
        print("❌  Kokoro not installed.")
        print("    Run: pip install -r _engine/tts/requirements.txt")
        sys.exit(1)

    # Check model files exist
    if not os.path.exists(MODEL_PATH):
        print(f"❌  Model file not found: {MODEL_PATH}")
        print("    Run npm run setup to download it.")
        sys.exit(1)

    if not os.path.exists(VOICES_PATH):
        print(f"❌  Voices file not found: {VOICES_PATH}")
        print("    Run npm run setup to download it.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    wav_path        = os.path.join(output_dir, "narration.wav")
    txt_path        = os.path.join(output_dir, "narration.txt")
    transcript_path = os.path.join(output_dir, "transcript.json")

    print(f"🎙️  Generating voice ({voice} — {VOICES.get(voice, 'custom')})...")
    kokoro = Kokoro(MODEL_PATH, VOICES_PATH)
    samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0, lang="en-gb" if voice.startswith("b") else "en-us")

    import soundfile as sf
    sf.write(wav_path, samples, sample_rate)
    print(f"✅  narration.wav  → {wav_path}")

    # Save plain text copy
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Build word-level timestamps (character-proportional, bounded to total duration)
    words          = text.split()
    total_duration = len(samples) / sample_rate
    total_chars    = sum(len(w) for w in words)
    transcript     = []
    t = 0.0
    for word in words:
        word_dur = (len(word) / total_chars) * total_duration
        transcript.append({
            "word":  word,
            "start": round(t, 3),
            "end":   round(min(t + word_dur, total_duration), 3),
        })
        t = min(t + word_dur, total_duration)

    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump({"timing": "estimated-character-proportional", "duration": round(total_duration, 3), "words": transcript}, f, indent=2)
    print(f"✅  transcript.json → {transcript_path}")
    print(f"📊  Total duration: {round(total_duration, 1)}s  |  {len(words)} words")

    return wav_path, transcript_path, round(total_duration, 3)


def generate_voice_segments(segments: list, output_dir: str):
    """
    Generate narration from multiple voice segments, stitch into one WAV,
    and produce a merged transcript.json with correct cumulative timestamps.

    segments: list of {"voice": str, "text": str}
    Returns: (wav_path, transcript_path, total_duration, segment_boundaries)
             segment_boundaries = list of (voice, label, start_time, end_time)
    """
    if not segments or any(not s["text"].strip() for s in segments):
        raise ValueError("Provide at least one non-empty voice segment")
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf
        import numpy as np
    except ImportError:
        print("❌  Kokoro not installed.")
        print("    Run: pip install -r _engine/tts/requirements.txt")
        sys.exit(1)

    if not os.path.exists(MODEL_PATH):
        print(f"❌  Model file not found: {MODEL_PATH}")
        sys.exit(1)
    if not os.path.exists(VOICES_PATH):
        print(f"❌  Voices file not found: {VOICES_PATH}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    kokoro = Kokoro(MODEL_PATH, VOICES_PATH)

    all_samples    = []
    all_words      = []
    sample_rate    = None
    offset         = 0.0          # cumulative time offset
    boundaries     = []           # (voice, label, start_t, end_t)

    for seg in segments:
        voice = seg["voice"]
        text  = seg["text"].strip()
        label = VOICES.get(voice, voice)
        print(f"🎙️  Segment [{voice} — {label}]: \"{text[:60]}{'...' if len(text)>60 else ''}\"")

        samples, sr = kokoro.create(text, voice=voice, speed=1.0, lang="en-gb" if voice.startswith("b") else "en-us")
        if sample_rate is None:
            sample_rate = sr
        seg_duration = len(samples) / sr

        # Build word timestamps for this segment (char-proportional)
        words      = text.split()
        total_chars = sum(len(w) for w in words)
        t = 0.0
        for word in words:
            word_dur = (len(word) / total_chars) * seg_duration if total_chars else 0
            all_words.append({
                "word":  word,
                "start": round(offset + t, 3),
                "end":   round(offset + min(t + word_dur, seg_duration), 3),
            })
            t = min(t + word_dur, seg_duration)

        boundaries.append((voice, label, round(offset, 3), round(offset + seg_duration, 3)))
        all_samples.append(samples)
        offset += seg_duration

    # Stitch all audio segments
    combined   = np.concatenate(all_samples)
    total_dur  = round(len(combined) / sample_rate, 3)

    wav_path        = os.path.join(output_dir, "narration.wav")
    transcript_path = os.path.join(output_dir, "transcript.json")

    import soundfile as sf
    sf.write(wav_path, combined, sample_rate)
    print(f"✅  narration.wav  → {wav_path}")

    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump({"timing": "estimated-character-proportional", "duration": total_dur, "words": all_words}, f, indent=2)
    print(f"✅  transcript.json → {transcript_path}")
    print(f"📊  Total duration: {round(total_dur, 1)}s  |  {len(all_words)} words")

    print("\n🎚️  Voice segment boundaries:")
    for voice, label, start, end in boundaries:
        print(f"    {voice:12s} ({label:30s})  {start:.3f}s → {end:.3f}s")

    return wav_path, transcript_path, total_dur, boundaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate voice narration from a script.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--input",  required=True,  help="Path to your script .md file")
    parser.add_argument("--out",    required=True,  help="Output directory (e.g. compositions/my-feature/)")
    parser.add_argument("--voice",  default="af_heart",
                        help="Voice to use. Options:\n" +
                             "\n".join(f"  {k}  — {v}" for k, v in VOICES.items()))
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌  Script not found: {args.input}")
        sys.exit(1)

    text = read_script(args.input)
    if not text:
        print("❌  Script is empty after parsing. Check your file has a Narration section.")
        sys.exit(1)

    print(f"📝  Script loaded ({len(text.split())} words)")
    generate_voice(text, args.out, voice=args.voice)
