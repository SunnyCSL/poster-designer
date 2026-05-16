"""
Poster Designer — FastAPI REST API Server
Integrates state.py (state engine) and sse.py (SSE manager).
"""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse

from .state import State, get_state, TEMPLATES
from .sse import SSEManager

# ---------------------------------------------------------------------------
# App + global instances
# ---------------------------------------------------------------------------

app = FastAPI(title="Poster Designer API")
state: State = get_state()
sse = SSEManager()

# ---------------------------------------------------------------------------
# CORS — allow all origins for PWA on GitHub Pages
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    print(f"{request.method} {request.url.path} — {response.status_code} ({duration_ms:.1f}ms)")
    return response

# ---------------------------------------------------------------------------
# Startup — ensure uploads directory exists
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    Path("server/uploads").mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/state")
async def get_state_endpoint():
    """Return full state JSON."""
    return state.current()


@app.post("/api/element")
async def add_element(request: Request):
    """Add a new element. Body: { type, content?, style?, position?, agent? }"""
    body = await request.json()
    element = state.add_element(
        type=body["type"],
        content=body.get("content", ""),
        style=body.get("style"),
        position=body.get("position"),
        agent=body.get("agent", "api"),
    )
    await sse.broadcast("element_added", {"id": element["id"], "type": element["type"]})
    return element, 201


@app.patch("/api/element/{element_id}")
async def update_element(element_id: str, request: Request):
    """Partial update element. Body: { content?, style?, position?, layer?, locked?, visible? }"""
    body = await request.json()
    agent = body.pop("agent", "api")
    element = state.update_element(element_id, body, agent=agent)
    await sse.broadcast("element_updated", {"id": element_id})
    return element


@app.delete("/api/element/{element_id}")
async def delete_element(element_id: str, request: Request):
    """Delete an element."""
    agent = request.query_params.get("agent", "api")
    state.delete_element(element_id, agent=agent)
    await sse.broadcast("element_deleted", {"id": element_id})
    return "", 204


@app.post("/api/undo")
async def undo(request: Request):
    """Undo last operation. Returns restored state."""
    try:
        body = await request.json()
        agent = body.get("agent", "api")
    except Exception:
        agent = "api"
    restored = state.undo(agent=agent)
    await sse.broadcast("state_replaced", {})
    return restored


@app.post("/api/template")
async def apply_template(request: Request):
    """Apply template. Body: { name: "A4"|"A3"|"Square"|"Mobile"|"Wide", agent? }"""
    body = await request.json()
    meta = state.apply_template(name=body["name"], agent=body.get("agent", "api"))
    await sse.broadcast("state_replaced", {"template": body["name"]})
    return meta


@app.post("/api/background")
async def set_background(request: Request):
    """Set background. Body: { type, color?, gradient?, image? }"""
    body = await request.json()
    agent = body.pop("agent", "api")
    bg = state.set_background(body, agent=agent)
    await sse.broadcast("element_updated", {})
    return bg


@app.post("/api/batch")
async def batch_operations(request: Request):
    """
    Apply multiple operations atomically.
    Body: { operations: [{ op: "add"|"update"|"delete", ... }] }
    """
    body = await request.json()
    results = []
    for op in body["operations"]:
        op_type = op.pop("op")
        agent = op.pop("agent", "api")
        if op_type == "add":
            results.append(state.add_element(**op, agent=agent))
        elif op_type == "update":
            el_id = op.pop("element_id")
            results.append(state.update_element(el_id, op, agent=agent))
        elif op_type == "delete":
            el_id = op.pop("element_id")
            state.delete_element(el_id, agent=agent)
            results.append({"id": el_id, "deleted": True})
        else:
            results.append({"error": f"Unknown op: {op_type}"})
    count = len(results)
    await sse.broadcast("state_replaced", {})
    return {"results": results, "count": count}


@app.post("/api/upload")
async def upload_file(file: UploadFile):
    """Upload a file to server/uploads/. Returns { url: "/uploads/filename" }"""
    upload_dir = Path("server/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or "upload"
    dest = upload_dir / filename
    content = await file.read()
    dest.write_bytes(content)
    return {"url": f"/uploads/{filename}"}


@app.get("/api/history")
async def get_history(limit: int = 20):
    """Return recent history entries."""
    return state.history(limit=limit)


@app.get("/api/templates")
async def list_templates():
    """Return available template definitions."""
    return TEMPLATES


@app.post("/api/reorder")
async def reorder_layers(request: Request):
    """Reorder element layers. Body: { ordered_ids: ["el_003", "el_001", "el_002"] }"""
    body = await request.json()
    agent = body.pop("agent", "api")
    state.reorder_layers(body["ordered_ids"], agent=agent)
    await sse.broadcast("state_replaced", {})
    return {"ok": True}


@app.post("/api/compose")
async def compose_poster():
    """Render current state into a poster image. Returns PNG file."""
    data = state.current()
    from server.compose import compose
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "poster.png"
    compose(data, output_path=output_path)
    await sse.broadcast("compose_complete", {"path": str(output_path)})
    return {"status": "ok", "path": str(output_path)}


@app.post("/api/export")
async def export_poster(format: str = "png"):
    """Export poster as PNG or PDF."""
    data = state.current()
    from server.compose import compose
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    ext = format.lower()
    if ext not in ("png", "pdf"):
        ext = "png"
    output_path = output_dir / f"poster.{ext}"
    img = compose(data)
    if ext == "png":
        img.save(str(output_path), "PNG")
    elif ext == "pdf":
        img.save(str(output_path), "PDF", resolution=data["meta"]["dpi"])
    return FileResponse(
        str(output_path),
        media_type=f"image/{ext}" if ext == "png" else "application/pdf",
    )


@app.get("/api/events")
async def sse_events(request: Request):
    """
    SSE endpoint — subscribes the client to real-time state updates.
    Headers disable buffering so events arrive immediately.
    """
    conn_id = await sse.register()
    return StreamingResponse(
        sse.subscribe(conn_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
