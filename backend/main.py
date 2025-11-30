"""
AgroSky Insight - Backend API
FastAPI application for satellite data analysis
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
from pathlib import Path
import logging
import os

# Load Sentinel Hub credentials from config.py
try:
    from config import SENTINEL_CLIENT_ID, SENTINEL_CLIENT_SECRET, SENTINEL_INSTANCE_ID
    if SENTINEL_CLIENT_ID:
        os.environ['SENTINEL_CLIENT_ID'] = SENTINEL_CLIENT_ID
    if SENTINEL_CLIENT_SECRET:
        os.environ['SENTINEL_CLIENT_SECRET'] = SENTINEL_CLIENT_SECRET
    if SENTINEL_INSTANCE_ID:
        os.environ['SENTINEL_INSTANCE_ID'] = SENTINEL_INSTANCE_ID
except ImportError:
    pass  # config.py not found or credentials not set

from api.routes import router as api_router
from api.forecast_routes import router as forecast_router
from auth.routes import router as auth_router
from database import Base, engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AgroSky Insight API",
    description="Agricultural field monitoring using Sentinel-2 satellite data",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",
        "https://agrosky-frontend.onrender.com",  # Production frontend URL
        "https://*.onrender.com"  # Allow all Render.com subdomains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

# Create results directory if it doesn't exist
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

# Mount static files for results
app.mount("/results", StaticFiles(directory="results"), name="results")

# Добавляем exception handler для ValidationError
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"❌ Validation error for {request.url.path}:")
    logger.error(f"Body: {await request.body()}")
    logger.error(f"Errors: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(await request.body())}
    )

# Include API routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api/v1")
app.include_router(forecast_router, prefix="/api/v1/forecast", tags=["ML Forecast"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AgroSky Insight API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )



