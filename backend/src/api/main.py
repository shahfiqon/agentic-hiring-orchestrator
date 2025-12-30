"""FastAPI application for the Agentic Hiring Orchestrator.

This module provides REST API endpoints for evaluating candidates
using the multi-agent hiring evaluation system.

Usage:
    pdm run api
    # or
    uvicorn src.api.main:app --reload --port 8000
"""

import logging
import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, status, BackgroundTasks
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
# In-Memory Job Store
# ============================================================================

class JobStatus(str, Enum):
    """Status of a background job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Job model for tracking evaluation jobs."""
    job_id: str
    status: JobStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    request_data: Dict[str, Any]


# In-memory job store (for PoC - use Redis/DB in production)
jobs_store: Dict[str, Job] = {}


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


class JobSubmissionResponse(BaseModel):
    """Response model for job submission."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")


class JobStatusResponse(BaseModel):
    """Response model for job status check."""
    job_id: str
    status: JobStatus
    progress: Optional[str] = None
    result: Optional[EvaluationResponse] = None
    error: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


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
# Background Job Processing
# ============================================================================

async def process_evaluation_job(job_id: str, request_data: EvaluationRequest):
    """
    Background task to process evaluation workflow.

    Args:
        job_id: Unique job identifier
        request_data: Evaluation request data
    """
    job = jobs_store.get(job_id)
    if not job:
        logger.error(f"Job {job_id} not found in store")
        return

    try:
        # Update job status to processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow().isoformat()
        job.progress = "Starting evaluation workflow..."
        logger.info(f"Job {job_id}: Started processing")

        # Import here to avoid circular dependencies
        from src.graph import run_hiring_workflow

        # Update progress
        job.progress = "Running orchestrator and panel agents..."

        # Execute the workflow
        result = await run_hiring_workflow(
            job_description=request_data.job_description,
            resume=request_data.resume,
            company_context=request_data.company_context
        )

        # Update progress
        job.progress = "Normalizing results..."

        # Normalize the response to match frontend expectations
        agent_reviews = []
        for review in result.get("panel_reviews", []):
            review_dict = review.model_dump() if hasattr(review, 'model_dump') else review
            if "agent_role" in review_dict:
                review_dict["agent_name"] = review_dict.pop("agent_role")
            agent_reviews.append(review_dict)

        working_memories = []
        for agent_name, memory in result.get("agent_working_memory", {}).items():
            memory_dict = memory.model_dump() if hasattr(memory, 'model_dump') else memory
            if "agent_name" not in memory_dict:
                memory_dict["agent_name"] = agent_name
            working_memories.append(memory_dict)

        decision_packet = result.get("decision_packet")
        if decision_packet:
            decision_dict = decision_packet.model_dump() if hasattr(decision_packet, 'model_dump') else decision_packet
            if "recommendation" in decision_dict and decision_dict["recommendation"]:
                rec = decision_dict["recommendation"]
                recommendation_map = {
                    "Hire": "hire",
                    "Lean hire": "lean_hire",
                    "Lean no": "lean_no",
                    "No": "no"
                }
                decision_dict["recommendation"] = recommendation_map.get(rec, rec.lower().replace(" ", "_"))
            if "confidence" in decision_dict and "confidence_level" not in decision_dict:
                decision_dict["confidence_level"] = decision_dict.pop("confidence")
        else:
            decision_dict = {}

        rubric = result.get("rubric")
        rubric_dict = rubric.model_dump() if hasattr(rubric, 'model_dump') else (rubric or {})

        interview_plan = result.get("interview_plan")
        interview_plan_dict = interview_plan.model_dump() if hasattr(interview_plan, 'model_dump') else (interview_plan or {})

        metadata = result.get("workflow_metadata", {})

        # Build the final result
        evaluation_result = {
            "job_description": request_data.job_description,
            "resume": request_data.resume,
            "company_context": request_data.company_context,
            "rubric": rubric_dict,
            "working_memories": working_memories,
            "agent_reviews": agent_reviews,
            "decision_packet": decision_dict,
            "interview_plan": interview_plan_dict,
            "metadata": metadata
        }

        # Update job with results
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow().isoformat()
        job.result = evaluation_result
        job.progress = "Evaluation completed successfully"

        logger.info(f"Job {job_id}: Completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id}: Failed with error: {str(e)}", exc_info=True)
        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow().isoformat()
        job.error = str(e)
        job.progress = "Evaluation failed"


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


@app.post("/evaluate", response_model=JobSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_evaluation(request: EvaluationRequest, background_tasks: BackgroundTasks) -> JobSubmissionResponse:
    """Submit a candidate evaluation job for asynchronous processing.

    Args:
        request: Evaluation request with job description and resume
        background_tasks: FastAPI background tasks

    Returns:
        JobSubmissionResponse with job ID for polling

    Raises:
        HTTPException: If job submission fails
    """
    try:
        logger.info(f"Received evaluation request")
        logger.info(f"Job description length: {len(request.job_description)}")
        logger.info(f"Resume length: {len(request.resume)}")

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Create job entry
        job = Job(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow().isoformat(),
            request_data={
                "job_description": request.job_description,
                "resume": request.resume,
                "company_context": request.company_context
            }
        )

        # Store job in memory
        jobs_store[job_id] = job

        # Add background task
        background_tasks.add_task(process_evaluation_job, job_id, request)

        logger.info(f"Job {job_id}: Submitted successfully")

        return JobSubmissionResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Evaluation job submitted successfully. Use the job_id to check status."
        )

    except Exception as e:
        logger.error(f"Job submission failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job submission failed: {str(e)}"
        )


@app.get("/evaluate/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get the status of an evaluation job.

    Args:
        job_id: Unique job identifier

    Returns:
        JobStatusResponse with current job status and results (if completed)

    Raises:
        HTTPException: If job not found
    """
    job = jobs_store.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Build response based on job status
    response_data = {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at
    }

    # Include result only if completed
    if job.status == JobStatus.COMPLETED and job.result:
        response_data["result"] = EvaluationResponse(**job.result)

    return JobStatusResponse(**response_data)


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
