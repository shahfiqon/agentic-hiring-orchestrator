"""
Output formatting utilities for console display of workflow results.

Provides comprehensive formatting functions for all result types including
decision packets, interview plans, agent reviews, and working memories.
"""

from typing import Dict, Any, List
import json
from datetime import datetime

from src.models.packet import DecisionPacket
from src.models.interview import InterviewPlan, InterviewQuestion
from src.models.review import AgentReview
from src.models.memory import WorkingMemory
from src.models.rubric import Rubric


def format_rubric_summary(rubric: Rubric) -> str:
    """Format rubric with categories, weights, must-haves, and scoring criteria."""
    lines = []
    lines.append("┌─────────────────────────────────────────────────────────────┐")
    lines.append("│                      📋 RUBRIC SUMMARY                      │")
    lines.append("└─────────────────────────────────────────────────────────────┘")
    lines.append("")

    # Categories with weights
    lines.append("📊 Categories:")
    for category in rubric.categories:
        weight_pct = int(category.weight * 100)
        must_have = " [MUST-HAVE]" if category.is_must_have else ""
        lines.append(f"  • {category.name} (Weight: {weight_pct}%){must_have}")
        lines.append(f"    {category.description}")
        
        # Extract indicators from highest score level
        if category.scoring_criteria:
            highest_score = max(category.scoring_criteria, key=lambda x: x.score_value)
            if highest_score.indicators:
                indicators_preview = ', '.join(highest_score.indicators[:3])
                lines.append(f"    Key indicators (score {highest_score.score_value}): {indicators_preview}")
        lines.append("")

    # Must-haves (categories marked as must-have)
    must_have_categories = [c for c in rubric.categories if c.is_must_have]
    if must_have_categories:
        lines.append("🎯 Must-Have Categories:")
        for category in must_have_categories:
            lines.append(f"  • {category.name}")
            lines.append(f"    {category.description}")
        lines.append("")

    # Scoring scale (implicit 0-5 scale from ScoringCriteria)
    lines.append("📈 Scoring Scale:")
    lines.append(f"  • Range: 0 - 5")
    lines.append(f"  • 0 = No evidence, 3 = Solid/Adequate, 5 = Exceptional")
    lines.append("")

    return "\n".join(lines)


def format_agent_review(review: AgentReview, show_details: bool = True) -> str:
    """Format agent review with category scores, evidence, and assessment."""
    lines = []

    # Header
    lines.append(f"┌─────────────────────────────────────────────────────────────┐")
    lines.append(f"│  Agent: {review.agent_role.upper():<50} │")
    lines.append(f"└─────────────────────────────────────────────────────────────┘")
    lines.append("")

    # Category scores
    lines.append("📊 Category Scores:")
    for cat_score in review.category_scores:
        score_bar = "█" * int(cat_score.score) + "░" * (5 - int(cat_score.score))
        confidence_indicator = f"[{cat_score.confidence}]"
        lines.append(f"  • {cat_score.category_name}: {cat_score.score}/5.0 [{score_bar}] {confidence_indicator}")
        if show_details and cat_score.evidence:
            for evidence in cat_score.evidence[:2]:  # Show first 2 evidence items
                evidence_text = evidence.resume_text
                evidence_short = evidence_text[:80] + "..." if len(evidence_text) > 80 else evidence_text
                lines.append(f"    - {evidence_short}")
    lines.append("")

    # Overall assessment
    lines.append(f"Overall: {review.overall_assessment[:200]}...")
    lines.append("")

    # Strengths
    if review.top_strengths:
        lines.append("✅ Top Strengths:")
        for strength in review.top_strengths[:3]:
            lines.append(f"  • {strength}")
        lines.append("")

    # Risks
    if review.top_risks:
        lines.append("⚠️  Top Risks:")
        for risk in review.top_risks[:3]:
            lines.append(f"  • {risk}")
        lines.append("")

    # Follow-up questions
    if show_details and review.follow_up_questions:
        lines.append("❓ Follow-up Questions:")
        for q in review.follow_up_questions[:2]:
            lines.append(f"  • {q}")
        lines.append("")

    return "\n".join(lines)


def format_working_memory(memory: WorkingMemory, agent_role: str) -> str:
    """Format working memory with observations, cross-references, and analysis."""
    lines = []

    lines.append(f"💭 Working Memory - {agent_role.upper()}")
    lines.append("─" * 60)
    lines.append("")

    # Key observations
    if memory.key_observations:
        lines.append("🔍 Key Observations:")
        for obs in memory.key_observations[:5]:
            lines.append(f"  • {obs}")
        lines.append("")

    # Cross-references
    if memory.cross_references:
        lines.append("🔗 Cross-References:")
        for ref in memory.cross_references[:3]:
            lines.append(f"  • {ref}")
        lines.append("")

    # Timeline analysis
    if memory.timeline_analysis:
        lines.append("📅 Timeline Analysis:")
        for timeline in memory.timeline_analysis[:3]:
            lines.append(f"  • {timeline}")
        lines.append("")

    # Missing information
    if memory.missing_information:
        lines.append("❓ Missing Information:")
        for missing in memory.missing_information[:3]:
            lines.append(f"  • {missing}")
        lines.append("")

    # Ambiguities
    if memory.ambiguities:
        lines.append("⚠️  Ambiguities:")
        for amb in memory.ambiguities[:3]:
            lines.append(f"  • {amb}")
        lines.append("")

    return "\n".join(lines)


def format_decision_packet(packet: DecisionPacket) -> str:
    """Format decision packet with scores, recommendation, and analysis."""
    lines = []

    lines.append("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    lines.append("┃                    🎯 DECISION PACKET                       ┃")
    lines.append("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
    lines.append("")

    # Overall score and recommendation
    score_bar = "█" * int(packet.overall_fit_score * 2) + "░" * (10 - int(packet.overall_fit_score * 2))
    lines.append(f"📊 Overall Fit Score: {packet.overall_fit_score:.2f}/5.0 [{score_bar}]")

    # Recommendation with emoji
    rec_emoji = {
        "Hire": "✅",
        "Lean hire": "👍",
        "Lean no": "👎",
        "No": "❌"
    }
    if packet.recommendation:
        emoji = rec_emoji.get(packet.recommendation, "❓")
        lines.append(f"{emoji} Recommendation: {packet.recommendation}")
    else:
        lines.append("❓ Recommendation: Pending interview")
    lines.append(f"💪 Confidence: {packet.confidence}")
    lines.append("")

    # Strengths
    if packet.top_strengths:
        lines.append("✅ Top Strengths:")
        for strength in packet.top_strengths:
            lines.append(f"  • {strength}")
        lines.append("")

    # Risks
    if packet.top_risks:
        lines.append("⚠️  Top Risks:")
        for risk in packet.top_risks:
            lines.append(f"  • {risk}")
        lines.append("")

    # Must-have gaps
    if packet.must_have_gaps:
        lines.append("❌ Must-Have Gaps:")
        for gap in packet.must_have_gaps:
            lines.append(f"  • {gap}")
        lines.append("")

    # Disagreements
    if packet.disagreements:
        lines.append("🔥 Panel Disagreements:")
        for dis in packet.disagreements:
            lines.append(f"  • Category: {dis.category_name}")
            lines.append(f"    Scores: {', '.join([f'{a}: {s}' for a, s in dis.agent_scores.items()])}")
            lines.append(f"    Reason: {dis.reason}")
            lines.append(f"    Resolution: {dis.resolution_approach}")
        lines.append("")

    return "\n".join(lines)


def format_interview_plan(plan: InterviewPlan) -> str:
    """Format interview plan grouped by interviewer role."""
    lines = []

    lines.append("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    lines.append("┃                   📋 INTERVIEW PLAN                         ┃")
    lines.append("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
    lines.append("")

    # Priority areas
    if plan.priority_areas:
        lines.append("🎯 Priority Areas:")
        for area in plan.priority_areas:
            lines.append(f"  • {area}")
        lines.append("")

    # Time estimate
    if plan.time_estimate_minutes:
        lines.append(f"⏱️  Estimated Duration: {plan.time_estimate_minutes} minutes")
        lines.append("")

    # Display questions by interviewer
    for interviewer, questions in plan.questions_by_interviewer.items():
        lines.append(f"👤 Interviewer: {interviewer.upper()}")
        lines.append("─" * 60)
        lines.append("")

        for i, q in enumerate(questions, 1):
            lines.append(f"  Question {i}: {q.question}")
            lines.append(f"  Category: {q.category}")

            if q.what_to_listen_for:
                lines.append(f"  👂 Listen for: {', '.join(q.what_to_listen_for[:3])}")

            if q.red_flags:
                lines.append(f"  🚩 Red flags: {', '.join(q.red_flags[:2])}")

            if q.follow_up_prompts:
                lines.append(f"  💬 Follow-ups: {q.follow_up_prompts[0]}")

            lines.append("")

    return "\n".join(lines)


def format_workflow_results(result: Dict[str, Any], verbose: bool = False) -> str:
    """Master formatter combining all outputs into comprehensive report."""
    lines = []

    # Header
    lines.append("")
    lines.append("╔═══════════════════════════════════════════════════════════════╗")
    lines.append("║          AGENTIC HIRING WORKFLOW - EXECUTION REPORT           ║")
    lines.append("╚═══════════════════════════════════════════════════════════════╝")
    lines.append("")

    # Rubric
    if "rubric" in result:
        lines.append(format_rubric_summary(result["rubric"]))
        lines.append("")

    # Panel reviews (condensed unless verbose)
    if "panel_reviews" in result:
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                    👥 PANEL REVIEWS                         │")
        lines.append("└─────────────────────────────────────────────────────────────┘")
        lines.append("")

        for review in result["panel_reviews"]:
            lines.append(format_agent_review(review, show_details=verbose))
            lines.append("")

    # Working memories (only in verbose mode)
    if verbose and "agent_working_memory" in result:
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                  💭 WORKING MEMORIES                        │")
        lines.append("└─────────────────────────────────────────────────────────────┘")
        lines.append("")

        for agent_role, memory in result["agent_working_memory"].items():
            lines.append(format_working_memory(memory, agent_role))
            lines.append("")

    # Decision packet
    if "decision_packet" in result:
        lines.append(format_decision_packet(result["decision_packet"]))
        lines.append("")

    # Interview plan
    if "interview_plan" in result:
        lines.append(format_interview_plan(result["interview_plan"]))
        lines.append("")

    return "\n".join(lines)


def format_execution_metadata(
    duration_seconds: float,
    timestamp: datetime,
    job_desc_preview: str,
    resume_preview: str
) -> str:
    """Format execution metadata for display."""
    lines = []

    lines.append("┌─────────────────────────────────────────────────────────────┐")
    lines.append("│                  ⚙️  EXECUTION METADATA                     │")
    lines.append("└─────────────────────────────────────────────────────────────┘")
    lines.append("")
    lines.append(f"🕐 Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"⏱️  Duration: {duration_seconds:.2f} seconds")
    lines.append("")
    lines.append("📄 Job Description:")
    lines.append(f"  {job_desc_preview[:150]}...")
    lines.append("")
    lines.append("📄 Resume:")
    lines.append(f"  {resume_preview[:150]}...")
    lines.append("")

    return "\n".join(lines)


def format_validation_summary(
    has_all_fields: bool,
    panel_consistent: bool,
    disagreements_detected: bool,
    decision_valid: bool
) -> str:
    """Format validation summary."""
    lines = []

    lines.append("┌─────────────────────────────────────────────────────────────┐")
    lines.append("│                 ✓ VALIDATION SUMMARY                        │")
    lines.append("└─────────────────────────────────────────────────────────────┘")
    lines.append("")

    def status_icon(valid: bool) -> str:
        return "✅" if valid else "❌"

    lines.append(f"{status_icon(has_all_fields)} All required fields present")
    lines.append(f"{status_icon(panel_consistent)} Panel consistency verified")
    lines.append(f"{status_icon(disagreements_detected)} Disagreements properly detected")
    lines.append(f"{status_icon(decision_valid)} Decision packet valid")
    lines.append("")

    all_valid = all([has_all_fields, panel_consistent, disagreements_detected, decision_valid])
    if all_valid:
        lines.append("🎉 All validation checks passed!")
    else:
        lines.append("⚠️  Some validation checks failed - review output above")
    lines.append("")

    return "\n".join(lines)
