"""Main FastAPI application"""
from fastapi import FastAPI
from app.routes.health import router as health_router

app = FastAPI(
    title="AI Agent Backend",
    description="Backend service for AI agents",
    version="1.0.0"
)

# Include routers
app.include_router(health_router, tags=["Health"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Agent Backend API", "version": "1.0.0"}
