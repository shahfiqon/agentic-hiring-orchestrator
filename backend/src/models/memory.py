"""
Working Memory Models for Two-Pass Evaluation Pattern

This module implements the working memory system described in 004-memory-integration.md,
enabling a two-pass evaluation approach:

1. **First Pass (Observation Extraction)**: Agents scan the resume and extract structured
   observations into WorkingMemory, noting key strengths, risks, cross-references between
   sections, timeline inconsistencies, and information gaps.

2. **Second Pass (Context-Aware Evaluation)**: Agents use the WorkingMemory to perform
   rubric-based evaluation with full context, reducing hallucinations and improving
   accuracy by grounding evaluations in explicitly documented observations.

The working memory enables:
- Cross-referencing claims against evidence across resume sections
- Identifying timeline gaps and career trajectory patterns
- Documenting ambiguities that need clarification in interviews
- Providing structured context for disagreement resolution

Usage Example:
    # First pass: Extract observations
    memory = WorkingMemory(
        agent_role="Tech",
        key_observations=[
            KeyObservation(
                category="Multi-Agent Systems",
                observation="Designed LangGraph orchestration with 4 specialized agents",
                evidence_location="Experience > Senior Engineer section",
                strength_or_risk="strength"
            )
        ],
        cross_references=[
            CrossReference(
                claim="5+ years Python experience",
                claim_location="Skills section",
                supporting_evidence=["2019-2024 roles all list Python"],
                contradictory_evidence=[],
                assessment="well-supported"
            )
        ]
    )

    # Second pass: Evaluate with memory context
    review = agent.evaluate_with_memory(rubric, memory)
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class KeyObservation(BaseModel):
    """
    Individual observation extracted from resume during first pass.

    Each observation captures a specific strength, risk, or neutral finding
    tied to a rubric category, with evidence location for traceability.
    """

    category: str = Field(
        ...,
        min_length=1,
        description="Rubric category this observation relates to (e.g., 'Multi-Agent Systems')"
    )
    observation: str = Field(
        ...,
        min_length=1,
        description="What the agent noticed in the resume"
    )
    evidence_location: str = Field(
        ...,
        min_length=1,
        description="Where this was found (e.g., 'Experience > Senior Engineer section')"
    )
    strength_or_risk: Literal["strength", "risk", "neutral"] = Field(
        ...,
        description="Classification of this observation"
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "category": "Multi-Agent Systems",
                "observation": "Designed LangGraph orchestration with 4 specialized agents (HR, Tech, Compliance, Product) using TypedDict state management",
                "evidence_location": "Experience > Senior Engineer, Acme Corp section",
                "strength_or_risk": "strength"
            }
        }
    )


class CrossReference(BaseModel):
    """
    Links between resume sections for claim verification.

    Enables agents to verify claims by cross-referencing evidence across
    multiple resume sections, identifying well-supported vs. unsupported claims.
    """

    claim: str = Field(
        ...,
        min_length=1,
        description="The claim being made in the resume"
    )
    claim_location: str = Field(
        ...,
        min_length=1,
        description="Where the claim appears (section/subsection)"
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Resume sections that support this claim"
    )
    contradictory_evidence: List[str] = Field(
        default_factory=list,
        description="Resume sections that contradict this claim"
    )
    assessment: Literal[
        "well-supported",
        "partially-supported",
        "unsupported",
        "contradictory"
    ] = Field(
        ...,
        description="Overall assessment of claim validity"
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "claim": "5+ years Python experience",
                "claim_location": "Skills > Programming Languages section",
                "supporting_evidence": [
                    "Experience > Senior Engineer (2021-2024): Python microservices",
                    "Experience > Engineer (2019-2021): Python data pipelines",
                    "Projects > Open source: Python CLI tool"
                ],
                "contradictory_evidence": [],
                "assessment": "well-supported"
            }
        }
    )

    @model_validator(mode='after')
    def validate_has_evidence(self) -> 'CrossReference':
        """Ensure at least one type of evidence exists."""
        if not self.supporting_evidence and not self.contradictory_evidence:
            raise ValueError(
                "CrossReference must have at least supporting_evidence or contradictory_evidence"
            )
        return self


class WorkingMemory(BaseModel):
    """
    Complete agent notes from first pass of resume analysis.

    Contains structured observations, cross-references, timeline analysis,
    and gap identification. Provides context for second-pass evaluation
    and supports disagreement resolution with evidence trails.
    """

    agent_role: Literal["HR", "Tech", "Product", "Compliance"] = Field(
        ...,
        description="Role of the agent who created this memory"
    )
    key_observations: List[KeyObservation] = Field(
        ...,
        min_length=3,
        max_length=15,
        description="5-8 key observations extracted from resume"
    )
    cross_references: List[CrossReference] = Field(
        default_factory=list,
        description="Links between resume sections for claim verification"
    )
    timeline_analysis: Optional[str] = Field(
        default=None,
        description="Career trajectory patterns, gaps, or progression notes"
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Expected information that is absent from resume"
    )
    ambiguities: List[str] = Field(
        default_factory=list,
        description="Unclear statements that need clarification in interview"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this working memory was created"
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "agent_role": "Tech",
                "key_observations": [
                    {
                        "category": "Multi-Agent Systems",
                        "observation": "Designed LangGraph orchestration with 4 specialized agents using TypedDict state management and parallel execution",
                        "evidence_location": "Experience > Senior Engineer section",
                        "strength_or_risk": "strength"
                    },
                    {
                        "category": "LLM Integration",
                        "observation": "Implemented two-pass evaluation pattern with working memory for context-aware reviews",
                        "evidence_location": "Experience > Recent project details",
                        "strength_or_risk": "strength"
                    },
                    {
                        "category": "Production Experience",
                        "observation": "No mention of error handling, monitoring, or observability in LLM systems",
                        "evidence_location": "N/A - absent from all sections",
                        "strength_or_risk": "risk"
                    }
                ],
                "cross_references": [
                    {
                        "claim": "Expert in LangGraph and LangChain",
                        "claim_location": "Skills > Frameworks section",
                        "supporting_evidence": [
                            "Experience > Built hiring orchestrator with LangGraph",
                            "Projects > Contributed to LangChain ecosystem"
                        ],
                        "contradictory_evidence": [],
                        "assessment": "well-supported"
                    }
                ],
                "timeline_analysis": "Consistent progression: Junior (2019) -> Mid (2021) -> Senior (2023). Each role shows increased scope and technical leadership.",
                "missing_information": [
                    "Team size and collaboration experience",
                    "Production incident handling experience",
                    "Metrics/KPIs for LLM system performance"
                ],
                "ambiguities": [
                    "What does 'orchestrated multi-agent system' mean in practice? Scale? Complexity?",
                    "LangGraph experience timeline unclear - when did they start?"
                ],
                "created_at": "2024-01-15T10:30:00"
            }
        }
    )

    @model_validator(mode='after')
    def validate_agent_role(self) -> 'WorkingMemory':
        """Ensure agent_role is valid."""
        valid_roles = ["HR", "Tech", "Product", "Compliance"]
        if self.agent_role not in valid_roles:
            raise ValueError(
                f"agent_role must be one of {valid_roles}, got '{self.agent_role}'"
            )
        return self

    @model_validator(mode='after')
    def validate_observations_count(self) -> 'WorkingMemory':
        """Ensure reasonable number of key observations."""
        count = len(self.key_observations)
        if count < 3 or count > 15:
            raise ValueError(
                f"key_observations should have 3-15 items for meaningful analysis, got {count}"
            )
        return self

    def get_observations_for_category(self, category_name: str) -> List[KeyObservation]:
        """
        Retrieve all observations for a specific rubric category.

        Args:
            category_name: Name of the rubric category to filter by

        Returns:
            List of KeyObservation objects matching the category
        """
        return [
            obs for obs in self.key_observations
            if obs.category == category_name
        ]

    def get_cross_references_by_assessment(
        self,
        assessment: str
    ) -> List[CrossReference]:
        """
        Filter cross-references by assessment type.

        Args:
            assessment: One of "well-supported", "partially-supported",
                       "unsupported", "contradictory"

        Returns:
            List of CrossReference objects matching the assessment
        """
        return [
            ref for ref in self.cross_references
            if ref.assessment == assessment
        ]

    def validate_against_rubric(self, rubric) -> bool:
        """
        Validate that observation categories match rubric categories.

        Args:
            rubric: Rubric object with categories to validate against

        Returns:
            True if all observation categories exist in rubric, False otherwise
        """
        rubric_categories = {cat.name for cat in rubric.categories}
        observation_categories = {obs.category for obs in self.key_observations}

        invalid_categories = observation_categories - rubric_categories
        return len(invalid_categories) == 0

    def get_priority_gaps(self) -> List[str]:
        """
        Combine missing information and ambiguities for interview planning.

        Returns:
            Combined list of gaps and ambiguities that need clarification
        """
        return self.missing_information + self.ambiguities
