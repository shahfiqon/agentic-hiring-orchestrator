"""Rubric models for structured evaluation criteria.

This module defines Pydantic models for creating and managing evaluation rubrics:
- ScoringCriteria: Individual score level definitions (0-5 scale)
- RubricCategory: Weighted evaluation categories with scoring criteria
- Rubric: Complete evaluation framework with validation
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator, ConfigDict


class ScoringCriteria(BaseModel):
    """Defines what a specific score level (0-5) means for a rubric category.

    Each scoring criteria provides clear indicators and descriptions to ensure
    consistent evaluation across different reviewers.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    score_value: int = Field(
        ge=0,
        le=5,
        description="Score level from 0 (no evidence) to 5 (exceptional)"
    )
    description: str = Field(
        min_length=1,
        description="Clear description of what this score level represents"
    )
    indicators: List[str] = Field(
        min_length=1,
        description="Observable behaviors or evidence that indicate this score level"
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "score_value": 0,
                    "description": "No evidence of agent orchestration experience",
                    "indicators": [
                        "No mention of multi-agent systems",
                        "No experience with agent frameworks",
                        "No understanding of agent coordination patterns"
                    ]
                },
                {
                    "score_value": 3,
                    "description": "Solid understanding with practical implementation",
                    "indicators": [
                        "Implemented basic multi-agent workflows",
                        "Used frameworks like LangGraph or CrewAI",
                        "Coordinated 2-3 specialized agents",
                        "Handled agent state management"
                    ]
                },
                {
                    "score_value": 5,
                    "description": "Expert-level orchestration with complex systems",
                    "indicators": [
                        "Designed sophisticated multi-agent architectures",
                        "Handled 5+ specialized agents with dynamic routing",
                        "Implemented advanced coordination patterns",
                        "Optimized agent communication and state sharing",
                        "Published or presented on agent orchestration"
                    ]
                }
            ]
        }
    )


class RubricCategory(BaseModel):
    """A weighted evaluation category with scoring criteria.

    Each category represents a distinct aspect of candidate evaluation
    (e.g., technical skills, domain knowledge) with clear scoring levels.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    name: str = Field(
        min_length=1,
        description="Category name (e.g., 'Agent Orchestration Depth')"
    )
    description: str = Field(
        min_length=1,
        description="What this category evaluates and why it matters"
    )
    weight: float = Field(
        ge=0.0,
        le=1.0,
        description="Category weight in overall scoring (0.0-1.0, all weights must sum to 1.0)"
    )
    is_must_have: bool = Field(
        description="Whether this represents a required qualification (critical gap if low score)"
    )
    scoring_criteria: List[ScoringCriteria] = Field(
        min_length=3,
        description="Score level definitions, minimum of 3 levels (typically 0, 3, 5)"
    )

    @model_validator(mode='after')
    def validate_scoring_criteria(self) -> 'RubricCategory':
        """Ensure at least 3 scoring criteria levels are defined."""
        if len(self.scoring_criteria) < 3:
            raise ValueError(
                f"Category '{self.name}' must have at least 3 scoring criteria levels "
                f"(e.g., 0, 3, 5). Found {len(self.scoring_criteria)} levels."
            )

        # Verify score values are unique
        score_values = [sc.score_value for sc in self.scoring_criteria]
        if len(score_values) != len(set(score_values)):
            raise ValueError(
                f"Category '{self.name}' has duplicate score values. "
                f"Each score level must be unique."
            )

        return self

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "Agent Orchestration Depth",
                    "description": "Evaluates experience designing and implementing multi-agent systems with coordination, state management, and dynamic routing",
                    "weight": 0.25,
                    "is_must_have": True,
                    "scoring_criteria": [
                        {
                            "score_value": 0,
                            "description": "No evidence of agent orchestration",
                            "indicators": ["No multi-agent experience"]
                        },
                        {
                            "score_value": 3,
                            "description": "Solid practical implementation",
                            "indicators": ["Used LangGraph or similar", "Coordinated 2-3 agents"]
                        },
                        {
                            "score_value": 5,
                            "description": "Expert-level orchestration",
                            "indicators": ["Complex architectures", "5+ agents", "Published work"]
                        }
                    ]
                }
            ]
        }
    )


class Rubric(BaseModel):
    """Complete evaluation framework for a role.

    Defines weighted categories with scoring criteria, ensuring comprehensive
    and consistent candidate evaluation. Validates that weights sum to 1.0
    and at least one must-have category exists.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    role_title: str = Field(
        min_length=1,
        description="Job title being evaluated (e.g., 'Senior AI Engineer - Agentic Systems')"
    )
    categories: List[RubricCategory] = Field(
        min_length=1,
        description="Evaluation categories (typically 5 categories covering key competencies)"
    )
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when this rubric was created"
    )

    @model_validator(mode='after')
    def validate_weights_sum(self) -> 'Rubric':
        """Ensure category weights sum to 1.0 (within tolerance)."""
        total_weight = sum(category.weight for category in self.categories)
        tolerance = 0.01

        if abs(total_weight - 1.0) > tolerance:
            raise ValueError(
                f"Category weights must sum to 1.0 (±{tolerance}). "
                f"Current sum: {total_weight:.4f}. "
                f"Weights: {[(c.name, c.weight) for c in self.categories]}"
            )

        return self

    @model_validator(mode='after')
    def validate_must_have_exists(self) -> 'Rubric':
        """Ensure at least one must-have category is defined."""
        must_haves = [c for c in self.categories if c.is_must_have]

        if not must_haves:
            raise ValueError(
                "At least one category must be marked as 'is_must_have' to identify "
                "critical requirements for the role."
            )

        return self

    def get_category_by_name(self, name: str) -> Optional[RubricCategory]:
        """Retrieve a category by its name.

        Args:
            name: The category name to search for

        Returns:
            The matching RubricCategory if found, None otherwise
        """
        for category in self.categories:
            if category.name == name:
                return category
        return None

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "role_title": "Senior AI Engineer - Agentic Systems",
                    "categories": [
                        {
                            "name": "Agent Orchestration Depth",
                            "description": "Multi-agent system design and coordination",
                            "weight": 0.25,
                            "is_must_have": True,
                            "scoring_criteria": [
                                {"score_value": 0, "description": "No experience", "indicators": ["None"]},
                                {"score_value": 3, "description": "Solid experience", "indicators": ["2-3 agents"]},
                                {"score_value": 5, "description": "Expert level", "indicators": ["5+ agents"]}
                            ]
                        },
                        {
                            "name": "LLM Integration Expertise",
                            "description": "Working with LLM APIs and prompt engineering",
                            "weight": 0.20,
                            "is_must_have": True,
                            "scoring_criteria": [
                                {"score_value": 0, "description": "No experience", "indicators": ["None"]},
                                {"score_value": 3, "description": "Production usage", "indicators": ["OpenAI API"]},
                                {"score_value": 5, "description": "Advanced techniques", "indicators": ["Custom fine-tuning"]}
                            ]
                        },
                        {
                            "name": "Python/FastAPI Proficiency",
                            "description": "Backend development skills",
                            "weight": 0.20,
                            "is_must_have": False,
                            "scoring_criteria": [
                                {"score_value": 0, "description": "No experience", "indicators": ["None"]},
                                {"score_value": 3, "description": "Competent", "indicators": ["Built APIs"]},
                                {"score_value": 5, "description": "Expert", "indicators": ["Complex systems"]}
                            ]
                        },
                        {
                            "name": "System Design & Architecture",
                            "description": "Designing scalable distributed systems",
                            "weight": 0.20,
                            "is_must_have": False,
                            "scoring_criteria": [
                                {"score_value": 0, "description": "No experience", "indicators": ["None"]},
                                {"score_value": 3, "description": "Good designs", "indicators": ["Microservices"]},
                                {"score_value": 5, "description": "Exceptional", "indicators": ["Large scale"]}
                            ]
                        },
                        {
                            "name": "Domain Knowledge (Hiring/HR Tech)",
                            "description": "Understanding of hiring workflows",
                            "weight": 0.15,
                            "is_must_have": False,
                            "scoring_criteria": [
                                {"score_value": 0, "description": "No experience", "indicators": ["None"]},
                                {"score_value": 3, "description": "Some exposure", "indicators": ["Built HR tools"]},
                                {"score_value": 5, "description": "Deep expertise", "indicators": ["HR domain expert"]}
                            ]
                        }
                    ],
                    "generated_at": "2025-01-15T10:30:00"
                }
            ]
        }
    )
