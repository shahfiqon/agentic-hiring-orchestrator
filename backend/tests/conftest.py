"""
Pytest fixtures and test utilities for the hiring orchestrator test suite.

This module provides reusable fixtures for creating valid test data objects,
mocking LLM responses, and helper functions for test assertions.
"""

import pytest
from datetime import datetime
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock

from src.models.rubric import Rubric, RubricCategory, ScoringCriteria
from src.models.review import AgentReview, CategoryScore, Evidence
from src.models.packet import DecisionPacket, Disagreement
from src.models.interview import InterviewPlan, InterviewQuestion
from src.models.memory import WorkingMemory, KeyObservation, CrossReference


# ============================================================================
# Sample Text Data Fixtures
# ============================================================================

@pytest.fixture
def sample_job_description() -> str:
    """Sample job description for a Senior AI Engineer position."""
    return """
    Senior AI Engineer - Agentic Systems

    We're seeking a Senior AI Engineer to build production agentic workflows using LangGraph,
    Claude, and modern Python frameworks. You'll design multi-agent orchestration systems,
    implement evaluation frameworks, and ensure compliance with AI safety standards.

    Requirements:
    - 5+ years Python experience with async/await patterns
    - Deep knowledge of LLM agent frameworks (LangGraph, LangChain, CrewAI)
    - Production experience with structured outputs and prompt engineering
    - Strong understanding of AI safety, bias mitigation, and PII handling
    - Experience with FastAPI, Pydantic, and async workflows

    Nice to have:
    - Contributions to open-source AI projects
    - Experience with LLM observability tools (LangSmith, Weights & Biases)
    - Knowledge of graph-based state machines
    """


@pytest.fixture
def sample_resume_strong() -> str:
    """Sample resume for a strong candidate."""
    return """
    Jane Smith - Senior AI Engineer

    Experience:
    - Built production agentic workflows at TechCorp using LangGraph and Claude (2022-2024)
    - Designed multi-agent orchestration systems processing 10K+ evaluations/day
    - Implemented comprehensive AI safety framework with PII detection and bias mitigation
    - Led team of 4 engineers building FastAPI-based LLM evaluation platform

    Technical Skills:
    - Languages: Python (expert), TypeScript (proficient)
    - Frameworks: LangGraph, LangChain, FastAPI, Pydantic
    - LLM Tools: Claude API, OpenAI API, LangSmith observability
    - Async patterns, structured outputs, prompt engineering

    Education:
    - MS Computer Science, Stanford University (2018)
    - BS Computer Science, MIT (2016)

    Open Source:
    - Core contributor to LangGraph (50+ merged PRs)
    - Maintainer of popular prompt engineering library (2K+ stars)
    """


@pytest.fixture
def sample_resume_moderate() -> str:
    """Sample resume for a moderate candidate with some gaps."""
    return """
    John Doe - Software Engineer

    Experience:
    - Software Engineer at StartupCo building chatbot features (2021-2024)
    - Used OpenAI API for basic RAG applications
    - Worked with FastAPI and Python for backend development
    - Some experience with async patterns and API design

    Technical Skills:
    - Languages: Python (intermediate), JavaScript (proficient)
    - Frameworks: FastAPI, Flask, React
    - Basic knowledge of LLM APIs and prompt engineering

    Education:
    - BS Computer Science, State University (2020)

    Projects:
    - Built personal chatbot using LangChain
    - Experimented with agent frameworks in side projects
    """


@pytest.fixture
def sample_company_context() -> str:
    """Sample company context for rubric generation."""
    return """
    We're a Series B startup building AI-powered hiring tools. Our tech stack
    emphasizes production reliability, AI safety, and scalable agent orchestration.
    We value candidates who can build robust systems while maintaining high ethical
    standards around bias and privacy.
    """


# ============================================================================
# Rubric Fixtures
# ============================================================================

@pytest.fixture
def sample_scoring_criteria() -> List[ScoringCriteria]:
    """Sample scoring criteria for a rubric category."""
    return [
        ScoringCriteria(score_value=0, description="No evidence of skill", indicators=["No experience mentioned"]),
        ScoringCriteria(score_value=1, description="Basic awareness, no practical experience", indicators=["Theoretical knowledge only"]),
        ScoringCriteria(score_value=2, description="Some practical experience with guidance", indicators=["Guided projects", "Limited scope"]),
        ScoringCriteria(score_value=3, description="Solid experience, can work independently", indicators=["Independent work", "Production experience"]),
        ScoringCriteria(score_value=4, description="Expert level, can mentor others", indicators=["Mentorship", "Advanced implementations"]),
        ScoringCriteria(score_value=5, description="Industry-leading expertise, innovator", indicators=["Published work", "Open source contributions"]),
    ]


@pytest.fixture
def sample_rubric_category(sample_scoring_criteria) -> RubricCategory:
    """Sample rubric category for LLM agent experience."""
    return RubricCategory(
        name="LLM Agent Frameworks",
        description="Experience with agentic orchestration frameworks like LangGraph",
        weight=0.3,
        is_must_have=True,
        scoring_criteria=sample_scoring_criteria,
    )


@pytest.fixture
def sample_rubric(sample_scoring_criteria) -> Rubric:
    """Sample complete rubric with multiple categories."""
    return Rubric(
        role_title="Senior AI Engineer - Agentic Systems",
        categories=[
            RubricCategory(
                name="LLM Agent Frameworks",
                description="Experience with LangGraph, LangChain, or similar frameworks",
                weight=0.3,
                is_must_have=True,
                scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Python & Async Patterns",
                description="Advanced Python with async/await experience",
                weight=0.25,
                is_must_have=True,
                scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="AI Safety & Compliance",
                description="Understanding of bias mitigation, PII handling, AI ethics",
                weight=0.25,
                is_must_have=True,
                scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Production Experience",
                description="Scaled production systems with monitoring and observability",
                weight=0.2,
                is_must_have=False,
                scoring_criteria=sample_scoring_criteria,
            ),
        ]
    )


# ============================================================================
# Review Fixtures
# ============================================================================

@pytest.fixture
def sample_evidence() -> Evidence:
    """Sample evidence for a category score."""
    return Evidence(
        resume_text="Candidate built production agentic workflows at TechCorp using LangGraph",
        line_reference="Experience section, 2nd bullet",
        interpretation="Demonstrates hands-on experience with target framework",
    )


@pytest.fixture
def sample_category_score(sample_evidence) -> CategoryScore:
    """Sample category score with evidence."""
    return CategoryScore(
        category_name="LLM Agent Frameworks",
        score=4,
        evidence=[sample_evidence],
        confidence="high",
    )


@pytest.fixture
def sample_hr_review(sample_rubric) -> AgentReview:
    """Sample HR agent review with full category coverage."""
    return AgentReview(
        agent_role="HR",
        category_scores=[
            CategoryScore(
                category_name="LLM Agent Frameworks",
                score=4,
                evidence=[
                    Evidence(
                        resume_text="Built production LangGraph workflows at TechCorp",
                        line_reference="Experience section, 1st role",
                        interpretation="Strong hands-on experience with target framework",
                    )
                ],
                confidence="high",
            ),
            CategoryScore(
                category_name="Python & Async Patterns",
                score=4,
                evidence=[
                    Evidence(
                        resume_text="Expert Python experience with async/await patterns",
                        line_reference="Skills section",
                        interpretation="Meets technical bar for role",
                    )
                ],
                confidence="high",
            ),
            CategoryScore(
                category_name="AI Safety & Compliance",
                score=4,
                evidence=[
                    Evidence(
                        resume_text="Implemented AI safety framework with PII detection",
                        line_reference="Experience section, 3rd bullet",
                        interpretation="Strong compliance awareness",
                    )
                ],
                confidence="medium",
            ),
            CategoryScore(
                category_name="Production Experience",
                score=4,
                evidence=[
                    Evidence(
                        resume_text="Scaled systems processing 10K+ evaluations/day",
                        line_reference="Experience section, 2nd bullet",
                        interpretation="Proven production experience",
                    )
                ],
                confidence="high",
            ),
        ],
        overall_assessment="Strong candidate with proven production experience and solid technical skills across all key areas.",
        top_strengths=[
            "Production-scale LangGraph implementation",
            "Strong AI safety and compliance awareness",
            "Expert Python and async programming skills"
        ],
        top_risks=[
            "Limited mention of team leadership",
            "No specific hiring domain experience",
            "Unclear depth of open source contributions"
        ],
        follow_up_questions=[
            "Can you describe your experience leading technical teams?",
            "What is your familiarity with hiring workflows and HR technology?"
        ],
        expected_rubric_categories=["LLM Agent Frameworks", "Python & Async Patterns", "AI Safety & Compliance", "Production Experience"],
    )


@pytest.fixture
def sample_tech_review(sample_rubric) -> AgentReview:
    """Sample tech agent review with different scores."""
    return AgentReview(
        agent_role="Tech",
        category_scores=[
            CategoryScore(
                category_name="LLM Agent Frameworks",
                score=5,
                evidence=[
                    Evidence(
                        resume_text="Core contributor to LangGraph with 50+ merged PRs",
                        line_reference="Open Source section",
                        interpretation="Industry-leading expertise and innovation",
                    )
                ],
                confidence="high",
            ),
            CategoryScore(
                category_name="Python & Async Patterns",
                score=4,
                evidence=[
                    Evidence(
                        resume_text="Advanced async patterns in production systems",
                        line_reference="Experience section, current role",
                        interpretation="Expert-level technical skills",
                    )
                ],
                confidence="high",
            ),
            CategoryScore(
                category_name="AI Safety & Compliance",
                score=3,
                evidence=[
                    Evidence(
                        resume_text="Basic PII handling implementation",
                        line_reference="Experience section, 3rd bullet",
                        interpretation="Understands concepts but limited depth",
                    )
                ],
                confidence="medium",
            ),
            CategoryScore(
                category_name="Production Experience",
                score=5,
                evidence=[
                    Evidence(
                        resume_text="Built highly scalable evaluation platform",
                        line_reference="Experience section, current role - 1st bullet",
                        interpretation="Exceptional production engineering",
                    )
                ],
                confidence="high",
            ),
        ],
        overall_assessment="Exceptional technical candidate with deep expertise in LLM frameworks and production systems. Minor gaps in AI safety depth.",
        top_strengths=[
            "Industry-leading LangGraph expertise with 50+ open source contributions",
            "Exceptional production engineering and scalability experience",
            "Expert-level Python and async programming"
        ],
        top_risks=[
            "Limited depth in AI safety and bias mitigation",
            "May need guidance on compliance requirements",
            "Unclear experience with team mentorship"
        ],
        follow_up_questions=[
            "How have you approached AI safety and bias mitigation in your LLM systems?",
            "Can you describe your experience mentoring junior engineers?"
        ],
        expected_rubric_categories=["LLM Agent Frameworks", "Python & Async Patterns", "AI Safety & Compliance", "Production Experience"],
    )


# ============================================================================
# Working Memory Fixtures
# ============================================================================

@pytest.fixture
def sample_key_observation() -> KeyObservation:
    """Sample key observation from working memory."""
    return KeyObservation(
        category="LLM Agent Frameworks",
        observation="Candidate is core LangGraph contributor with deep framework knowledge",
        evidence_location="Open Source section",
        strength_or_risk="strength",
    )


@pytest.fixture
def sample_cross_reference() -> CrossReference:
    """Sample cross-reference linking multiple evidence points."""
    return CrossReference(
        claim="Strong production agentic systems experience",
        claim_location="Skills section",
        supporting_evidence=["Built LangGraph workflows at TechCorp", "Core LangGraph contributor"],
        contradictory_evidence=[],
        assessment="well-supported",
    )


@pytest.fixture
def sample_working_memory() -> WorkingMemory:
    """Sample working memory for HR agent."""
    return WorkingMemory(
        agent_role="HR",
        key_observations=[
            KeyObservation(
                category="LLM Agent Frameworks",
                observation="Core LangGraph contributor with 50+ merged PRs",
                evidence_location="Open Source section",
                strength_or_risk="strength",
            ),
            KeyObservation(
                category="Python & Async Patterns",
                observation="Expert Python with production async experience",
                evidence_location="Skills section",
                strength_or_risk="strength",
            ),
            KeyObservation(
                category="AI Safety & Compliance",
                observation="Implemented PII detection and bias mitigation framework",
                evidence_location="Experience section, 3rd bullet",
                strength_or_risk="strength",
            ),
            KeyObservation(
                category="Production Experience",
                observation="Scaled systems to 10K+ evaluations/day",
                evidence_location="Experience section, 2nd bullet",
                strength_or_risk="strength",
            ),
            KeyObservation(
                category="LLM Agent Frameworks",
                observation="No mention of alternative frameworks like CrewAI",
                evidence_location="N/A - missing from resume",
                strength_or_risk="risk",
            ),
        ],
        cross_references=[
            CrossReference(
                claim="Strong LangGraph expertise",
                claim_location="Skills section",
                supporting_evidence=["TechCorp production work", "Open source contributions"],
                contradictory_evidence=[],
                assessment="well-supported",
            ),
        ],
        ambiguities=[
            "Depth of AI safety knowledge unclear - need to probe bias mitigation strategies"
        ],
    )


# ============================================================================
# Decision Packet Fixtures
# ============================================================================

@pytest.fixture
def sample_disagreement() -> Disagreement:
    """Sample disagreement between agents."""
    return Disagreement(
        category_name="AI Safety & Compliance",
        agent_scores={"HR": 4, "Tech": 3},
        reason="HR agent focused on comprehensive framework implementation, while Tech agent noted limited depth in bias mitigation",
        resolution_approach="Probe bias mitigation strategies in interview to clarify depth of knowledge",
    )


@pytest.fixture
def sample_decision_packet() -> DecisionPacket:
    """Sample decision packet for hire recommendation."""
    return DecisionPacket(
        role_title="Senior AI Engineer - Agentic Systems",
        overall_fit_score=4.1,
        recommendation="Lean hire",
        confidence="high",
        top_strengths=[
            "Industry-leading LangGraph expertise with 50+ open source contributions",
            "Exceptional production engineering and scalability experience",
            "Expert-level Python and async programming"
        ],
        top_risks=[
            "Limited depth in AI safety and bias mitigation",
            "May need guidance on compliance requirements",
            "Unclear experience with team mentorship"
        ],
        must_have_gaps=[],
        disagreements=[
            Disagreement(
                category_name="AI Safety & Compliance",
                agent_scores={"HR": 4, "Tech": 3},
                reason="HR agent focused on comprehensive framework implementation, while Tech agent noted limited depth in bias mitigation",
                resolution_approach="Probe bias mitigation strategies in interview to clarify depth of knowledge",
            ),
        ],
    )


# ============================================================================
# Interview Plan Fixtures
# ============================================================================

@pytest.fixture
def sample_interview_question() -> InterviewQuestion:
    """Sample interview question."""
    return InterviewQuestion(
        question="Can you walk me through your approach to bias mitigation in LLM systems?",
        category="AI Safety & Compliance",
        interviewer_role="Tech",
        what_to_listen_for=[
            "Specific bias mitigation techniques",
            "Understanding of fairness metrics",
            "Production experience with bias detection"
        ],
        red_flags=[
            "Only theoretical knowledge",
            "No concrete examples"
        ],
        follow_up_prompts=[
            "Can you describe a specific instance where you detected and mitigated bias?",
            "What metrics did you use to measure fairness?"
        ],
    )


@pytest.fixture
def sample_interview_plan() -> InterviewPlan:
    """Sample interview plan with questions."""
    return InterviewPlan(
        questions_by_interviewer={
            "Tech": [
                InterviewQuestion(
                    question="Describe your AI safety framework implementation - what bias mitigation techniques did you use?",
                    category="AI Safety & Compliance",
                    interviewer_role="Tech",
                    what_to_listen_for=[
                        "Specific bias mitigation techniques",
                        "Understanding of fairness metrics"
                    ],
                    red_flags=["Only theoretical knowledge"],
                ),
            ],
            "Compliance": [
                InterviewQuestion(
                    question="How do you handle PII detection in production agentic workflows?",
                    category="AI Safety & Compliance",
                    interviewer_role="Compliance",
                    what_to_listen_for=[
                        "PII detection strategies",
                        "Compliance framework knowledge"
                    ],
                    red_flags=["No concrete PII handling experience"],
                ),
            ],
        },
        priority_areas=[
            "AI Safety & Compliance depth",
            "Bias mitigation strategies",
        ],
    )


# ============================================================================
# Mock LLM Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_rubric(sample_rubric):
    """Mock LLM that returns a structured rubric."""
    mock = Mock()
    mock.invoke = Mock(return_value=sample_rubric)
    return mock


@pytest.fixture
def mock_llm_review(sample_hr_review):
    """Mock LLM that returns a structured agent review."""
    mock = Mock()
    mock.invoke = Mock(return_value=sample_hr_review)
    return mock


@pytest.fixture
def mock_llm_memory(sample_working_memory):
    """Mock LLM that returns structured working memory."""
    mock = Mock()
    mock.invoke = Mock(return_value=sample_working_memory)
    return mock


@pytest.fixture
def mock_llm_decision_packet(sample_decision_packet):
    """Mock LLM that returns a structured decision packet."""
    mock = Mock()
    mock.invoke = Mock(return_value=sample_decision_packet)
    return mock


@pytest.fixture
def mock_llm_interview_plan(sample_interview_plan):
    """Mock LLM that returns a structured interview plan."""
    mock = Mock()
    mock.invoke = Mock(return_value=sample_interview_plan)
    return mock


# ============================================================================
# State Fixtures
# ============================================================================

@pytest.fixture
def sample_state_initial(sample_job_description, sample_resume_strong, sample_company_context) -> Dict[str, Any]:
    """Initial state with job description and resume."""
    return {
        "job_description": sample_job_description,
        "resume": sample_resume_strong,
        "company_context": sample_company_context,
        "rubric": None,
        "panel_reviews": [],
        "agent_working_memory": {},
        "decision_packet": None,
        "interview_plan": None,
        "disagreements": [],
        "metadata": {
            "workflow_start_time": datetime.now().isoformat(),
            "node_execution_order": [],
        },
    }


@pytest.fixture
def sample_state_with_rubric(sample_state_initial, sample_rubric) -> Dict[str, Any]:
    """State after orchestrator node execution."""
    state = sample_state_initial.copy()
    state["rubric"] = sample_rubric
    state["metadata"]["node_execution_order"].append("orchestrator")
    return state


@pytest.fixture
def sample_state_with_reviews(sample_state_with_rubric, sample_hr_review, sample_tech_review, sample_working_memory) -> Dict[str, Any]:
    """State after panel agent execution."""
    state = sample_state_with_rubric.copy()
    state["panel_reviews"] = [sample_hr_review, sample_tech_review]
    # Create a Tech working memory for proper dict structure
    tech_memory = WorkingMemory(
        agent_role="Tech",
        key_observations=[
            KeyObservation(
                category="LLM Agent Frameworks",
                observation="Core LangGraph contributor",
                evidence_location="Open Source",
                strength_or_risk="strength",
            ),
            KeyObservation(
                category="Python & Async Patterns",
                observation="Expert Python",
                evidence_location="Skills",
                strength_or_risk="strength",
            ),
            KeyObservation(
                category="AI Safety & Compliance",
                observation="Basic implementation",
                evidence_location="Experience",
                strength_or_risk="risk",
            ),
        ],
    )
    state["agent_working_memory"] = {"HR": sample_working_memory, "Tech": tech_memory}
    state["metadata"]["node_execution_order"].extend(["hr_agent", "tech_agent"])
    return state
