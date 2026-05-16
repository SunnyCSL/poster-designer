#!/usr/bin/env python3
"""
Vision → Poster Decomposition Pipeline
Takes a reference image, analyzes it with mmx vision, converts to structured
elements, and optionally creates a poster via the poster CLI.

Usage:
  # Just analyze (saves vision description + design spec)
  python3 scripts/vision-to-poster.py reference.jpg --analyze

  # Full auto pipeline (analyze + auto-create poster)
  python3 scripts/vision-to-poster.py reference.jpg --auto --template A4

  # Create poster from pre-existing spec
  python3 scripts/vision-to-poster.py reference.jpg --create

  # CLI wrapper
  poster from-vision reference.jpg --template A4 --auto
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional

# === Configuration ===
POSTER_SERVER = os.environ.get("POSTER_SERVER", "http://localhost:8000")
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"


def vision_analyze(image_path: str) -> str:
    """Run mmx vision describe on the image. Returns raw description text."""
    result = subprocess.run(
        ["mmx", "vision", "describe", str(image_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Vision failed: {result.stderr}")
    return result.stdout.strip()


def extract_design_spec(description: str, image_path: str) -> dict:
    """
    Extract design elements from vision description using heuristics.
    Produces a best-guess spec that can be refined by an LLM or manually.
    """
    spec = {
        "image_path": str(image_path),
        "background": {"type": "solid", "color": "#ffffff"},
        "elements": [],
        "design_notes": [],
    }

    lines = description.lower()

    # ── Background color detection ───────────────────────────────────────────
    color_map = {
        "navy": "#1a2744",
        "dark blue": "#0a1628",
        "blue": "#1a3a6b",
        "black": "#0d0d0d",
        "dark": "#1a1a2e",
        "white": "#ffffff",
        "cream": "#fff8e7",
        "red": "#8b0000",
        "dark red": "#4a0000",
        "gold": "#c9a227",
        "yellow": "#f5c842",
        "green": "#1b5e20",
        "purple": "#2d1b69",
        "orange": "#d35400",
        "pink": "#c0392b",
        "teal": "#0d7377",
    }

    for color_name, hex_color in color_map.items():
        if color_name in lines:
            spec["background"]["color"] = hex_color
            spec["design_notes"].append(f"Detected background tone: {color_name}")
            break

    # ── Text element detection ───────────────────────────────────────────────
    # Patterns for text content in vision descriptions
    text_patterns = [
        # "text that says 'HELLO'" / "text: 'Hello'" / "words 'HELLO WORLD'"
        r"(?:text|heading|title|label|words?|文字|標題)[:\s]+['\"]?([A-Za-z0-9\s\u4e00-\u9fff]{2,60})['\"]?",
        # Quoted uppercase strings (common in poster vision output)
        r"['\"]([A-Z]{2,30})['\"]",
        # After "contains:" or "showing:" mention
        r"(?:showing|contains|includes)[:\s]+['\"]?([A-Za-z0-9\s\u4e00-\u9fff]{2,50})",
    ]

    y_offset = 40
    for pattern in text_patterns:
        for match in re.finditer(pattern, description, re.IGNORECASE):
            text = match.group(1).strip()
            # Filter out noise
            if len(text) < 2:
                continue
            if text.lower() in ("none", "null", "unknown", "undefined"):
                continue

            is_heading = match.re.pattern in (text_patterns[0], text_patterns[1]) and len(text) < 25

            element = {
                "type": "text",
                "content": text,
                "position": {"x": 30, "y": y_offset, "width": 240, "height": 40},
                "style": {
                    "fontSize": 42 if is_heading else 24,
                    "fontWeight": "bold" if is_heading else "normal",
                    "color": "#ffffff" if _is_dark(spec["background"]["color"]) else "#000000",
                    "textAlign": "center" if is_heading else "left",
                },
            }
            spec["elements"].append(element)
            spec["design_notes"].append(f"Detected text element: '{text[:40]}'")
            y_offset += 60

    # ── Color accent detection ───────────────────────────────────────────────
    accent_colors = []
    for color_name, hex_color in color_map.items():
        if color_name in lines and hex_color != spec["background"]["color"]:
            accent_colors.append(hex_color)

    if accent_colors:
        spec["accent_colors"] = accent_colors[:3]
        spec["design_notes"].append(f"Detected accent colors: {accent_colors}")

    # ── Layout hints ────────────────────────────────────────────────────────
    if "left" in lines and "right" in lines:
        spec["layout_hint"] = "horizontal_split"
    if "top" in lines and "bottom" in lines:
        spec["layout_hint"] = "vertical_split"
    if any(w in lines for w in ["center", "middle"]):
        spec["layout_hint"] = "centered"
    if "vertical" in lines or "portrait" in lines:
        spec["layout_hint"] = "portrait"
    if "horizontal" in lines or "landscape" in lines:
        spec["layout_hint"] = "landscape"

    return spec


def _is_dark(hex_color: str) -> bool:
    """Rough luminance check."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) < 6:
        return False
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5
    except ValueError:
        return False


def analyze_image(image_path: str) -> tuple[str, dict]:
    """Phase 1: Analyze image and produce structured design spec."""
    print(f"🔍 Analyzing: {image_path}")
    description = vision_analyze(image_path)

    OUTPUT_DIR.mkdir(exist_ok=True)

    # Save raw description
    stem = Path(image_path).stem
    desc_path = OUTPUT_DIR / f"{stem}_vision.txt"
    desc_path.write_text(description, encoding="utf-8")
    print(f"   📝 Vision description → {desc_path}")

    # Extract structured spec
    spec = extract_design_spec(description, image_path)

    # Save structured spec
    spec_path = OUTPUT_DIR / f"{stem}_spec.json"
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"   📋 Design spec → {spec_path}")

    return description, spec


def _run_poster(args: list[str], server: str) -> subprocess.CompletedProcess:
    """Run a poster CLI command and return the result."""
    cmd = [
        sys.executable,
        str(PROJECT_DIR / "cli" / "poster"),
        "--server", server,
    ] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def auto_create(image_path: str, template: str = "A4", server: str = POSTER_SERVER) -> None:
    """
    Phase 2: Run full pipeline — analyze + create poster via poster CLI.
    """
    description, spec = analyze_image(image_path)

    print(f"\n🎨 Creating poster from analysis...")
    print(f"   Template: {template} | Server: {server}")

    # Create new design
    res = _run_poster(["new", template], server)
    if res.returncode != 0:
        print(f"   ⚠️  poster new failed (server may not be running): {res.stderr.strip()}")
    else:
        print(f"   ✅ poster new {template}")

    # Set background
    bg = spec.get("background", {}).get("color", "#ffffff")
    res = _run_poster(["set-bg", "--color", bg], server)
    if res.returncode == 0:
        print(f"   ✅ poster set-bg #{bg}")

    # Add detected elements
    for i, el in enumerate(spec.get("elements", []), 1):
        if el["type"] == "text":
            pos = el.get("position", {})
            style = el.get("style", {})
            cmd = [
                "add-text", el["content"],
                "--x", str(pos.get("x", 30)),
                "--y", str(pos.get("y", 40 + (i - 1) * 60)),
                "--font-size", str(style.get("fontSize", 24)),
                "--color", style.get("color", "#000000"),
            ]
            if style.get("fontWeight") == "bold":
                cmd.append("--bold")
            if style.get("textAlign") == "center":
                cmd.extend(["--text-align", "center"])

            res = _run_poster(cmd, server)
            if res.returncode == 0:
                print(f"   ✅ add-text '{el['content'][:30]}'")
            else:
                print(f"   ⚠️  add-text failed: {res.stderr.strip()}")

    # Compose
    res = _run_poster(["compose"], server)
    if res.returncode == 0:
        print(f"   ✅ poster compose")

    print(f"\n✅ Pipeline complete for: {image_path}")
    print(f"   Run 'poster --server {server} state' to inspect the result.")


def print_analysis(image_path: str) -> None:
    """Print analysis to stdout (for piping to Nexi)."""
    description, spec = analyze_image(image_path)
    print("\n" + "=" * 60)
    print("VISION ANALYSIS OUTPUT")
    print("=" * 60)
    print(description)
    print("\n" + "-" * 60)
    print("STRUCTURED SPEC (saved to output/<stem>_spec.json):")
    print("-" * 60)
    print(json.dumps(spec, indent=2, ensure_ascii=False))
    print("\n💡 Run with --auto to auto-create poster, or --create to load spec and create.")


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="vision-to-poster",
        description="Vision → Poster decomposition pipeline. Analyze a reference image "
                    "and convert it to poster elements.",
    )
    parser.add_argument(
        "image",
        help="Path to the reference image",
    )
    parser.add_argument(
        "--template", "-t",
        default="A4",
        choices=["A4", "A3", "Square", "Mobile", "Wide"],
        help="Template size for auto-create (default: A4)",
    )
    parser.add_argument(
        "--server", "-s",
        default=POSTER_SERVER,
        help=f"Poster API server URL (default: {POSTER_SERVER})",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze only — output vision description + spec, no poster creation",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Full auto pipeline: analyze + create poster via poster CLI",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create poster from pre-existing spec file (runs compose at end)",
    )

    args = parser.parse_args()

    image_path = Path(args.image).resolve()
    if not image_path.exists():
        print(f"❌ Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    server = args.server

    if args.analyze or not (args.auto or args.create):
        # Default: analyze + print summary
        print_analysis(str(image_path))
        if not args.analyze:
            print("\n💡 Tip: --auto to auto-create poster | --analyze for analysis-only mode")

    elif args.auto:
        auto_create(str(image_path), template=args.template, server=server)

    elif args.create:
        # Load existing spec and create poster
        stem = image_path.stem
        spec_path = OUTPUT_DIR / f"{stem}_spec.json"
        if not spec_path.exists():
            print(f"❌ No spec file found. Run --analyze first to generate: {spec_path}", file=sys.stderr)
            sys.exit(1)

        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        print(f"📋 Loading spec from: {spec_path}")

        # Create new design
        res = _run_poster(["new", args.template], server)
        if res.returncode != 0:
            print(f"⚠️  poster new failed (server may not be running): {res.stderr.strip()}")
        else:
            print(f"✅ poster new {args.template}")

        # Set background
        bg = spec.get("background", {}).get("color", "#ffffff")
        _run_poster(["set-bg", "--color", bg], server)
        print(f"✅ poster set-bg #{bg}")

        # Add elements
        for el in spec.get("elements", []):
            if el["type"] == "text":
                pos = el.get("position", {})
                style = el.get("style", {})
                cmd = [
                    "add-text", el["content"],
                    "--x", str(pos.get("x", 30)),
                    "--y", str(pos.get("y", 40)),
                    "--font-size", str(style.get("fontSize", 24)),
                    "--color", style.get("color", "#000000"),
                ]
                if style.get("fontWeight") == "bold":
                    cmd.append("--bold")
                _run_poster(cmd, server)

        _run_poster(["compose"], server)
        print(f"✅ poster compose")
        print(f"\n✅ Poster created from spec: {spec_path}")


if __name__ == "__main__":
    main()