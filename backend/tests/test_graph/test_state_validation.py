"""
Integration tests for state validation between workflow stages.

Tests validation checkpoints between orchestrator, panel agents, and synthesis.
"""

import pytest
from unittest.mock import Mock

from src.state import HiringWorkflowState, validate_panel_memory_consistency, StateValidationError


class TestStateValidation:
    """Tests for state validation between workflow stages."""

    def test_validate_panel_memory_consistency_success(
        self, sample_hr_review, sample_tech_review, sample_working_memory
    ):
        """Test successful validation when panel reviews and memory match."""
        hr_memory = sample_working_memory.model_copy()
        hr_memory.agent_role = "HR"

        tech_memory = sample_working_memory.model_copy()
        tech_memory.agent_role = "Tech"

        state = {
            "panel_reviews": [sample_hr_review, sample_tech_review],
            "agent_working_memory": {
                "HR": hr_memory,
                "Tech": tech_memory,
            },
        }

        # Should not raise
        validate_panel_memory_consistency(state)

    def test_validate_panel_memory_missing_agent(
        self, sample_hr_review, sample_tech_review, sample_working_memory
    ):
        """Test validation fails when agent review exists but memory is missing."""
        hr_memory = sample_working_memory.model_copy()
        hr_memory.agent_role = "HR"

        state = {
            "panel_reviews": [sample_hr_review, sample_tech_review],
            "agent_working_memory": {
                "HR": hr_memory,
                # Missing Tech memory
            },
        }

        with pytest.raises(StateValidationError) as exc_info:
            validate_panel_memory_consistency(state)
        assert "missing" in str(exc_info.value).lower() or "mismatch" in str(exc_info.value).lower()

    def test_validate_panel_memory_extra_agent(
        self, sample_hr_review, sample_working_memory
    ):
        """Test validation fails when memory exists without corresponding review."""
        hr_memory = sample_working_memory.model_copy()
        hr_memory.agent_role = "HR"

        tech_memory = sample_working_memory.model_copy()
        tech_memory.agent_role = "Tech"

        state = {
            "panel_reviews": [sample_hr_review],  # Only HR review
            "agent_working_memory": {
                "HR": hr_memory,
                "Tech": tech_memory,  # Extra memory
            },
        }

        with pytest.raises(StateValidationError) as exc_info:
            validate_panel_memory_consistency(state)
        assert "extra" in str(exc_info.value).lower() or "mismatch" in str(exc_info.value).lower()

    def test_validate_panel_memory_role_mismatch(
        self, sample_hr_review, sample_working_memory
    ):
        """Test validation fails when agent roles don't match."""
        # Create memory with wrong role
        wrong_memory = sample_working_memory.model_copy()
        wrong_memory.agent_role = "Tech"  # Mismatched role

        state = {
            "panel_reviews": [sample_hr_review],  # HR review
            "agent_working_memory": {
                "HR": wrong_memory,  # But Tech memory (role mismatch)
            },
        }

        # Validation should detect the mismatch
        with pytest.raises(StateValidationError):
            validate_panel_memory_consistency(state)

    def test_state_validation_checkpoint(self, sample_state_with_reviews):
        """Test validation checkpoint behavior in workflow."""
        # Test that validation function can be called as checkpoint
        # The validate function should not raise if state is valid

        # Should not raise if state is valid
        validate_panel_memory_consistency(sample_state_with_reviews)

        # If we get here, validation passed (no exception raised)
