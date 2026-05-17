# Poster Designer — Shape Library Expansion Spec

## Status
Draft for implementation.

---

## 1. Overview

The Poster Designer PWA currently has only 4 shapes: Rectangle, Circle, Triangle, Line.
This spec expands the library to **24 shapes** across **6 categories**, implemented via `fabric.Path`
so all shapes work uniformly with fabric.js's selection, scaling, rotation, and styling.

**Key design decisions:**
- All new shapes use `fabric.Path` (SVG path syntax) so they behave identically to the built-in shapes.
- The HTML shape picker becomes a **scrollable categorized panel** (not a single row).
- Shape metadata (name, category, SVG path, default size hint) is declared in a single `SHAPES` constant — the picker UI and the canvas rendering both consume it.
- No backend changes are required; shapes are purely client-side rendering. The `shape` field on the element JSON is the key identifier sent to the server and stored in `state.json`.

---

## 2. Shape Catalog

All coordinates use a **100×100 viewport** centered at (0,0) for the path definition. The `left`/`top` and `width`/`height` of the fabric object are set independently at render time (from the element's `position` in mm). `fill: 'transparent'` is used for open shapes (lines, arrows, brackets); `fill: styleColor` for closed shapes.

| # | Internal ID | Display Name | Category | Emoji | SVG Path | fill | Notes |
|---|-------------|--------------|----------|-------|----------|------|-------|
| 1 | `rect` | Rectangle | Basic | 🟪 | `M-50,-50 L50,-50 L50,50 L-50,50 Z` | color | existing |
| 2 | `circle` | Circle | Basic | ⭕ | (fabric.Circle) | color | existing |
| 3 | `triangle` | Triangle | Basic | 🔺 | `M0,-50 L50,40 L-50,40 Z` | color | existing |
| 4 | `line` | Line | Basic | ➖ | `M-50,0 L50,0` | transparent (stroke) | existing |
| 5 | `star` | Star | Basic | ⭐ | `M0,-50 L12,-18 L47,-15 L21,9 L29,42 L0,24 L-29,42 L-21,9 L-47,-15 L-12,-18 Z` | color | 5-pointed star |
| 6 | `pentagon` | Pentagon | Basic | Pentagon | `M0,-50 L48,-15 L29,41 L-29,41 L-48,-15 Z` | color | |
| 7 | `hexagon` | Hexagon | Basic | ⬡ | `M0,-50 L43,-25 L43,25 L0,50 L-43,25 L-43,-25 Z` | color | |
| 8 | `octagon` | Octagon | Basic | 🟧 | `M-21,-50 L21,-50 L50,-21 L50,21 L21,50 L-21,50 L-50,21 L-50,-21 Z` | color | |
| 9 | `diamond` | Diamond | Basic | 🔷 | `M0,-50 L40,0 L0,50 L-40,0 Z` | color | |
| 10 | `parallelogram` | Parallelogram | Basic | ▱ | `M-40,-30 L50,-30 L40,30 L-50,30 Z` | color | |
| 11 | `trapezoid` | Trapezoid | Basic | трапеция | `M-50,-35 L50,-35 L35,35 L-35,35 Z` | color | |
| 12 | `arrow-right` | Arrow Right | Arrows | ➡ | `M-50,0 L30,0 L30,-25 L60,0 L30,25 L30,0 Z` | color | filled arrow |
| 13 | `arrow-left` | Arrow Left | Arrows | ⬅ | `M50,0 L-30,0 L-30,-25 L-60,0 L-30,25 L-30,0 Z` | color | |
| 14 | `arrow-up` | Arrow Up | Arrows | ⬆ | `M0,50 L0,-30 L-25,-30 L0,-60 L25,-30 L0,-30 Z` | color | |
| 15 | `arrow-down` | Arrow Down | Arrows | ⬇ | `M0,-50 L0,30 L-25,30 L0,60 L25,30 L0,30 Z` | color | |
| 16 | `chevron-right` | Chevron Right | Arrows | › | `M-30,-40 L10,-40 L50,0 L10,40 L-30,40 L-50,0 Z` | transparent | open chevron |
| 17 | `chevron-left` | Chevron Left | Arrows | ‹ | `M30,-40 L-10,-40 L-50,0 L-10,40 L30,40 L50,0 Z` | transparent | |
| 18 | `heart` | Heart | Symbols | ❤️ | `M0,35 C0,35 -50,-15 -50,-30 C-50,-50 -25,-50 0,-30 C25,-50 50,-50 50,-30 C50,-15 0,35 0,35 Z` | color | |
| 19 | `cross` | Cross | Symbols | ✚ | `M-30,-50 L30,-50 L30,-30 L50,-30 L50,30 L30,30 L30,50 L-30,50 L-30,30 L-50,30 L-50,-30 L-30,-30 Z` | color | plus/cross shape |
| 20 | `plus` | Plus | Symbols | ➕ | `M-50,0 L50,0 M0,-50 L0,50` | transparent (stroke) | just two lines |
| 21 | `minus` | Minus | Symbols | ➖ | `M-50,0 L50,0` | transparent (stroke) | horizontal line |
| 22 | `cloud` | Cloud | Nature | ☁ | `M-40,20 C-55,20 -60,5 -50,0 C-55,-15 -35,-20 -20,-10 C-10,-25 20,-25 30,-10 C50,-15 55,5 40,20 L40,35 L-40,35 Z` | color | |
| 23 | `moon` | Moon | Nature | 🌙 | `M20,-45 C40,-45 50,-20 40,5 C50,25 30,45 5,45 C-25,45 -40,15 -30,-15 C-20,-40 0,-45 20,-45 Z` | color | crescent |
| 24 | `sun` | Sun | Nature | ☀ | `M0,-50 L0,50 M-50,0 L50,0 M-35,-35 L35,35 M35,-35 L-35,35` + circle | transparent (stroke) | rays + center circle |
| 25 | `drop` | Droplet | Nature | 💧 | `M0,-50 C25,-20 50,20 0,50 C-50,20 -25,-20 0,-50 Z` | color | |
| 26 | `triangle-right` | Triangle Right | Basic | ▶ | `M-50,-40 L40,-40 L40,40 L-50,-40 Z` | color | |
| 27 | `bracket-right` | Bracket Right | Symbols | ] | `M20,-50 L-35,-50 L-35,50 L20,50` | transparent (stroke) | open bracket |
| 28 | `bracket-left` | Bracket Left | Symbols | [ | `M-20,-50 L35,-50 L35,50 L-20,50` | transparent (stroke) | |

---

## 3. Category Groupings

| Category | Shapes |
|----------|--------|
| **Basic** | Rectangle, Circle, Triangle, Line, Star, Pentagon, Hexagon, Octagon, Diamond, Parallelogram, Trapezoid, Triangle Right |
| **Arrows** | Arrow Right, Arrow Left, Arrow Up, Arrow Down, Chevron Right, Chevron Left |
| **Symbols** | Heart, Cross, Plus, Minus, Bracket Right, Bracket Left |
| **Nature** | Cloud, Moon, Sun, Droplet |

---

## 4. UI Layout — Shape Picker

Replace the flat single-row `shape-row` with a scrollable panel with collapsible category sections.

### Proposed HTML Structure

```html
<div id="shape-picker">
  <div id="shape-sheet">
    <div class="shape-category" data-category="Basic">
      <div class="shape-category-header">
        <span class="shape-category-title">Basic</span>
        <span class="shape-category-chevron">▼</span>
      </div>
      <div class="shape-category-items">
        <!-- shape-opt elements -->
      </div>
    </div>
    <!-- repeat per category -->
  </div>
</div>
```

### CSS Requirements

```css
/* Container */
#shape-picker {
  position: fixed;
  bottom: 80px;         /* above bottom toolbar */
  left: 50%;
  transform: translateX(-50%);
  z-index: 200;
  display: none;
  flex-direction: column;
  max-height: 320px;
  overflow-y: auto;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 8px;
  gap: 4px;
  width: 360px;
}

#shape-picker.visible { display: flex; }

/* Category */
.shape-category { }
.shape-category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-dim);
  user-select: none;
}
.shape-category-header:hover { color: var(--text); }

.shape-category-items {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  padding: 4px 2px;
}
.shape-category.collapsed .shape-category-items { display: none; }

/* Individual shape option */
.shape-opt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  border-radius: 8px;
  cursor: pointer;
}
.shape-opt:hover { background: var(--hover); }
.shape-opt svg { width: 28px; height: 28px; }
.shape-opt span { font-size: 10px; color: var(--text-dim); }
```

---

## 5. JavaScript Shape Registry

Add a `SHAPES` constant at the top of the `<script>` block that drives both the picker rendering and the canvas rendering.

```javascript
const SHAPES = {
  // ── BASIC ──────────────────────────────────────────────────────────────
  rect: {
    label: 'Rectangle', category: 'Basic',
    svg: `<rect x="4" y="4" width="20" height="16" rx="2" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Rect({
      left: x, top: y, width: w, height: h,
      fill: style.fillColor || style.color || '#58A6FF',
      originX: 'left', originY: 'top', angle,
      rx: 4, ry: 4,
    }),
  },
  circle: {
    label: 'Circle', category: 'Basic',
    svg: `<circle cx="14" cy="14" r="10" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Circle({
      left: x, top: y, radius: Math.min(w, h) / 2,
      fill: style.fillColor || style.color || '#58A6FF',
      originX: 'left', originY: 'top', angle,
    }),
  },
  triangle: {
    label: 'Triangle', category: 'Basic',
    svg: `<polygon points="14,2 26,26 2,26" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Triangle({
      left: x, top: y, width: w, height: h,
      fill: style.fillColor || style.color || '#58A6FF',
      originX: 'left', originY: 'top', angle,
    }),
  },
  line: {
    label: 'Line', category: 'Basic',
    svg: `<line x1="2" y1="14" x2="26" y2="14" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Line([x, y, x + w, y], {
      stroke: style.strokeColor || style.color || '#58A6FF',
      strokeWidth: style.strokeWidth || 3,
    }),
  },
  star: {
    label: 'Star', category: 'Basic',
    svg: `<polygon points="14,1 17.5,9 26,9 19.5,14.5 22,23 14,18 6,23 8.5,14.5 2,9 10.5,9" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M0,-50 L12,-18 L47,-15 L21,9 L29,42 L0,24 L-29,42 L-21,9 L-47,-15 L-12,-18 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  pentagon: {
    label: 'Pentagon', category: 'Basic',
    svg: `<polygon points="14,1 26,9 22,25 6,25 2,9" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M0,-50 L48,-15 L29,41 L-29,41 L-48,-15 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  hexagon: {
    label: 'Hexagon', category: 'Basic',
    svg: `<polygon points="14,1 25,7 25,21 14,27 3,21 3,7" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M0,-50 L43,-25 L43,25 L0,50 L-43,25 L-43,-25 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  octagon: {
    label: 'Octagon', category: 'Basic',
    svg: `<polygon points="7,1 21,1 27,7 27,21 21,27 7,27 1,21 1,7" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M-21,-50 L21,-50 L50,-21 L50,21 L21,50 L-21,50 L-50,21 L-50,-21 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  diamond: {
    label: 'Diamond', category: 'Basic',
    svg: `<polygon points="14,1 27,14 14,27 1,14" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M0,-50 L40,0 L0,50 L-40,0 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  parallelogram: {
    label: 'Parallelogram', category: 'Basic',
    svg: `<polygon points="5,5 25,5 20,23 0,23" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M-40,-30 L50,-30 L40,30 L-50,30 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  trapezoid: {
    label: 'Trapezoid', category: 'Basic',
    svg: `<polygon points="3,7 25,7 20,25 8,25" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M-50,-35 L50,-35 L35,35 L-35,35 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  'triangle-right': {
    label: 'Triangle R', category: 'Basic',
    svg: `<polygon points="1,4 27,14 1,24" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M-50,-40 L40,-40 L40,40 L-50,-40 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },

  // ── ARROWS ─────────────────────────────────────────────────────────────
  'arrow-right': {
    label: 'Arrow →', category: 'Arrows',
    svg: `<polygon points="1,14 21,14 21,6 28,14 21,22 21,14" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M-50,0 L30,0 L30,-25 L60,0 L30,25 L30,0 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  'arrow-left': {
    label: 'Arrow ←', category: 'Arrows',
    svg: `<polygon points="27,14 7,14 7,6 0,14 7,22 7,14" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M50,0 L-30,0 L-30,-25 L-60,0 L-30,25 L-30,0 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  'arrow-up': {
    label: 'Arrow ↑', category: 'Arrows',
    svg: `<polygon points="14,1 14,21 6,21 14,28 22,21 14,21" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M0,50 L0,-30 L-25,-30 L0,-60 L25,-30 L0,-30 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  'arrow-down': {
    label: 'Arrow ↓', category: 'Arrows',
    svg: `<polygon points="14,27 14,7 6,7 14,0 22,7 14,7" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M0,-50 L0,30 L-25,30 L0,60 L25,30 L0,30 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  'chevron-right': {
    label: 'Chevron →', category: 'Arrows',
    svg: `<polyline points="4,5 20,14 4,23" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M-30,-40 L10,-40 L50,0 L10,40 L-30,40 L-50,0 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: 'transparent',
        stroke: style.strokeColor || style.color || '#58A6FF',
        strokeWidth: 3, strokeLineCap: 'round', strokeLineJoin: 'round',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  'chevron-left': {
    label: 'Chevron ←', category: 'Arrows',
    svg: `<polyline points="24,5 8,14 24,23" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M30,-40 L-10,-40 L-50,0 L-10,40 L30,40 L50,0 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: 'transparent',
        stroke: style.strokeColor || style.color || '#58A6FF',
        strokeWidth: 3, strokeLineCap: 'round', strokeLineJoin: 'round',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },

  // ── SYMBOLS ─────────────────────────────────────────────────────────────
  heart: {
    label: 'Heart', category: 'Symbols',
    svg: `<path d="M14,26 C14,26 2,16 2,9 C2,3 7,1 11,4 C13,5.5 14,7.5 14,7.5 C14,7.5 15,5.5 17,4 C21,1 26,3 26,9 C26,16 14,26 14,26Z" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M0,35 C0,35 -50,-15 -50,-30 C-50,-50 -25,-50 0,-30 C25,-50 50,-50 50,-30 C50,-15 0,35 0,35 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  cross: {
    label: 'Cross', category: 'Symbols',
    svg: `<polygon points="10,1 20,1 20,10 29,10 29,1 39,1 39,11 29,20 29,29 20,29 20,39 10,39 10,29 1,20 1,11 10,11" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M-30,-50 L30,-50 L30,-30 L50,-30 L50,30 L30,30 L30,50 L-30,50 L-30,30 L-50,30 L-50,-30 L-30,-30 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  plus: {
    label: 'Plus', category: 'Symbols',
    svg: `<line x1="14" y1="2" x2="14" y2="26" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><line x1="2" y1="14" x2="26" y2="14" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path('M-50,0 L50,0 M0,-50 L0,50', {
      left: x, top: y, scaleX: w / 100, scaleY: h / 100,
      fill: 'transparent',
      stroke: style.strokeColor || style.color || '#58A6FF',
      strokeWidth: 4, strokeLineCap: 'round',
      originX: 'left', originY: 'top', angle,
    }),
  },
  minus: {
    label: 'Minus', category: 'Symbols',
    svg: `<line x1="2" y1="14" x2="26" y2="14" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path('M-50,0 L50,0', {
      left: x, top: y, scaleX: w / 100, scaleY: h / 100,
      fill: 'transparent',
      stroke: style.strokeColor || style.color || '#58A6FF',
      strokeWidth: 4, strokeLineCap: 'round',
      originX: 'left', originY: 'top', angle,
    }),
  },
  'bracket-right': {
    label: 'Bracket ]', category: 'Symbols',
    svg: `<polyline points="22,4 8,4 8,24 22,24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path('M20,-50 L-35,-50 L-35,50 L20,50', {
      left: x, top: y, scaleX: w / 100, scaleY: h / 100,
      fill: 'transparent',
      stroke: style.strokeColor || style.color || '#58A6FF',
      strokeWidth: 4, strokeLineCap: 'round', strokeLineJoin: 'round',
      originX: 'left', originY: 'top', angle,
    }),
  },
  'bracket-left': {
    label: 'Bracket [', category: 'Symbols',
    svg: `<polyline points="6,4 20,4 20,24 6,24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path('M-20,-50 L35,-50 L35,50 L-20,50', {
      left: x, top: y, scaleX: w / 100, scaleY: h / 100,
      fill: 'transparent',
      stroke: style.strokeColor || style.color || '#58A6FF',
      strokeWidth: 4, strokeLineCap: 'round', strokeLineJoin: 'round',
      originX: 'left', originY: 'top', angle,
    }),
  },

  // ── NATURE ─────────────────────────────────────────────────────────────
  cloud: {
    label: 'Cloud', category: 'Nature',
    svg: `<path d="M7,22 C3,22 1,18 3,15 C1,10 6,6 12,8 C15,2 23,2 26,8 C32,6 37,11 35,16 L35,24 L3,24 Z" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M-40,20 C-55,20 -60,5 -50,0 C-55,-15 -35,-20 -20,-10 C-10,-25 20,-25 30,-10 C50,-15 55,5 40,20 L40,35 L-40,35 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  moon: {
    label: 'Moon', category: 'Nature',
    svg: `<path d="M22,4 C16,4 12,9 14,16 C16,23 23,27 28,24 C20,28 10,20 12,9 C14,0 20,-2 22,4Z" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M20,-45 C40,-45 50,-20 40,5 C50,25 30,45 5,45 C-25,45 -40,15 -30,-15 C-20,-40 0,-45 20,-45 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
  sun: {
    label: 'Sun', category: 'Nature',
    svg: `<line x1="14" y1="1" x2="14" y2="5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="14" y1="23" x2="14" y2="27" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="1" y1="14" x2="5" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="23" y1="14" x2="27" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="14" cy="14" r="6" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => {
      // Sun is a group: lines + center circle
      const centerX = x + w / 2, centerY = y + h / 2;
      const rayLen = w * 0.4;
      const grp = [
        new fabric.Line([centerX, centerY - rayLen * 1.5, centerX, centerY - rayLen * 0.6], {
          stroke: style.strokeColor || style.color || '#F59E0B', strokeWidth: 3, strokeLineCap: 'round',
        }),
        new fabric.Line([centerX, centerY + rayLen * 0.6, centerX, centerY + rayLen * 1.5], {
          stroke: style.strokeColor || style.color || '#F59E0B', strokeWidth: 3, strokeLineCap: 'round',
        }),
        new fabric.Line([centerX - rayLen * 1.5, centerY, centerX - rayLen * 0.6, centerY], {
          stroke: style.strokeColor || style.color || '#F59E0B', strokeWidth: 3, strokeLineCap: 'round',
        }),
        new fabric.Line([centerX + rayLen * 0.6, centerY, centerX + rayLen * 1.5, centerY], {
          stroke: style.strokeColor || style.color || '#F59E0B', strokeWidth: 3, strokeLineCap: 'round',
        }),
        new fabric.Circle({ left: x, top: y, radius: w * 0.28,
          fill: style.fillColor || style.color || '#F59E0B',
          originX: 'left', originY: 'top', angle,
        }),
      ];
      return grp;
    },
  },
  drop: {
    label: 'Droplet', category: 'Nature',
    svg: `<path d="M14,2 C22,10 27,17 14,27 C1,17 6,10 14,2Z" fill="currentColor"/>`,
    fabric: (style, x, y, w, h, angle) => new fabric.Path(
      'M0,-50 C25,-20 50,20 0,50 C-50,20 -25,-20 0,-50 Z', {
        left: x, top: y, scaleX: w / 100, scaleY: h / 100,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle,
      }
    ),
  },
};
```

---

## 6. Rendering — `addElementToCanvas` Update

The `addElementToCanvas` function (around line 616) currently has an if/else chain for `circle`, `triangle`, `line`, `rect`. Replace with a dispatch on `SHAPES`:

```javascript
function addElementToCanvas(el, selectIt = false) {
  const x = mmToPx(el.position?.x || 0);
  const y = mmToPx(el.position?.y || 0);
  const w = mmToPx(el.position?.width || 60);
  const h = mmToPx(el.position?.height || 60);
  const angle = el.position?.rotation || 0;
  const style = el.style || {};
  const shapeType = el.shape || style.shape || 'rect';

  let obj = null;

  if (SHAPES[shapeType]?.fabric) {
    const result = SHAPES[shapeType].fabric(style, x, y, w, h, angle);
    if (Array.isArray(result)) {
      // composite (e.g. sun = lines + circle group)
      const grp = new fabric.Group(result, {
        left: x, top: y,
        originX: 'left', originY: 'top', angle,
      });
      obj = grp;
    } else {
      obj = result;
    }
  } else {
    // fallback to built-in shapes
    if (shapeType === 'circle') {
      obj = new fabric.Circle({ left: x, top: y, radius: Math.min(w, h) / 2,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle });
    } else if (shapeType === 'triangle') {
      obj = new fabric.Triangle({ left: x, top: y, width: w, height: h,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle });
    } else if (shapeType === 'line') {
      obj = new fabric.Line([x, y, x + w, y], {
        stroke: style.strokeColor || style.color || '#58A6FF',
        strokeWidth: style.strokeWidth || 2 });
    } else {
      obj = new fabric.Rect({ left: x, top: y, width: w, height: h,
        fill: style.fillColor || style.color || '#58A6FF',
        originX: 'left', originY: 'top', angle });
    }
  }

  if (obj) {
    obj.set({ selectable: !el.locked, evented: !el.locked, visible: el.visible !== false });
    obj.setCoords();
    fabricCanvas.add(obj);
    if (selectIt) fabricCanvas.setActiveObject(obj);
  }
}
```

---

## 7. Shape Picker — Dynamic Rendering

Replace the static HTML shape options with dynamic rendering from `SHAPES`:

```javascript
function buildShapePicker() {
  const sheet = document.getElementById('shape-sheet');
  sheet.innerHTML = '';

  // Group by category
  const cats = {};
  for (const [id, info] of Object.entries(SHAPES)) {
    if (!cats[info.category]) cats[info.category] = [];
    cats[info.category].push({ id, ...info });
  }

  const CATEGORY_ORDER = ['Basic', 'Arrows', 'Symbols', 'Nature'];

  for (const catName of CATEGORY_ORDER) {
    const items = cats[catName];
    if (!items?.length) continue;

    const catDiv = document.createElement('div');
    catDiv.className = 'shape-category';
    catDiv.dataset.category = catName;

    // Header
    const hdr = document.createElement('div');
    hdr.className = 'shape-category-header';
    hdr.innerHTML = `<span class="shape-category-title">${catName}</span><span class="shape-category-chevron">▼</span>`;
    hdr.addEventListener('click', () => {
      catDiv.classList.toggle('collapsed');
    });
    catDiv.appendChild(hdr);

    // Items grid
    const grid = document.createElement('div');
    grid.className = 'shape-category-items';
    for (const item of items) {
      const opt = document.createElement('div');
      opt.className = 'shape-opt';
      opt.dataset.shape = item.id;
      opt.innerHTML = `<svg viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg" style="color:var(--accent)">${item.svg}</svg><span>${item.label}</span>`;
      opt.addEventListener('click', async () => {
        const shape = opt.dataset.shape;
        hideShapePicker();
        try {
          const res = await fetch(`${SERVER}/api/element`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: 'shape', shape,
              style: { color: '#58A6FF', fillColor: '#58A6FF', strokeColor: '#58A6FF' },
              position: { x: 80, y: 80, width: 60, height: 60 },
            }),
          });
          if (!res.ok) throw new Error();
          const el = await res.json();
          addElementToCanvas(el, true);
          const active = fabricCanvas.getActiveObject();
          if (active) active.elementId = el.id;
        } catch {
          showError('Failed to add shape');
        }
      });
      grid.appendChild(opt);
    }
    catDiv.appendChild(grid);
    sheet.appendChild(catDiv);
  }
}
```

Call `buildShapePicker()` once on page load (after DOM is ready).

---

## 8. Backend — `state.py` Notes

- No changes required to `server/state.py` or `server/main.py`.
- The `shape` field on an element is just stored in the element JSON and passed through.
- The `add_element` API accepts `style.shape` which gets persisted in the element's `style` object.
- Future shape-specific properties (e.g., star points count) can be added to `style` without schema changes.

---

## 9. Implementation Phases

### Phase 1 — Core (HTML/CSS only)
- Add `SHAPES` constant with `fabric` and `svg` for all 24 shapes.
- Add `buildShapePicker()` function and call it on load.
- Replace static HTML shape picker with the dynamic build.
- Update `addElementToCanvas` to dispatch via `SHAPES[shapeType].fabric()`.
- Add CSS for category headers and collapse/expand.

### Phase 2 — Polish
- Add collapse state persistence (localStorage).
- Add shape search/filter input at top of picker.
- Animate picker open/close (slide-up fade-in).

### Phase 3 — Enhancements (future)
- Custom shape upload (SVG import).
- Shape presets per category (e.g., starburst, callout bubbles).

---

## 10. Reference — fabric.js Path Tips

- Path coordinates are relative to the path's **own origin** (0,0), not canvas. Set `left`/`top` on the fabric object to position.
- Use `scaleX`/`scaleY` to scale the path to the desired pixel dimensions. Alternatively use `fabric.Path(pathString, { width, height, ... })` with `scaleX = targetWidth / width`.
- For open shapes (lines, arrows, chevrons): set `fill: 'transparent'` and use `stroke` + `strokeWidth`.
- For closed shapes: set `fill` and optionally `stroke` + `strokeWidth`.
- `strokeLineCap: 'round'` and `strokeLineJoin: 'round'` make拐角 look cleaner on arrow/chevron shapes.
- The `fabric.Group` constructor accepts an array of objects, useful for composite shapes like the sun.