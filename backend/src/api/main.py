"""FastAPI application for the Agentic Hiring Orchestrator.

This module provides REST API endpoints for evaluating candidates
using the multi-agent hiring evaluation system.

Usage:
    pdm run api
    # or
    uvicorn src.api.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


# ============================================================================
# Request/Response Models
# ============================================================================

class CandidateInput(BaseModel):
    """Input model for candidate evaluation requests."""
    name: str = Field(..., description="Candidate's full name")
    role: str = Field(..., description="Target role/position")
    resume: str = Field(..., description="Resume content or summary")
    experience_years: int = Field(..., ge=0, description="Years of experience")
    skills: List[str] = Field(default_factory=list, description="List of skills")


class EvaluationResponse(BaseModel):
    """Response model for evaluation results."""
    candidate_id: str = Field(..., description="Unique candidate identifier")
    status: str = Field(..., description="Evaluation status")
    message: str = Field(..., description="Status message")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    llm_provider: str = Field(..., description="Configured LLM provider")


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup
    logger.info("Starting Agentic Hiring Orchestrator API")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Environment: {'development' if settings.api_reload else 'production'}")

    # TODO: Initialize graph and other resources here
    # graph = create_graph()

    yield

    # Shutdown
    logger.info("Shutting down Agentic Hiring Orchestrator API")
    # TODO: Cleanup resources here


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Agentic Hiring Orchestrator",
    description="Multi-agent hiring evaluation system using LangGraph",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Agentic Hiring Orchestrator API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        llm_provider=settings.llm_provider
    )


@app.post("/evaluate", response_model=EvaluationResponse, status_code=status.HTTP_202_ACCEPTED)
async def evaluate_candidate(candidate: CandidateInput) -> EvaluationResponse:
    """Evaluate a candidate using the multi-agent system.

    Args:
        candidate: Candidate information and resume

    Returns:
        EvaluationResponse with evaluation status

    Raises:
        HTTPException: If evaluation fails
    """
    try:
        logger.info(f"Received evaluation request for: {candidate.name}")

        # TODO: Implement actual graph execution
        # result = await run_evaluation_graph(candidate)

        # For now, return a placeholder response
        return EvaluationResponse(
            candidate_id=f"candidate_{candidate.name.replace(' ', '_').lower()}",
            status="accepted",
            message=f"Evaluation queued for {candidate.name}. Graph execution to be implemented."
        )

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@app.get("/config", response_model=Dict[str, Any])
async def get_config() -> Dict[str, Any]:
    """Get current API configuration (non-sensitive values only)."""
    return {
        "llm_provider": settings.llm_provider,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "enable_working_memory": settings.enable_working_memory,
        "enable_product_agent": settings.enable_product_agent,
        "max_panel_agents": settings.max_panel_agents,
        "parallel_execution": settings.parallel_execution,
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "path": str(request.url)
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
