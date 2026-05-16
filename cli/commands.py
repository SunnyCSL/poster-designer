"""PosterCLI — Core CLI logic for Poster Designer API client."""

import urllib.request
import urllib.error
import json
import re
from typing import Any, Optional


def _kebab_to_camelCase(kebab: str) -> str:
    """Convert kebab-case to camelCase."""
    parts = kebab.split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _parse_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Flatten CLI kwargs into nested API payload.

    Converts:
      --font-size 48        → {"style": {"fontSize": 48}}
      --position.x 100     → {"position": {"x": 100}}
      --color "#ff0000"     → {"style": {"color": "#ff0000"}}
      --rotation 15        → {"rotation": 15}
    """
    result: dict[str, Any] = {}

    for key, value in kwargs.items():
        if value is None:
            continue

        # Handle nested prefixes: position.x, style.fontSize, etc.
        if "." in key:
            prefix, rest = key.split(".", 1)
            if prefix not in result:
                result[prefix] = {}
            # Convert rest to camelCase if needed
            rest_camel = _kebab_to_camelCase(rest) if "-" in rest else rest
            result[prefix][rest_camel] = value
        else:
            # Flatten: convert kebab-case to camelCase for top-level
            camel = _kebab_to_camelCase(key) if "-" in key else key
            result[camel] = value

    return result


def _api_call(method: str, url: str, data: Optional[dict] = None,
              files: Optional[dict] = None) -> dict:
    """Make an HTTP request to the Poster API."""
    try:
        if files:
            # Multipart form upload
            import email.mime.multipart as mime_multipart
            boundary = "----FormBoundary"
            body, content_type = _encode_multipart(boundary, data or {}, files)
            req = urllib.request.Request(url, data=body)
            req.add_header("Content-Type", content_type)
        elif data is not None:
            body = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=body, method=method)
            req.add_header("Content-Type", "application/json")
        else:
            req = urllib.request.Request(url, method=method)

        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            msg = err_body.get("detail", str(e.reason))
        except Exception:
            msg = str(e.reason)
        raise PosterAPIError(f"HTTP {e.code}: {msg}")

    except urllib.error.URLError as e:
        raise PosterAPIError(f"Connection error: {e.reason}")

    except json.JSONDecodeError:
        raise PosterAPIError("Invalid JSON response from server")


def _encode_multipart(boundary: str, fields: dict, files: dict) -> tuple[bytes, str]:
    """Encode dict as multipart/form-data."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    import email.encoders

    msg = MIMEMultipart("form-data", boundary=boundary)
    for key, value in fields.items():
        if isinstance(value, (list, tuple)):
            for v in value:
                msg.attach(_make_part(key, str(v)))
        else:
            msg.attach(_make_part(key, str(value)))

    for key, filepath in files.items():
        with open(filepath, "rb") as f:
            data = f.read()
        part = MIMEBase("application", "octet-stream")
        part.set_payload(data)
        email.encoders.encode_base64(part)
        filename = filepath.name if hasattr(filepath, "name") else filepath
        part.add_header("Content-Disposition", f"form-data; name=\"{key}\"; filename=\"{filename}\"")
        msg.attach(part)

    return msg.as_bytes(), f"multipart/form-data; boundary={boundary}"


def _make_part(key: str, value: str):
    from email.mime.nonmultipart import MIMENonMultipart
    part = MIMENonMultipart("application", "x-www-form-urlencoded")
    part["Content-Disposition"] = f"form-data; name=\"{key}\""
    part.set_payload(value)
    return part


class PosterAPIError(Exception):
    """Raised when the API returns an error."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class PosterCLI:
    """CLI client for the Poster Designer REST API."""

    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server = server_url.rstrip("/")

    # ─── State ─────────────────────────────────────────────────────────────────

    def get_state(self) -> dict:
        """GET /api/state — return current canvas state."""
        return _api_call("GET", f"{self.server}/api/state")

    def new_design(self, template: str = "A4") -> dict:
        """POST /api/template — create a new design from a template."""
        return _api_call("POST", f"{self.server}/api/template",
                         {"name": template})

    def get_history(self, limit: int = 20) -> dict:
        """GET /api/history — return recent commands."""
        return _api_call("GET", f"{self.server}/api/history?limit={limit}")

    def list_templates(self) -> dict:
        """GET /api/templates — list available templates."""
        return _api_call("GET", f"{self.server}/api/templates")

    # ─── Elements ──────────────────────────────────────────────────────────────

    def add_text(self, content: str, x: float = 0, y: float = 0, **kwargs) -> dict:
        """POST /api/element — add a text element."""
        payload = _parse_kwargs(kwargs)
        payload["type"] = "text"
        payload["content"] = content
        payload["position"] = payload.get("position", {})
        payload["position"]["x"] = x
        payload["position"]["y"] = y
        return _api_call("POST", f"{self.server}/api/element", payload)

    def add_image(self, src: str, x: float = 0, y: float = 0, **kwargs) -> dict:
        """POST /api/element — add an image element."""
        payload = _parse_kwargs(kwargs)
        payload["type"] = "image"
        payload["content"] = src
        payload["position"] = payload.get("position", {})
        payload["position"]["x"] = x
        payload["position"]["y"] = y
        return _api_call("POST", f"{self.server}/api/element", payload)

    def add_shape(self, shape_type: str, x: float = 0, y: float = 0,
                  w: float = 100, h: float = 100, **kwargs) -> dict:
        """POST /api/element — add a shape element (rect|circle|line)."""
        payload = _parse_kwargs(kwargs)
        payload["type"] = "shape"
        payload["shapeType"] = shape_type
        payload["position"] = payload.get("position", {})
        payload["position"]["x"] = x
        payload["position"]["y"] = y
        payload["size"] = payload.get("size", {})
        payload["size"]["width"] = w
        payload["size"]["height"] = h
        return _api_call("POST", f"{self.server}/api/element", payload)

    def update_element(self, el_id: str, **kwargs) -> dict:
        """PATCH /api/element/{id} — update an element."""
        payload = _parse_kwargs(kwargs)
        return _api_call("PATCH", f"{self.server}/api/element/{el_id}", payload)

    def remove_element(self, el_id: str) -> dict:
        """DELETE /api/element/{id} — remove an element."""
        return _api_call("DELETE", f"{self.server}/api/element/{el_id}")

    def reorder_layers(self, ordered_ids: list[str]) -> dict:
        """POST /api/reorder — reorder element layers."""
        return _api_call("POST", f"{self.server}/api/reorder",
                         {"elementIds": ordered_ids})

    # ─── Background ────────────────────────────────────────────────────────────

    def set_background(self, **bg_kwargs) -> dict:
        """POST /api/background — set canvas background."""
        payload = _parse_kwargs(bg_kwargs)
        return _api_call("POST", f"{self.server}/api/background", payload)

    # ─── Utility ───────────────────────────────────────────────────────────────

    def undo(self) -> dict:
        """POST /api/undo — undo last operation."""
        return _api_call("POST", f"{self.server}/api/undo")

    def batch(self, operations_file: str) -> dict:
        """POST /api/batch — apply a batch of operations from a JSON file."""
        with open(operations_file, "r", encoding="utf-8") as f:
            operations = json.load(f)
        return _api_call("POST", f"{self.server}/api/batch", operations)

    def upload(self, filepath: str) -> dict:
        """POST /api/upload — upload an image file."""
        return _api_call("POST", f"{self.server}/api/upload",
                         files={"file": filepath})

    def compose(self) -> dict:
        """POST /api/compose — compose/flatten the current design."""
        return _api_call("POST", f"{self.server}/api/compose")

    def export(self, fmt: str = "png") -> dict:
        """POST /api/export — export the design to a file."""
        return _api_call("POST", f"{self.server}/api/export", {"format": fmt})

    def load(self, filepath: str) -> dict:
        """POST /api/state — load state from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            state = json.load(f)
        return _api_call("POST", f"{self.server}/api/state", state)

    def save(self, filepath: str) -> dict:
        """GET /api/state — fetch current state and save to a JSON file."""
        state = _api_call("GET", f"{self.server}/api/state")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        return state
