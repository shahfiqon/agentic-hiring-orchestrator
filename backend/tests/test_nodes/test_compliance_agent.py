"""Unit tests for compliance agent node."""

import pytest
from unittest.mock import Mock, patch

from src.nodes.compliance_agent import compliance_agent_node


class TestComplianceAgentNode:
    """Tests for compliance agent node functions."""

    @patch("src.nodes.compliance_agent.get_structured_llm")
    def test_compliance_agent_node_success(
        self, mock_get_llm, sample_state_with_rubric, sample_working_memory
    ):
        """Test full compliance agent execution."""
        # Create compliance-specific mocks
        compliance_memory = sample_working_memory.model_copy()
        compliance_memory.agent_role = "Compliance"

        compliance_review = Mock()
        compliance_review.agent_role = "Compliance"
        compliance_review.category_scores = []

        mock_llm = Mock()
        mock_llm.invoke = Mock(side_effect=[compliance_memory, compliance_review])
        mock_get_llm.return_value = mock_llm

        result = compliance_agent_node(sample_state_with_rubric)

        assert "panel_reviews" in result
        assert "agent_working_memory" in result
        assert result["panel_reviews"][0].agent_role == "Compliance"
        assert "Compliance" in result["agent_working_memory"]
        assert result["agent_working_memory"]["Compliance"].agent_role == "Compliance"
