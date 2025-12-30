"""Unit tests for synthesis node."""

import pytest
from unittest.mock import Mock

from src.nodes.synthesis import (
    synthesis_node,
    _detect_disagreements,
    _calculate_weighted_average_score,
    _create_decision_packet,
    _create_interview_plan,
)


class TestSynthesisHelpers:
    """Tests for synthesis helper functions."""

    def test_detect_disagreements_no_disagreement(
        self, sample_rubric, sample_hr_review, sample_tech_review
    ):
        """Test disagreement detection when scores are similar."""
        # Modify reviews to have similar scores
        hr_review = sample_hr_review.model_copy()
        tech_review = sample_tech_review.model_copy()

        # Set all scores to 4 (no disagreement)
        for score in hr_review.category_scores:
            score.score = 4
        for score in tech_review.category_scores:
            score.score = 4

        disagreements = _detect_disagreements([hr_review, tech_review], sample_rubric)
        assert len(disagreements) == 0

    def test_detect_disagreements_with_disagreement(
        self, sample_rubric, sample_hr_review, sample_tech_review
    ):
        """Test disagreement detection when delta >= 1."""
        # sample_tech_review has score=5 for LLM Agent Frameworks
        # sample_hr_review has score=4 for LLM Agent Frameworks
        # This should not trigger disagreement (delta < 1)

        # Modify to create actual disagreement
        hr_review = sample_hr_review.model_copy()
        tech_review = sample_tech_review.model_copy()

        # Set one score to 5, another to 2 (delta = 3)
        hr_review.category_scores[0].score = 5
        tech_review.category_scores[0].score = 2

        disagreements = _detect_disagreements([hr_review, tech_review], sample_rubric)
        assert len(disagreements) >= 1

    def test_calculate_weighted_average_score(
        self, sample_hr_review, sample_tech_review
    ):
        """Test weighted average score calculation."""
        category_name = "LLM Agent Frameworks"
        avg_score = _calculate_weighted_average_score(
            category_name, [sample_hr_review, sample_tech_review]
        )

        # HR=4, Tech=5, average should be 4.5
        assert avg_score == 4.5

    def test_create_decision_packet(
        self, sample_rubric, sample_hr_review, sample_tech_review, sample_working_memory
    ):
        """Test decision packet creation."""
        packet = _create_decision_packet(
            sample_rubric,
            [sample_hr_review, sample_tech_review],
            [],
            {"HR": sample_working_memory},
        )

        assert packet.overall_fit_score >= 0.0
        assert packet.overall_fit_score <= 5.0
        assert packet.confidence in ["low", "medium", "high"]

    def test_create_interview_plan(
        self, sample_rubric, sample_hr_review, sample_tech_review, sample_disagreement, sample_working_memory
    ):
        """Test interview plan generation."""
        # Create Tech working memory
        tech_memory = sample_working_memory.model_copy()
        tech_memory.agent_role = "Tech"

        plan = _create_interview_plan(
            sample_rubric,
            [sample_hr_review, sample_tech_review],
            [sample_disagreement],
            {"HR": sample_working_memory, "Tech": tech_memory},
        )

        assert len(plan.priority_areas) >= 1
        # Check that questions were created (total across all interviewers)
        total_questions = sum(len(questions) for questions in plan.questions_by_interviewer.values())
        assert total_questions >= 1


class TestSynthesisNode:
    """Tests for synthesis_node function."""

    def test_synthesis_node_success(
        self, sample_state_with_reviews, sample_rubric
    ):
        """Test successful synthesis execution."""
        result = synthesis_node(sample_state_with_reviews)

        assert "disagreements" in result
        assert "decision_packet" in result
        assert "interview_plan" in result
        assert isinstance(result["disagreements"], list)

    def test_synthesis_node_missing_rubric(self):
        """Test error when rubric is missing."""
        state = {"panel_reviews": [], "agent_working_memory": {}}

        with pytest.raises(ValueError) as exc_info:
            synthesis_node(state)
        assert "Rubric is required" in str(exc_info.value)

    def test_synthesis_node_missing_panel_reviews(self, sample_rubric):
        """Test error when panel reviews are missing."""
        state = {"rubric": sample_rubric, "agent_working_memory": {}}

        with pytest.raises(ValueError) as exc_info:
            synthesis_node(state)
        assert "Panel reviews are required" in str(exc_info.value)
