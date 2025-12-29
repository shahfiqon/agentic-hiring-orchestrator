"""
LangGraph State Schema for Hiring Workflow

This module defines the complete state schema for the hiring evaluation workflow.
LangGraph uses this TypedDict to manage state transitions across nodes.

## Workflow State Flow

```
Initial State:
├─ job_description (str)
├─ resume (str)
└─ company_context (Optional[str])

    ↓ [Orchestrator Node]

After Orchestrator:
└─ rubric (Rubric) ← Generated evaluation framework

    ↓ [Panel Agents - Parallel Execution]

After Panel Agents:
├─ panel_reviews (List[AgentReview]) ← HR, Tech, Compliance, (Product) reviews
└─ agent_working_memory (Dict[str, WorkingMemory]) ← Structured observations by agent

    ↓ [Synthesis Node]

Final State:
├─ disagreements (List[Disagreement]) ← Score conflicts between agents
├─ decision_packet (DecisionPacket) ← Final hiring recommendation
├─ interview_plan (InterviewPlan) ← Role-specific questions
└─ workflow_metadata (Dict[str, Any]) ← Execution tracking
```

## State Management Notes

- **Immutability**: LangGraph treats state updates as immutable; each node returns
  partial state updates that are merged into the full state.

- **Reducer Functions**: For list fields like `panel_reviews`, LangGraph can use
  reducer functions to append rather than replace (configured in graph definition).

- **Type Safety**: TypedDict provides compile-time type checking for state access
  and updates throughout the workflow.

## Example State Transitions

```python
# Initial state
state = {
    "job_description": "Senior Backend Engineer...",
    "resume": "John Doe, 5+ years Python...",
    "company_context": "Series B startup, AI infrastructure"
}

# After orchestrator node
state.update({
    "rubric": Rubric(categories=[...], scoring_bands=[...])
})

# After panel agents (parallel execution)
state.update({
    "panel_reviews": [
        AgentReview(agent_role="HR", ...),
        AgentReview(agent_role="Tech", ...),
        AgentReview(agent_role="Compliance", ...)
    ],
    "agent_working_memory": {
        "HR": WorkingMemory(agent_role="HR", key_observations=[...]),
        "Tech": WorkingMemory(agent_role="Tech", key_observations=[...]),
        "Compliance": WorkingMemory(agent_role="Compliance", key_observations=[...])
    }
})

# After synthesis node
state.update({
    "disagreements": [Disagreement(...)],
    "decision_packet": DecisionPacket(...),
    "interview_plan": InterviewPlan(...)
})
```
"""

from typing import Any, Dict, List, Optional, TypedDict

from backend.src.models.interview import InterviewPlan
from backend.src.models.memory import WorkingMemory
from backend.src.models.packet import DecisionPacket, Disagreement
from backend.src.models.review import AgentReview
from backend.src.models.rubric import Rubric


class HiringWorkflowState(TypedDict, total=False):
    """
    Complete state schema for the hiring evaluation workflow.

    This TypedDict defines all fields that flow through the LangGraph workflow,
    from initial inputs through orchestration, panel evaluation, and final synthesis.

    Fields are marked as required (total=True default) or optional based on when
    they are populated in the workflow. The `total=False` parameter allows all
    fields to be optional, matching LangGraph's partial state update pattern.

    ## Field Population Timeline

    **Initial State (provided by user/system):**
    - job_description: Job posting text
    - resume: Candidate resume text
    - company_context: Optional additional context

    **After Orchestrator Node:**
    - rubric: Generated evaluation framework with categories and scoring bands

    **After Panel Agents (parallel execution):**
    - panel_reviews: One AgentReview per agent (HR, Tech, Compliance, optionally Product)
    - agent_working_memory: WorkingMemory objects keyed by agent role
      (e.g., {"HR": WorkingMemory(...), "Tech": WorkingMemory(...)})

    **After Synthesis Node:**
    - disagreements: Score conflicts between agents requiring resolution
    - decision_packet: Final hiring recommendation with evidence and confidence
    - interview_plan: Role-specific interview questions

    **Throughout Workflow:**
    - workflow_metadata: Execution tracking (timestamps, node order, errors)
      Common keys: "start_time", "end_time", "node_execution_order", "errors"
    """

    # ==================== Input Fields ====================
    # Provided at workflow initiation

    job_description: str
    """Job posting text defining role requirements and expectations."""

    resume: str
    """Candidate resume text to be evaluated."""

    company_context: Optional[str]
    """Additional company information, culture notes, or hiring priorities."""

    # ==================== Orchestrator Outputs ====================
    # Populated by orchestrator node

    rubric: Rubric
    """
    Generated evaluation rubric with categories, criteria, and scoring bands.
    Created by orchestrator based on job description and company context.
    """

    # ==================== Panel Agent Outputs ====================
    # Populated by parallel panel agent execution

    panel_reviews: List[AgentReview]
    """
    Reviews from each panel agent (HR, Tech, Compliance, optionally Product).
    Each review contains category scores, rationales, and recommendations.
    Length typically 3-4 depending on whether Product agent is included.
    """

    agent_working_memory: Dict[str, WorkingMemory]
    """
    Working memory objects keyed by agent role.
    Structure: {"HR": WorkingMemory(...), "Tech": WorkingMemory(...), ...}

    Contains structured observations from first-pass resume analysis,
    enabling context-aware evaluation and disagreement resolution.
    Keys must match agent_role values in panel_reviews.
    """

    # ==================== Synthesis Outputs ====================
    # Populated by synthesis node

    disagreements: List[Disagreement]
    """
    Score conflicts between agents requiring resolution or documentation.
    Empty list if agents are aligned on all categories.
    """

    decision_packet: DecisionPacket
    """
    Final hiring recommendation with aggregate scores, evidence summary,
    and confidence assessment. Synthesizes all panel reviews.
    """

    interview_plan: InterviewPlan
    """
    Role-specific interview questions generated from rubric categories
    and working memory gaps. Includes time allocations and evaluation focus.
    """

    # ==================== Metadata ====================
    # Updated throughout workflow execution

    workflow_metadata: Dict[str, Any]
    """
    Execution metadata for observability and debugging.

    Common keys:
    - start_time (str): ISO timestamp when workflow started
    - end_time (str): ISO timestamp when workflow completed
    - node_execution_order (List[str]): Sequence of executed nodes
    - errors (List[Dict]): Any errors encountered during execution
    - agent_execution_times (Dict[str, float]): Per-agent execution duration
    - llm_token_usage (Dict[str, int]): Token consumption tracking
    """


# ==================== State Validation Utilities ====================


class StateValidationError(Exception):
    """
    Raised when state validation fails due to inconsistent or invalid data.

    This exception is used specifically for state integrity checks that detect
    mismatches between related state fields (e.g., panel_reviews and agent_working_memory).
    """
    pass


def validate_panel_memory_consistency(state: HiringWorkflowState) -> None:
    """
    Validate that agent_working_memory keys match panel_reviews agent roles.

    This function ensures consistency between panel_reviews and agent_working_memory
    by verifying that:
    1. All agent roles in panel_reviews have corresponding working memory entries
    2. All working memory keys correspond to valid panel review agents
    3. Agent role keys are normalized to expected literals (HR, Tech, Product, Compliance)

    This validation should be called in the panel fan-in step BEFORE passing state
    to the synthesis node, ensuring that synthesis has consistent and complete data.

    Args:
        state: HiringWorkflowState after panel agents have executed

    Raises:
        StateValidationError: If panel_reviews and agent_working_memory have mismatched
            agent role keys, or if keys don't match expected literals

    Example:
        >>> state = {
        ...     "panel_reviews": [
        ...         AgentReview(agent_role="HR", ...),
        ...         AgentReview(agent_role="Tech", ...),
        ...     ],
        ...     "agent_working_memory": {
        ...         "HR": WorkingMemory(agent_role="HR", ...),
        ...         "Tech": WorkingMemory(agent_role="Tech", ...),
        ...     }
        ... }
        >>> validate_panel_memory_consistency(state)  # Passes

        >>> state_invalid = {
        ...     "panel_reviews": [
        ...         AgentReview(agent_role="HR", ...),
        ...     ],
        ...     "agent_working_memory": {
        ...         "Tech": WorkingMemory(agent_role="Tech", ...),
        ...     }
        ... }
        >>> validate_panel_memory_consistency(state_invalid)
        StateValidationError: Panel reviews and agent working memory have mismatched agent roles...
    """
    # Expected valid agent role literals
    VALID_AGENT_ROLES = {"HR", "Tech", "Product", "Compliance"}

    # Check if both fields exist in state
    panel_reviews = state.get("panel_reviews")
    agent_working_memory = state.get("agent_working_memory")

    # If either field is missing, skip validation (not yet populated)
    if panel_reviews is None or agent_working_memory is None:
        return

    # Extract agent roles from panel_reviews
    panel_agent_roles = {review.agent_role for review in panel_reviews}

    # Extract keys from agent_working_memory
    memory_agent_roles = set(agent_working_memory.keys())

    # Validate that panel agent roles are all valid literals
    invalid_panel_roles = panel_agent_roles - VALID_AGENT_ROLES
    if invalid_panel_roles:
        raise StateValidationError(
            f"Invalid agent roles in panel_reviews: {sorted(invalid_panel_roles)}. "
            f"Expected one of: {sorted(VALID_AGENT_ROLES)}"
        )

    # Validate that memory keys are all valid literals
    invalid_memory_roles = memory_agent_roles - VALID_AGENT_ROLES
    if invalid_memory_roles:
        raise StateValidationError(
            f"Invalid agent roles in agent_working_memory: {sorted(invalid_memory_roles)}. "
            f"Expected one of: {sorted(VALID_AGENT_ROLES)}"
        )

    # Check for mismatches between panel_reviews and agent_working_memory
    missing_from_memory = panel_agent_roles - memory_agent_roles
    extra_in_memory = memory_agent_roles - panel_agent_roles

    if missing_from_memory or extra_in_memory:
        error_parts = []

        if missing_from_memory:
            error_parts.append(
                f"Missing from agent_working_memory: {sorted(missing_from_memory)}"
            )

        if extra_in_memory:
            error_parts.append(
                f"Extra in agent_working_memory (no corresponding panel review): {sorted(extra_in_memory)}"
            )

        raise StateValidationError(
            f"Panel reviews and agent working memory have mismatched agent roles. "
            f"{'; '.join(error_parts)}. "
            f"Panel review agents: {sorted(panel_agent_roles)}, "
            f"Working memory agents: {sorted(memory_agent_roles)}"
        )

    # Additional validation: ensure WorkingMemory.agent_role matches the dictionary key
    for memory_key, working_memory in agent_working_memory.items():
        if working_memory.agent_role != memory_key:
            raise StateValidationError(
                f"WorkingMemory agent_role mismatch: dictionary key is '{memory_key}' "
                f"but WorkingMemory.agent_role is '{working_memory.agent_role}'. "
                f"These must be identical."
            )
