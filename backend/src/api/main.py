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

class EvaluationRequest(BaseModel):
    """Input model for candidate evaluation requests."""
    job_description: str = Field(..., description="Job description text")
    resume: str = Field(..., description="Candidate resume text")
    company_context: str | None = Field(None, description="Optional company context")


class EvaluationResponse(BaseModel):
    """Response model for evaluation results."""
    job_description: str
    resume: str
    company_context: str | None
    rubric: Dict[str, Any]
    working_memories: List[Dict[str, Any]]
    agent_reviews: List[Dict[str, Any]]
    decision_packet: Dict[str, Any]
    interview_plan: Dict[str, Any]
    metadata: Dict[str, Any] | None


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


@app.post("/evaluate", response_model=EvaluationResponse, status_code=status.HTTP_200_OK)
async def evaluate_candidate(request: EvaluationRequest) -> EvaluationResponse:
    """Evaluate a candidate using the multi-agent system.

    Args:
        request: Evaluation request with job description and resume

    Returns:
        EvaluationResponse with complete workflow results

    Raises:
        HTTPException: If evaluation fails
    """
    try:
        logger.info(f"Received evaluation request")
        logger.info(f"Job description length: {len(request.job_description)}")
        logger.info(f"Resume length: {len(request.resume)}")

        # Import here to avoid circular dependencies
        from src.graph import run_hiring_workflow

        # Execute the workflow
        result = await run_hiring_workflow(
            job_description=request.job_description,
            resume=request.resume,
            company_context=request.company_context
        )

        # Normalize the response to match frontend expectations
        # Comment 3: Map panel_reviews to agent_reviews, convert agent_working_memory dict to array,
        # and normalize recommendation/confidence casing and enums

        # Convert panel_reviews to agent_reviews with normalized agent_name
        agent_reviews = []
        for review in result.get("panel_reviews", []):
            review_dict = review.model_dump() if hasattr(review, 'model_dump') else review
            # Normalize agent_role to agent_name
            if "agent_role" in review_dict:
                review_dict["agent_name"] = review_dict.pop("agent_role")
            agent_reviews.append(review_dict)

        # Convert agent_working_memory dict to working_memories array
        working_memories = []
        for agent_name, memory in result.get("agent_working_memory", {}).items():
            memory_dict = memory.model_dump() if hasattr(memory, 'model_dump') else memory
            # Ensure agent_name is set
            if "agent_name" not in memory_dict:
                memory_dict["agent_name"] = agent_name
            working_memories.append(memory_dict)

        # Normalize decision_packet fields (recommendation and confidence casing)
        decision_packet = result.get("decision_packet")
        if decision_packet:
            decision_dict = decision_packet.model_dump() if hasattr(decision_packet, 'model_dump') else decision_packet

            # Normalize recommendation enum values to match frontend expectations
            # Backend: "Hire", "Lean hire", "Lean no", "No"
            # Frontend: "hire", "lean_hire", "lean_no", "no"
            if "recommendation" in decision_dict and decision_dict["recommendation"]:
                rec = decision_dict["recommendation"]
                recommendation_map = {
                    "Hire": "hire",
                    "Lean hire": "lean_hire",
                    "Lean no": "lean_no",
                    "No": "no"
                }
                decision_dict["recommendation"] = recommendation_map.get(rec, rec.lower().replace(" ", "_"))

            # Normalize confidence to confidence_level if needed
            if "confidence" in decision_dict and "confidence_level" not in decision_dict:
                decision_dict["confidence_level"] = decision_dict.pop("confidence")
        else:
            decision_dict = {}

        # Convert other Pydantic models to dicts
        rubric = result.get("rubric")
        rubric_dict = rubric.model_dump() if hasattr(rubric, 'model_dump') else (rubric or {})

        interview_plan = result.get("interview_plan")
        interview_plan_dict = interview_plan.model_dump() if hasattr(interview_plan, 'model_dump') else (interview_plan or {})

        # Build metadata
        metadata = result.get("workflow_metadata", {})

        # Return the normalized response
        return EvaluationResponse(
            job_description=request.job_description,
            resume=request.resume,
            company_context=request.company_context,
            rubric=rubric_dict,
            working_memories=working_memories,
            agent_reviews=agent_reviews,
            decision_packet=decision_dict,
            interview_plan=interview_plan_dict,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
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
