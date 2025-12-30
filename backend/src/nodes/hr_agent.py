"""HR Agent Node - Evaluates cultural fit, seniority, and leadership potential.

This module implements the HR agent's two-pass evaluation workflow:
1. Extract WorkingMemory: Gather observations about cultural fit, leadership, communication
2. Evaluate with Memory: Generate rubric-based scores using extracted context
"""

import logging
from typing import Dict

from src.state import HiringWorkflowState
from src.models.memory import WorkingMemory
from src.models.review import AgentReview
from src.utils.llm import get_structured_llm
from src.prompts.agent_prompts import (
    WORKING_MEMORY_EXTRACTION_PROMPT,
    HR_EVALUATION_PROMPT,
)

logger = logging.getLogger(__name__)


def _extract_working_memory(state: HiringWorkflowState) -> WorkingMemory:
    """Extract HR-focused observations from resume.

    Args:
        state: Current workflow state containing resume and rubric

    Returns:
        WorkingMemory object with HR-specific observations

    Raises:
        ValueError: If required state fields are missing or validation fails
    """
    logger.debug("Extracting working memory for HR agent")

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
        agent_role="HR",
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
        if working_memory.agent_role != "HR":
            raise ValueError(f"Expected agent_role='HR', got '{working_memory.agent_role}'")

        # Validate working memory against rubric categories
        if not working_memory.validate_against_rubric(rubric):
            raise ValueError(
                "Working memory contains observation categories that do not match rubric categories. "
                "All observations must align with the provided rubric."
            )

        logger.info(f"Successfully extracted {len(working_memory.key_observations)} observations for HR agent")
        return working_memory

    except Exception as e:
        logger.error(f"Failed to extract working memory: {e}")
        raise


def _evaluate_with_memory(state: HiringWorkflowState, working_memory: WorkingMemory) -> AgentReview:
    """Generate HR evaluation using working memory context.

    Args:
        state: Current workflow state containing resume and rubric
        working_memory: Previously extracted observations and context

    Returns:
        AgentReview object with HR-specific category scores

    Raises:
        ValueError: If required state fields are missing or validation fails
    """
    logger.debug("Evaluating resume with HR working memory")

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
    formatted_prompt = HR_EVALUATION_PROMPT.format(
        resume=resume,
        rubric=rubric_json,
        working_memory=memory_json,
    )

    try:
        # Get structured LLM instance for AgentReview
        llm = get_structured_llm(AgentReview)
        logger.debug("Invoking LLM for HR evaluation")

        # Invoke LLM to generate review
        review = llm.invoke(formatted_prompt)

        # Set expected categories for Pydantic validation
        review.expected_rubric_categories = expected_categories

        # Validate agent role
        if review.agent_role != "HR":
            raise ValueError(f"Expected agent_role='HR', got '{review.agent_role}'")

        logger.info(f"Successfully generated HR evaluation with {len(review.category_scores)} category scores")
        return review

    except Exception as e:
        logger.error(f"Failed to generate HR evaluation: {e}")
        raise


def hr_agent_node(state: HiringWorkflowState) -> Dict:
    """HR Agent Node - Two-pass evaluation for cultural fit and leadership.

    This node executes a two-pass evaluation process:
    1. Extract working memory: Gather HR-focused observations (seniority, leadership,
       communication, career trajectory)
    2. Evaluate with memory: Generate rubric-based scores using extracted context

    The two-pass approach ensures the agent builds comprehensive context before scoring,
    reducing hasty judgments and improving evaluation quality.

    Args:
        state: Current workflow state with resume, rubric, and company context

    Returns:
        Dictionary with state updates:
        - panel_reviews: List containing HR agent's review (appended by LangGraph reducer)
        - agent_working_memory: Dict mapping "HR" to WorkingMemory object

    Raises:
        ValueError: If state validation fails or agent role mismatches occur
    """
    logger.info("Starting HR agent evaluation")

    try:
        # Pass 1: Extract working memory
        working_memory = _extract_working_memory(state)
        logger.debug(f"HR working memory extracted: {len(working_memory.key_observations)} observations, "
                    f"{len(working_memory.cross_references)} cross-references")

        # Pass 2: Evaluate with memory context
        review = _evaluate_with_memory(state, working_memory)
        logger.info(f"HR evaluation completed successfully with {len(review.category_scores)} categories scored")

        # Retrieve existing agent_working_memory and merge with current agent's memory
        existing_memory = state.get("agent_working_memory", {})
        merged_memory = existing_memory.copy()
        merged_memory["HR"] = working_memory

        # Return state updates
        return {
            "panel_reviews": [review],  # Will be appended by LangGraph reducer
            "agent_working_memory": merged_memory,
        }

    except Exception as e:
        logger.error(f"HR agent node failed: {e}")
        raise
