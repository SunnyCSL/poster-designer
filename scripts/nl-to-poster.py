#!/usr/bin/env python3
"""
NL → Poster Pipeline
Converts natural language description into a poster via structured element generation.

Usage:
    python3 scripts/nl-to-poster.py "A blue poster with gold title 'Grand Opening' and subtitle in white" --template A4

    # With reference image for style
    python3 scripts/nl-to-poster.py "Match the style of this poster" --image reference.jpg --template Square

    # Pipe from stdin
    echo "Create a modern poster for a tech conference" | python3 scripts/nl-to-poster.py --template Wide
"""

import json
import subprocess
import sys
import re
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
POSTER_SERVER = os.environ.get("POSTER_SERVER", "http://localhost:8000")


def parse_nl(description: str) -> dict:
    """Parse natural language into design spec."""
    spec = {
        "template": "A4",
        "background": {"type": "solid", "color": "#ffffff"},
        "elements": [],
        "style_hints": []
    }

    text = description.lower()

    # Detect template
    if "square" in text or "1:1" in text or "instagram" in text:
        spec["template"] = "Square"
    elif "mobile" in text or "9:16" in text or "portrait" in text or "story" in text:
        spec["template"] = "Mobile"
    elif "wide" in text or "16:9" in text or "banner" in text or "landscape" in text:
        spec["template"] = "Wide"
    elif "a3" in text:
        spec["template"] = "A3"

    # Detect background color
    bg_map = {
        "blue": "#1a3a6b", "dark blue": "#0a1628", "navy": "#1a2744",
        "black": "#000000", "dark": "#1a1a2e",
        "white": "#ffffff", "light": "#f0f0f8",
        "red": "#8b0000", "dark red": "#4a0000",
        "gold": "#1a1a0a", "yellow": "#fff8dc",
        "green": "#004d40", "purple": "#2d1b69",
        "gray": "#333333", "grey": "#333333",
    }
    for word, color in bg_map.items():
        if f"{word} background" in text or f"{word} bg" in text or text.startswith(word):
            spec["background"]["color"] = color
            break

    # Extract quoted text (titles, headings, content)
    quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', description)
    titles = [t[0] or t[1] for t in quoted if (t[0] or t[1]).strip()]

    # Detect key phrases
    has_logo = "logo" in text

    # Build elements
    y_pos = 50

    # Main title (first quote or detected heading)
    if titles:
        title = titles[0]
        is_dark = sum(int(spec["background"]["color"][i:i+2], 16) for i in (1,3,5)) / 3 < 128
        title_color = "#ffffff" if is_dark else "#000000"

        spec["elements"].append({
            "type": "text",
            "content": title,
            "style": {
                "fontSize": 48 if "bold" in text else 36,
                "fontWeight": "bold" if ("bold" in text or "large" in text or len(title) < 15) else "400",
                "color": "#ffd700" if ("gold" in text or "金色" in description or "accent" in text) else title_color,
                "textAlign": "center" if "center" in text or "centered" in text or "middle" in text else "left",
            },
            "position": {"x": 50, "y": y_pos, "width": 200, "height": 50}
        })
        y_pos += 70

    # Subtitle (second quote or detected)
    if len(titles) > 1:
        subtitle = titles[1]
        is_dark = sum(int(spec["background"]["color"][i:i+2], 16) for i in (1,3,5)) / 3 < 128
        subtitle_color = "#cccccc" if is_dark else "#666666"

        spec["elements"].append({
            "type": "text",
            "content": subtitle,
            "style": {
                "fontSize": 24,
                "fontWeight": "400",
                "color": subtitle_color,
                "textAlign": spec["elements"][0]["style"]["textAlign"],
            },
            "position": {"x": 50, "y": y_pos, "width": 200, "height": 30}
        })
        y_pos += 50

    # Date/extra info (third quote)
    if len(titles) > 2:
        extra = titles[2]
        spec["elements"].append({
            "type": "text",
            "content": extra,
            "style": {"fontSize": 18, "fontWeight": "400", "color": "#999999", "textAlign": "center"},
            "position": {"x": 50, "y": y_pos + 20, "width": 200, "height": 25}
        })

    # Logo placeholder if detected
    if has_logo:
        spec["elements"].append({
            "type": "shape",
            "content": "rect",
            "style": {"fill": "#555555"},
            "position": {"x": 20, "y": 20, "width": 40, "height": 20}
        })

    spec["style_hints"] = []
    if "modern" in text: spec["style_hints"].append("modern")
    if "minimal" in text: spec["style_hints"].append("minimal")
    if "elegant" in text: spec["style_hints"].append("elegant")
    if "professional" in text: spec["style_hints"].append("professional")

    return spec


def create_poster(spec: dict, server: str = POSTER_SERVER):
    """Create poster from spec using poster CLI."""
    def run(args):
        cmd = ["python3", str(PROJECT_DIR / "cli" / "poster"), "--server", server] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"  ❌ {' '.join(args)}: {result.stderr.strip()}", file=sys.stderr)
        else:
            out = result.stdout.strip()
            print(f"  ✅ {' '.join(args)}")
            if out:
                for line in out.split("\n")[:2]:
                    print(f"     {line}")

    # Create new design
    run(["new", spec["template"]])

    # Set background
    run(["set-bg", "--color", spec["background"]["color"]])

    # Add elements
    for el in spec.get("elements", []):
        if el["type"] == "text":
            cmd = ["add-text", el["content"]]
            pos = el.get("position", {})
            cmd.extend(["--x", str(pos.get("x", 50))])
            cmd.extend(["--y", str(pos.get("y", 50))])
            cmd.extend(["--width", str(pos.get("width", 200))])
            cmd.extend(["--height", str(pos.get("height", 40))])
            style = el.get("style", {})
            if style.get("fontSize"):
                cmd.extend(["--font-size", str(style["fontSize"])])
            if style.get("fontWeight") == "bold":
                cmd.append("--bold")
            if style.get("color"):
                cmd.extend(["--color", style["color"]])
            if style.get("textAlign") and style["textAlign"] != "left":
                cmd.extend(["--text-align", style["textAlign"]])
            run(cmd)
        elif el["type"] == "shape":
            cmd = ["add-shape", el.get("content", "rect")]
            pos = el.get("position", {})
            cmd.extend(["--x", str(pos.get("x", 0))])
            cmd.extend(["--y", str(pos.get("y", 0))])
            cmd.extend(["--width", str(pos.get("width", 50))])
            cmd.extend(["--height", str(pos.get("height", 50))])
            style = el.get("style", {})
            if style.get("fill"):
                cmd.extend(["--fill", style["fill"]])
            run(cmd)
        elif el["type"] == "image":
            cmd = ["add-image", el.get("content", "")]
            pos = el.get("position", {})
            cmd.extend(["--x", str(pos.get("x", 0))])
            cmd.extend(["--y", str(pos.get("y", 0))])
            cmd.extend(["--width", str(pos.get("width", 100))])
            cmd.extend(["--height", str(pos.get("height", 100))])
            run(cmd)

    # Compose
    run(["compose"])

    print(f"\n🎉 Poster created!")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Natural Language → Poster")
    parser.add_argument("description", nargs="?", help="Text description of the poster")
    parser.add_argument("--template", help="Template override")
    parser.add_argument("--server", default=POSTER_SERVER)
    parser.add_argument("--image", help="Reference image for style")
    parser.add_argument("--dry-run", action="store_true", help="Show spec without creating")

    args = parser.parse_args()

    server = args.server

    # Get description from args or stdin
    if args.description:
        description = args.description
    else:
        description = sys.stdin.read().strip()

    if not description:
        print("❌ No description provided. Use: echo '...' | python3 nl-to-poster.py", file=sys.stderr)
        sys.exit(1)

    # If reference image, run vision analysis too
    if args.image:
        try:
            from scripts.vision_to_poster import analyze_image as vision_analyze
            _, vision_spec = vision_analyze(args.image)
            description += f"\n\nReference image analysis: background={vision_spec.get('background',{}).get('color','#ffffff')}"
        except Exception as e:
            print(f"⚠️  Vision analysis failed: {e}", file=sys.stderr)

    print(f"📝 Processing: {description[:100]}{'...' if len(description) > 100 else ''}")

    # Parse NL to spec
    spec = parse_nl(description)

    if args.template:
        spec["template"] = args.template

    print(f"\n📐 Design Spec:")
    print(f"  Template: {spec['template']}")
    print(f"  Background: {spec['background']['color']}")
    print(f"  Elements: {len(spec['elements'])}")
    print(f"  Style: {', '.join(spec.get('style_hints', [])) or 'default'}")

    if args.dry_run:
        print("\n📋 Full Spec:")
        print(json.dumps(spec, indent=2, ensure_ascii=False))
        return

    # Create poster
    create_poster(spec, server=server)

    # Print info
    print(f"\n📎 Commands you can run:")
    print(f"  poster state                    # View current state")
    print(f"  poster compose                  # Render poster")
    print(f"  poster export --format png      # Export PNG")
    print(f"  poster undo                     # Undo last change")


if __name__ == "__main__":
    main()
