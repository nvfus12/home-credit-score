from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.database.connection import init_db
from app.services.credit_scorer import CreditScoringService
from app.services.explainer import SHAPExplanationService
from app.services.risk_classifier import RiskClassificationEngine
from app.services.drift_monitor import DriftMonitoringService
from app.api import routes_predict, routes_history, routes_monitoring

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown lifecycles."""
    print("Initializing CreditLens AI services...")
    
    # 1. Initialize SQLite Database Schema
    await init_db()
    print("Inference logs database initialized.")

    # 2. Instantiate and attach core services to app state
    scorer = CreditScoringService()
    explainer = SHAPExplanationService(scorer)
    classifier = RiskClassificationEngine()
    drift_monitor = DriftMonitoringService()

    app.state.scorer = scorer
    app.state.explainer = explainer
    app.state.classifier = classifier
    app.state.drift_monitor = drift_monitor

    yield
    
    # Clean up operations on shutdown if any
    print("Shutting down CreditLens AI services...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers (with version prefix /api/v1)
app.include_router(routes_predict.router, prefix="/api/v1")
app.include_router(routes_history.router, prefix="/api/v1")
app.include_router(routes_monitoring.router, prefix="/api/v1")

# Ensure static asset folders exist
os.makedirs(settings.STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(settings.STATIC_DIR, "js"), exist_ok=True)
os.makedirs(os.path.join(settings.STATIC_DIR, "assets"), exist_ok=True)

# Mount Static Folder for Frontend access (CSS, JS, images, reports)
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

@app.get("/")
async def read_root():
    """Serves the main single page web application."""
    index_path = os.path.join(settings.STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "Welcome to CreditLens AI API. Frontend index.html not found in static directory.",
        "api_documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    scorer_ready = app.state.scorer.is_ready() if hasattr(app.state, 'scorer') else False
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "ml_model_loaded": scorer_ready
    }
