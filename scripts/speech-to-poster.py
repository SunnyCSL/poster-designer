#!/usr/bin/env python3
"""
Speech → Poster Pipeline
Takes an audio file or records from microphone, transcribes with whisper, creates poster.

Usage:
    python3 scripts/speech-to-poster.py audio.mp3 --template A4
    python3 scripts/speech-to-poster.py --record          # Record from mic

Requirements:
    - openai-whisper (pip install openai-whisper) OR
    - Use edge-tts's built-in recognition OR
    - Pass raw text directly
"""

import subprocess
import sys
import os
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


def transcribe(audio_path: str) -> str:
    """
    Transcribe audio file to text.
    Tries whisper if available, otherwise falls back to simple approaches.
    """
    # Try whisper
    try:
        result = subprocess.run(
            ["whisper", audio_path, "--language", "zh", "--output_format", "txt"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass

    # Try whisper from python
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, language="zh")
        return result["text"].strip()
    except ImportError:
        pass

    # Fallback: return filename as placeholder
    print("⚠️  Whisper not available. Install with: pip install openai-whisper", file=sys.stderr)
    print("ℹ️  For now, pass text directly to nl-to-poster.py", file=sys.stderr)
    return ""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Speech → Poster")
    parser.add_argument("audio", nargs="?", help="Audio file path")
    parser.add_argument("--template", default=None)
    parser.add_argument("--server", default=os.environ.get("POSTER_SERVER", "http://localhost:8000"))
    parser.add_argument("--record", action="store_true", help="Record from microphone")

    args = parser.parse_args()

    if args.record:
        print("🎤 Recording from microphone... (Ctrl+C to stop)", file=sys.stderr)
        # Use arecord or sox
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            audio_path = f.name
        try:
            subprocess.run(["arecord", "-d", "10", "-f", "cd", audio_path], timeout=15)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("❌ arecord not available", file=sys.stderr)
            sys.exit(1)
    elif args.audio:
        audio_path = args.audio
    else:
        parser.print_help()
        sys.exit(1)

    text = transcribe(audio_path)
    if not text:
        sys.exit(1)

    print(f"📝 Transcribed: {text}")

    # Pass to nl-to-poster
    cmd = ["python3", str(PROJECT_DIR / "scripts" / "nl-to-poster.py"), text]
    if args.template:
        cmd.extend(["--template", args.template])
    if args.server:
        cmd.extend(["--server", args.server])

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
