# Smart Campus Access Control - FastAPI Backend
# Main application entry point

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn
import time
import logging
from contextlib import asynccontextmanager

# Import database components
from database.connection import get_db, create_tables, check_connection, health_check as db_health_check
from services.database_service import DatabaseService

# Import routers
from routers import auth, vehicles, logs, alerts, dashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Smart Campus Access Control API...")
    
    # Check database connection
    if check_connection():
        logger.info("✅ Database connection established")
        
        # Create tables if they don't exist
        create_tables()
        logger.info("✅ Database tables verified")
    else:
        logger.error("❌ Database connection failed - some features may not work")
    
    logger.info("🎉 API startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Smart Campus Access Control API...")

# Create FastAPI application
app = FastAPI(
    title="Smart Campus Access Control API",
    description="Backend API for campus security system with ID verification and vehicle OCR",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure appropriately for production
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "detail": "An unexpected error occurred",
            "timestamp": time.time()
        }
    )

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Smart Campus Access Control API",
        "status": "running",
        "version": "1.0.0",
        "description": "Backend API for campus security system with ID verification and vehicle OCR",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "api": "/api"
        },
        "features": [
            "ID Verification",
            "Vehicle Registration", 
            "License Plate Recognition",
            "Access Logging",
            "Security Alerts",
            "Dashboard Analytics"
        ]
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check endpoint"""
    try:
        # Database health check
        db_health = db_health_check()
        
        # Service health check
        db_service = DatabaseService(db)
        system_health = db_service.get_system_health()
        
        return {
            "status": "healthy",
            "service": "access-control-api",
            "version": "1.0.0",
            "timestamp": time.time(),
            "database": db_health,
            "system": system_health,
            "uptime": "running"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "access-control-api",
                "version": "1.0.0",
                "timestamp": time.time(),
                "error": str(e)
            }
        )

@app.get("/api/status")
async def api_status(db: Session = Depends(get_db)):
    """API status with database statistics"""
    try:
        db_service = DatabaseService(db)
        dashboard_data = db_service.get_dashboard_data(days=1)
        
        return {
            "api_status": "operational",
            "database_status": "connected",
            "timestamp": time.time(),
            "today_stats": dashboard_data.get("access_statistics", {}),
            "system_health": dashboard_data.get("user_statistics", {}),
            "active_alerts": len(dashboard_data.get("active_alerts", []))
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "api_status": "degraded",
                "database_status": "error",
                "timestamp": time.time(),
                "error": str(e)
            }
        )

# Legacy endpoints for backward compatibility
@app.post("/verify_id")
async def verify_id_legacy(request: dict, db: Session = Depends(get_db)):
    """Legacy ID verification endpoint (redirects to new API)"""
    from routers.auth import verify_id, IDVerificationRequest
    
    verification_request = IDVerificationRequest(
        id_number=request.get("id_number", ""),
        scan_method=request.get("scan_method", "manual")
    )
    
    return await verify_id(
        verification_request,
        gate_id=request.get("gate_id", "MAIN_GATE"),
        db=db
    )

@app.post("/register_vehicle")
async def register_vehicle_legacy(request: dict, db: Session = Depends(get_db)):
    """Legacy vehicle registration endpoint (redirects to new API)"""
    from routers.vehicles import register_vehicle, VehicleRegistrationRequest
    
    registration_request = VehicleRegistrationRequest(
        license_plate=request.get("license_plate", ""),
        owner_id=request.get("owner_id", ""),
        vehicle_type=request.get("vehicle_type", ""),
        color=request.get("color"),
        model=request.get("model")
    )
    
    return await register_vehicle(registration_request, db=db)

@app.get("/logs")
async def get_logs_legacy(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Legacy logs endpoint (redirects to new API)"""
    from routers.logs import get_access_logs
    
    return await get_access_logs(
        limit=limit,
        offset=offset,
        db=db
    )

@app.get("/alerts/recent")
async def get_recent_alerts_legacy(db: Session = Depends(get_db)):
    """Legacy recent alerts endpoint (redirects to new API)"""
    from routers.alerts import get_recent_alerts
    
    return await get_recent_alerts(db=db)

if __name__ == "__main__":
    print("🏫 Smart Campus Access Control System")
    print("📡 Starting FastAPI server...")
    print("🔗 API Documentation: http://localhost:8000/docs")
    print("📊 Dashboard API: http://localhost:8000/api/dashboard")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )