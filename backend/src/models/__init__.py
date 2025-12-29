"""Data models for the Agentic Hiring Orchestrator.

This package contains Pydantic models for:
- Rubrics: Evaluation criteria and scoring definitions
- Reviews: Agent evaluations with evidence
- Packets: Decision synthesis and recommendations
- Interviews: Question generation for follow-up
- Memory: Working memory for two-pass evaluation
"""

from .interview import InterviewQuestion, InterviewPlan
from .memory import CrossReference, KeyObservation, WorkingMemory
from .packet import Disagreement, DecisionPacket
from .review import AgentReview, CategoryScore, Evidence
from .rubric import Rubric, RubricCategory, ScoringCriteria

__all__ = [
    # Interview models
    "InterviewPlan",
    "InterviewQuestion",
    # Memory models
    "CrossReference",
    "KeyObservation",
    "WorkingMemory",
    # Packet models
    "DecisionPacket",
    "Disagreement",
    # Review models
    "AgentReview",
    "CategoryScore",
    "Evidence",
    # Rubric models
    "Rubric",
    "RubricCategory",
    "ScoringCriteria",
]
