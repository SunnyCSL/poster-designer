# Camera Shape Scanner — Feature Specification

## 1. Overview

**Name:** Camera Shape Scanner
**Type:** PWA Feature
**Summary:** Allows users to photograph a physical shape with the device camera, automatically detects and outlines its contour, lets the user refine the outline, and imports it as an editable `fabric.Path` object on the poster canvas.
**Target:** Mobile-first (iOS Safari, Android Chrome), desktop fallback.

---

## 2. UI Flow

```
[Tap "Scan Shape" button]
        ↓
[Camera modal opens]
    → Live preview with crosshair overlay
    → Rear camera (default), toggle front/back button
    → Flash toggle button
    → Capture button (large, centred)
        ↓
[Photo captured → processing overlay]
        ↓
[Detection preview screen]
    → Edge outline overlaid on photo
    → "Retake" / "Use This" buttons
    → Loading spinner during edge detection
        ↓
[Anchor adjustment screen]
    → Draggable anchor points on the contour
    → Tap to add anchor, long-press to remove
    → "Straighten" button (snaps to lines/curves)
    → "Close Path" toggle (auto-close last→first)
    → "Confirm" / "Cancel" buttons
        ↓
[Shape added to poster canvas]
    → fabric.Path created with default semi-transparent fill
    → Immediately selected for move/scale/rotate
```

---

## 3. UI Components

### 3.1 Entry Point — "Scan Shape" Button

- **Location:** Inside the Shape picker sheet (`#shape-sheet`), as a 5th option alongside Rectangle, Circle, Triangle, Line.
- **Appearance:**
  ```html
  <div class="shape-opt" id="btn-scan-shape">
    <div style="font-size:28px;">📷</div>
    <span>Scan</span>
  </div>
  ```
- **Trigger:** Opens the camera modal.

### 3.2 Camera Modal

- **Container:** Full-screen overlay, z-index `80`.
- **Background:** `rgba(0,0,0,0.95)`.
- **Layout (top to bottom):**
  - **Top bar (48px):** "Cancel" (left), "Scan Shape" title (centre), Flash icon button (right)
  - **Camera preview:** Full-bleed `<video>` element, mirrored on front camera
  - **Crosshair overlay:** Semi-transparent centre rectangle (60% width, 50% height) with corner brackets — indicates scan target area
  - **Bottom controls (100px):**
    - Thumbnail of last photo (left, 56px circle)
    - Capture button (centre, 72px white circle, 64px inner circle)
    - Camera flip button (right, icon)
- **Flash states:** Off (default) → On → Auto (cycle on tap)

### 3.3 Processing Overlay

- Shown immediately after capture.
- Semi-transparent dark overlay covering the captured photo.
- Centred spinner + "Analyzing shape…" text.
- Auto-advances when contour detection is complete.

### 3.4 Detection Preview Screen

- **Canvas element** showing the captured photo.
- **SVG overlay** drawn on top showing the detected contour as a stroke (2px, `--accent` colour).
- Filled regions outside the contour are darkened (mask effect).
- **Bottom bar:** "Retake" (secondary) + "Adjust" (primary accent) buttons.
- If no shape detected: error banner "No clear shape found — try better lighting" with "Retake" button.

### 3.5 Anchor Adjustment Screen

- Same canvas + SVG overlay as Detection Preview, but anchor points are visible and draggable.
- **Anchor points:** 12px circles, `--accent` fill, white 2px border.
- **Active anchor:** larger (16px), pulsing animation.
- **Controls above canvas:**
  - "Add Point" toggle — when ON, tapping canvas adds anchor
  - "Straighten Lines" button — auto-detects and snaps collinear points
  - "Close Path" toggle (ON by default)
- **Controls below canvas:**
  - "Undo" (removes last added anchor)
  - "Confirm Shape" (primary)
  - "Cancel"

### 3.6 Shape on Canvas

- Once confirmed, a `fabric.Path` object is created and added to the poster canvas.
- Default fill: `rgba(88, 166, 255, 0.25)` (accent blue, 25% opacity).
- Stroke: `rgba(88, 166, 255, 0.6)`, 1.5px.
- The object is immediately selected so the user can move/resize/rotate it.
- A toast/flash message: "Shape added — drag to position".

---

## 4. Technical Architecture

### 4.1 Camera Access (`CameraManager` class)

```javascript
class CameraManager {
  stream: MediaStream | null
  facingMode: 'environment' | 'user'

  async start(previewEl)        // opens camera, renders to <video>
  async switchCamera()          // flips facingMode and restarts
  async toggleFlash()          // cycles: off → on → auto
  capture(): ImageData          // draws video frame to off-screen canvas
  stop()                        // stops all tracks
}
```

- Uses `navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: { ideal: 1920 } } })`.
- Falls back to any available camera if `facingMode` is not supported.
- On permission denial: shows error banner with instructions to enable in browser settings.

### 4.2 Edge Detection Pipeline

**Step 1 — Grayscale & resize**
- Capture at max 1920×1920 px (for performance).
-缩放至 800px max dimension for detection, preserving aspect ratio.
- Convert to grayscale using canvas `getImageData` + pixel manipulation.

**Step 2 — Gaussian blur**
- 5×5 Gaussian kernel to reduce noise.

**Step 3 — Sobel gradient magnitude**
- Compute Gx and Gy using 3×3 Sobel kernels.
- Magnitude = `sqrt(Gx² + Gy²)`.

**Step 4 — Non-maximum suppression (NMS)**
- Thins edges to 1-pixel width.

**Step 5 — Double threshold**
- `low = 50`, `high = 150` (adjustable via hidden debug panel).
- Strong edges: `> high` → kept.
- Weak edges: `> low && < high` → kept if connected to strong edge.
- Everything else → discarded.

**Step 6 — Edge tracking by hysteresis**
- Keeps only connected weak edges that link to strong edges.

**Step 7 — Contour extraction**
- Moore-neighbour tracing or scanline approach to find closed contours.
- Filter by area: discard contours smaller than 0.5% of image area.
- Sort by perimeter descending → take the largest.

**Step 8 — Simplification**
- Douglas-Peucker algorithm with tolerance 2px (in detection-image space).
- Outputs an array of `{x, y}` points (anchor points).

### 4.3 Path Conversion

```javascript
function contourToFabricPath(points, sourceW, sourceH, targetW, targetH) {
  // Scale points to target canvas dimensions
  const scaled = points.map(p => ({
    x: (p.x / sourceW) * targetW,
    y: (p.y / sourceH) * targetH,
  }));

  // Convert to SVG path string (M, L, Q, Z)
  const pathStr = pointsToSVGPath(scaled);
  // e.g. "M 10,20 L 30,40 L 50,60 Z"

  return new fabric.Path(pathStr, {
    fill: 'rgba(88,166,255,0.25)',
    stroke: 'rgba(88,166,255,0.6)',
    strokeWidth: 1.5,
    selectable: true,
    evented: true,
  });
}
```

- The path is added via `fabricCanvas.add(path)` and `fabricCanvas.setActiveObject(path)`.
- The canvas coordinates are in mm (via `mmToPx`) not screen pixels, so the detection coordinates are scaled to the canvas dimensions.

### 4.4 Anchor Point Editing

- Anchors rendered as absolutely-positioned `<div>` elements over the preview canvas.
- Each anchor stores its index in the contour array.
- `pointerdown` → `pointermove` → `pointerup` drag handling.
- While dragging, the SVG overlay is updated in real-time.
- "Straighten" runs Ramer-Douglas-Peucker on selected segments with a tighter tolerance (1px).

### 4.5 File Structure

All Camera Shape Scanner code lives in a single self-contained `<script>` block added to `pwa/index.html`. It is partitioned into:

```
// === Camera Manager ===
// === Edge Detector (pure pixel processing) ===
// === Contour Processor (scanline tracing) ===
// === UI Controller (modal state machine) ===
// === Path Builder (SVG string → fabric.Path) ===
```

### 4.6 Web Workers

- Edge detection runs in a **Web Worker** (`camera-edge-worker.js`) to avoid blocking the main thread UI.
- Worker receives `ImageData` (grayscale pixel array), returns contour points.
- Worker file lives at `pwa/camera-edge-worker.js` and is loaded via `URL.createObjectURL(workerBlob)` inline or as a separate file.
- Fallback: synchronous (blocking) version if Worker is unavailable.

---

## 5. Error Handling & Edge Cases

| Scenario | Handling |
|---|---|
| Camera permission denied | Full-screen message with "Open Settings" link and "Use Photo Library Instead" button |
| No camera hardware found | Banner: "Camera not available on this device" + hide scan button |
| Very low light (detection fails) | "Could not detect a clear shape. Try in better lighting or use a contrasting background." + Retake |
| Shape too small (< 1% of image area) | Same message as above |
| Detected contour has > 500 points | Auto-simplify with higher tolerance |
| User confirms with < 3 points | Minimum 3 points enforced (triangle fallback) |
| Browser does not support getUserMedia | Graceful degradation: show "Camera not supported" and hide scan button |

---

## 6. Performance Targets

- Camera open → preview visible: < 1.5s
- Capture → edge detection result: < 3s on mid-range mobile (Snapdragon 7xx / A13 Bionic)
- Anchor drag: 60fps (use `requestAnimationFrame` for SVG updates)
- Edge detection worker: < 2s for 800×800 grayscale image

---

## 7. Dependencies & CDN Resources

No new external libraries required. Edge detection is implemented from scratch using Canvas pixel manipulation and the Web Worker API. The feature adds:

1. **`pwa/camera-edge-worker.js`** — Web Worker file for edge detection
2. **Inline `<script>` block** appended to `pwa/index.html` — all UI and business logic

Optional future enhancement: Replace custom edge detection with [opencv.js](https://docs.opencv.org/4.x/d4/da1/tutorial_js_binding.html) WASM build for higher quality contours. This would add ~2MB WASM but dramatically improve detection accuracy on complex shapes.

---

## 8. CSS Variables (new additions to existing `:root`)

```css
--scanner-accent: #58A6FF;
--scanner-bg: rgba(0,0,0,0.95);
--scanner-anchor: #58A6FF;
--scanner-stroke: rgba(88,166,255,0.8);
--scanner-fill: rgba(88,166,255,0.25);
--scanner-overlay: rgba(0,0,0,0.6);
```

---

## 9. State Machine

```
CLOSED
  ↓ [tap "Scan"]
OPEN_CAMERA → PREVIEW
  ↓ [capture]
PROCESSING
  ↓ [detection done]
DETECTION_PREVIEW
  ↓ [tap "Adjust"]
ANCHOR_EDIT
  ↓ [tap "Confirm"]
→ fabric.Path added → CLOSED

Any state:
  ↓ [tap "Cancel" / "Retake"]
→ CLOSED (retake returns to OPEN_CAMERA)
```

---

## 10. API: Adding Scanned Shape to Poster

```javascript
// Called by UI layer once user confirms anchors
async function addScannedShapeToCanvas(points) {
  const state = getCurrentState(); // mmToPx conversion needed
  const targetW = mmToPx(state.meta.width_mm);
  const targetH = mmToPx(state.meta.height_mm);

  const pathStr = pointsToSVGPath(scalePoints(points, sourceW, sourceH, targetW, targetH));
  const fabPath = new fabric.Path(pathStr, {
    fill: 'rgba(88,166,255,0.25)',
    stroke: 'rgba(88,166,255,0.6)',
    strokeWidth: mmToPx(0.5), // 0.5mm stroke
  });

  fabricCanvas.add(fabPath);
  fabricCanvas.setActiveObject(fabPath);
  fabricCanvas.renderAll();

  // Sync to server
  const element = {
    id: generateId(),
    type: 'shape',
    shape: 'path',
    pathData: pathStr,
    style: { fillColor: 'rgba(88,166,255,0.25)', strokeColor: 'rgba(88,166,255,0.6)' },
    position: { x: 0, y: 0 },
  };
  await fetch(`${SERVER}/api/element`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(element),
  });
}
```

---

## 11. Mobile-Specific Considerations

- **iOS Safari:** `getUserMedia` requires HTTPS. Works on localhost. Must handle `MediaDevices` not being available before use — check `navigator.mediaDevices?.getUserMedia`.
- **Orientation change:** Re-fit canvas and re-render anchors on `window.resize` / `orientationchange`.
- **Notch / dynamic island:** Camera modal uses `padding-top: env(safe-area-inset-top)` and `padding-bottom: env(safe-area-inset-bottom)` to avoid being obscured.
- **Memory:** Process images at max 1920px dimension. Reuse `ImageData` buffers between frames.