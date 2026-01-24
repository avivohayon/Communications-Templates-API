"""
Development server entry point.

Run this file to start the FastAPI application in development mode.
"""
import uvicorn


if __name__ == "__main__":
    print("🚀 Starting FastAPI server...")
    print("📚 API Documentation: http://localhost:8002/docs")
    print("❤️  Health Check: http://localhost:8002/health")
    print("⌨️  Press Ctrl+C to stop")
    print()
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
