"""FastAPI main application for Supply Chain Knowledge Graph API"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from mcp_server import create_mcp_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    settings = get_settings()
    logger.info(f"Starting Supply Chain KG API")
    logger.info(f"Environment: {settings.environment}")
    yield
    # Shutdown
    logger.info("Shutting down Supply Chain KG API")


# Create FastAPI app
app = FastAPI(
    title="Supply Chain Knowledge Graph API",
    description="MCP-based API for supply chain knowledge graph operations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create MCP routes
create_mcp_router(app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Supply Chain Knowledge Graph API",
        "version": "1.0.0",
        "docs": "/docs",
        "mcp_tools": "/mcp/tools",
        "health": "/health"
    }


@app.get("/api/v1/status")
async def status():
    """API status endpoint"""
    settings = get_settings()
    return {
        "status": "operational",
        "environment": settings.environment,
        "features": {
            "neo4j": bool(settings.neo4j_uri),
            "postgres": bool(settings.postgres_host),
            "openbb": bool(settings.openbb_pat),
            "kimi": bool(settings.kimi_client_id)
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
