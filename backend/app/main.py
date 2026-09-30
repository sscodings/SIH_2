import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.ws import ws_manager
from app.core.security import SecurityHeadersMiddleware, require_user, require_role
from app.api.v1 import (
    auth, complaints, cases, wallets, entities, watchlist,
    alerts, freeze, reports, verify, analytics, admin, webhooks, system, ingest
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

# Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware (Env configured, no wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Native WebSocket Endpoint (protected with token authentication in Section 5)
@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    from app.core.ws import handle_websocket_connection
    await handle_websocket_connection(websocket)

# Include API v1 routers with role-based access control
prefix = settings.API_V1_STR

# Public & Hybrid Auth
app.include_router(auth.router, prefix=prefix)
app.include_router(verify.router, prefix=prefix)
app.include_router(ingest.router, prefix=prefix)

# Investigator / General Protected Routers (require_user)
app.include_router(cases.router, prefix=prefix, dependencies=[Depends(require_user)])
app.include_router(complaints.router, prefix=prefix, dependencies=[Depends(require_user)])
app.include_router(wallets.router, prefix=prefix, dependencies=[Depends(require_user)])
app.include_router(entities.router, prefix=prefix, dependencies=[Depends(require_user)])
app.include_router(watchlist.router, prefix=prefix, dependencies=[Depends(require_user)])
app.include_router(alerts.router, prefix=prefix, dependencies=[Depends(require_user)])
app.include_router(freeze.router, prefix=prefix, dependencies=[Depends(require_user)])
app.include_router(reports.router, prefix=prefix, dependencies=[Depends(require_user)])
app.include_router(system.router, prefix=prefix, dependencies=[Depends(require_user)])

# Supervisor / Admin Protected Routers
app.include_router(analytics.router, prefix=prefix, dependencies=[Depends(require_role("supervisor", "admin"))])
app.include_router(admin.audit_router, prefix=prefix, dependencies=[Depends(require_role("supervisor", "admin"))])

# Admin Only Routers
app.include_router(admin.router, prefix=prefix, dependencies=[Depends(require_role("admin"))])
app.include_router(webhooks.router, prefix=prefix, dependencies=[Depends(require_role("admin"))])

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "mode": settings.CHAINNETRA_MODE,
        "docs": "/docs",
        "api_v1": prefix
    }
