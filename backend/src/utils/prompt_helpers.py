"""Prompt formatting utilities for structured prompt generation.

This module provides helper functions to format Pydantic models into readable
prompt strings, validate prompt templates, and extract information for use in
prompt construction.
"""

from typing import List

from models.rubric import Rubric
from models.memory import WorkingMemory


def format_rubric_for_prompt(rubric: Rubric) -> str:
    """Convert Rubric object to readable string for evaluation prompts.

    Formats the rubric in a structured way that is easy for LLMs to parse
    and use during evaluation.

    Args:
        rubric: Rubric object to format

    Returns:
        Formatted rubric string with categories, weights, and scoring criteria

    Example:
        >>> from backend.src.models.rubric import Rubric
        >>> rubric = Rubric(role_title="Senior Engineer", categories=[...])
        >>> formatted = format_rubric_for_prompt(rubric)
        >>> print(formatted)
        **Role: Senior Engineer**

        ## Evaluation Categories

        ### 1. Agent Orchestration Depth (Weight: 0.25, Must-Have: Yes)
        ...
    """
    lines = [
        f"**Role: {rubric.role_title}**",
        "",
        "## Evaluation Categories",
        ""
    ]

    for i, category in enumerate(rubric.categories, start=1):
        # Category header
        must_have_label = "Yes" if category.is_must_have else "No"
        lines.append(
            f"### {i}. {category.name} (Weight: {category.weight:.2f}, Must-Have: {must_have_label})"
        )
        lines.append(f"{category.description}")
        lines.append("")

        # Scoring criteria
        lines.append("**Scoring Criteria:**")
        for criteria in sorted(category.scoring_criteria, key=lambda x: x.score_value):
            lines.append(f"- **Score {criteria.score_value}**: {criteria.description}")
            lines.append("  - Indicators:")
            for indicator in criteria.indicators:
                lines.append(f"    - {indicator}")
        lines.append("")

    return "\n".join(lines)


def format_working_memory_for_prompt(memory: WorkingMemory) -> str:
    """Format WorkingMemory object for use in evaluation prompts.

    Converts the working memory into a structured string that can be
    referenced during the second-pass evaluation.

    Args:
        memory: WorkingMemory object to format

    Returns:
        Formatted working memory string with all observations and analysis

    Example:
        >>> from backend.src.models.memory import WorkingMemory
        >>> memory = WorkingMemory(agent_role="Tech", key_observations=[...])
        >>> formatted = format_working_memory_for_prompt(memory)
        >>> print(formatted)
        ## Working Memory (Tech Agent)

        ### Key Observations
        ...
    """
    lines = [
        f"## Working Memory ({memory.agent_role} Agent)",
        ""
    ]

    # Key observations grouped by category
    lines.append("### Key Observations")
    lines.append("")

    # Group observations by category
    observations_by_category = {}
    for obs in memory.key_observations:
        if obs.category not in observations_by_category:
            observations_by_category[obs.category] = []
        observations_by_category[obs.category].append(obs)

    for category, observations in observations_by_category.items():
        lines.append(f"**{category}:**")
        for obs in observations:
            strength_label = obs.strength_or_risk.upper()
            lines.append(f"- [{strength_label}] {obs.observation}")
            lines.append(f"  - Evidence: {obs.evidence_location}")
        lines.append("")

    # Cross-references
    if memory.cross_references:
        lines.append("### Cross-References")
        lines.append("")
        for ref in memory.cross_references:
            lines.append(f"**Claim:** \"{ref.claim}\" ({ref.claim_location})")
            lines.append(f"**Assessment:** {ref.assessment}")
            if ref.supporting_evidence:
                lines.append("**Supporting Evidence:**")
                for evidence in ref.supporting_evidence:
                    lines.append(f"  - {evidence}")
            if ref.contradictory_evidence:
                lines.append("**Contradictory Evidence:**")
                for evidence in ref.contradictory_evidence:
                    lines.append(f"  - {evidence}")
            lines.append("")

    # Timeline analysis
    if memory.timeline_analysis:
        lines.append("### Timeline Analysis")
        lines.append("")
        lines.append(memory.timeline_analysis)
        lines.append("")

    # Missing information
    if memory.missing_information:
        lines.append("### Missing Information")
        lines.append("")
        for info in memory.missing_information:
            lines.append(f"- {info}")
        lines.append("")

    # Ambiguities
    if memory.ambiguities:
        lines.append("### Ambiguities Needing Clarification")
        lines.append("")
        for ambiguity in memory.ambiguities:
            lines.append(f"- {ambiguity}")
        lines.append("")

    return "\n".join(lines)


def extract_categories_list(rubric: Rubric) -> List[str]:
    """Extract category names from rubric for working memory extraction.

    Provides a simple list of category names that can be used in prompts
    to guide agents on which categories to extract observations for.

    Args:
        rubric: Rubric object to extract categories from

    Returns:
        List of category names

    Example:
        >>> from backend.src.models.rubric import Rubric
        >>> rubric = Rubric(role_title="Senior Engineer", categories=[...])
        >>> categories = extract_categories_list(rubric)
        >>> print(categories)
        ['Agent Orchestration Depth', 'LLM Integration Expertise', ...]
    """
    return [category.name for category in rubric.categories]


def format_categories_for_prompt(rubric: Rubric) -> str:
    """Format rubric categories as a bulleted list for prompts.

    Creates a simple, readable list of categories that can be inserted
    into working memory extraction prompts.

    Args:
        rubric: Rubric object to extract categories from

    Returns:
        Formatted string with bulleted category list

    Example:
        >>> from backend.src.models.rubric import Rubric
        >>> rubric = Rubric(role_title="Senior Engineer", categories=[...])
        >>> formatted = format_categories_for_prompt(rubric)
        >>> print(formatted)
        The rubric has 5 categories to evaluate:

        1. Agent Orchestration Depth (Must-Have)
        2. LLM Integration Expertise (Must-Have)
        ...
    """
    lines = [
        f"The rubric has {len(rubric.categories)} categories to evaluate:",
        ""
    ]

    for i, category in enumerate(rubric.categories, start=1):
        must_have_label = " (Must-Have)" if category.is_must_have else ""
        lines.append(f"{i}. {category.name}{must_have_label}")

    return "\n".join(lines)


def validate_prompt_placeholders(template: str, required_keys: List[str]) -> bool:
    """Validate that all required placeholders exist in a prompt template.

    Checks that a prompt template contains all required placeholder keys
    using Python's string formatting syntax (e.g., {key_name}).

    Args:
        template: Prompt template string to validate
        required_keys: List of required placeholder keys

    Returns:
        True if all required placeholders exist, False otherwise

    Example:
        >>> template = "Hello {name}, you are {age} years old."
        >>> validate_prompt_placeholders(template, ["name", "age"])
        True
        >>> validate_prompt_placeholders(template, ["name", "age", "city"])
        False
    """
    import string

    # Parse template for placeholders
    formatter = string.Formatter()
    placeholders = {
        field_name
        for _, field_name, _, _ in formatter.parse(template)
        if field_name is not None
    }

    # Check if all required keys are present
    required_set = set(required_keys)
    return required_set.issubset(placeholders)


def get_missing_placeholders(template: str, required_keys: List[str]) -> List[str]:
    """Identify missing placeholders in a prompt template.

    Returns a list of required placeholder keys that are missing from
    the template.

    Args:
        template: Prompt template string to validate
        required_keys: List of required placeholder keys

    Returns:
        List of missing placeholder keys

    Example:
        >>> template = "Hello {name}, you are {age} years old."
        >>> get_missing_placeholders(template, ["name", "age", "city"])
        ['city']
    """
    import string

    # Parse template for placeholders
    formatter = string.Formatter()
    placeholders = {
        field_name
        for _, field_name, _, _ in formatter.parse(template)
        if field_name is not None
    }

    # Find missing keys
    required_set = set(required_keys)
    missing = required_set - placeholders

    return sorted(list(missing))


def format_agent_review_simple(review) -> str:
    """Format AgentReview object into simple readable summary.

    Creates a concise summary of an agent's review suitable for display
    or inclusion in other prompts.

    Args:
        review: AgentReview object to format

    Returns:
        Formatted review summary string

    Example:
        >>> from backend.src.models.review import AgentReview
        >>> review = AgentReview(agent_role="Tech", ...)
        >>> formatted = format_agent_review_simple(review)
        >>> print(formatted)
        ## Tech Agent Review

        **Overall Assessment:**
        Strong technical candidate...
        ...
    """
    lines = [
        f"## {review.agent_role} Agent Review",
        "",
        "**Overall Assessment:**",
        review.overall_assessment,
        "",
        "**Category Scores:**"
    ]

    for score in review.category_scores:
        lines.append(f"- {score.category_name}: {score.score}/5 ({score.confidence} confidence)")

    lines.append("")
    lines.append("**Top Strengths:**")
    for i, strength in enumerate(review.top_strengths, start=1):
        lines.append(f"{i}. {strength}")

    lines.append("")
    lines.append("**Top Risks:**")
    for i, risk in enumerate(review.top_risks, start=1):
        lines.append(f"{i}. {risk}")

    return "\n".join(lines)
