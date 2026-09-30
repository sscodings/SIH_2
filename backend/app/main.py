import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.ws import ws_manager
from backend.app.api.v1 import (
    auth, complaints, cases, wallets, entities, watchlist,
    alerts, freeze, reports, verify, analytics, admin, webhooks, system
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chainnetra")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Real-Time Cryptocurrency Fraud Attribution, Multi-Chain Tracing, and Evidence Generation Platform for Law Enforcement",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Native WebSocket Endpoint
@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            if action == "subscribe":
                topic = data.get("topic", "all")
                ws_manager.subscribe(websocket, topic)
                await websocket.send_json({"event": "subscribed", "topic": topic})
            elif action == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        ws_manager.disconnect(websocket)

# Include API v1 routers
prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=prefix)
app.include_router(complaints.router, prefix=prefix)
app.include_router(cases.router, prefix=prefix)
app.include_router(wallets.router, prefix=prefix)
app.include_router(entities.router, prefix=prefix)
app.include_router(watchlist.router, prefix=prefix)
app.include_router(alerts.router, prefix=prefix)
app.include_router(freeze.router, prefix=prefix)
app.include_router(reports.router, prefix=prefix)
app.include_router(verify.router, prefix=prefix)
app.include_router(analytics.router, prefix=prefix)
app.include_router(admin.router, prefix=prefix)
app.include_router(admin.audit_router, prefix=prefix)
app.include_router(webhooks.router, prefix=prefix)
app.include_router(system.router, prefix=prefix)

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "mode": settings.CHAINNETRA_MODE,
        "docs": "/docs",
        "api_v1": prefix
    }
