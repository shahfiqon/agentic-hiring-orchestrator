"""
Unit tests for review models (AgentReview, CategoryScore, Evidence).

Tests cover validation logic, edge cases, helper methods, and rubric coverage.
"""

import pytest
from pydantic import ValidationError

from src.models.review import AgentReview, CategoryScore, Evidence
from tests.test_utils import create_valid_agent_review, get_category_score_by_name


class TestEvidence:
    """Tests for Evidence model."""

    def test_valid_evidence(self):
        """Test creating valid evidence."""
        evidence = Evidence(
            resume_text="Candidate built production LangGraph workflows at TechCorp",
            line_reference="Experience section, 2nd bullet",
            interpretation="Demonstrates hands-on experience with target framework",
        )
        assert "LangGraph" in evidence.resume_text
        assert "hands-on experience" in evidence.interpretation

    def test_non_empty_text(self):
        """Test that resume_text cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            Evidence(
                resume_text="",
                interpretation="Some interpretation",
            )
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_non_empty_interpretation(self):
        """Test that interpretation cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            Evidence(
                resume_text="Some evidence text",
                interpretation="",
            )
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_json_serialization(self, sample_evidence):
        """Test JSON serialization and deserialization."""
        json_data = sample_evidence.model_dump()

        assert "resume_text" in json_data
        assert "interpretation" in json_data

        # Deserialize
        evidence_copy = Evidence(**json_data)
        assert evidence_copy.resume_text == sample_evidence.resume_text
        assert evidence_copy.interpretation == sample_evidence.interpretation


class TestCategoryScore:
    """Tests for CategoryScore model."""

    def test_valid_category_score(self, sample_evidence):
        """Test creating valid category score."""
        score = CategoryScore(
            category_name="LLM Agent Frameworks",
            score=4,
            evidence=[sample_evidence],
            confidence="high",
        )
        assert score.category_name == "LLM Agent Frameworks"
        assert score.score == 4
        assert len(score.evidence) == 1
        assert score.confidence == "high"

    def test_score_range_validation(self, sample_evidence):
        """Test that score must be in range 0-5."""
        # Valid scores
        for score_val in range(6):
            score = CategoryScore(
                category_name="Test",
                score=score_val,
                evidence=[sample_evidence],
                confidence="medium",
            )
            assert score.score == score_val

        # Invalid scores
        with pytest.raises(ValidationError) as exc_info:
            CategoryScore(
                category_name="Test",
                score=-1,
                evidence=[sample_evidence],
                confidence="medium",
            )
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            CategoryScore(
                category_name="Test",
                score=6,
                evidence=[sample_evidence],
                confidence="medium",
            )
        assert "less than or equal to 5" in str(exc_info.value)

    def test_evidence_requirement(self):
        """Test that at least one evidence is required."""
        evidence = Evidence(resume_text="Test evidence", interpretation="Test")

        # Valid: with evidence
        score = CategoryScore(
            category_name="Test",
            score=3,
            evidence=[evidence],
            confidence="medium",
        )
        assert len(score.evidence) == 1

        # Invalid: empty evidence list
        with pytest.raises(ValidationError) as exc_info:
            CategoryScore(
                category_name="Test",
                score=3,
                evidence=[],
                confidence="medium",
            )
        assert "List should have at least 1 item" in str(exc_info.value)

    def test_confidence_levels(self, sample_evidence):
        """Test valid confidence levels."""
        valid_levels = ["low", "medium", "high"]

        for level in valid_levels:
            score = CategoryScore(
                category_name="Test",
                score=3,
                evidence=[sample_evidence],
                confidence=level,
            )
            assert score.confidence == level

        # Invalid confidence level
        with pytest.raises(ValidationError) as exc_info:
            CategoryScore(
                category_name="Test",
                score=3,
                evidence=[sample_evidence],
                confidence="invalid_level",
            )
        assert "Input should be 'high', 'medium' or 'low'" in str(exc_info.value)

    def test_multiple_evidence_items(self):
        """Test category score with multiple evidence items."""
        evidence_list = [
            Evidence(resume_text="Evidence 1", interpretation="Interpretation 1"),
            Evidence(resume_text="Evidence 2", interpretation="Interpretation 2"),
            Evidence(resume_text="Evidence 3", interpretation="Interpretation 3"),
        ]
        score = CategoryScore(
            category_name="Test",
            score=4,
            evidence=evidence_list,
            confidence="high",
        )
        assert len(score.evidence) == 3

    def test_json_serialization(self, sample_category_score):
        """Test JSON serialization and deserialization."""
        json_data = sample_category_score.model_dump()

        assert json_data["category_name"] == "LLM Agent Frameworks"
        assert json_data["score"] == 4
        assert json_data["confidence"] == "high"
        assert len(json_data["evidence"]) >= 1

        # Deserialize
        score_copy = CategoryScore(**json_data)
        assert score_copy.category_name == sample_category_score.category_name
        assert score_copy.score == sample_category_score.score


class TestAgentReview:
    """Tests for AgentReview model."""

    def test_valid_agent_review(self, sample_hr_review):
        """Test creating valid agent review."""
        assert sample_hr_review.agent_role == "HR"
        assert len(sample_hr_review.category_scores) == 4
        assert len(sample_hr_review.expected_rubric_categories) == 4

    def test_agent_role_literals(self, sample_category_score):
        """Test that agent_role must be one of the valid literals."""
        valid_roles = ["HR", "Tech", "Compliance"]

        for role in valid_roles:
            review = AgentReview(
                agent_role=role,
                category_scores=[sample_category_score],
                overall_assessment="Test assessment",
                top_strengths=["Strength 1", "Strength 2", "Strength 3"],
                top_risks=["Risk 1", "Risk 2", "Risk 3"],
                follow_up_questions=["Question 1"],
                expected_rubric_categories=["LLM Agent Frameworks"],
            )
            assert review.agent_role == role

        # Invalid role
        with pytest.raises(ValidationError) as exc_info:
            AgentReview(
                agent_role="invalid_agent",
                category_scores=[sample_category_score],
                overall_assessment="Test assessment",
                top_strengths=["Strength 1", "Strength 2", "Strength 3"],
                top_risks=["Risk 1", "Risk 2", "Risk 3"],
                follow_up_questions=["Question 1"],
                expected_rubric_categories=["LLM Agent Frameworks"],
            )
        assert "invalid" in str(exc_info.value).lower() and "agent" in str(exc_info.value).lower()

    def test_unique_category_scores(self):
        """Test that category scores must have unique category names."""
        evidence = Evidence(resume_text="Test", interpretation="Test")

        # Valid: unique categories
        unique_scores = [
            CategoryScore(category_name="Cat1", score=3, evidence=[evidence], confidence="medium"),
            CategoryScore(category_name="Cat2", score=4, evidence=[evidence], confidence="high"),
        ]
        review = AgentReview(
            agent_role="HR",
            category_scores=unique_scores,
            overall_assessment="Test assessment",
            top_strengths=["Strength 1", "Strength 2", "Strength 3"],
            top_risks=["Risk 1", "Risk 2", "Risk 3"],
            follow_up_questions=["Question 1"],
            expected_rubric_categories=["Cat1", "Cat2"],
        )
        assert len(review.category_scores) == 2

        # Invalid: duplicate categories
        duplicate_scores = [
            CategoryScore(category_name="Cat1", score=3, evidence=[evidence], confidence="medium"),
            CategoryScore(category_name="Cat1", score=4, evidence=[evidence], confidence="high"),
        ]
        with pytest.raises(ValidationError) as exc_info:
            AgentReview(
                agent_role="HR",
                category_scores=duplicate_scores,
                overall_assessment="Test assessment",
                top_strengths=["Strength 1", "Strength 2", "Strength 3"],
                top_risks=["Risk 1", "Risk 2", "Risk 3"],
                follow_up_questions=["Question 1"],
                expected_rubric_categories=["Cat1"],
            )
        assert "Duplicate category scores found" in str(exc_info.value)

    def test_rubric_coverage_validation(self):
        """Test validation against expected rubric categories."""
        evidence = Evidence(resume_text="Test", interpretation="Test")

        # Valid: covers all expected categories
        scores = [
            CategoryScore(category_name="Cat1", score=3, evidence=[evidence], confidence="medium"),
            CategoryScore(category_name="Cat2", score=4, evidence=[evidence], confidence="high"),
        ]
        review = AgentReview(
            agent_role="HR",
            category_scores=scores,
            overall_assessment="Test assessment",
            top_strengths=["Strength 1", "Strength 2", "Strength 3"],
            top_risks=["Risk 1", "Risk 2", "Risk 3"],
            follow_up_questions=["Question 1"],
            expected_rubric_categories=["Cat1", "Cat2"],
        )
        assert len(review.category_scores) == 2

        # Invalid: missing expected category
        incomplete_scores = [
            CategoryScore(category_name="Cat1", score=3, evidence=[evidence], confidence="medium"),
        ]
        with pytest.raises(ValidationError) as exc_info:
            AgentReview(
                agent_role="HR",
                category_scores=incomplete_scores,
                overall_assessment="Test assessment",
                top_strengths=["Strength 1", "Strength 2", "Strength 3"],
                top_risks=["Risk 1", "Risk 2", "Risk 3"],
                follow_up_questions=["Question 1"],
                expected_rubric_categories=["Cat1", "Cat2"],
            )
        assert ("missing" in str(exc_info.value).lower() or "cover" in str(exc_info.value).lower()) and "categor" in str(exc_info.value).lower()

        # Invalid: extra category not in rubric
        extra_scores = [
            CategoryScore(category_name="Cat1", score=3, evidence=[evidence], confidence="medium"),
            CategoryScore(category_name="Cat2", score=4, evidence=[evidence], confidence="high"),
            CategoryScore(category_name="Cat3", score=5, evidence=[evidence], confidence="high"),
        ]
        with pytest.raises(ValidationError) as exc_info:
            AgentReview(
                agent_role="HR",
                category_scores=extra_scores,
                overall_assessment="Test assessment",
                top_strengths=["Strength 1", "Strength 2", "Strength 3"],
                top_risks=["Risk 1", "Risk 2", "Risk 3"],
                follow_up_questions=["Question 1"],
                expected_rubric_categories=["Cat1", "Cat2"],
            )
        assert ("unexpected" in str(exc_info.value).lower() or "not in" in str(exc_info.value).lower()) and "categor" in str(exc_info.value).lower()

    def test_get_score_for_category(self, sample_hr_review):
        """Test get_score_for_category helper method."""
        # Find existing category
        score = sample_hr_review.get_score_for_category("LLM Agent Frameworks")
        assert score is not None
        assert score.category_name == "LLM Agent Frameworks"
        assert score.score == 4

        # Try to find non-existent category
        missing = sample_hr_review.get_score_for_category("Non-existent Category")
        assert missing is None

    def test_json_serialization(self, sample_hr_review):
        """Test JSON serialization and deserialization."""
        json_data = sample_hr_review.model_dump()

        assert json_data["agent_role"] == "HR"
        assert len(json_data["category_scores"]) == 4
        assert "expected_rubric_categories" in json_data

        # Deserialize
        review_copy = AgentReview(**json_data)
        assert review_copy.agent_role == sample_hr_review.agent_role
        assert len(review_copy.category_scores) == len(sample_hr_review.category_scores)

    def test_edge_case_single_category(self):
        """Test agent review with single category."""
        evidence = Evidence(resume_text="Test", interpretation="Test")
        score = CategoryScore(
            category_name="Only Category",
            score=4,
            evidence=[evidence],
            confidence="high",
        )
        review = AgentReview(
            agent_role="HR",
            category_scores=[score],
            overall_assessment="Test assessment",
            top_strengths=["Strength 1", "Strength 2", "Strength 3"],
            top_risks=["Risk 1", "Risk 2", "Risk 3"],
            follow_up_questions=["Question 1"],
            expected_rubric_categories=["Only Category"],
        )
        assert len(review.category_scores) == 1

    def test_varying_confidence_levels(self):
        """Test agent review with varying confidence levels across categories."""
        evidence = Evidence(resume_text="Test", interpretation="Test")
        scores = [
            CategoryScore(category_name="Cat1", score=5, evidence=[evidence], confidence="high"),
            CategoryScore(category_name="Cat2", score=3, evidence=[evidence], confidence="medium"),
            CategoryScore(category_name="Cat3", score=2, evidence=[evidence], confidence="low"),
        ]
        review = AgentReview(
            agent_role="Tech",
            category_scores=scores,
            overall_assessment="Test assessment",
            top_strengths=["Strength 1", "Strength 2", "Strength 3"],
            top_risks=["Risk 1", "Risk 2", "Risk 3"],
            follow_up_questions=["Question 1"],
            expected_rubric_categories=["Cat1", "Cat2", "Cat3"],
        )
        assert review.category_scores[0].confidence == "high"
        assert review.category_scores[1].confidence == "medium"
        assert review.category_scores[2].confidence == "low"
