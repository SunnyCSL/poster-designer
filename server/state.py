"""
Poster Designer — State Engine
state.json CRUD + element operations + history/undo + template presets
All coordinates in mm. Agent CLI and Human PWA share state.json.
"""

from __future__ import annotations

import json
import copy
import sys
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Template presets (mm, 300 dpi)
# ---------------------------------------------------------------------------

TEMPLATES = {
    "A4":       {"width_mm": 297,  "height_mm": 210,  "dpi": 300},
    "A3":       {"width_mm": 420,  "height_mm": 297,  "dpi": 300},
    "Square":   {"width_mm": 200,  "height_mm": 200,  "dpi": 300},
    "Mobile":   {"width_mm": 105,  "height_mm": 187,  "dpi": 300},
    "Wide":     {"width_mm": 333,  "height_mm": 187,  "dpi": 300},
}

# ---------------------------------------------------------------------------
# Default element style defaults
# ---------------------------------------------------------------------------
DEFAULT_TEXT_STYLE = {
    "fontFamily": "Noto Sans",
    "fontSize": 24,
    "fontWeight": "400",
    "color": "#000000",
    "textAlign": "left",
    "lineHeight": 1.4,
    "letterSpacing": 0,
}

# ---------------------------------------------------------------------------
# Core State class
# ---------------------------------------------------------------------------

class State:
    STATE_FILE = Path(__file__).parent.parent / "state.json"
    MAX_HISTORY = 50

    def __init__(self, state_file: str | Path | None = None) -> None:
        self.state_file = Path(state_file) if state_file else self.STATE_FILE
        self._data: dict = {}
        self.load()

    # ------------------------------------------------------------------ load / save

    def load(self) -> dict:
        """Load state.json. Creates default if missing or corrupt."""
        if self.state_file.exists():
            try:
                self._data = json.loads(self.state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = self._default_state()
        else:
            self._data = self._default_state()
        return self._data

    def save(self) -> None:
        """Atomically write state.json."""
        self._data["last_updated"] = datetime.now(timezone.utc).isoformat()
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.state_file)

    # ------------------------------------------------------------------ internal helpers

    def _px(self, mm: float) -> int:
        return round(mm * self._data["meta"]["dpi"] / 25.4)

    def _mm(self, px: int) -> float:
        return round(px / (self._data["meta"]["dpi"] / 25.4), 2)

    def _next_id(self) -> str:
        """Auto-increment element ID."""
        nums = [0]
        for el in self._data.get("elements", []):
            try:
                nums.append(int(el["id"].split("_")[1]))
            except (IndexError, ValueError):
                pass
        return f"el_{max(nums) + 1:03d}"

    def _touch_element(self, el_id: str) -> dict:
        for el in self._data["elements"]:
            if el["id"] == el_id:
                return el
        raise KeyError(f"Element {el_id!r} not found")

    def _push_history(self, agent: str, action: str, element_id: str | None = None) -> None:
        """Add a history snapshot."""
        snap = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "action": action,
            "element_id": element_id,
            "snapshot": self._minimal_snapshot(),
        }
        self._data.setdefault("history", []).append(snap)
        # trim
        if len(self._data["history"]) > self.MAX_HISTORY:
            self._data["history"][:] = self._data["history"][-self.MAX_HISTORY:]

    def _minimal_snapshot(self) -> dict:
        """Shallow-copy snapshot for history — element dicts are copied to avoid shared refs."""
        return {
            "version": self._data["version"],
            "edited_by": self._data["edited_by"],
            "last_updated": self._data["last_updated"],
            "meta": self._data["meta"],
            "background": self._data["background"],
            "elements": [dict(el) for el in self._data["elements"]],
            "history": [],
        }

    # ------------------------------------------------------------------ default state

    def _default_state(self) -> dict:
        meta = self._build_meta("A4")
        return {
            "version": 1,
            "edited_by": None,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "meta": meta,
            "background": {"type": "solid", "color": "#ffffff", "gradient": None, "image": None},
            "elements": [],
            "history": [],
        }

    def _build_meta(self, template: str) -> dict:
        t = TEMPLATES.get(template, TEMPLATES["A4"])
        dpi = t["dpi"]
        w_px = round(t["width_mm"] * dpi / 25.4)
        h_px = round(t["height_mm"] * dpi / 25.4)
        return {
            "template": template,
            "width_mm": t["width_mm"],
            "height_mm": t["height_mm"],
            "dpi": dpi,
            "width_px": w_px,
            "height_px": h_px,
        }

    # ------------------------------------------------------------------ public API — state-level

    def reload(self) -> dict:
        return self.load()

    def current(self) -> dict:
        """Return full state snapshot (deep-copy)."""
        return copy.deepcopy(self._data)

    def meta(self) -> dict:
        return copy.deepcopy(self._data["meta"])

    def set_edited_by(self, who: str | None) -> None:
        self._data["edited_by"] = who
        self.save()

    # ------------------------------------------------------------------ public API — template

    def apply_template(self, name: str, agent: str = "system") -> dict:
        """
        Apply template by name (A4 | A3 | Square | Mobile | Wide).
        Resets elements and background, pushes history.
        """
        if name not in TEMPLATES:
            raise ValueError(f"Unknown template {name!r}. Available: {list(TEMPLATES)}")
        self._push_history(agent, f"apply_template:{name}")
        self._data["meta"] = self._build_meta(name)
        self._data["elements"] = []
        self._data["background"] = {"type": "solid", "color": "#ffffff", "gradient": None, "image": None}
        self.save()
        return self.meta()

    def list_templates(self) -> dict:
        return copy.deepcopy(TEMPLATES)

    # ------------------------------------------------------------------ public API — background

    def set_background(self, bg: dict, agent: str = "system") -> dict:
        """
        bg: { type: "solid"|"gradient"|"image", color?, gradient?, image? }
        """
        self._push_history(agent, "set_background")
        self._data["background"] = copy.deepcopy(bg)
        self.save()
        return copy.deepcopy(self._data["background"])

    def get_background(self) -> dict:
        return copy.deepcopy(self._data["background"])

    # ------------------------------------------------------------------ public API — element CRUD

    def add_element(
        self,
        type: str,                     # "text" | "image" | "shape"
        content: str = "",
        style: dict | None = None,
        position: dict | None = None,
        agent: str = "system",
    ) -> dict:
        """
        Add a new element. position in mm. Auto-assigns id and layer.
        Returns the created element.
        """
        layers = [el.get("layer", 0) for el in self._data["elements"]]
        layer = (max(layers) + 1) if layers else 0

        default_pos = {
            "x": 0.0, "y": 0.0,
            "width": self._data["meta"]["width_mm"] / 2,
            "height": 20.0,
            "rotation": 0,
        }
        el = {
            "id": self._next_id(),
            "type": type,
            "content": content,
            "style": copy.deepcopy(style if style is not None else DEFAULT_TEXT_STYLE),
            "position": copy.deepcopy(position if position is not None else default_pos),
            "layer": layer,
            "locked": False,
            "visible": True,
            "group": None,
        }
        self._data["elements"].append(el)
        self.save()
        self._push_history(agent, "add_element", element_id=el["id"])
        return copy.deepcopy(el)

    def get_element(self, el_id: str) -> dict:
        return copy.deepcopy(self._touch_element(el_id))

    def list_elements(self) -> list[dict]:
        return copy.deepcopy(self._data["elements"])

    def update_element(self, el_id: str, patch: dict, agent: str = "system") -> dict:
        """
        Partial update: keys under 'style', 'position', or top-level
        (content, layer, locked, visible, group).
        """
        self._push_history(agent, f"update_element:{el_id}", element_id=el_id)
        el = self._touch_element(el_id)

        for key in ("content", "layer", "locked", "visible", "group"):
            if key in patch:
                el[key] = patch[key]

        if "style" in patch:
            el["style"].update(patch["style"])
        if "position" in patch:
            el["position"].update(patch["position"])

        self.save()
        return copy.deepcopy(el)

    def delete_element(self, el_id: str, agent: str = "system") -> None:
        self._push_history(agent, f"delete_element:{el_id}", element_id=el_id)
        self._data["elements"] = [e for e in self._data["elements"] if e["id"] != el_id]
        self.save()

    def move_element(self, el_id: str, x: float, y: float, agent: str = "system") -> dict:
        return self.update_element(el_id, {"position": {"x": x, "y": y}}, agent)

    def resize_element(self, el_id: str, w: float, h: float, agent: str = "system") -> dict:
        return self.update_element(el_id, {"position": {"width": w, "height": h}}, agent)

    def reorder_layers(self, ordered_ids: list[str], agent: str = "system") -> None:
        """Set layer order explicitly. Missing IDs are removed."""
        self._push_history(agent, "reorder_layers")
        layer_map = {eid: i for i, eid in enumerate(ordered_ids)}
        for el in self._data["elements"]:
            if el["id"] in layer_map:
                el["layer"] = layer_map[el["id"]]
        self.save()

    # ------------------------------------------------------------------ public API — history / undo

    def history(self, limit: int = 20) -> list[dict]:
        """Return recent history entries (newest last)."""
        entries = self._data.get("history", [])
        return copy.deepcopy(entries[-limit:])

    def undo(self, agent: str = "system") -> dict:
        """
        Restore to previous snapshot. Returns restored state or current if no history.
        """
        hist = self._data.get("history", [])
        if len(hist) < 2:
            return copy.deepcopy(self._data)
        # snapshot current (undo point) then pop it
        undo_snapshot = copy.deepcopy(self._data)
        self._data["history"].pop()
        # restore from previous snapshot
        prev = hist[-1]["snapshot"]          # snapshot BEFORE the action being undone
        self._data = copy.deepcopy(prev)
        # push undo snapshot (post-restore state) for potential redo
        self._push_history(agent, "undo")
        self.save()
        return copy.deepcopy(self._data)

    # ------------------------------------------------------------------ convenient view helpers

    def summary(self) -> str:
        meta = self._data["meta"]
        bg = self._data["background"]
        elems = self._data["elements"]
        return (
            f"State(template={meta['template']} {meta['width_mm']}x{meta['height_mm']}mm "
            f"{meta['dpi']}dpi, bg={bg['type']}, elements={len(elems)}, "
            f"history={len(self._data.get('history',[]))})"
        )


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_instance: State | None = None

def get_state(state_file: str | Path | None = None) -> State:
    global _instance
    if _instance is None or state_file is not None:
        _instance = State(state_file)
    return _instance


if __name__ == "__main__":
    s = get_state()
    print("Templates:", list(TEMPLATES))
    print(s.summary())
    e = s.add_element("text", content="Hello Poster", agent="cli")
    print("Added element:", e["id"])
    print("Position:", e["position"])
    s.move_element(e["id"], 50, 30, agent="cli")
    print("After move:", s.get_element(e["id"])["position"])
    print("History:", s.history())