"""
Poster Designer — Compose Engine
Renders state.json elements into a raster image (PNG).
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Optional

# System font paths for CJK
SYSTEM_FONTS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansTC-Regular.ttf",
]

def _find_font(family: str, bold: bool = False, size: int = 24) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Find a font file on the system by family name."""
    # Try specific CJK fonts based on family hint
    candidates = []
    if "CJK" not in family and "Noto" not in family:
        candidates.append("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
        candidates.append("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc")
    
    for fp in candidates:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except (IOError, OSError):
                pass
    
    for fp in SYSTEM_FONTS:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except (IOError, OSError):
                pass
    
    return ImageFont.load_default()


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Parse #RRGGBB hex color to RGB tuple."""
    if not color or not color.startswith("#"):
        return (0, 0, 0)
    return (
        int(color[1:3], 16),
        int(color[3:5], 16),
        int(color[5:7], 16),
    )


def compose(state: dict, output_path: Optional[str | Path] = None) -> Image.Image:
    """
    Render state dict into a PIL Image.
    
    Args:
        state: Full state dict from state.json
        output_path: If provided, save PNG to this path
    
    Returns:
        PIL Image object
    """
    meta = state["meta"]
    w_px = meta["width_px"]
    h_px = meta["height_px"]
    dpi = meta["dpi"]
    
    # Create canvas
    img = Image.new("RGBA", (w_px, h_px), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw background
    bg = state["background"]
    if bg["type"] == "solid":
        color = bg.get("color", "#ffffff")
        r, g, b = _hex_to_rgb(color)
        img = Image.new("RGBA", (w_px, h_px), (r, g, b, 255))
        draw = ImageDraw.Draw(img)
    elif bg["type"] == "gradient":
        # Simple linear gradient top-to-bottom
        colors = bg.get("gradient", {}).get("colors", ["#ffffff", "#cccccc"])
        gradient_steps = len(colors)
        for y in range(h_px):
            t = y / h_px
            idx = min(int(t * gradient_steps), gradient_steps - 1)
            r, g, b = _hex_to_rgb(colors[idx])
            for x in range(w_px):
                img.putpixel((x, y), (r, g, b, 255))
    
    # Sort elements by layer
    elements = sorted(state.get("elements", []), key=lambda e: e.get("layer", 0))
    
    for el in elements:
        if not el.get("visible", True):
            continue
        
        pos = el["position"]
        # Convert mm to px
        x = round(pos["x"] * dpi / 25.4)
        y = round(pos["y"] * dpi / 25.4)
        w = round(pos.get("width", 0) * dpi / 25.4)
        h = round(pos.get("height", 0) * dpi / 25.4)
        rotation = pos.get("rotation", 0)
        
        if el["type"] == "text":
            content = el.get("content", "")
            style = el.get("style", {})
            font_size = max(6, round(style.get("fontSize", 24) * dpi / 72))  # pt at 72dpi base
            font_family = style.get("fontFamily", "Noto Sans")
            font_color = style.get("color", "#000000")
            r2, g2, b2 = _hex_to_rgb(font_color)
            text_align = style.get("textAlign", "left")
            font_weight = style.get("fontWeight", "400")
            
            # Try to load font with bold variant
            try:
                if font_weight == "bold":
                    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
                    if Path(font_path).exists():
                        font = ImageFont.truetype(font_path, font_size)
                    else:
                        font = _find_font(font_family, bold=True, size=font_size)
                else:
                    font = _find_font(font_family, size=font_size)
            except (IOError, OSError):
                font = _find_font(font_family, size=font_size)
            
            # Handle multiline text
            lines = content.split("\n")
            line_height = int(font_size * style.get("lineHeight", 1.4))
            
            for i, line in enumerate(lines):
                line_y = y + i * line_height
                bbox = draw.textbbox((0, 0), line, font=font)
                text_w = bbox[2] - bbox[0]
                
                if text_align == "center":
                    text_x = x + (w - text_w) // 2
                elif text_align == "right":
                    text_x = x + max(0, w - text_w)
                else:
                    text_x = x
                
                draw.text((text_x, line_y), line, fill=(r2, g2, b2, 255), font=font)
        
        elif el["type"] == "image":
            src = el.get("content", "")
            # Try to find the image file
            uploads_dir = Path(__file__).parent / "uploads"
            img_path = uploads_dir / src
            if not img_path.exists():
                img_path = Path(src)
            if img_path.exists():
                try:
                    paste_img = Image.open(img_path).convert("RGBA")
                    if w > 0 and h > 0:
                        paste_img = paste_img.resize((w, h), Image.Resampling.LANCZOS)
                    img.paste(paste_img, (x, y), paste_img)
                except (IOError, OSError):
                    pass  # Skip bad images
        
        elif el["type"] == "shape":
            style = el.get("style", {})
            fill = style.get("fill", style.get("bg", "#cccccc"))
            stroke = style.get("stroke", None)
            stroke_w = max(0, style.get("strokeWidth", 0))
            
            # Parse fill color
            if fill and fill.startswith("#"):
                r2, g2, b2 = _hex_to_rgb(fill)
                fill_rgba = (r2, g2, b2, 255)
            else:
                fill_rgba = (200, 200, 200, 255)
            
            shape_type = el.get("content", "rect").lower()
            
            # Draw with rotation support
            if rotation:
                # Create a separate layer for rotation
                shape_layer = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
                shape_draw = ImageDraw.Draw(shape_layer)
                
                if shape_type in ("rect", "rectangle"):
                    shape_draw.rectangle([x, y, x + w, y + h], fill=fill_rgba)
                elif shape_type in ("circle", "ellipse", "oval"):
                    shape_draw.ellipse([x, y, x + w, y + h], fill=fill_rgba)
                elif shape_type == "line":
                    shape_draw.line([x, y, x + w, y + h], fill=fill_rgba, width=max(1, stroke_w))
                
                rotated = shape_layer.rotate(rotation, center=(x + w//2, y + h//2), expand=False)
                img = Image.alpha_composite(img, rotated)
            else:
                if shape_type in ("rect", "rectangle"):
                    draw.rectangle([x, y, x + w, y + h], fill=fill_rgba)
                elif shape_type in ("circle", "ellipse", "oval"):
                    draw.ellipse([x, y, x + w, y + h], fill=fill_rgba)
                elif shape_type == "line":
                    draw.line([x, y, x + w, y + h], fill=fill_rgba, width=max(1, stroke_w))
    
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output), "PNG")
    
    return img