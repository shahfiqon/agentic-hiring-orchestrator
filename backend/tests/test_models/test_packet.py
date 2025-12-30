"""
Unit tests for decision packet models (DecisionPacket, Disagreement).

Tests cover validation logic, computed fields, edge cases, and helper methods.
"""

import pytest
from pydantic import ValidationError

from src.models.packet import DecisionPacket, Disagreement


class TestDisagreement:
    """Tests for Disagreement model."""

    def test_valid_disagreement(self, sample_disagreement):
        """Test creating valid disagreement."""
        assert sample_disagreement.category_name == "AI Safety & Compliance"
        assert sample_disagreement.agent_scores == {"HR": 4, "Tech": 3}
        assert sample_disagreement.score_delta == 1

    def test_score_delta_computed_field(self):
        """Test score_delta computed field calculation."""
        # Delta = 1
        disagreement1 = Disagreement(
            category_name="Test Category",
            agent_scores={"HR": 4, "Tech": 3},
            reason="Different perspectives on evidence",
            resolution_approach="Interview to clarify",
        )
        assert disagreement1.score_delta == 1

        # Delta = 2 (reversed order should still be positive)
        disagreement2 = Disagreement(
            category_name="Test Category",
            agent_scores={"Tech": 2, "Compliance": 4},
            reason="Different focus areas",
            resolution_approach="Review evidence",
        )
        assert disagreement2.score_delta == 2

        # Delta = 3
        disagreement3 = Disagreement(
            category_name="Test Category",
            agent_scores={"HR": 5, "Tech": 2},
            reason="Major disagreement",
            resolution_approach="Extended interview",
        )
        assert disagreement3.score_delta == 3

    def test_score_delta_validation(self):
        """Test that score_delta must be >= 1."""
        # Valid: delta = 1
        disagreement = Disagreement(
            category_name="Test",
            agent_scores={"HR": 4, "Tech": 3},
            reason="Minor difference",
            resolution_approach="Quick check",
        )
        assert disagreement.score_delta >= 1

        # Invalid: delta = 0 (same scores)
        with pytest.raises(ValidationError) as exc_info:
            Disagreement(
                category_name="Test",
                agent_scores={"HR": 3, "Tech": 3},
                reason="Same score",
                resolution_approach="Not needed",
            )
        assert "no significant disagreement" in str(exc_info.value)

    def test_valid_agent_roles(self):
        """Test that agent roles must be valid literals."""
        valid_roles = ["HR", "Tech", "Product", "Compliance"]

        # Test all valid role combinations
        for role1 in valid_roles:
            for role2 in valid_roles:
                if role1 != role2:
                    disagreement = Disagreement(
                        category_name="Test",
                        agent_scores={role1: 4, role2: 2},
                        reason="Different perspectives",
                        resolution_approach="Interview",
                    )
                    assert role1 in disagreement.agent_scores
                    assert role2 in disagreement.agent_scores

        # Invalid agent role
        with pytest.raises(ValidationError) as exc_info:
            Disagreement(
                category_name="Test",
                agent_scores={"invalid_agent": 4, "Tech": 2},
                reason="Test",
                resolution_approach="Test",
            )
        assert "Invalid agent roles in disagreement" in str(exc_info.value)

    def test_score_range_validation(self):
        """Test that scores must be in range 0-5."""
        # Valid scores
        disagreement = Disagreement(
            category_name="Test",
            agent_scores={"HR": 5, "Tech": 0},
            reason="Extreme difference",
            resolution_approach="Interview",
        )
        assert disagreement.agent_scores["HR"] == 5
        assert disagreement.agent_scores["Tech"] == 0

        # Invalid score > 5
        with pytest.raises(ValidationError) as exc_info:
            Disagreement(
                category_name="Test",
                agent_scores={"HR": 6, "Tech": 3},
                reason="Test",
                resolution_approach="Test",
            )
        assert "Invalid score 6" in str(exc_info.value)

        # Invalid score < 0
        with pytest.raises(ValidationError) as exc_info:
            Disagreement(
                category_name="Test",
                agent_scores={"HR": 4, "Tech": -1},
                reason="Test",
                resolution_approach="Test",
            )
        assert "Invalid score -1" in str(exc_info.value)

    def test_json_serialization(self, sample_disagreement):
        """Test JSON serialization and deserialization."""
        json_data = sample_disagreement.model_dump()

        assert json_data["category_name"] == "AI Safety & Compliance"
        assert json_data["agent_scores"] == {"HR": 4, "Tech": 3}
        assert json_data["score_delta"] == 1
        assert "reason" in json_data
        assert "resolution_approach" in json_data

        # Deserialize (need to exclude computed field)
        json_data_for_deserialize = {k: v for k, v in json_data.items() if k != 'score_delta'}
        disagreement_copy = Disagreement(**json_data_for_deserialize)
        assert disagreement_copy.category_name == sample_disagreement.category_name
        assert disagreement_copy.score_delta == sample_disagreement.score_delta


class TestDecisionPacket:
    """Tests for DecisionPacket model."""

    def test_valid_decision_packet_hire(self, sample_decision_packet):
        """Test creating valid hire decision packet."""
        assert sample_decision_packet.overall_fit_score == 4.1
        assert sample_decision_packet.recommendation == "Lean hire"
        assert sample_decision_packet.confidence == "high"
        assert len(sample_decision_packet.must_have_gaps) == 0
        assert len(sample_decision_packet.disagreements) == 1

    def test_valid_decision_packet_no_hire(self):
        """Test creating valid no hire decision packet."""
        packet = DecisionPacket(
            role_title="Senior AI Engineer",
            overall_fit_score=2.3,
            recommendation="No",
            confidence="high",
            top_strengths=["Basic Python skills", "Good communication", "Quick learner"],
            top_risks=["No LLM experience", "No production experience", "Missing must-have skills"],
            must_have_gaps=["LLM Agent Frameworks", "Python & Async Patterns"],
            disagreements=[],
        )
        assert packet.recommendation == "No"
        assert len(packet.must_have_gaps) == 2

    def test_valid_decision_packet_lean_hire(self):
        """Test creating valid lean hire decision packet."""
        packet = DecisionPacket(
            role_title="Senior AI Engineer",
            overall_fit_score=3.5,
            recommendation="Lean hire",
            confidence="medium",
            top_strengths=["Good technical skills", "Strong communication", "Fast learner"],
            top_risks=["Limited domain experience", "Some skill gaps", "Needs mentoring"],
            must_have_gaps=[],
            disagreements=[
                Disagreement(
                    category_name="AI Safety",
                    agent_scores={"HR": 4, "Compliance": 2},
                    reason="Different assessment of compliance knowledge",
                    resolution_approach="Interview to clarify understanding",
                ),
            ],
        )
        assert packet.recommendation == "Lean hire"
        assert packet.confidence == "medium"

    def test_score_range_validation(self):
        """Test that overall_fit_score must be in range 0-5."""
        # Valid scores (with appropriate recommendations for each score)
        test_cases = [
            (0.0, "No"),
            (2.5, "Lean no"),
            (5.0, "Hire"),
        ]
        for score, rec in test_cases:
            packet = DecisionPacket(
                role_title="Test Role",
                overall_fit_score=score,
                recommendation=rec,
                confidence="medium",
                top_strengths=["Strength 1", "Strength 2", "Strength 3"],
                top_risks=["Risk 1", "Risk 2", "Risk 3"],
                must_have_gaps=[],
                disagreements=[],
            )
            assert packet.overall_fit_score == score

        # Invalid: negative score
        with pytest.raises(ValidationError) as exc_info:
            DecisionPacket(
                role_title="Test Role",
                overall_fit_score=-0.5,
                recommendation="No",
                confidence="high",
                top_strengths=["S1", "S2", "S3"],
                top_risks=["R1", "R2", "R3"],
                must_have_gaps=[],
                disagreements=[],
            )
        assert "greater than or equal to 0" in str(exc_info.value)

        # Invalid: score > 5
        with pytest.raises(ValidationError) as exc_info:
            DecisionPacket(
                role_title="Test Role",
                overall_fit_score=5.5,
                recommendation="Hire",
                confidence="high",
                top_strengths=["S1", "S2", "S3"],
                top_risks=["R1", "R2", "R3"],
                must_have_gaps=[],
                disagreements=[],
            )
        assert "less than or equal to 5" in str(exc_info.value)

    def test_recommendation_literals(self):
        """Test that recommendation must be one of the valid literals."""
        valid_recommendations = ["Hire", "Lean hire", "Lean no", "No"]

        for rec in valid_recommendations:
            # Skip "Hire" with low score to avoid validation error
            score = 4.0 if rec in ["Hire", "Lean hire"] else 2.0
            packet = DecisionPacket(
                role_title="Test Role",
                overall_fit_score=score,
                recommendation=rec,
                confidence="medium",
                top_strengths=["S1", "S2", "S3"],
                top_risks=["R1", "R2", "R3"],
                must_have_gaps=[],
                disagreements=[],
            )
            assert packet.recommendation == rec

        # Invalid recommendation
        with pytest.raises(ValidationError) as exc_info:
            DecisionPacket(
                role_title="Test Role",
                overall_fit_score=3.0,
                recommendation="Maybe",
                confidence="medium",
                top_strengths=["S1", "S2", "S3"],
                top_risks=["R1", "R2", "R3"],
                must_have_gaps=[],
                disagreements=[],
            )
        assert "Input should be 'Hire', 'Lean hire', 'Lean no' or 'No'" in str(exc_info.value)

    def test_confidence_literals(self):
        """Test that confidence must be one of the valid literals."""
        valid_confidences = ["low", "medium", "high"]

        for conf in valid_confidences:
            packet = DecisionPacket(
                role_title="Test Role",
                overall_fit_score=3.0,
                recommendation="Lean hire",
                confidence=conf,
                top_strengths=["S1", "S2", "S3"],
                top_risks=["R1", "R2", "R3"],
                must_have_gaps=[],
                disagreements=[],
            )
            assert packet.confidence == conf

        # Invalid confidence
        with pytest.raises(ValidationError) as exc_info:
            DecisionPacket(
                role_title="Test Role",
                overall_fit_score=3.0,
                recommendation="Lean hire",
                confidence="very_high",
                top_strengths=["S1", "S2", "S3"],
                top_risks=["R1", "R2", "R3"],
                must_have_gaps=[],
                disagreements=[],
            )
        assert "Input should be 'high', 'medium' or 'low'" in str(exc_info.value)

    def test_has_critical_gaps_method(self):
        """Test has_critical_gaps helper method."""
        # No gaps
        packet1 = DecisionPacket(
            role_title="Test Role",
            overall_fit_score=4.0,
            recommendation="Hire",
            confidence="high",
            top_strengths=["S1", "S2", "S3"],
            top_risks=["R1", "R2", "R3"],
            must_have_gaps=[],
            disagreements=[],
        )
        assert packet1.has_critical_gaps() is False

        # Has gaps
        packet2 = DecisionPacket(
            role_title="Test Role",
            overall_fit_score=2.0,
            recommendation="No",
            confidence="high",
            top_strengths=["S1", "S2", "S3"],
            top_risks=["R1", "R2", "R3"],
            must_have_gaps=["Critical Skill"],
            disagreements=[],
        )
        assert packet2.has_critical_gaps() is True

    def test_hire_with_must_have_gaps_validation(self):
        """Test that Hire recommendation cannot have must-have gaps."""
        # Valid: Hire with no gaps
        packet = DecisionPacket(
            role_title="Test Role",
            overall_fit_score=4.5,
            recommendation="Hire",
            confidence="high",
            top_strengths=["S1", "S2", "S3"],
            top_risks=["R1", "R2", "R3"],
            must_have_gaps=[],
            disagreements=[],
        )
        assert packet.recommendation == "Hire"

        # Invalid: Hire with gaps
        with pytest.raises(ValidationError) as exc_info:
            DecisionPacket(
                role_title="Test Role",
                overall_fit_score=4.5,
                recommendation="Hire",
                confidence="high",
                top_strengths=["S1", "S2", "S3"],
                top_risks=["R1", "R2", "R3"],
                must_have_gaps=["Critical Skill"],
                disagreements=[],
            )
        assert "Cannot recommend hiring with critical qualification gaps" in str(exc_info.value)

    def test_confidence_based_on_disagreements(self):
        """Test that confidence should be lower with many disagreements."""
        # High confidence with no disagreements
        packet1 = DecisionPacket(
            role_title="Test Role",
            overall_fit_score=4.0,
            recommendation="Hire",
            confidence="high",
            top_strengths=["S1", "S2", "S3"],
            top_risks=["R1", "R2", "R3"],
            must_have_gaps=[],
            disagreements=[],
        )
        assert packet1.confidence == "high"
        assert len(packet1.disagreements) == 0

        # Lower confidence with disagreements
        packet2 = DecisionPacket(
            role_title="Test Role",
            overall_fit_score=3.5,
            recommendation="Lean hire",
            confidence="medium",
            top_strengths=["S1", "S2", "S3"],
            top_risks=["R1", "R2", "R3"],
            must_have_gaps=[],
            disagreements=[
                Disagreement(
                    category_name="Cat1",
                    agent_scores={"HR": 5, "Tech": 2},
                    reason="Different perspectives",
                    resolution_approach="Interview",
                ),
            ],
        )
        assert packet2.confidence == "medium"
        assert len(packet2.disagreements) == 1

    def test_json_serialization(self, sample_decision_packet):
        """Test JSON serialization and deserialization."""
        json_data = sample_decision_packet.model_dump()

        assert json_data["overall_fit_score"] == 4.1
        assert json_data["recommendation"] == "Lean hire"
        assert json_data["confidence"] == "high"
        assert "disagreements" in json_data
        assert "must_have_gaps" in json_data
        assert "generated_at" in json_data

        # Deserialize (need to exclude generated_at to avoid issues, and handle computed fields in disagreements)
        json_data_copy = json_data.copy()
        # Remove computed fields from disagreements
        if "disagreements" in json_data_copy:
            json_data_copy["disagreements"] = [
                {k: v for k, v in d.items() if k != 'score_delta'}
                for d in json_data_copy["disagreements"]
            ]

        packet_copy = DecisionPacket(**json_data_copy)
        assert packet_copy.overall_fit_score == sample_decision_packet.overall_fit_score
        assert packet_copy.recommendation == sample_decision_packet.recommendation

    def test_edge_case_borderline_score(self):
        """Test decision packet with borderline score."""
        packet = DecisionPacket(
            role_title="Test Role",
            overall_fit_score=3.0,
            recommendation="Lean hire",
            confidence="medium",
            top_strengths=["S1", "S2", "S3"],
            top_risks=["R1", "R2", "R3"],
            must_have_gaps=[],
            disagreements=[],
        )
        assert packet.overall_fit_score == 3.0
        assert packet.recommendation == "Lean hire"

    def test_score_recommendation_alignment(self):
        """Test validation of score-recommendation alignment."""
        # Valid: high score with positive recommendation
        packet1 = DecisionPacket(
            role_title="Test Role",
            overall_fit_score=4.5,
            recommendation="Hire",
            confidence="high",
            top_strengths=["S1", "S2", "S3"],
            top_risks=["R1", "R2", "R3"],
            must_have_gaps=[],
            disagreements=[],
        )
        assert packet1.overall_fit_score >= 4.0

        # Invalid: high score with "No" recommendation
        with pytest.raises(ValidationError) as exc_info:
            DecisionPacket(
                role_title="Test Role",
                overall_fit_score=4.5,
                recommendation="No",
                confidence="high",
                top_strengths=["S1", "S2", "S3"],
                top_risks=["R1", "R2", "R3"],
                must_have_gaps=[],
                disagreements=[],
            )
        assert "seems inconsistent" in str(exc_info.value)

        # Invalid: low score with "Hire" recommendation
        with pytest.raises(ValidationError) as exc_info:
            DecisionPacket(
                role_title="Test Role",
                overall_fit_score=1.5,
                recommendation="Hire",
                confidence="high",
                top_strengths=["S1", "S2", "S3"],
                top_risks=["R1", "R2", "R3"],
                must_have_gaps=[],
                disagreements=[],
            )
        assert "seems inconsistent" in str(exc_info.value)
