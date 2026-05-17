# Poster Designer PWA — Feature Expansion Spec

**Version:** 1.0  
**Date:** 2026-05-17  
**Status:** Draft  
**Based on:** Canvas (Canva), Figma, and industry best practices

---

## 1. Overview

The Poster Designer PWA is a mobile-first collaborative design tool built on Fabric.js.
Current features are minimal stubs. This document specifies a comprehensive expansion plan for
four tool areas: **Image**, **Text**, **Background**, and **Export**.

---

## 2. Architecture Baseline

- **Framework:** Fabric.js v5.3.0 (canvas engine)
- **Backend:** Node.js server with REST API (`/api/...`)
- **Rendering:** Fabric.js canvas; state synced via SSE (`/api/events`)
- **State:** `currentState = { meta, background, elements[] }` (loaded from `/api/state`)
- **Coordinates:** All positions stored in mm, converted to px via `mmToPx()` (DPI=300)
- **Server URL:** Configurable via `?server=` URL param, defaults to `localhost:8000`

### Current API endpoints (known)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/element` | Add element |
| PATCH | `/api/element/:id` | Update element |
| DELETE | `/api/element/:id?agent=pwa` | Delete element |
| POST | `/api/background` | Set background |
| POST | `/api/export` | Export PNG |
| GET | `/api/state` | Full state |
| POST | `/api/template` | Apply template |
| POST | `/api/undo` | Undo |
| GET | `/api/events` | SSE stream |
| POST | `/api/upload` | Upload file (mentioned) |

---

## 3. IMAGE Tool Expansion

### 3.1 File Upload (Local Device)

**Current state:** Placeholder only — `showError('Image upload coming soon')`

**Implementation:**
- Add `<input type="file" accept="image/*" id="image-file-input" hidden>`
- Show bottom-sheet/menu overlay with two options: **Upload from Device** and **Import from URL**
- On file selected: read as DataURL → POST to `/api/upload` → receive URL → add as image element

```js
// Sheet option structure
- "📁 Upload from Device" → triggers file input click
- "🔗 Import from URL" → prompt for URL input
```

**Server requirement:** `/api/upload` endpoint returns `{ url: string }`

**Fabric integration:**
```js
fabric.Image.fromURL(imageUrl, (img) => {
  const scale = targetW / img.width;
  img.set({ left: x, top: y, scaleX: scale, scaleY: scale });
  fabricCanvas.add(img);
}, { crossOrigin: 'anonymous' });
```

### 3.2 URL Image Import

**UI:** Dialog/prompt to enter image URL, validated with CORS proxy fallback if needed.
Store URL in `element.content` as the canonical source.

### 3.3 Image Filters

Fabric.js v5 supports `filters` array on `fabric.Image`. Implement a filter panel (modal/sheet):

| Filter | Description | Fabric.js property |
|--------|-------------|---------------------|
| Grayscale | Convert to B&W | `fabric.Grayscale` |
| Sepia | Warm vintage tone | `fabric.Sepia` |
| Blur | Gaussian blur | `fabric.Blur` + `blur` value 0–1 |
| Brightness | Lighten/darken | `fabric.Brightness` + value -1 to 1 |
| Contrast | Increase/decrease | `fabric.Contrast` + value -1 to 1 |
| Saturation | Color intensity | `fabric.Saturation` + value -1 to 1 |

**UI pattern:** Bottom sheet with horizontal slider for each filter.
Apply on selection of image element; show "Filters" button in context bar.

### 3.4 Image Crop & Resize

**Crop tool:**
- Fabric.js v5 has `fabric.Image.prototype.setCropzoom()` and crop area support
- Alternative: render image in a clipping rect (`fabric.Rect` with `clipPath`)
- Show overlay with draggable crop handles on image

**Resize with aspect lock:**
- Hold lock icon toggle → resize proportionally
- Free resize allows independent X/Y scaling
- Corner drag maintains aspect by default (Fabric.js behavior)

**Presets for aspect ratio:**
- 1:1 (Square)
- 4:3 (Standard)
- 16:9 (Widescreen)
- 9:16 (Story/Reel)
- 3:4 (Portrait)
- Free

### 3.5 Stock Photo Integration (Unsplash / Pexels)

**UI:** Search modal with text input + grid of results

**Endpoints:**
```
Unsplash:   GET https://api.unsplash.com/search/photos?query={q}&per_page=20
            Headers: Authorization: Client-ID {ACCESS_KEY}
Pexels:     GET https://api.pexels.com/v1/search?query={q}&per_page=20
            Headers: Authorization: {API_KEY}
```

**Implementation notes:**
- Use free tier APIs (Unsplash: 50 req/hour; Pexels: 200 req/hour)
- Cache last 20 results per query in memory
- Click result → add to canvas (download URL + attribution in element metadata)
- Show "Photo by [Author] on [Service]" attribution text on canvas element

**PWA API fallback:** If server has own stock integration, proxy through `/api/stock?provider=unsplash&q=...`

---

## 4. TEXT Tool Expansion

### 4.1 Font Family Picker

**Current state:** Only `style.fontFamily || 'Noto Sans'` hardcoded

**Google Fonts integration:**
Load Google Fonts dynamically:
```js
const GOOGLE_FONTS = [
  'Roboto', 'Open Sans', 'Lato', 'Montserrat', 'Oswald',
  'Playfair Display', 'Merriweather', 'Poppins', 'Raleway', 'Ubuntu',
  'Noto Sans', 'Noto Serif', 'Archivo Black', 'Bebas Neue', 'Pacifico'
];
// Load via: https://fonts.googleapis.com/css2?family=Roboto:wght@400;700
```

**UI:** Font family dropdown in context bar when text selected.
Display font name in its own typeface (live preview).

**Weight options per font:** 300, 400, 500, 600, 700, 900 (where supported)

### 4.2 Text Style Toggles

Add to context bar when text selected:

| Control | Options | Fabric.js property |
|---------|---------|---------------------|
| Bold | toggle | `fontWeight: 'bold' / 'normal'` |
| Italic | toggle | `fontStyle: 'italic' / 'normal'` |
| Underline | toggle | `underline: true / false` |
| Strikethrough | toggle | `linethrough: true / false` |
| Case | Normal / Uppercase / Lowercase / Capitalize | `charCase` (custom, apply via JS) |

Icon buttons group: **B** `I` `U` `S` — each toggleable (highlight when active).

### 4.3 Letter Spacing & Line Height

Add sliders in context bar:
- **Letter spacing:** -5 to +20 (fabric `fontFamily` CSS property, Fabric uses canvas context)
  - Use `ctx.letterSpacing` on canvas 2D context (Fabric exposes via object properties)
- **Line height:** 0.8 to 3.0 (default 1.4) — Fabric's `lineHeight` property

### 4.4 Text Shadow / Drop Shadow

Add a "fx" button in context bar → opens shadow panel:
- **X offset:** -20 to +20 px
- **Y offset:** -20 to +20 px
- **Blur:** 0 to 20 px
- **Color:** with opacity (alpha)

**Fabric implementation:** `fabric.Textbox` does not have built-in shadow. Use `fabric.Shadow`:
```js
obj.set({
  shadow: new fabric.Shadow({
    color: 'rgba(0,0,0,0.5)',
    blur: 10,
    offsetX: 4,
    offsetY: 4
  })
});
```

### 4.5 Text Outline (Stroke)

Add outline controls in same "fx" panel:
- **Stroke color:** color picker
- **Stroke width:** 0 to 10 px

**Fabric implementation:**
```js
obj.set({
  stroke: '#000000',
  strokeWidth: 2
});
```
Note: Requires `paintFirst: 'stroke'` for proper rendering on Textbox.

### 4.6 Text Rotation Input

Add rotation input in context bar:
- **Degrees:** 0–360 circular dial or number input
- **Snap:** optional 0°, 45°, 90° snap

**Fabric:** `obj.set('angle', value)` — already supported, just expose UI.

### 4.7 Text Alignment (Already Partial)

Currently supports `textAlign: 'left' | 'center' | 'right'`.
Expand with:
- **Align left** `⌒`
- **Align center** `⊡`
- **Align right** `⌐`
- **Justify** `≡` (for multi-line text)

### 4.8 Multi-Column Text Support

**UI:** "Columns" slider (1 to 4) when text element selected.
**Implementation:** For a `Textbox`, set `width` per column and use manual line breaks
or create multiple text objects side by side.
*Note: Fabric.js Textbox doesn't natively support columns. Alternative: create
a wrapper group of text objects.*

### 4.9 Text Background / Highlight

Add color picker for text background in context bar:
- **Background color** (with alpha/opacity slider)
- Enable when text element selected

**Fabric implementation:**
```js
obj.set({
  textBackgroundColor: 'rgba(255,255,0,0.3)'
});
```
Note: Fabric.js `textBackgroundColor` available on Textbox.

### 4.10 Curved / Warped Text (Arc Path)

Fabric.js doesn't natively curve Textbox, but `fabric.Path` + `fabric.Text` along path works.
**UI approach:**
1. Add "Curve" button in context bar → opens arc control panel
2. **Arc presets:** Flat → slight curve → U-shape → circular
3. Use SVG path text or approximate with positioned characters

**Alternative simpler implementation:** Apply `skewX`/`skewY` for a perspective warp effect:
```js
obj.set({ skewX: 15 }); // lean right
```

---

## 5. BACKGROUND Tool Expansion

### 5.1 Solid Color with Opacity

Currently: `fabricCanvas.backgroundColor = '#ffffff'` (no alpha support).

**Improvement:** Use a full-canvas rect object for background (Fabric.js limitation: `backgroundColor`
does not support opacity). Implementation:

```js
// Add background rect that fills canvas
const bgRect = new fabric.Rect({
  left: 0, top: 0,
  width: canvasWidth, height: canvasHeight,
  fill: colorWithAlpha, // rgba() or fabric gradient
  selectable: false, evented: false, excludeFromExport: false,
  elementId: '__background__'
});
fabricCanvas.add(bgRect);
fabricCanvas.sendToBack(bgRect);
```

Add opacity slider (0–100%) alongside solid color picker.

### 5.2 Gradient Editor

**Current state:** Partial — supports `gradient` type with `angle` and `stops[]`

**Expand to full gradient editor:**

**Linear gradient:**
- **Angle:** 0–360° with visual dial
- **Stops:** 2–8 color stops with position slider (0–100%)
- **Add stop** button; click stop to remove

**Radial gradient:**
- Add `type: 'radial'` to background state
- **Center X/Y:** position of focal point
- **Radius:** 0–100%
- Same color stops as linear

**UI:** Bottom sheet with:
- Gradient type toggle: Linear / Radial
- Angle slider (for linear) or center point picker
- Color stop timeline (like Photoshop/GCanva)
- Add/remove stop buttons

**Fabric implementation:**
```js
const g = new fabric.Gradient({
  type: 'linear', // or 'radial'
  gradientUnits: 'pixels',
  coords: { x1: 0, y1: 0, x2: w, y2: 0 }, // angle-based
  colorStops: [
    { offset: 0, color: '#ff0000' },
    { offset: 1, color: '#0000ff' }
  ]
});
bgRect.set('fill', g);
```

### 5.3 Image as Background

When user selects "Image" in BG panel:
1. Show image upload/URL dialog
2. Apply image as canvas background (full cover, centered)
3. Optional overlay: semi-transparent solid color over image

**Fabric implementation:** `fabricCanvas.backgroundImage = url`
```js
fabric.Image.fromURL(url, (img) => {
  img.set({
    width: fabricCanvas.width,
    height: fabricCanvas.height,
    originX: 'left', originY: 'top'
  });
  fabricCanvas.backgroundImage = img;
  fabricCanvas.renderAll();
});
```

### 5.4 Pattern Backgrounds

Add built-in pattern library:

| Pattern Name | Description |
|--------------|-------------|
| Dots | White dots on dark background, configurable size |
| Stripes | Diagonal or horizontal stripes, configurable angle/color |
| Grid | Subtle grid lines |
| Chevron | V-shaped repeating pattern |
| Halftone | Dot-screen pattern |
| Confetti | Scattered shapes |

**Implementation:**
- Use `<canvas>` to render pattern → convert to data URL → set as background image
- Or use `fabric.Pattern` with `fabric.PatternPaint` for repeating fill

**UI:** Pattern picker grid in BG sheet, click to apply. Show customization options per pattern.

### 5.5 Background Blur & Overlay

**Blur:** When background is an image, add blur control slider (0–20px).
Use CSS filter on the background image element or Fabric.js `Blur` filter on the image object.

**Overlay:** Semi-transparent solid color layer over image or pattern background.
- Overlay color + opacity slider
- Render as separate rect on top of background

---

## 6. EXPORT Tool Expansion

### 6.1 PNG with Transparency

**Current:** Export via server `/api/export` returns PNG (presumably with white background).

**Change:** Add "Transparent background" checkbox in export panel.
When checked: `fabricCanvas.backgroundColor = null` and background elements excluded from export.

**Client-side alternative:**
```js
const dataURL = canvas.toDataURL({
  format: 'png',
  enableRetinaScaling: true,
  multiplier: exportMultiplier
});
```

### 6.2 JPEG Export with Quality Control

Add JPEG format option with quality slider (1–100, default 90).

**Implementation:**
```js
const dataURL = canvas.toDataURL({
  format: 'jpeg',
  quality: 0.9,
  multiplier: exportMultiplier
});
```

### 6.3 PDF Export (A4 / A3 / Letter)

**Implementation options:**
1. **Server-side:** POST to `/api/export` with `{ format: 'pdf', size: 'A4' }` → use `pdfkit` or similar on server
2. **Client-side:** Use `jsPDF` library in PWA

**Sizes:**
| Name | Dimensions (mm) | Dimensions (px at 300dpi) |
|------|-----------------|---------------------------|
| A4 | 210 × 297 | 2480 × 3508 |
| A3 | 297 × 420 | 3508 × 4961 |
| Letter | 215.9 × 279.4 | 2551 × 3307 |

**UI:** Export sheet with format selector (PNG / JPEG / PDF) and size preset dropdown.

### 6.4 SVG Export

**Implementation:**
```js
const svg = fabricCanvas.toSVG({
  width: canvasWidth,
  height: canvasHeight,
  viewBox: { x: 0, y: 0, width: canvasWidth, height: canvasHeight }
});
// Download as .svg file
```

Add checkbox for "Include background" in SVG export.

### 6.5 Social Media Presets

Add preset sizes in export panel:

| Platform | Format | Dimensions (px) | Aspect |
|----------|--------|-----------------|--------|
| Instagram Story | Story | 1080 × 1920 | 9:16 |
| Instagram Post | Post | 1080 × 1080 | 1:1 |
| Instagram Wide | Landscape | 1080 × 1350 | 4:5 |
| Twitter/X Header | Header | 1500 × 500 | 3:1 |
| Twitter/X Post | Post | 1200 × 675 | 16:9 |
| Facebook Cover | Cover | 820 × 312 | 41:15 |
| YouTube Thumbnail | Thumb | 1280 × 720 | 16:9 |
| LinkedIn Banner | Banner | 1584 × 396 | 4:1 |

**UI:** "Social Presets" section in export sheet — grid of platform icons.
On click: change canvas dimensions to preset, then show export options.

### 6.6 Resolution / DPI Selector

Add DPI picker: 72 (web), 150 (screen), 300 (print), 600 (high-quality print).

**Multiplier calculation:**
```js
const baseDPI = 72;
const dpiMultiplier = selectedDPI / baseDPI;
// For 300 DPI export on 300 DPI canvas: multiplier = 1
// For 600 DPI: multiplier = 2
```

### 6.7 Background Bleed / Margin Options

Add margin/bleed settings in export:
- **Bleed:** 0–10 mm (default 3mm for print)
- **Safe zone:** Visual indicator showing inner margin

**Implementation:** Scale canvas to include bleed, render background extended beyond trim edge.

---

## 7. Context Bar UI Improvements

### 7.1 Element-Type-Aware Controls

Currently shows only: Delete, Size slider, Color picker (hardcoded for text/shape).

**Expand to dynamic panel based on selected element type:**

| Element Type | Controls Shown |
|--------------|----------------|
| Text | Font family, size, bold/italic/underline/strikethrough toggles, color, alignment, letter spacing, line height, shadow toggle, rotation |
| Image | Opacity, filters button, crop button, aspect lock toggle, flip H/V, reset |
| Shape | Fill color, stroke color, stroke width, border radius, opacity |
| All | Lock toggle, opacity slider, delete, duplicate, layer controls |

**Implementation:** `updateContextBar()` checks `active.type` and rebuilds inner HTML accordingly.

### 7.2 Layer Ordering

Add buttons in context bar:
- **⬆ Bring Forward** — `fabricCanvas.bringForward(obj)`
- **⬇ Send Backward** — `fabricCanvas.sendBackwards(obj)`
- **⬆ Bring to Front** — `fabricCanvas.bringToFront(obj)`
- **⬇ Send to Back** — `fabricCanvas.sendToBack(obj)`

Icon buttons next to delete.

### 7.3 Alignment Tools

Show alignment buttons in context bar when 2+ elements selected:
- **Align left** `|⌒`
- **Align center** `⊡`
- **Align right** `⌐|`
- **Align top** `⌒`
- **Align middle** `⊡`
- **Align bottom** `⌐`

Use Fabric.js selection bounding box for alignment calculations.

### 7.4 Lock / Unlock Element

Add lock button: `🔒` / `🔓`
- Toggle `obj.selectable = false; obj.evented = false` (locked)
- Or toggle via `obj.lockMovementX/Y` etc.

### 7.5 Duplicate Element

Add duplicate button: `📋`
- Clone object with `obj.clone()` → offset by 10mm → add to canvas → sync to server
- New element gets new `elementId` from server POST

### 7.6 Opacity Slider

Add opacity slider (0–100%) for all element types.
```js
obj.set({ opacity: 0.5 });
fabricCanvas.renderAll();
```

---

## 8. Implementation Priorities

### Phase 1 (MVP) — Quick Wins
1. Image file upload (existing `/api/upload` endpoint)
2. Image URL import
3. JPEG export + quality control
4. Text font family picker (Google Fonts)
5. Text bold/italic/underline toggles
6. Background solid color with opacity
7. Layer ordering controls (bring forward/backward)
8. Duplicate element

### Phase 2 (Core UX)
1. Text shadow/outline effects
2. Gradient editor (linear)
3. Image crop tool
4. Text alignment controls (justify)
5. Context bar — element-type-aware dynamic controls
6. Lock/unlock element
7. Opacity slider
8. SVG export

### Phase 3 (Polish)
1. Image filters (grayscale, blur, brightness, contrast, sepia)
2. Curved text (arc path)
3. Radial gradient
4. Pattern backgrounds
5. Stock photo search (Unsplash/Pexels)
6. PDF export
7. Social media presets
8. DPI/resolution selector

---

## 9. UI Component Inventory

| Component | Type | States | Location |
|-----------|------|--------|---------|
| Tool button | `.tool-btn` | default, active, disabled | Bottom bar |
| Context bar | `#ctx-bar` | hidden, visible, dynamic content | Fixed top of bottom area |
| Sheet/Bottom sheet | `#menu-sheet` style | open, closed | Overlay |
| Slider | `.ctx-slider` | default, active, disabled | Context bar |
| Color picker | `.ctx-color` + `<input type="color">` | default | Context bar |
| Toggle button group | icon-btn group | on/off per button | Context bar |
| Font dropdown | `<select>` | default, open, selected | Context bar |
| Export panel | bottom sheet | format selection, options | Overlay |
| Image filter panel | bottom sheet | slider per filter | Overlay |

---

## 10. Notes & Edge Cases

- **CORS:** Image URLs must be loaded with `crossOrigin: 'anonymous'` for Fabric.js filters to work. Use proxy server if needed.
- **Memory:** Large images should be resized before adding to canvas (max 2000px on any side).
- **Undo:** Server has `/api/undo` but not `/api/redo` — phase 3 could add redo.
- **Multi-select:** Fabric.js handles multi-select via shift-click; alignment tools should work on selection.
- **RTL text:** Not currently supported; Figma/Canva support for Arabic/Hebrew requires `direction` property.
- **Offline:** PWA service worker already registered; consider caching Google Fonts for offline use.

---

## 11. Reference Sources

- Canva Help Center: image resize, crop, gradients, transparency, text effects (curved text, shadow/outline)
- Figma Learn: text properties, export formats (PNG, JPEG, SVG, PDF), resolution settings
- Fabric.js v5.3.0 documentation: Gradient, Shadow, filters, Image operations
- Unsplash API documentation: photo search endpoints
- Pexels API documentation: stock photo search

---

*End of spec.*