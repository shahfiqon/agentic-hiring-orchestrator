"""Review models for agent evaluations with evidence-based scoring.

This module defines Pydantic models for structured agent reviews:
- Evidence: Direct citations from resume/application materials
- CategoryScore: Score with supporting evidence for a rubric category
- AgentReview: Complete evaluation from a single agent perspective
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator, ConfigDict


class Evidence(BaseModel):
    """Direct evidence citation from resume or application materials.

    Ensures all scoring decisions are grounded in specific, verifiable
    information from candidate materials.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    resume_text: str = Field(
        min_length=1,
        description="Direct quote from resume, cover letter, or application materials"
    )
    line_reference: Optional[str] = Field(
        default=None,
        description="Location reference for traceability (e.g., 'Experience section, 2nd bullet', 'Skills: line 3')"
    )
    interpretation: str = Field(
        min_length=1,
        description="Explanation of why this evidence matters for the scoring decision"
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "resume_text": "Designed and implemented multi-agent orchestration system using LangGraph to coordinate 4 specialized agents (research, analysis, synthesis, validation) for automated report generation",
                    "line_reference": "Experience section, Current Role - 3rd bullet",
                    "interpretation": "Demonstrates hands-on experience with LangGraph framework and coordination of multiple specialized agents, directly relevant to agent orchestration depth requirement"
                }
            ]
        }
    )


class CategoryScore(BaseModel):
    """Score for a single rubric category with evidence and confidence.

    Each score must be supported by at least one piece of evidence
    and include gaps or missing information for transparency.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    category_name: str = Field(
        min_length=1,
        description="Must match a category name from the evaluation rubric"
    )
    score: int = Field(
        ge=0,
        le=5,
        description="Score from 0 (no evidence) to 5 (exceptional) based on rubric criteria"
    )
    evidence: List[Evidence] = Field(
        min_length=1,
        description="Required evidence citations supporting this score (minimum 1 piece of evidence)"
    )
    gaps: List[str] = Field(
        default_factory=list,
        description="Missing or unclear information that prevented a higher score"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level in this score based on evidence quality and completeness"
    )

    @model_validator(mode='after')
    def validate_evidence_not_empty(self) -> 'CategoryScore':
        """Ensure at least one piece of evidence is provided."""
        if not self.evidence or len(self.evidence) == 0:
            raise ValueError(
                f"Category '{self.category_name}' score must include at least one "
                f"piece of evidence. Evidence-based evaluation is required."
            )
        return self

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "category_name": "Agent Orchestration Depth",
                    "score": 4,
                    "evidence": [
                        {
                            "resume_text": "Designed multi-agent orchestration system using LangGraph to coordinate 4 specialized agents",
                            "line_reference": "Experience section, Current Role - 3rd bullet",
                            "interpretation": "Shows practical LangGraph experience with multiple agents"
                        },
                        {
                            "resume_text": "Implemented dynamic agent routing based on task complexity and agent availability",
                            "line_reference": "Experience section, Current Role - 5th bullet",
                            "interpretation": "Demonstrates understanding of advanced coordination patterns"
                        }
                    ],
                    "gaps": [
                        "No mention of handling 5+ agents (required for score of 5)",
                        "Unclear if they've designed agent communication protocols from scratch",
                        "No published work or presentations on agent orchestration mentioned"
                    ],
                    "confidence": "high"
                }
            ]
        }
    )


class AgentReview(BaseModel):
    """Complete evaluation from a single agent perspective.

    Each agent (HR, Tech, Product, Compliance) provides category scores
    with evidence, overall assessment, and follow-up questions.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    agent_role: Literal["HR", "Tech", "Product", "Compliance"] = Field(
        description="Agent perspective: HR (culture/communication), Tech (technical skills), Product (product sense), Compliance (legal/regulatory)"
    )
    category_scores: List[CategoryScore] = Field(
        min_length=1,
        description="One score per rubric category, each with supporting evidence"
    )
    overall_assessment: str = Field(
        min_length=1,
        description="Summary assessment paragraph synthesizing category scores and overall fit"
    )
    top_strengths: List[str] = Field(
        min_length=3,
        max_length=5,
        description="3-5 key strengths with references to specific evidence"
    )
    top_risks: List[str] = Field(
        min_length=3,
        max_length=5,
        description="3-5 key risks, concerns, or areas needing validation"
    )
    follow_up_questions: List[str] = Field(
        min_length=1,
        description="Questions to ask in interview to validate assumptions or probe gaps"
    )
    expected_rubric_categories: Optional[List[str]] = Field(
        default=None,
        description="Expected rubric category names for validation. If provided, category_scores must cover exactly these categories."
    )

    @model_validator(mode='after')
    def validate_agent_role(self) -> 'AgentReview':
        """Validate agent role is one of the allowed values."""
        valid_roles = ["HR", "Tech", "Product", "Compliance"]
        if self.agent_role not in valid_roles:
            raise ValueError(
                f"Invalid agent_role '{self.agent_role}'. Must be one of: {valid_roles}"
            )
        return self

    @model_validator(mode='after')
    def validate_category_scores_unique(self) -> 'AgentReview':
        """Ensure each category is scored exactly once."""
        category_names = [cs.category_name for cs in self.category_scores]
        if len(category_names) != len(set(category_names)):
            duplicates = [name for name in category_names if category_names.count(name) > 1]
            raise ValueError(
                f"Duplicate category scores found: {set(duplicates)}. "
                f"Each category must be scored exactly once."
            )
        return self

    @model_validator(mode='after')
    def validate_rubric_category_coverage(self) -> 'AgentReview':
        """Ensure category_scores cover all expected rubric categories exactly once, with no extras."""
        if self.expected_rubric_categories is None:
            return self

        expected_set = set(self.expected_rubric_categories)
        actual_set = {cs.category_name for cs in self.category_scores}

        missing_categories = expected_set - actual_set
        unexpected_categories = actual_set - expected_set

        if missing_categories or unexpected_categories:
            error_parts = []
            if missing_categories:
                error_parts.append(f"Missing categories: {sorted(missing_categories)}")
            if unexpected_categories:
                error_parts.append(f"Unexpected categories: {sorted(unexpected_categories)}")

            raise ValueError(
                f"Rubric category coverage validation failed. {'; '.join(error_parts)}. "
                f"Expected categories: {sorted(expected_set)}"
            )

        return self

    def get_score_for_category(self, category_name: str) -> Optional[CategoryScore]:
        """Retrieve the score for a specific category.

        Args:
            category_name: The category name to search for

        Returns:
            The matching CategoryScore if found, None otherwise
        """
        for category_score in self.category_scores:
            if category_score.category_name == category_name:
                return category_score
        return None

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "agent_role": "Tech",
                    "category_scores": [
                        {
                            "category_name": "Agent Orchestration Depth",
                            "score": 4,
                            "evidence": [
                                {
                                    "resume_text": "Designed multi-agent orchestration system using LangGraph",
                                    "line_reference": "Experience - 3rd bullet",
                                    "interpretation": "Practical LangGraph experience"
                                }
                            ],
                            "gaps": ["No 5+ agent systems mentioned"],
                            "confidence": "high"
                        },
                        {
                            "category_name": "LLM Integration Expertise",
                            "score": 5,
                            "evidence": [
                                {
                                    "resume_text": "Built production LLM pipeline handling 10M+ requests/month with GPT-4 and Claude",
                                    "line_reference": "Experience - 1st bullet",
                                    "interpretation": "Production-scale LLM experience"
                                }
                            ],
                            "gaps": [],
                            "confidence": "high"
                        }
                    ],
                    "overall_assessment": "Strong technical candidate with deep LLM and agent orchestration experience. Demonstrated production-scale system design and hands-on implementation with modern frameworks. Primary gap is limited evidence of managing 5+ agent systems, though the 4-agent system shows solid foundation. Technical depth is exceptional, particularly in LLM integration and prompt engineering.",
                    "top_strengths": [
                        "Production-scale LLM experience (10M+ requests/month) with multiple providers (Evidence: Experience - 1st bullet)",
                        "Hands-on LangGraph implementation coordinating 4 specialized agents (Evidence: Experience - 3rd bullet)",
                        "Advanced prompt engineering with documented performance improvements (Evidence: Projects section)",
                        "Strong Python/FastAPI background with 5+ years experience (Evidence: Skills section)"
                    ],
                    "top_risks": [
                        "No evidence of 5+ agent systems - may need time to scale to more complex orchestration",
                        "Limited HR/hiring domain knowledge - will need onboarding on domain-specific workflows",
                        "No mention of testing strategies for non-deterministic LLM systems"
                    ],
                    "follow_up_questions": [
                        "Walk me through how you designed the state management for your 4-agent LangGraph system",
                        "What strategies did you use to handle failures and retries in your multi-agent orchestration?",
                        "How did you test and validate the behavior of non-deterministic LLM outputs?",
                        "Have you worked with hierarchical agent structures or only peer-to-peer coordination?"
                    ]
                }
            ]
        }
    )
