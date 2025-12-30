"""Unit tests for HR agent node - tests two-pass evaluation pattern."""

import pytest
from unittest.mock import Mock, patch

from src.nodes.hr_agent import hr_agent_node, _extract_working_memory, _evaluate_with_memory


class TestHRAgentNode:
    """Tests for HR agent node functions."""

    @patch("src.nodes.hr_agent.get_structured_llm")
    def test_extract_working_memory_success(
        self, mock_get_llm, sample_state_with_rubric, sample_working_memory
    ):
        """Test successful working memory extraction."""
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value=sample_working_memory)
        mock_get_llm.return_value = mock_llm

        result = _extract_working_memory(sample_state_with_rubric)

        assert result.agent_role == "HR"
        assert len(result.key_observations) >= 3
        mock_llm.invoke.assert_called_once()

    @patch("src.nodes.hr_agent.get_structured_llm")
    def test_evaluate_with_memory_success(
        self, mock_get_llm, sample_state_with_rubric, sample_working_memory, sample_hr_review
    ):
        """Test successful evaluation with working memory."""
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value=sample_hr_review)
        mock_get_llm.return_value = mock_llm

        result = _evaluate_with_memory(sample_state_with_rubric, sample_working_memory)

        assert result.agent_role == "HR"
        assert len(result.category_scores) > 0
        mock_llm.invoke.assert_called_once()

    @patch("src.nodes.hr_agent.get_structured_llm")
    def test_hr_agent_node_full_execution(
        self, mock_get_llm, sample_state_with_rubric, sample_working_memory, sample_hr_review
    ):
        """Test full two-pass HR agent execution."""
        # Mock both passes
        mock_llm = Mock()
        mock_llm.invoke = Mock(side_effect=[sample_working_memory, sample_hr_review])
        mock_get_llm.return_value = mock_llm

        result = hr_agent_node(sample_state_with_rubric)

        assert "panel_reviews" in result
        assert "agent_working_memory" in result
        assert len(result["panel_reviews"]) == 1
        assert result["panel_reviews"][0].agent_role == "HR"
        assert "HR" in result["agent_working_memory"]
        assert result["agent_working_memory"]["HR"].agent_role == "HR"

    def test_extract_working_memory_missing_resume(self):
        """Test error when resume is missing."""
        state = {"rubric": Mock()}

        with pytest.raises(ValueError) as exc_info:
            _extract_working_memory(state)
        assert "Resume is missing" in str(exc_info.value)

    def test_extract_working_memory_missing_rubric(self):
        """Test error when rubric is missing."""
        state = {"resume": "Test resume"}

        with pytest.raises(ValueError) as exc_info:
            _extract_working_memory(state)
        assert "Rubric is missing" in str(exc_info.value)
