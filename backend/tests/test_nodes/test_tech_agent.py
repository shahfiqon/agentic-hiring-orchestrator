"""Unit tests for tech agent node - similar structure to HR agent."""

import pytest
from unittest.mock import Mock, patch

from src.nodes.tech_agent import tech_agent_node, _extract_working_memory, _evaluate_with_memory


class TestTechAgentNode:
    """Tests for tech agent node functions."""

    @patch("src.nodes.tech_agent.get_structured_llm")
    def test_tech_agent_node_success(
        self, mock_get_llm, sample_state_with_rubric, sample_working_memory, sample_tech_review
    ):
        """Test full tech agent execution."""
        # Modify working memory for tech agent
        tech_memory = sample_working_memory.model_copy()
        tech_memory.agent_role = "Tech"

        mock_llm = Mock()
        mock_llm.invoke = Mock(side_effect=[tech_memory, sample_tech_review])
        mock_get_llm.return_value = mock_llm

        result = tech_agent_node(sample_state_with_rubric)

        assert "panel_reviews" in result
        assert "agent_working_memory" in result
        assert result["panel_reviews"][0].agent_role == "Tech"
        assert "Tech" in result["agent_working_memory"]
        assert result["agent_working_memory"]["Tech"].agent_role == "Tech"

    @patch("src.nodes.tech_agent.get_structured_llm")
    def test_tech_agent_technical_focus(
        self, mock_get_llm, sample_state_with_rubric, sample_working_memory, sample_tech_review
    ):
        """Test that tech agent focuses on technical areas."""
        # Create proper Tech working memory
        tech_memory = sample_working_memory.model_copy()
        tech_memory.agent_role = "Tech"

        mock_llm = Mock()
        mock_llm.invoke = Mock(side_effect=[tech_memory, sample_tech_review])
        mock_get_llm.return_value = mock_llm

        result = tech_agent_node(sample_state_with_rubric)

        # Verify tech agent role
        assert result["panel_reviews"][0].agent_role == "Tech"
        assert "Tech" in result["agent_working_memory"]
