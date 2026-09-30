import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # topic -> set of WebSockets
        self.active_subscriptions: Dict[str, Set[WebSocket]] = {
            "all": set(),
            "inbox": set(),
            "alerts": set()
        }
        self.case_subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_subscriptions["all"].add(websocket)

    def disconnect(self, websocket: WebSocket):
        for topic, sockets in self.active_subscriptions.items():
            sockets.discard(websocket)
        for case_id, sockets in self.case_subscriptions.items():
            sockets.discard(websocket)

    def subscribe(self, websocket: WebSocket, topic: str):
        if topic.startswith("trace:"):
            case_id = topic.split(":", 1)[1]
            if case_id not in self.case_subscriptions:
                self.case_subscriptions[case_id] = set()
            self.case_subscriptions[case_id].add(websocket)
        else:
            if topic not in self.active_subscriptions:
                self.active_subscriptions[topic] = set()
            self.active_subscriptions[topic].add(websocket)

    async def broadcast_event(self, topic: str, event_type: str, data: dict):
        message = json.dumps({"topic": topic, "event": event_type, "data": data})
        targets: Set[WebSocket] = set()

        if topic == "inbox":
            targets = self.active_subscriptions.get("inbox", set()).union(self.active_subscriptions["all"])
        elif topic == "alerts":
            targets = self.active_subscriptions.get("alerts", set()).union(self.active_subscriptions["all"])
        elif topic.startswith("trace:"):
            case_id = topic.split(":", 1)[1]
            targets = self.case_subscriptions.get(case_id, set()).union(self.active_subscriptions["all"])
        else:
            targets = self.active_subscriptions.get(topic, set()).union(self.active_subscriptions["all"])

        dead_sockets = set()
        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.warning(f"Error sending ws message: {e}")
                dead_sockets.add(ws)

        for dead in dead_sockets:
            self.disconnect(dead)

ws_manager = ConnectionManager()
