"""
Unit tests for working memory models (WorkingMemory, KeyObservation, CrossReference).

Tests cover validation logic, edge cases, and helper methods.
"""

import pytest
from pydantic import ValidationError

from src.models.memory import WorkingMemory, KeyObservation, CrossReference


class TestKeyObservation:
    """Tests for KeyObservation model."""

    def test_valid_key_observation_strength(self, sample_key_observation):
        """Test creating valid strength observation."""
        assert sample_key_observation.category == "LLM Agent Frameworks"
        assert "LangGraph contributor" in sample_key_observation.observation
        assert sample_key_observation.strength_or_risk == "strength"

    def test_valid_key_observation_gap(self):
        """Test creating valid risk observation."""
        observation = KeyObservation(
            category="AI Safety & Compliance",
            observation="No mention of bias mitigation strategies",
            evidence_location="N/A - missing from resume",
            strength_or_risk="risk",
        )
        assert observation.strength_or_risk == "risk"

    def test_non_empty_fields(self):
        """Test that category and observation cannot be empty."""
        # Empty category
        with pytest.raises(ValidationError) as exc_info:
            KeyObservation(
                category="",
                observation="Test observation",
                evidence_location="Test location",
                strength_or_risk="strength",
            )
        assert "String should have at least 1 character" in str(exc_info.value)

        # Empty observation
        with pytest.raises(ValidationError) as exc_info:
            KeyObservation(
                category="Test Category",
                observation="",
                evidence_location="Test location",
                strength_or_risk="strength",
            )
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_observation_type_literals(self):
        """Test that strength_or_risk must be valid literal."""
        valid_types = ["strength", "risk", "neutral"]

        for obs_type in valid_types:
            observation = KeyObservation(
                category="Test",
                observation="Test observation",
                evidence_location="Test location",
                strength_or_risk=obs_type,
            )
            assert observation.strength_or_risk == obs_type

        # Invalid type
        with pytest.raises(ValidationError) as exc_info:
            KeyObservation(
                category="Test",
                observation="Test",
                evidence_location="Test location",
                strength_or_risk="invalid_type",
            )
        assert "Input should be 'strength', 'risk' or 'neutral'" in str(exc_info.value)

    def test_json_serialization(self, sample_key_observation):
        """Test JSON serialization and deserialization."""
        json_data = sample_key_observation.model_dump()

        assert json_data["category"] == "LLM Agent Frameworks"
        assert json_data["strength_or_risk"] == "strength"

        # Deserialize
        observation_copy = KeyObservation(**json_data)
        assert observation_copy.category == sample_key_observation.category
        assert observation_copy.strength_or_risk == sample_key_observation.strength_or_risk


class TestCrossReference:
    """Tests for CrossReference model."""

    def test_valid_cross_reference_strong_corroboration(self, sample_cross_reference):
        """Test creating valid cross-reference with strong corroboration."""
        assert sample_cross_reference.claim == "Strong production agentic systems experience"
        assert len(sample_cross_reference.supporting_evidence) == 2
        assert len(sample_cross_reference.contradictory_evidence) == 0
        assert sample_cross_reference.assessment == "well-supported"

    def test_valid_cross_reference_with_contradiction(self):
        """Test creating cross-reference with contradicting evidence."""
        cross_ref = CrossReference(
            claim="Expert in AI safety",
            claim_location="Skills section",
            supporting_evidence=["Implemented basic PII handling"],
            contradictory_evidence=["No mention of bias mitigation", "Limited depth in compliance"],
            assessment="contradictory",
        )
        assert cross_ref.assessment == "contradictory"
        assert len(cross_ref.contradictory_evidence) == 2

    def test_at_least_one_evidence_required(self):
        """Test that at least one evidence type is required."""
        # Valid: supporting evidence only
        cross_ref1 = CrossReference(
            claim="Test claim",
            claim_location="Test location",
            supporting_evidence=["Evidence 1"],
            contradictory_evidence=[],
            assessment="partially-supported",
        )
        assert len(cross_ref1.supporting_evidence) == 1

        # Valid: contradictory evidence only
        cross_ref2 = CrossReference(
            claim="Test claim",
            claim_location="Test location",
            supporting_evidence=[],
            contradictory_evidence=["Evidence 1"],
            assessment="unsupported",
        )
        assert len(cross_ref2.contradictory_evidence) == 1

        # Valid: both types of evidence
        cross_ref3 = CrossReference(
            claim="Test claim",
            claim_location="Test location",
            supporting_evidence=["Support 1"],
            contradictory_evidence=["Contradict 1"],
            assessment="contradictory",
        )
        assert len(cross_ref3.supporting_evidence) == 1
        assert len(cross_ref3.contradictory_evidence) == 1

        # Invalid: no evidence at all
        with pytest.raises(ValidationError) as exc_info:
            CrossReference(
                claim="Test claim",
                claim_location="Test location",
                supporting_evidence=[],
                contradictory_evidence=[],
                assessment="well-supported",
            )
        assert "CrossReference must have at least supporting_evidence or contradictory_evidence" in str(exc_info.value)

    def test_assessment_literals(self):
        """Test that assessment must be valid literal."""
        valid_assessments = [
            "well-supported",
            "partially-supported",
            "unsupported",
            "contradictory",
        ]

        for assessment in valid_assessments:
            cross_ref = CrossReference(
                claim="Test",
                claim_location="Test location",
                supporting_evidence=["Evidence"],
                contradictory_evidence=[],
                assessment=assessment,
            )
            assert cross_ref.assessment == assessment

        # Invalid assessment
        with pytest.raises(ValidationError) as exc_info:
            CrossReference(
                claim="Test",
                claim_location="Test location",
                supporting_evidence=["Evidence"],
                contradictory_evidence=[],
                assessment="invalid_assessment",
            )
        assert "Input should be" in str(exc_info.value)

    def test_json_serialization(self, sample_cross_reference):
        """Test JSON serialization and deserialization."""
        json_data = sample_cross_reference.model_dump()

        assert "claim" in json_data
        assert "claim_location" in json_data
        assert "supporting_evidence" in json_data
        assert "contradictory_evidence" in json_data
        assert "assessment" in json_data

        # Deserialize
        cross_ref_copy = CrossReference(**json_data)
        assert cross_ref_copy.claim == sample_cross_reference.claim
        assert cross_ref_copy.claim_location == sample_cross_reference.claim_location
        assert cross_ref_copy.assessment == sample_cross_reference.assessment


class TestWorkingMemory:
    """Tests for WorkingMemory model."""

    def test_valid_working_memory(self, sample_working_memory):
        """Test creating valid working memory."""
        assert sample_working_memory.agent_role == "HR"
        assert len(sample_working_memory.key_observations) == 5
        assert len(sample_working_memory.cross_references) == 1
        assert len(sample_working_memory.ambiguities) == 1

    def test_agent_role_validation(self):
        """Test that agent_role must be valid literal."""
        valid_roles = ["HR", "Tech", "Product", "Compliance"]

        for role in valid_roles:
            memory = WorkingMemory(
                agent_role=role,
                key_observations=[
                    KeyObservation(
                        category="Test",
                        observation="Obs 1",
                        evidence_location="Location 1",
                        strength_or_risk="strength",
                    ),
                    KeyObservation(
                        category="Test",
                        observation="Obs 2",
                        evidence_location="Location 2",
                        strength_or_risk="risk",
                    ),
                    KeyObservation(
                        category="Test",
                        observation="Obs 3",
                        evidence_location="Location 3",
                        strength_or_risk="strength",
                    ),
                ],
                cross_references=[],
                ambiguities=[],
            )
            assert memory.agent_role == role

        # Invalid role
        with pytest.raises(ValidationError) as exc_info:
            WorkingMemory(
                agent_role="invalid_agent",
                key_observations=[
                    KeyObservation(
                        category="Test",
                        observation="Obs",
                        evidence_location="Location",
                        strength_or_risk="strength",
                    ),
                ] * 3,
                cross_references=[],
                ambiguities=[],
            )
        # Pydantic's literal validation happens first, giving a different error message
        error_msg = str(exc_info.value).lower()
        assert "input should be" in error_msg and ("hr" in error_msg or "tech" in error_msg)

    def test_observation_count_validation(self):
        """Test that key_observations must be between 3 and 15."""
        # Valid: exactly 3 observations (minimum)
        memory1 = WorkingMemory(
            agent_role="HR",
            key_observations=[
                KeyObservation(
                    category="Test",
                    observation=f"Observation {i}",
                    evidence_location=f"Location {i}",
                    strength_or_risk="strength",
                )
                for i in range(3)
            ],
            cross_references=[],
            ambiguities=[],
        )
        assert len(memory1.key_observations) == 3

        # Valid: exactly 15 observations (maximum)
        memory2 = WorkingMemory(
            agent_role="HR",
            key_observations=[
                KeyObservation(
                    category="Test",
                    observation=f"Observation {i}",
                    evidence_location=f"Location {i}",
                    strength_or_risk="strength",
                )
                for i in range(15)
            ],
            cross_references=[],
            ambiguities=[],
        )
        assert len(memory2.key_observations) == 15

        # Invalid: too few observations
        with pytest.raises(ValidationError) as exc_info:
            WorkingMemory(
                agent_role="HR",
                key_observations=[
                    KeyObservation(
                        category="Test",
                        observation="Obs 1",
                        evidence_location="Location 1",
                        strength_or_risk="strength",
                    ),
                    KeyObservation(
                        category="Test",
                        observation="Obs 2",
                        evidence_location="Location 2",
                        strength_or_risk="risk",
                    ),
                ],
                cross_references=[],
                ambiguities=[],
            )
        # Pydantic validation happens before custom validator
        assert "list should have at least 3 items" in str(exc_info.value).lower()

        # Invalid: too many observations
        with pytest.raises(ValidationError) as exc_info:
            WorkingMemory(
                agent_role="HR",
                key_observations=[
                    KeyObservation(
                        category="Test",
                        observation=f"Observation {i}",
                        evidence_location=f"Location {i}",
                        strength_or_risk="strength",
                    )
                    for i in range(16)
                ],
                cross_references=[],
                ambiguities=[],
            )
        # Pydantic validation happens before custom validator
        assert "list should have at most 15 items" in str(exc_info.value).lower()

    def test_get_observations_for_category(self, sample_working_memory):
        """Test get_observations_for_category helper method."""
        # Get observations for existing category
        llm_obs = sample_working_memory.get_observations_for_category("LLM Agent Frameworks")
        assert len(llm_obs) == 2  # One strength, one risk

        # Get observations for category with no observations
        missing_obs = sample_working_memory.get_observations_for_category("Non-existent Category")
        assert len(missing_obs) == 0

    def test_get_cross_references_by_assessment(self, sample_working_memory):
        """Test get_cross_references_by_assessment helper method."""
        # Get well-supported cross-references
        strong_refs = sample_working_memory.get_cross_references_by_assessment("well-supported")
        assert len(strong_refs) == 1

        # Get contradictory cross-references (none exist)
        conflicting_refs = sample_working_memory.get_cross_references_by_assessment("contradictory")
        assert len(conflicting_refs) == 0

    def test_validate_against_rubric(self, sample_working_memory, sample_rubric):
        """Test validate_against_rubric category matching."""
        # All observations should match rubric categories
        rubric_categories = {cat.name for cat in sample_rubric.categories}

        for observation in sample_working_memory.key_observations:
            assert observation.category in rubric_categories

    def test_cross_references_optional(self):
        """Test that cross_references are optional."""
        memory = WorkingMemory(
            agent_role="HR",
            key_observations=[
                KeyObservation(
                    category="Test",
                    observation=f"Observation {i}",
                    evidence_location=f"Location {i}",
                    strength_or_risk="strength",
                )
                for i in range(3)
            ],
            cross_references=[],
            ambiguities=[],
        )
        assert len(memory.cross_references) == 0

    def test_ambiguities_optional(self):
        """Test that ambiguities are optional."""
        memory = WorkingMemory(
            agent_role="HR",
            key_observations=[
                KeyObservation(
                    category="Test",
                    observation=f"Observation {i}",
                    evidence_location=f"Location {i}",
                    strength_or_risk="strength",
                )
                for i in range(3)
            ],
            cross_references=[],
            ambiguities=[],
        )
        assert len(memory.ambiguities) == 0

    def test_json_serialization(self, sample_working_memory):
        """Test JSON serialization and deserialization."""
        json_data = sample_working_memory.model_dump()

        assert json_data["agent_role"] == "HR"
        assert len(json_data["key_observations"]) == 5
        assert "cross_references" in json_data
        assert "ambiguities" in json_data

        # Deserialize
        memory_copy = WorkingMemory(**json_data)
        assert memory_copy.agent_role == sample_working_memory.agent_role
        assert len(memory_copy.key_observations) == len(sample_working_memory.key_observations)

    def test_mixed_observation_types(self):
        """Test working memory with mixed observation types."""
        memory = WorkingMemory(
            agent_role="Tech",
            key_observations=[
                KeyObservation(category="Cat1", observation="Strength 1", evidence_location="Loc1", strength_or_risk="strength"),
                KeyObservation(category="Cat1", observation="Strength 2", evidence_location="Loc2", strength_or_risk="strength"),
                KeyObservation(category="Cat2", observation="Risk 1", evidence_location="Loc3", strength_or_risk="risk"),
                KeyObservation(category="Cat2", observation="Risk 2", evidence_location="Loc4", strength_or_risk="risk"),
                KeyObservation(category="Cat3", observation="Neutral 1", evidence_location="Loc5", strength_or_risk="neutral"),
            ],
            cross_references=[],
            ambiguities=["General ambiguity about depth"],
        )
        assert len(memory.key_observations) == 5

        # Count by type
        strengths = [obs for obs in memory.key_observations if obs.strength_or_risk == "strength"]
        risks = [obs for obs in memory.key_observations if obs.strength_or_risk == "risk"]
        neutrals = [obs for obs in memory.key_observations if obs.strength_or_risk == "neutral"]

        assert len(strengths) == 2
        assert len(risks) == 2
        assert len(neutrals) == 1

    def test_multiple_cross_references(self):
        """Test working memory with multiple cross-references."""
        memory = WorkingMemory(
            agent_role="Compliance",
            key_observations=[
                KeyObservation(
                    category="Test",
                    observation=f"Observation {i}",
                    evidence_location=f"Location {i}",
                    strength_or_risk="strength",
                )
                for i in range(5)
            ],
            cross_references=[
                CrossReference(
                    claim="Claim 1",
                    claim_location="Location 1",
                    supporting_evidence=["Evidence A"],
                    contradictory_evidence=[],
                    assessment="well-supported",
                ),
                CrossReference(
                    claim="Claim 2",
                    claim_location="Location 2",
                    supporting_evidence=["Evidence B", "Evidence C"],
                    contradictory_evidence=["Evidence D"],
                    assessment="contradictory",
                ),
                CrossReference(
                    claim="Claim 3",
                    claim_location="Location 3",
                    supporting_evidence=[],
                    contradictory_evidence=["Evidence E"],
                    assessment="unsupported",
                ),
            ],
            ambiguities=["Ambiguity 1", "Ambiguity 2"],
        )
        assert len(memory.cross_references) == 3
        assert len(memory.ambiguities) == 2
