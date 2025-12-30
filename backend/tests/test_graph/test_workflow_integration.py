"""
Integration tests for full hiring workflow execution.

Tests mock all LLM calls and verify end-to-end state transitions
through orchestrator → panel agents → synthesis.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.graph import run_hiring_workflow
from src.models.rubric import Rubric
from src.models.review import AgentReview
from src.models.memory import WorkingMemory
from src.models.packet import DecisionPacket
from src.models.interview import InterviewPlan


class TestWorkflowIntegration:
    """Integration tests for full workflow execution."""

    @patch("src.nodes.orchestrator.get_structured_llm")
    @patch("src.nodes.hr_agent.get_structured_llm")
    @patch("src.nodes.tech_agent.get_structured_llm")
    @patch("src.nodes.compliance_agent.get_structured_llm")
    def test_end_to_end_workflow(
        self,
        mock_compliance_llm,
        mock_tech_llm,
        mock_hr_llm,
        mock_orchestrator_llm,
        sample_job_description,
        sample_resume_strong,
        sample_company_context,
        sample_rubric,
        sample_hr_review,
        sample_tech_review,
        sample_working_memory,
    ):
        """Test complete workflow from inputs to final outputs."""
        # Mock orchestrator
        orchestrator_mock = Mock()
        orchestrator_mock.invoke = Mock(return_value=sample_rubric)
        mock_orchestrator_llm.return_value = orchestrator_mock

        # Mock HR agent (two passes)
        hr_memory = sample_working_memory.model_copy()
        hr_memory.agent_role = "HR"
        hr_mock = Mock()
        hr_mock.invoke = Mock(side_effect=[hr_memory, sample_hr_review])
        mock_hr_llm.return_value = hr_mock

        # Mock Tech agent (two passes)
        tech_memory = sample_working_memory.model_copy()
        tech_memory.agent_role = "Tech"
        tech_mock = Mock()
        tech_mock.invoke = Mock(side_effect=[tech_memory, sample_tech_review])
        mock_tech_llm.return_value = tech_mock

        # Mock Compliance agent (two passes)
        compliance_memory = sample_working_memory.model_copy()
        compliance_memory.agent_role = "Compliance"
        compliance_review = sample_hr_review.model_copy()
        compliance_review.agent_role = "Compliance"
        compliance_mock = Mock()
        compliance_mock.invoke = Mock(side_effect=[compliance_memory, compliance_review])
        mock_compliance_llm.return_value = compliance_mock

        # Execute workflow
        final_state = run_hiring_workflow(
            job_description=sample_job_description,
            resume=sample_resume_strong,
            company_context=sample_company_context,
        )

        # Verify final state structure
        assert "rubric" in final_state
        assert "panel_reviews" in final_state
        assert "agent_working_memory" in final_state
        assert "decision_packet" in final_state
        assert "interview_plan" in final_state
        assert "disagreements" in final_state

        # Verify orchestrator output
        assert isinstance(final_state["rubric"], Rubric)
        assert len(final_state["rubric"].categories) > 0

        # Verify panel reviews
        assert len(final_state["panel_reviews"]) == 3  # HR, Tech, Compliance
        assert all(isinstance(r, AgentReview) for r in final_state["panel_reviews"])

        # Verify working memory is dict-shaped with uppercase role keys
        assert len(final_state["agent_working_memory"]) == 3
        assert isinstance(final_state["agent_working_memory"], dict)
        assert "HR" in final_state["agent_working_memory"]
        assert "Tech" in final_state["agent_working_memory"]
        assert "Compliance" in final_state["agent_working_memory"]
        assert all(isinstance(m, WorkingMemory) for m in final_state["agent_working_memory"].values())
        # Verify each WorkingMemory.agent_role matches its dict key
        for role_key, memory in final_state["agent_working_memory"].items():
            assert memory.agent_role == role_key

        # Verify decision packet
        assert isinstance(final_state["decision_packet"], DecisionPacket)
        assert 0.0 <= final_state["decision_packet"].weighted_average_score <= 5.0

        # Verify interview plan
        assert isinstance(final_state["interview_plan"], InterviewPlan)
        assert len(final_state["interview_plan"].questions) > 0

    @patch("src.nodes.orchestrator.get_structured_llm")
    def test_workflow_orchestrator_failure(
        self,
        mock_orchestrator_llm,
        sample_job_description,
        sample_resume_strong,
    ):
        """Test workflow handles orchestrator failure."""
        # Mock orchestrator to fail
        orchestrator_mock = Mock()
        orchestrator_mock.invoke = Mock(side_effect=Exception("LLM API error"))
        mock_orchestrator_llm.return_value = orchestrator_mock

        # Workflow should propagate the exception
        with pytest.raises(Exception) as exc_info:
            run_hiring_workflow(
                job_description=sample_job_description,
                resume=sample_resume_strong,
            )
        assert "LLM API error" in str(exc_info.value) or "Failed to generate rubric" in str(exc_info.value)

    def test_workflow_parallel_agent_execution(
        self,
        sample_job_description,
        sample_resume_strong,
    ):
        """Test that panel agents execute in parallel."""
        # This test would verify parallel execution timing
        # For now, just verify structure supports parallelism
        # Real implementation would use timing measurements

        # Mock all LLM calls
        with patch("src.nodes.orchestrator.get_structured_llm"), \
             patch("src.nodes.hr_agent.get_structured_llm"), \
             patch("src.nodes.tech_agent.get_structured_llm"), \
             patch("src.nodes.compliance_agent.get_structured_llm"):

            # Execution should complete successfully
            # Real test would verify timing shows parallelism
            pass

    @patch("src.nodes.orchestrator.get_structured_llm")
    @patch("src.nodes.hr_agent.get_structured_llm")
    @patch("src.nodes.tech_agent.get_structured_llm")
    @patch("src.nodes.compliance_agent.get_structured_llm")
    def test_workflow_metadata_tracking(
        self,
        mock_compliance_llm,
        mock_tech_llm,
        mock_hr_llm,
        mock_orchestrator_llm,
        sample_job_description,
        sample_resume_strong,
        sample_rubric,
        sample_hr_review,
        sample_working_memory,
    ):
        """Test that workflow tracks metadata correctly."""
        # Setup mocks (simplified)
        for mock in [mock_orchestrator_llm, mock_hr_llm, mock_tech_llm, mock_compliance_llm]:
            llm_mock = Mock()
            llm_mock.invoke = Mock(return_value=sample_rubric if mock == mock_orchestrator_llm else sample_working_memory)
            mock.return_value = llm_mock

        final_state = run_hiring_workflow(
            job_description=sample_job_description,
            resume=sample_resume_strong,
        )

        # Verify metadata exists
        assert "metadata" in final_state
        assert "workflow_start_time" in final_state["metadata"]
        assert "node_execution_order" in final_state["metadata"]

    @patch("src.nodes.orchestrator.get_structured_llm")
    @patch("src.nodes.hr_agent.get_structured_llm")
    def test_workflow_state_transitions(
        self,
        mock_hr_llm,
        mock_orchestrator_llm,
        sample_job_description,
        sample_resume_strong,
        sample_rubric,
        sample_working_memory,
        sample_hr_review,
    ):
        """Test state transitions between nodes."""
        # Mock orchestrator
        orchestrator_mock = Mock()
        orchestrator_mock.invoke = Mock(return_value=sample_rubric)
        mock_orchestrator_llm.return_value = orchestrator_mock

        # Mock HR agent
        hr_mock = Mock()
        hr_mock.invoke = Mock(side_effect=[sample_working_memory, sample_hr_review])
        mock_hr_llm.return_value = hr_mock

        # In real implementation, would trace state changes
        # between each node execution
        pass
