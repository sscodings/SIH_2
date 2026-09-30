import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional
from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect, status
from app.core.security import decode_token, is_token_revoked
from app.db.database import SessionLocal
from app.db.models import User, Case

logger = logging.getLogger("chainnetra.ws")

MAX_MESSAGE_SIZE = 65536  # 64 KB
MAX_MESSAGES_PER_SECOND = 10
IDLE_TIMEOUT_SECONDS = 300  # 5 minutes

class AuthenticatedWebSocket:
    def __init__(self, websocket: WebSocket, user_email: str, user_role: str, user_id: int):
        self.websocket = websocket
        self.user_email = user_email
        self.user_role = (user_role or "investigator").lower()
        self.user_id = user_id
        self.last_active = time.time()
        self.message_timestamps = []

    def is_rate_limited(self) -> bool:
        now = time.time()
        self.message_timestamps = [t for t in self.message_timestamps if t > now - 1.0]
        if len(self.message_timestamps) >= MAX_MESSAGES_PER_SECOND:
            return True
        self.message_timestamps.append(now)
        return False

class ConnectionManager:
    def __init__(self):
        # topic -> set of AuthenticatedWebSocket
        self.topic_subscriptions: Dict[str, Set[AuthenticatedWebSocket]] = defaultdict(set)
        # socket -> AuthenticatedWebSocket wrapper
        self.active_clients: Dict[WebSocket, AuthenticatedWebSocket] = {}

    def add_client(self, client: AuthenticatedWebSocket):
        self.active_clients[client.websocket] = client

    def remove_client(self, websocket: WebSocket):
        client = self.active_clients.pop(websocket, None)
        if client:
            for topic in list(self.topic_subscriptions.keys()):
                self.topic_subscriptions[topic].discard(client)
                if not self.topic_subscriptions[topic]:
                    self.topic_subscriptions.pop(topic, None)

    def is_case_authorized(self, client: AuthenticatedWebSocket, case_id_str: str) -> bool:
        if client.user_role in ("supervisor", "admin"):
            return True
        try:
            case_id = int(case_id_str)
            db = SessionLocal()
            try:
                case = db.query(Case).filter(Case.id == case_id).first()
                if case and case.created_by and case.created_by.lower() == client.user_email.lower():
                    return True
                return False
            finally:
                db.close()
        except Exception:
            return False

    def subscribe(self, websocket: WebSocket, topic: str) -> bool:
        client = self.active_clients.get(websocket)
        if not client:
            return False

        # Scoping verification: trace:{case_id} requires permission check
        if topic.startswith("trace:"):
            case_id = topic.split(":", 1)[1]
            if not self.is_case_authorized(client, case_id):
                return False

        self.topic_subscriptions[topic].add(client)
        return True

    def unsubscribe(self, websocket: WebSocket, topic: str):
        client = self.active_clients.get(websocket)
        if client and topic in self.topic_subscriptions:
            self.topic_subscriptions[topic].discard(client)

    async def broadcast_event(self, topic: str, event_type: str, data: dict):
        # Broadcasts ONLY to clients subscribed to this exact topic (no 'all' union)
        subscribers = set(self.topic_subscriptions.get(topic, set()))
        if not subscribers:
            return

        message = json.dumps({"topic": topic, "event": event_type, "data": data})
        dead_clients = set()

        for client in subscribers:
            try:
                await client.websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Error sending ws message to {client.user_email}: {e}")
                dead_clients.add(client.websocket)

        for dead_ws in dead_clients:
            self.remove_client(dead_ws)

ws_manager = ConnectionManager()

async def handle_websocket_connection(websocket: WebSocket):
    # Authenticate via query param token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401, reason="Authentication token missing")
        return

    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4401, reason="Invalid or expired token")
        return

    email = payload.get("sub")
    role = payload.get("role")
    jti = payload.get("jti")
    if not email or not role:
        await websocket.close(code=4401, reason="Missing token claims")
        return

    from app.db.database import get_db
    from app.main import app
    override = app.dependency_overrides.get(get_db)
    should_close = False
    if override:
        db_gen = override()
        db = next(db_gen)
    else:
        db = SessionLocal()
        should_close = True

    try:
        if is_token_revoked(db, jti):
            await websocket.close(code=4401, reason="Token revoked")
            return

        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_active:
            await websocket.close(code=4401, reason="User inactive or not found")
            return
        user_id = user.id
    except Exception as e:
        logger.warning(f"Error checking WS user in DB: {e}")
        user_id = 1
    finally:
        if should_close:
            db.close()

    await websocket.accept()
    client = AuthenticatedWebSocket(websocket=websocket, user_email=email, user_role=role, user_id=user_id)
    ws_manager.add_client(client)

    try:
        while True:
            # Receive raw text with timeout for idle detection
            try:
                raw_text = await asyncio.wait_for(websocket.receive_text(), timeout=IDLE_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                await websocket.close(code=1000, reason="Connection idle timeout")
                break

            client.last_active = time.time()

            # Message size limit
            if len(raw_text.encode('utf-8')) > MAX_MESSAGE_SIZE:
                await websocket.send_json({"error": "Message size exceeds maximum limit of 64KB"})
                continue

            # Per-connection rate limit
            if client.is_rate_limited():
                await websocket.send_json({"error": "Rate limit exceeded. Please slow down."})
                continue

            try:
                data = json.loads(raw_text)
            except Exception:
                await websocket.send_json({"error": "Invalid JSON payload"})
                continue

            action = data.get("action")
            if action == "subscribe":
                topic = data.get("topic")
                if not topic:
                    await websocket.send_json({"error": "Topic required for subscription"})
                    continue
                
                success = ws_manager.subscribe(websocket, topic)
                if success:
                    await websocket.send_json({"event": "subscribed", "topic": topic})
                else:
                    await websocket.send_json({"event": "subscription_denied", "topic": topic, "error": "Unauthorized to access this topic"})

            elif action == "unsubscribe":
                topic = data.get("topic")
                if topic:
                    ws_manager.unsubscribe(websocket, topic)
                    await websocket.send_json({"event": "unsubscribed", "topic": topic})

            elif action == "ping":
                await websocket.send_json({"event": "pong", "timestamp": int(time.time())})

            else:
                await websocket.send_json({"error": f"Unknown action '{action}'"})

    except WebSocketDisconnect:
        ws_manager.remove_client(websocket)
    except Exception as e:
        logger.warning(f"WebSocket session error: {e}")
        ws_manager.remove_client(websocket)
