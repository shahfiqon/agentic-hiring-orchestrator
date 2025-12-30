"""
Unit tests for orchestrator node.

Tests mock LLM calls to verify state updates, validation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch
from pydantic import ValidationError

from src.nodes.orchestrator import orchestrator_node
from src.models.rubric import Rubric


class TestOrchestratorNode:
    """Tests for orchestrator_node function."""

    @patch("src.nodes.orchestrator.get_structured_llm")
    def test_orchestrator_node_success(
        self, mock_get_llm, sample_state_initial, sample_rubric
    ):
        """Test successful rubric generation."""
        # Setup mock LLM
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value=sample_rubric)
        mock_get_llm.return_value = mock_llm

        # Execute node
        result = orchestrator_node(sample_state_initial)

        # Verify structure
        assert "rubric" in result
        assert isinstance(result["rubric"], Rubric)
        assert len(result["rubric"].categories) == 4

        # Verify LLM was called
        mock_llm.invoke.assert_called_once()

    @patch("src.nodes.orchestrator.get_structured_llm")
    def test_orchestrator_missing_job_description(self, mock_get_llm):
        """Test error handling when job_description is missing."""
        state = {"resume": "Test resume", "company_context": "Test context"}

        with pytest.raises(ValueError) as exc_info:
            orchestrator_node(state)
        assert "job_description" in str(exc_info.value)

    @patch("src.nodes.orchestrator.get_structured_llm")
    def test_orchestrator_missing_resume(self, mock_get_llm):
        """Test error handling when resume is missing."""
        state = {"job_description": "Test job", "company_context": "Test context"}

        with pytest.raises(ValueError) as exc_info:
            orchestrator_node(state)
        assert "resume" in str(exc_info.value)

    @patch("src.nodes.orchestrator.get_structured_llm")
    def test_orchestrator_graceful_missing_company_context(
        self, mock_get_llm, sample_rubric
    ):
        """Test that missing company_context is handled gracefully."""
        # Setup mock
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value=sample_rubric)
        mock_get_llm.return_value = mock_llm

        state = {"job_description": "Test job", "resume": "Test resume"}

        # Should not raise error
        result = orchestrator_node(state)
        assert "rubric" in result

    @patch("src.nodes.orchestrator.get_structured_llm")
    def test_orchestrator_llm_failure(self, mock_get_llm):
        """Test error handling when LLM fails."""
        # Setup mock to raise exception
        mock_llm = Mock()
        mock_llm.invoke = Mock(side_effect=Exception("LLM API error"))
        mock_get_llm.return_value = mock_llm

        state = {
            "job_description": "Test job",
            "resume": "Test resume",
            "company_context": "Test context",
        }

        with pytest.raises(Exception) as exc_info:
            orchestrator_node(state)
        assert "Failed to generate rubric" in str(exc_info.value)

    @patch("src.nodes.orchestrator.get_structured_llm")
    @patch("src.nodes.orchestrator.validate_rubric_completeness")
    @patch("src.nodes.orchestrator.validate_rubric_quality")
    @patch("src.nodes.orchestrator.validate_weight_distribution")
    def test_orchestrator_post_generation_validation(
        self,
        mock_weight_validation,
        mock_quality_validation,
        mock_completeness_validation,
        mock_get_llm,
        sample_state_initial,
        sample_rubric,
    ):
        """Test that post-generation validation runs."""
        # Setup mocks
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value=sample_rubric)
        mock_get_llm.return_value = mock_llm

        # Setup validation mocks to return warnings
        mock_completeness_validation.return_value = (False, ["Issue 1"])
        mock_quality_validation.return_value = (False, ["Issue 2"])
        mock_weight_validation.return_value = (False, ["Issue 3"])

        # Execute - should not raise even with validation warnings
        result = orchestrator_node(sample_state_initial)

        # Verify validation functions were called
        mock_completeness_validation.assert_called_once_with(sample_rubric)
        mock_quality_validation.assert_called_once_with(sample_rubric)
        mock_weight_validation.assert_called_once_with(sample_rubric)

        # Verify rubric was still returned
        assert "rubric" in result
