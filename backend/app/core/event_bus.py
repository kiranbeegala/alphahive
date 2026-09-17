import asyncio
import json
from typing import List, Dict, Any, Callable
from starlette.websockets import WebSocket

class EventBus:
    def __init__(self):
        self.subscribers: List[Callable[[Dict[str, Any]], Any]] = []
        self.active_websockets: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def register_websocket(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_websockets.append(websocket)

    async def unregister_websocket(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_websockets:
                self.active_websockets.remove(websocket)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        message = {
            "type": event_type,
            "data": data,
            "timestamp": data.get("timestamp")
        }
        
        # Notify in-memory subscribers
        for sub in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(sub):
                    asyncio.create_task(sub(message))
                else:
                    sub(message)
            except Exception as e:
                print(f"Error in event subscriber: {e}")

        # Broadcast to active WebSockets
        disconnected = []
        for ws in self.active_websockets:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    if ws in self.active_websockets:
                        self.active_websockets.remove(ws)

event_bus = EventBus()
