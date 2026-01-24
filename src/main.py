"""
Communications API - Main FastAPI Application

This is the entry point for the FastAPI application.
Registers all routers and configures the application.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config import setup_logging, settings
from src.database import init_db, close_db
from src.api.router_template import router as template_router
from src.api.router_message import router as message_router
from src.api.router_message_history import router as history_router

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database tables (if needed)
    - Shutdown: Close database connections
    """
    # Startup
    logger.info(f"🚀 Starting Communications API (Environment: {settings.ENVIRONMENT})")
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    yield  # Application runs
    
    # Shutdown
    logger.info("Shutting down Communications API...")
    await close_db()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Communications API",
    description="API for managing message templates and sending messages via Email and SMS",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================
# CORS CONFIGURATION
# ============================================================
# Allow requests from the frontend (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend
        "http://127.0.0.1:3000",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


# ============================================================
# ROUTERS
# ============================================================

# Register template router
app.include_router(template_router)
logger.info("📝 Registered router: /templates")

# Register message sending router
app.include_router(message_router, prefix="/messages")
logger.info("📨 Registered router: /messages")

# Register message history router
app.include_router(history_router, prefix="/messages")
logger.info("📊 Registered router: /messages/history")


# ============================================================
# ROOT & HEALTH ENDPOINTS
# ============================================================

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": "Communications API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns 200 if the application is running.
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


# ============================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    
    This catches any exceptions that slip through endpoint-level handling
    and returns a consistent error response.
    
    In production, you might want to:
    - Log to external monitoring (Sentry, DataDog, etc.)
    - Hide detailed error messages from clients
    - Return generic "Internal Server Error" messages
    """
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


# ============================================================
# STARTUP MESSAGE
# ============================================================

logger.info("=" * 60)
logger.info("Communications API initialized successfully")
logger.info("=" * 60)
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Log Level: {settings.LOG_LEVEL}")
logger.info(f"Rate Limit: {settings.MAX_MESSAGES_PER_RECIPIENT_PER_HOUR} messages/hour/recipient")
logger.info("=" * 60)
