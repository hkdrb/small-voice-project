import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Add parent directory to path to allow importing 'backend' package when running uvicorn from backend/ directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import auth, dashboard, survey, organization, users

from backend.database import init_db
app = FastAPI(title="SmallVoice API")

@app.on_event("startup")
def on_startup():
    init_db()
    # Preload embedding model to prevent timeout on first request
    try:
        from backend.services.analysis import get_embedding_model
        get_embedding_model()
        logging.info("Embedding model preloaded successfully on startup")
    except Exception as e:
        logging.error(f"Failed to preload embedding model: {e}")

# CORS Configuration
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_str:
    origins = [origin.strip() for origin in allowed_origins_str.split(",")]
else:
    # Default Fallback (for existing dev setups without .env update)
    origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501", 
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(survey.router, prefix="/api/surveys", tags=["surveys"])
app.include_router(organization.router, prefix="/api/organizations", tags=["organizations"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.get("/")
@app.get("/api")
@app.get("/api/")
def read_root():
    return {
        "message": "SmallVoice API is running",
        "version": os.getenv("GIT_COMMIT_HASH", "unknown"),
        "deployed_at": os.getenv("DEPLOY_TIMESTAMP", "unknown")
    }
