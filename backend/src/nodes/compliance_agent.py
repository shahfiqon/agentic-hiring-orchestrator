"""Compliance Agent Node - Evaluates PII handling, bias risks, and security awareness.

This module implements the Compliance agent's two-pass evaluation workflow:
1. Extract WorkingMemory: Gather observations about PII handling, security, bias awareness
2. Evaluate with Memory: Generate rubric-based scores using extracted context
"""

import logging
from typing import Dict

from backend.src.state import HiringWorkflowState
from backend.src.models.memory import WorkingMemory
from backend.src.models.review import AgentReview
from backend.src.utils.llm import get_structured_llm
from backend.src.prompts.agent_prompts import (
    WORKING_MEMORY_EXTRACTION_PROMPT,
    COMPLIANCE_EVALUATION_PROMPT,
)

logger = logging.getLogger(__name__)


def _extract_working_memory(state: HiringWorkflowState) -> WorkingMemory:
    """Extract Compliance-focused observations from resume.

    Args:
        state: Current workflow state containing resume and rubric

    Returns:
        WorkingMemory object with Compliance-specific observations

    Raises:
        ValueError: If required state fields are missing or validation fails
    """
    logger.debug("Extracting working memory for Compliance agent")

    # Extract and validate required inputs
    resume = state.get("resume")
    rubric = state.get("rubric")

    if not resume:
        raise ValueError("Resume is missing from state")
    if not rubric:
        raise ValueError("Rubric is missing from state")

    # Extract rubric category names
    category_names = [category.name for category in rubric.categories]
    formatted_category_names = "\n".join(f"- {name}" for name in category_names)

    # Format prompt with agent-specific context
    formatted_prompt = WORKING_MEMORY_EXTRACTION_PROMPT.format(
        agent_role="Compliance",
        resume=resume,
        categories=formatted_category_names,
    )

    try:
        # Get structured LLM instance for WorkingMemory
        llm = get_structured_llm(WorkingMemory)
        logger.debug("Invoking LLM for working memory extraction")

        # Invoke LLM to extract observations
        working_memory = llm.invoke(formatted_prompt)

        # Validate agent role
        if working_memory.agent_role != "Compliance":
            raise ValueError(f"Expected agent_role='Compliance', got '{working_memory.agent_role}'")

        # Validate working memory against rubric categories
        if not working_memory.validate_against_rubric(rubric):
            raise ValueError(
                "Working memory contains observation categories that do not match rubric categories. "
                "All observations must align with the provided rubric."
            )

        logger.info(f"Successfully extracted {len(working_memory.key_observations)} observations for Compliance agent")

        # Log warning if no compliance signals found
        if len(working_memory.key_observations) < 3:
            logger.warning("Fewer than 3 compliance observations extracted - candidate may lack compliance awareness")

        return working_memory

    except Exception as e:
        logger.error(f"Failed to extract working memory: {e}")
        raise


def _evaluate_with_memory(state: HiringWorkflowState, working_memory: WorkingMemory) -> AgentReview:
    """Generate Compliance evaluation using working memory context.

    Args:
        state: Current workflow state containing resume and rubric
        working_memory: Previously extracted observations and context

    Returns:
        AgentReview object with Compliance-specific category scores

    Raises:
        ValueError: If required state fields are missing or validation fails
    """
    logger.debug("Evaluating resume with Compliance working memory - focusing on PII handling and security awareness")

    # Extract and validate required inputs
    resume = state.get("resume")
    rubric = state.get("rubric")

    if not resume:
        raise ValueError("Resume is missing from state")
    if not rubric:
        raise ValueError("Rubric is missing from state")

    # Format rubric and working memory as JSON for prompt
    rubric_json = rubric.model_dump_json(indent=2)
    memory_json = working_memory.model_dump_json(indent=2)

    # Extract expected category names for validation
    expected_categories = [category.name for category in rubric.categories]

    # Format prompt with all required context
    formatted_prompt = COMPLIANCE_EVALUATION_PROMPT.format(
        resume=resume,
        rubric=rubric_json,
        working_memory=memory_json,
    )

    try:
        # Get structured LLM instance for AgentReview
        llm = get_structured_llm(AgentReview)
        logger.debug("Invoking LLM for Compliance evaluation")

        # Invoke LLM to generate review
        review = llm.invoke(formatted_prompt)

        # Set expected categories for Pydantic validation
        review.expected_rubric_categories = expected_categories

        # Validate agent role
        if review.agent_role != "Compliance":
            raise ValueError(f"Expected agent_role='Compliance', got '{review.agent_role}'")

        logger.info(f"Successfully generated Compliance evaluation with {len(review.category_scores)} category scores")
        return review

    except Exception as e:
        logger.error(f"Failed to generate Compliance evaluation: {e}")
        raise


def compliance_agent_node(state: HiringWorkflowState) -> Dict:
    """Compliance Agent Node - Two-pass evaluation for PII handling and security awareness.

    This node executes a two-pass evaluation process:
    1. Extract working memory: Gather Compliance-focused observations (PII handling awareness,
       bias risk identification, security posture, data retention practices, risk assessment)
    2. Evaluate with memory: Generate rubric-based scores using extracted context

    The two-pass approach ensures the agent builds comprehensive context before scoring,
    enabling thorough assessment of compliance and security awareness.

    Args:
        state: Current workflow state with resume, rubric, and company context

    Returns:
        Dictionary with state updates:
        - panel_reviews: List containing Compliance agent's review (appended by LangGraph reducer)
        - agent_working_memory: Dict mapping "Compliance" to WorkingMemory object

    Raises:
        ValueError: If state validation fails or agent role mismatches occur
    """
    logger.info("Starting Compliance agent evaluation")

    try:
        # Pass 1: Extract working memory
        working_memory = _extract_working_memory(state)
        logger.debug(f"Compliance working memory extracted: {len(working_memory.key_observations)} observations, "
                    f"{len(working_memory.cross_references)} cross-references")

        # Pass 2: Evaluate with memory context
        review = _evaluate_with_memory(state, working_memory)
        logger.info(f"Compliance evaluation completed successfully with {len(review.category_scores)} categories scored")

        # Retrieve existing agent_working_memory and merge with current agent's memory
        existing_memory = state.get("agent_working_memory", {})
        merged_memory = existing_memory.copy()
        merged_memory["Compliance"] = working_memory

        # Return state updates
        return {
            "panel_reviews": [review],  # Will be appended by LangGraph reducer
            "agent_working_memory": merged_memory,
        }

    except Exception as e:
        logger.error(f"Compliance agent node failed: {e}")
        raise
