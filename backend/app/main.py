import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.models import User, ActivityLog
from app.api import auth, users, activities, analytics, alerts, incidents

Base.metadata.create_all(bind=engine)

def bootstrap_defaults():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                username="admin",
                email="admin@sentinelai.internal",
                hashed_password=get_password_hash("AdminSecurePass123!"),
                role="Admin"
            )
            analyst_user = User(
                username="analyst",
                email="analyst@sentinelai.internal",
                hashed_password=get_password_hash("AnalystSecurePass123!"),
                role="Analyst"
            )
            standard_user = User(
                username="insider_target",
                email="user@sentinelai.internal",
                hashed_password=get_password_hash("UserPass123!"),
                role="User"
            )
            db.add_all([admin_user, analyst_user, standard_user])
            db.commit()

        # Seed baseline activity logs if table is empty
        if db.query(ActivityLog).count() == 0:
            sample_logs = [
                ActivityLog(user_id=1, action_type="LOGIN_SUCCESS", bytes_transferred=0.2, is_sensitive_file=False, failed_attempts=0, privilege_level=2, session_duration_sec=3600.0),
                ActivityLog(user_id=2, action_type="DOCUMENT_QUERY", bytes_transferred=12.4, is_sensitive_file=False, failed_attempts=0, privilege_level=1, session_duration_sec=1800.0),
                ActivityLog(user_id=3, action_type="FILE_READ", bytes_transferred=4.8, is_sensitive_file=False, failed_attempts=0, privilege_level=0, session_duration_sec=1200.0),
            ]
            db.add_all(sample_logs)
            db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_defaults()
    yield

app = FastAPI(title="SentinelAI Enterprise Platform", version="0.5.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(activities.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(incidents.router)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "sentinel-ai", "platform": "SentinelAI Enterprise Platform"}

# Frontend SPA distribution discovery
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
possible_dist_paths = [
    os.path.join(base_dir, "frontend", "dist"),
    os.path.abspath("frontend/dist"),
    os.path.abspath("../frontend/dist"),
    "/app/frontend/dist"
]
FRONTEND_DIST = next((p for p in possible_dist_paths if os.path.exists(p) and os.path.exists(os.path.join(p, "index.html"))), None)

if FRONTEND_DIST:
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ("health", "docs", "redoc", "openapi.json"):
            raise HTTPException(status_code=404, detail="Endpoint not found")
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "platform": "SentinelAI Enterprise Platform",
            "status": "ONLINE",
            "health": "/health",
            "api_docs": "/docs"
        }