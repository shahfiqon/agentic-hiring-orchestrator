"""Decision packet models for synthesized hiring recommendations.

This module defines Pydantic models for decision synthesis:
- Disagreement: Agent score conflicts requiring resolution
- DecisionPacket: Final hiring recommendation with evidence synthesis
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator, computed_field, ConfigDict


class Disagreement(BaseModel):
    """Captures significant score disagreements between agents.

    Highlights areas where agents have different perspectives,
    requiring discussion or interview validation.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    category_name: str = Field(
        min_length=1,
        description="Rubric category where disagreement occurred"
    )
    agent_scores: Dict[str, int] = Field(
        description="Mapping of agent role to score (e.g., {'HR': 4, 'Tech': 2, 'Product': 3})"
    )
    reason: str = Field(
        min_length=1,
        description="Explanation of why agents scored differently (different evidence, different priorities, etc.)"
    )
    resolution_approach: str = Field(
        min_length=1,
        description="How to resolve this disagreement (interview questions, reference checks, portfolio review, etc.)"
    )

    @computed_field
    @property
    def score_delta(self) -> float:
        """Calculate the maximum score difference between agents.

        Returns:
            The difference between highest and lowest scores
        """
        if not self.agent_scores:
            return 0.0

        scores = list(self.agent_scores.values())
        return float(max(scores) - min(scores))

    @model_validator(mode='after')
    def validate_agent_scores(self) -> 'Disagreement':
        """Ensure agent scores are valid and show actual disagreement."""
        if not self.agent_scores:
            raise ValueError(
                f"Category '{self.category_name}' disagreement must include "
                f"at least one agent score."
            )

        # Validate all scores are in 0-5 range
        for agent_role, score in self.agent_scores.items():
            if not isinstance(score, int) or score < 0 or score > 5:
                raise ValueError(
                    f"Invalid score {score} for agent '{agent_role}'. "
                    f"Scores must be integers from 0 to 5."
                )

        # Validate there's actual disagreement (delta > 0)
        if self.score_delta < 1:
            raise ValueError(
                f"Category '{self.category_name}' shows no significant disagreement "
                f"(delta: {self.score_delta}). Only include disagreements with delta >= 1."
            )

        # Validate agent roles are valid
        valid_roles = {"HR", "Tech", "Product", "Compliance"}
        invalid_roles = set(self.agent_scores.keys()) - valid_roles
        if invalid_roles:
            raise ValueError(
                f"Invalid agent roles in disagreement: {invalid_roles}. "
                f"Valid roles: {valid_roles}"
            )

        return self

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "category_name": "Domain Knowledge (Hiring/HR Tech)",
                    "agent_scores": {
                        "HR": 2,
                        "Tech": 4,
                        "Product": 3
                    },
                    "reason": "HR agent focused on lack of specific hiring workflow experience and gave low score. Tech agent focused on transferable skills from building similar B2B SaaS products and scored higher. Product agent took middle ground, noting some relevant product sense but gaps in HR-specific domain.",
                    "resolution_approach": "Ask behavioral questions about how they approach learning new domains and handling unfamiliar business contexts. Probe specific hiring workflow knowledge (sourcing, screening, interviewing, offer management) to validate actual gap size."
                }
            ]
        }
    )


class DecisionPacket(BaseModel):
    """Final hiring decision with synthesized recommendations.

    Combines all agent reviews into a weighted overall assessment
    with clear recommendation, strengths, risks, and action items.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    candidate_name: Optional[str] = Field(
        default=None,
        description="Candidate identifier (may be redacted for blind review)"
    )
    role_title: str = Field(
        min_length=1,
        description="Position being evaluated"
    )
    overall_fit_score: float = Field(
        ge=0.0,
        le=5.0,
        description="Weighted average score across all categories (0.0-5.0 scale)"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence in this recommendation based on evidence quality and agent agreement"
    )
    recommendation: Optional[Literal["Hire", "Lean hire", "Lean no", "No"]] = Field(
        default=None,
        description="Hiring recommendation (optional - may be withheld pending interview)"
    )
    top_strengths: List[str] = Field(
        min_length=3,
        max_length=5,
        description="3-5 strongest qualifications with evidence references from agent reviews"
    )
    top_risks: List[str] = Field(
        min_length=3,
        max_length=5,
        description="3-5 key risks, concerns, or areas requiring validation"
    )
    must_have_gaps: List[str] = Field(
        default_factory=list,
        description="Missing must-have requirements (critical gaps that may disqualify)"
    )
    disagreements: List[Disagreement] = Field(
        default_factory=list,
        description="Significant score disagreements between agents requiring resolution"
    )
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when this decision packet was created"
    )

    @model_validator(mode='after')
    def validate_overall_fit_score(self) -> 'DecisionPacket':
        """Ensure overall fit score is in valid range."""
        if self.overall_fit_score < 0.0 or self.overall_fit_score > 5.0:
            raise ValueError(
                f"overall_fit_score must be between 0.0 and 5.0. "
                f"Got: {self.overall_fit_score}"
            )
        return self

    @model_validator(mode='after')
    def validate_recommendation_alignment(self) -> 'DecisionPacket':
        """Validate recommendation aligns with score and must-have gaps."""
        if self.recommendation:
            # If critical must-have gaps exist, recommendation should not be "Hire"
            if self.must_have_gaps and self.recommendation == "Hire":
                raise ValueError(
                    f"Recommendation is 'Hire' but must-have gaps exist: {self.must_have_gaps}. "
                    f"Cannot recommend hiring with critical qualification gaps."
                )

            # Validate recommendation is reasonable given score
            if self.overall_fit_score >= 4.0 and self.recommendation in ["Lean no", "No"]:
                raise ValueError(
                    f"overall_fit_score is {self.overall_fit_score} (strong) but "
                    f"recommendation is '{self.recommendation}'. This seems inconsistent."
                )

            if self.overall_fit_score < 2.0 and self.recommendation in ["Hire", "Lean hire"]:
                raise ValueError(
                    f"overall_fit_score is {self.overall_fit_score} (weak) but "
                    f"recommendation is '{self.recommendation}'. This seems inconsistent."
                )

        return self

    def has_critical_gaps(self) -> bool:
        """Check if candidate is missing must-have requirements.

        Returns:
            True if any must-have gaps exist, False otherwise
        """
        return len(self.must_have_gaps) > 0

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "candidate_name": "Candidate #2847",
                    "role_title": "Senior AI Engineer - Agentic Systems",
                    "overall_fit_score": 4.2,
                    "confidence": "high",
                    "recommendation": "Lean hire",
                    "top_strengths": [
                        "Production-scale LLM experience with 10M+ requests/month across GPT-4 and Claude (Tech review, LLM Integration category)",
                        "Hands-on LangGraph implementation coordinating 4 specialized agents with state management (Tech review, Agent Orchestration category)",
                        "Strong system design skills with microservices and event-driven architectures (Tech review, System Design category)",
                        "Excellent communication and documentation as evidenced by technical blog posts (HR review, multiple categories)"
                    ],
                    "top_risks": [
                        "No evidence of 5+ agent systems - may need time to scale to more complex orchestration requirements",
                        "Limited HR/hiring domain knowledge - will require significant onboarding on domain workflows and terminology",
                        "No mention of testing strategies for non-deterministic LLM systems - gap in quality assurance approach",
                        "Score disagreement on Domain Knowledge (HR: 2, Tech: 4, Product: 3) needs interview validation"
                    ],
                    "must_have_gaps": [],
                    "disagreements": [
                        {
                            "category_name": "Domain Knowledge (Hiring/HR Tech)",
                            "agent_scores": {"HR": 2, "Tech": 4, "Product": 3},
                            "reason": "HR focused on lack of hiring-specific experience, Tech valued transferable B2B SaaS skills",
                            "resolution_approach": "Interview questions on domain learning and hiring workflow understanding"
                        }
                    ],
                    "generated_at": "2025-01-15T14:30:00"
                }
            ]
        }
    )
