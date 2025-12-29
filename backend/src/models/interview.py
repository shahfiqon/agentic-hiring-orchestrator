"""Interview plan models for structured candidate evaluation.

This module defines Pydantic models for interview generation:
- InterviewQuestion: Individual question with guidance for interviewers
- InterviewPlan: Complete interview structure organized by interviewer role
"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator, ConfigDict


class InterviewQuestion(BaseModel):
    """A single interview question with interviewer guidance.

    Provides actionable guidance for interviewers including what to
    listen for, red flags, and follow-up prompts.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    question: str = Field(
        min_length=1,
        description="The interview question to ask the candidate"
    )
    category: str = Field(
        min_length=1,
        description="Rubric category this question probes (e.g., 'Agent Orchestration Depth')"
    )
    interviewer_role: Literal["HR", "Tech", "Product", "Compliance"] = Field(
        description="Who should ask this question: 'HR', 'Tech', 'Product', or 'Compliance'"
    )
    what_to_listen_for: List[str] = Field(
        min_length=1,
        description="Key points, concepts, or evidence to assess in the candidate's response"
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Warning signs or concerning responses that indicate lack of qualification"
    )
    follow_up_prompts: Optional[List[str]] = Field(
        default=None,
        description="Additional probing questions to dig deeper based on initial response"
    )

    @model_validator(mode='after')
    def validate_question_not_empty(self) -> 'InterviewQuestion':
        """Ensure question is meaningful."""
        if not self.question.strip():
            raise ValueError("Question text cannot be empty or whitespace only.")
        return self

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "question": "Walk me through your LangGraph implementation that coordinated 4 specialized agents. How did you design the state management and handle failures?",
                    "category": "Agent Orchestration Depth",
                    "interviewer_role": "Tech",
                    "what_to_listen_for": [
                        "Specific LangGraph concepts: StateGraph, nodes, edges, checkpointing",
                        "Clear explanation of state schema and how it flowed between agents",
                        "Concrete failure handling strategies (retries, fallbacks, circuit breakers)",
                        "Understanding of agent coordination patterns (sequential, parallel, conditional)",
                        "Evidence of production experience (monitoring, debugging, iteration)"
                    ],
                    "red_flags": [
                        "Vague or generic answers without LangGraph-specific details",
                        "No mention of state management strategy",
                        "No concrete failure handling approach",
                        "Cannot explain how agents communicated or shared context",
                        "Seems to confuse LangGraph with simpler chain-based approaches"
                    ],
                    "follow_up_prompts": [
                        "What challenges did you face with state management and how did you solve them?",
                        "How did you test and validate the behavior of your multi-agent system?",
                        "If one agent failed, how did that affect the overall workflow?",
                        "How did you handle cases where agents disagreed or produced conflicting outputs?"
                    ]
                }
            ]
        }
    )


class InterviewPlan(BaseModel):
    """Complete interview structure organized by interviewer role.

    Distributes questions across multiple interviewers and identifies
    priority areas requiring extra attention.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    questions_by_interviewer: Dict[str, List[InterviewQuestion]] = Field(
        description="Questions grouped by interviewer role (e.g., {'Tech': [...], 'HR': [...]})"
    )
    time_estimate_minutes: Optional[int] = Field(
        default=None,
        gt=0,
        description="Estimated total interview duration in minutes (optional)"
    )
    priority_areas: List[str] = Field(
        min_length=1,
        description="Rubric categories needing most attention (gaps, disagreements, must-haves)"
    )

    @model_validator(mode='after')
    def validate_interviewer_roles(self) -> 'InterviewPlan':
        """Ensure all interviewer roles are valid and questions match their assigned role."""
        valid_roles = {"HR", "Tech", "Product", "Compliance"}
        invalid_roles = set(self.questions_by_interviewer.keys()) - valid_roles

        if invalid_roles:
            raise ValueError(
                f"Invalid interviewer roles: {invalid_roles}. "
                f"Valid roles: {valid_roles}"
            )

        # Ensure at least one interviewer has questions
        if not any(self.questions_by_interviewer.values()):
            raise ValueError(
                "Interview plan must include at least one question for at least one interviewer."
            )

        # Validate that each question's interviewer_role matches the dict key
        for role, questions in self.questions_by_interviewer.items():
            for question in questions:
                if question.interviewer_role != role:
                    raise ValueError(
                        f"Question interviewer_role mismatch: question has role '{question.interviewer_role}' "
                        f"but is assigned to '{role}' interviewer. Question: '{question.question[:50]}...'"
                    )
                if question.interviewer_role not in valid_roles:
                    raise ValueError(
                        f"Question has invalid interviewer_role '{question.interviewer_role}'. "
                        f"Valid roles: {valid_roles}"
                    )

        return self

    @model_validator(mode='after')
    def validate_priority_areas_not_empty(self) -> 'InterviewPlan':
        """Ensure priority areas are specified."""
        if not self.priority_areas:
            raise ValueError(
                "Interview plan must specify at least one priority area to focus on."
            )
        return self

    @model_validator(mode='after')
    def validate_question_distribution(self) -> 'InterviewPlan':
        """Warn if questions are heavily skewed to one interviewer."""
        if not self.questions_by_interviewer:
            return self

        question_counts = {
            role: len(questions)
            for role, questions in self.questions_by_interviewer.items()
            if questions
        }

        if not question_counts:
            return self

        # Check if one interviewer has more than 70% of all questions
        total_questions = sum(question_counts.values())
        if total_questions > 0:
            max_count = max(question_counts.values())
            if max_count / total_questions > 0.7:
                # This is a soft warning - we allow it but note the imbalance
                # In a production system, you might log this or add it to metadata
                pass

        return self

    def get_questions_for_role(self, role: str) -> List[InterviewQuestion]:
        """Retrieve all questions for a specific interviewer role.

        Args:
            role: The interviewer role (e.g., 'Tech', 'HR')

        Returns:
            List of interview questions for that role, empty list if none
        """
        return self.questions_by_interviewer.get(role, [])

    def total_questions(self) -> int:
        """Count total number of questions across all interviewers.

        Returns:
            Total question count
        """
        return sum(
            len(questions)
            for questions in self.questions_by_interviewer.values()
        )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "questions_by_interviewer": {
                        "Tech": [
                            {
                                "question": "Walk me through your LangGraph implementation with 4 agents. How did you handle state management?",
                                "category": "Agent Orchestration Depth",
                                "interviewer_role": "Tech",
                                "what_to_listen_for": [
                                    "LangGraph StateGraph concepts",
                                    "State schema design",
                                    "Failure handling strategies"
                                ],
                                "red_flags": [
                                    "Vague answers without specifics",
                                    "No state management strategy"
                                ],
                                "follow_up_prompts": [
                                    "What challenges did you face?",
                                    "How did you test the system?"
                                ]
                            },
                            {
                                "question": "How did you approach testing non-deterministic LLM outputs in production?",
                                "category": "LLM Integration Expertise",
                                "interviewer_role": "Tech",
                                "what_to_listen_for": [
                                    "Testing strategies for LLM systems",
                                    "Quality metrics and evaluation",
                                    "Handling variability"
                                ],
                                "red_flags": [
                                    "No testing strategy mentioned",
                                    "Only manual testing"
                                ],
                                "follow_up_prompts": [
                                    "What metrics did you track?",
                                    "How did you handle regressions?"
                                ]
                            }
                        ],
                        "HR": [
                            {
                                "question": "Tell me about a time you had to quickly learn a new business domain. How did you approach it?",
                                "category": "Domain Knowledge (Hiring/HR Tech)",
                                "interviewer_role": "HR",
                                "what_to_listen_for": [
                                    "Learning strategies and resourcefulness",
                                    "How they engage with domain experts",
                                    "Speed of domain knowledge acquisition"
                                ],
                                "red_flags": [
                                    "Resistance to learning new domains",
                                    "No concrete examples"
                                ],
                                "follow_up_prompts": [
                                    "How long did it take to become productive?",
                                    "What would you do differently next time?"
                                ]
                            }
                        ],
                        "Product": [
                            {
                                "question": "Given that you'll be building hiring automation tools, how would you balance automation efficiency with candidate experience?",
                                "category": "Domain Knowledge (Hiring/HR Tech)",
                                "interviewer_role": "Product",
                                "what_to_listen_for": [
                                    "Product sense and user empathy",
                                    "Understanding of hiring stakeholders",
                                    "Balance of technical and business needs"
                                ],
                                "red_flags": [
                                    "Only focuses on technical solution",
                                    "No mention of candidate or recruiter experience"
                                ],
                                "follow_up_prompts": [
                                    "How would you measure success?",
                                    "What tradeoffs would you consider?"
                                ]
                            }
                        ]
                    },
                    "time_estimate_minutes": 90,
                    "priority_areas": [
                        "Agent Orchestration Depth - validate 5+ agent experience gap",
                        "Domain Knowledge (Hiring/HR Tech) - resolve agent disagreement (HR: 2, Tech: 4)",
                        "Testing strategies for non-deterministic systems - identified gap by Tech agent"
                    ]
                }
            ]
        }
    )
