"""
Orchestrator node for the hiring workflow.

This module contains the main orchestrator node that generates a job-specific
evaluation rubric based on the job description, resume, and company context.
"""

import logging
from typing import Dict

from pydantic import ValidationError

from ..config import get_settings
from ..models.rubric import Rubric
from ..prompts.orchestrator_prompts import RUBRIC_GENERATION_PROMPT
from ..state import HiringWorkflowState
from ..utils.llm import get_structured_llm
from ..utils.validators import (
    validate_rubric_completeness,
    validate_rubric_quality,
    validate_weight_distribution,
)

# Configure logging
logger = logging.getLogger(__name__)


def orchestrator_node(state: HiringWorkflowState) -> Dict:
    """
    Generate a job-specific evaluation rubric from job description and context.

    This node extracts job requirements, company context, and candidate information
    from the state, then uses an LLM to generate a structured rubric with weighted
    evaluation categories and scoring criteria.

    Args:
        state: The current hiring workflow state containing:
            - job_description: The job posting or role requirements
            - resume: The candidate's resume text
            - company_context: Optional company-specific evaluation priorities

    Returns:
        Dictionary with single key 'rubric' containing the generated Rubric object.
        LangGraph will merge this into the existing state.

    Raises:
        ValueError: If required inputs are missing or invalid
        ValidationError: If LLM returns invalid rubric structure
        Exception: For unexpected errors during generation
    """
    logger.info("Starting orchestrator node execution")

    # Extract inputs from state
    job_description = state.get("job_description", "")
    resume = state.get("resume", "")
    company_context = state.get("company_context", "")

    # Validate required inputs
    if not job_description or not isinstance(job_description, str):
        raise ValueError(
            "job_description is required and must be a non-empty string"
        )

    if not resume or not isinstance(resume, str):
        raise ValueError(
            "resume is required and must be a non-empty string"
        )

    # Handle missing company_context gracefully
    if not company_context:
        company_context = "Not provided"
        logger.debug("No company_context provided, using default value")

    # Get settings for prompt formatting
    settings = get_settings()
    rubric_categories_count = settings.rubric_categories_count
    logger.info(f"Generating rubric with {rubric_categories_count} categories")

    # Format the prompt with inputs
    formatted_prompt = RUBRIC_GENERATION_PROMPT.format(
        rubric_categories_count=rubric_categories_count,
        job_description=job_description,
        company_context=company_context,
    )

    try:
        # Get structured LLM instance for Rubric generation
        llm = get_structured_llm(Rubric)

        # Invoke LLM to generate rubric
        logger.debug("Invoking LLM for rubric generation")
        rubric: Rubric = llm.invoke(formatted_prompt)
        logger.info(
            f"Successfully generated rubric with {len(rubric.categories)} categories"
        )

    except ValidationError as e:
        logger.error(f"Pydantic validation failed for generated rubric: {e}")
        raise ValueError(
            f"LLM returned invalid rubric structure: {e}"
        ) from e

    except ValueError as e:
        logger.error(f"LLM utility error: {e}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error during rubric generation: {e}")
        raise Exception(
            f"Failed to generate rubric: {str(e)}"
        ) from e

    # Post-generation validation
    logger.debug("Running post-generation validation checks")

    # Validate completeness
    is_complete, completeness_issues = validate_rubric_completeness(rubric)
    if not is_complete:
        for issue in completeness_issues:
            logger.warning(f"Completeness check: {issue}")

    # Validate quality
    is_quality, quality_issues = validate_rubric_quality(rubric)
    if not is_quality:
        for issue in quality_issues:
            logger.warning(f"Quality check: {issue}")

    # Validate weight distribution
    is_weighted, weight_issues = validate_weight_distribution(rubric)
    if not is_weighted:
        for issue in weight_issues:
            logger.warning(f"Weight distribution check: {issue}")

    # Log validation summary
    total_issues = len(completeness_issues) + len(quality_issues) + len(weight_issues)
    if total_issues > 0:
        logger.warning(
            f"Rubric generated with {total_issues} validation warning(s). "
            "See logs for details."
        )
    else:
        logger.info("Rubric passed all validation checks")

    # Return updated state
    return {"rubric": rubric}
