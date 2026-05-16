"""
Poster Designer — SSE Manager
asyncio-based Server-Sent Events manager with connection pool and broadcast.
Pushes real-time updates to Human PWA so it can reflect Agent changes.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

# ---------------------------------------------------------------------------
# Event types accepted by the SSE manager
# ---------------------------------------------------------------------------
EVENT_TYPES = (
    "element_added",
    "element_updated",
    "element_deleted",
    "state_replaced",
    "compose_complete",
    "agent_editing",
)


class SSEManager:
    """
    Manages SSE client connections and broadcasts events to all subscribers.

    Usage in FastAPI:
        @app.get("/events")
        async def events(conn_id: int = Depends(sse.register)):
            return sse.subscribe(conn_id)
    """

    def __init__(self) -> None:
        # connection_id -> asyncio.Queue of event strings
        self._connections: dict[int, asyncio.Queue] = {}
        # monotonically increasing connection counter
        self._counter = 0
        # guards _connections and _counter
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def register(self) -> int:
        """
        Register a new SSE client. Returns a unique connection_id.
        The caller should pass this ID to subscribe() immediately.
        """
        async with self._lock:
            self._counter += 1
            conn_id = self._counter
            self._connections[conn_id] = asyncio.Queue()
            return conn_id

    async def remove(self, conn_id: int) -> None:
        """
        Remove a client connection and discard its queue.
        Safe to call even if the client already disconnected.
        """
        async with self._lock:
            self._connections.pop(conn_id, None)

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    async def broadcast(self, event_type: str, payload: dict | None = None) -> None:
        """
        Push an event to every connected SSE client.

        event_type must be one of the EVENT_TYPES values.
        payload is an arbitrary dict that will be JSON-serialised.
        """
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Unknown SSE event type: {event_type!r}")

        event_dict = {"type": event_type, "payload": payload or {}}
        message = f"event: message\ndata: {json.dumps(event_dict)}\n\n"

        # Snapshot the current connection set under the lock, then
        # deliver concurrently so one slow client cannot block the others.
        async with self._lock:
            conn_ids = list(self._connections.keys())

        async def _push(conn_id: int, queue: asyncio.Queue) -> None:
            try:
                await asyncio.wait_for(queue.put(message), timeout=5.0)
            except asyncio.TimeoutError:
                # Client is too slow; drop it silently.
                pass

        if conn_ids:
            await asyncio.gather(
                *(_push(cid, self._connections[cid]) for cid in conn_ids),
                return_exceptions=True,
            )

    # ------------------------------------------------------------------
    # Subscription (used as a FastAPI streaming response)
    # ------------------------------------------------------------------

    async def subscribe(self, conn_id: int) -> AsyncGenerator[str, None]:
        """
        Yield SSE-formatted events for the given connection_id.

        The caller must call ``await remove(conn_id)`` after this generator
        exits (FastAPI handles this via ``finally``).

        Disconnection is detected when the response iterator is exhausted
        or cancelled — the caller is responsible for cleanup.
        """
        async with self._lock:
            queue = self._connections.get(conn_id)

        if queue is None:
            # Client was removed before it could subscribe — nothing to yield.
            return

        try:
            while True:
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            # Client disconnected (browser closed tab, network dropped, etc.)
            pass
        finally:
            # Ensure the queue is removed from the registry.
            # A second call to remove() from outside is safe.
            await self.remove(conn_id)
