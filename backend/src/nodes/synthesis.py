"""
Synthesis Node - Final aggregation and decision-making node.

This node:
1. Detects disagreements between panel agents
2. Enriches disagreements with working memory context
3. Creates a decision packet with aggregated scores and recommendations
4. Generates an interview plan to resolve ambiguities and disagreements
"""

import logging
from typing import Dict, List

from backend.src.state import HiringWorkflowState
from backend.src.models.packet import Disagreement, DecisionPacket
from backend.src.models.interview import InterviewPlan, InterviewQuestion
from backend.src.models.memory import WorkingMemory
from backend.src.models.review import AgentReview
from backend.src.models.rubric import Rubric

logger = logging.getLogger(__name__)


def _detect_disagreements(
    panel_reviews: List[AgentReview],
    rubric: Rubric
) -> List[Disagreement]:
    """
    Detect disagreements between agent scores across rubric categories.

    A disagreement is detected when the score delta (max - min) >= 1.0
    for a given category across all agents.

    Args:
        panel_reviews: List of agent reviews to compare
        rubric: Rubric defining evaluation categories

    Returns:
        List of Disagreement objects
    """
    logger.debug(f"Detecting disagreements across {len(panel_reviews)} panel reviews")

    disagreements = []

    # For each rubric category, collect agent scores
    for category in rubric.categories:
        category_name = category.name
        agent_scores = {}

        # Collect scores from all agents for this category
        for review in panel_reviews:
            agent_role = review.agent_role
            # Find the score for this category
            for score_item in review.category_scores:
                if score_item.category_name == category_name:
                    agent_scores[agent_role] = score_item.score
                    break

        # Skip if less than 2 agents scored this category
        if len(agent_scores) < 2:
            logger.debug(f"Skipping category '{category_name}' - only {len(agent_scores)} agent(s) scored it")
            continue

        # Calculate score delta
        scores = list(agent_scores.values())
        max_score = max(scores)
        min_score = min(scores)
        delta = max_score - min_score

        # Detect disagreement if delta >= 1.0
        if delta >= 1.0:
            logger.info(f"Disagreement detected in '{category_name}': delta={delta:.1f}")

            # Identify which agents scored high vs low
            high_agents = [role for role, score in agent_scores.items() if score == max_score]
            low_agents = [role for role, score in agent_scores.items() if score == min_score]

            # Generate initial reason
            reason = (
                f"Score conflict detected: {', '.join(high_agents)} scored {max_score}, "
                f"while {', '.join(low_agents)} scored {min_score} (delta: {delta:.1f}). "
                f"This suggests different priorities or interpretation of evidence."
            )

            # Suggest resolution approach
            if delta >= 2.0:
                resolution_approach = "Critical disagreement - requires interview validation and reference checks"
            else:
                resolution_approach = "Moderate disagreement - recommend targeted interview questions"

            disagreement = Disagreement(
                category_name=category_name,
                agent_scores=agent_scores,
                reason=reason,
                resolution_approach=resolution_approach
            )
            disagreements.append(disagreement)

    logger.info(f"Detected {len(disagreements)} disagreement(s)")
    return disagreements


def _enrich_disagreements_with_memory(
    disagreements: List[Disagreement],
    agent_working_memory: Dict[str, WorkingMemory]
) -> List[Disagreement]:
    """
    Enrich disagreements with context from agent working memory.

    Adds specific observations and cross-references from each agent's
    working memory to explain why they might have scored differently.

    Args:
        disagreements: List of disagreements to enrich
        agent_working_memory: Dict mapping agent role to WorkingMemory

    Returns:
        Enriched list of disagreements
    """
    logger.debug(f"Enriching {len(disagreements)} disagreements with working memory context")

    if not agent_working_memory:
        logger.warning("No working memory available - cannot enrich disagreements")
        return disagreements

    enriched_disagreements = []

    for disagreement in disagreements:
        category_name = disagreement.category_name
        enriched_reason = disagreement.reason + "\n\nWorking Memory Context:"

        # For each agent that scored this category, get their working memory
        for agent_role, score in disagreement.agent_scores.items():
            if agent_role not in agent_working_memory:
                logger.debug(f"No working memory found for {agent_role}")
                continue

            memory = agent_working_memory[agent_role]

            # Find observations related to this category
            relevant_observations = [
                obs for obs in memory.key_observations
                if category_name.lower() in obs.category.lower()
            ]

            # Add agent-specific context
            if relevant_observations:
                enriched_reason += f"\n- {agent_role} (score: {score}) noted:"
                for obs in relevant_observations[:2]:  # Limit to 2 most relevant
                    obs_text = f"{obs.observation}"
                    if obs.evidence_location:
                        obs_text += f" (from {obs.evidence_location})"
                    if obs.strength_or_risk:
                        obs_text += f" [{obs.strength_or_risk}]"
                    enriched_reason += f"\n  • {obs_text}"
            else:
                enriched_reason += f"\n- {agent_role} (score: {score}): No specific observations recorded for this category"

        # Create enriched disagreement
        enriched_disagreement = Disagreement(
            category_name=disagreement.category_name,
            agent_scores=disagreement.agent_scores,
            reason=enriched_reason,
            resolution_approach=disagreement.resolution_approach
        )
        enriched_disagreements.append(enriched_disagreement)

        logger.debug(f"Enriched disagreement for category '{category_name}'")

    return enriched_disagreements


def _calculate_weighted_average_score(
    category_name: str,
    panel_reviews: List[AgentReview]
) -> float:
    """
    Calculate the average score for a category across all agent reviews.

    Args:
        category_name: Name of the rubric category
        panel_reviews: List of agent reviews

    Returns:
        Average score for the category
    """
    scores = []

    for review in panel_reviews:
        for score_item in review.category_scores:
            if score_item.category_name == category_name:
                scores.append(score_item.score)
                break

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def _deduplicate_strengths_risks(items: List[str]) -> List[str]:
    """
    Deduplicate similar strengths or risks, prioritizing those mentioned by multiple agents.

    Args:
        items: List of strength or risk descriptions

    Returns:
        Deduplicated list (max 5 items)
    """
    # Count frequency of similar items (simple implementation)
    item_counts = {}
    for item in items:
        # Normalize for comparison
        key = item.lower().strip()
        if key not in item_counts:
            item_counts[key] = {"original": item, "count": 0}
        item_counts[key]["count"] += 1

    # Sort by frequency (descending) and take top 5
    sorted_items = sorted(
        item_counts.values(),
        key=lambda x: x["count"],
        reverse=True
    )

    return [item["original"] for item in sorted_items[:5]]


def _create_decision_packet(
    rubric: Rubric,
    panel_reviews: List[AgentReview],
    disagreements: List[Disagreement],
    agent_working_memory: Dict[str, WorkingMemory]
) -> DecisionPacket:
    """
    Create a decision packet aggregating panel reviews and scoring.

    Args:
        rubric: Evaluation rubric
        panel_reviews: List of agent reviews
        disagreements: List of detected disagreements
        agent_working_memory: Agent working memory

    Returns:
        DecisionPacket with aggregated decision
    """
    logger.debug("Creating decision packet")

    # Calculate overall fit score using weighted average
    overall_fit_score = 0.0
    total_weight = 0.0

    for category in rubric.categories:
        category_weight = category.weight
        avg_score = _calculate_weighted_average_score(category.name, panel_reviews)

        overall_fit_score += category_weight * avg_score
        total_weight += category_weight

        logger.debug(f"Category '{category.name}': avg_score={avg_score:.2f}, weight={category_weight}")

    if total_weight > 0:
        overall_fit_score = round(overall_fit_score / total_weight, 1)

    logger.info(f"Calculated overall fit score: {overall_fit_score}")

    # Determine confidence level
    num_disagreements = len(disagreements)
    if num_disagreements == 0:
        confidence = "high"
    elif num_disagreements <= 2:
        confidence = "medium"
    else:
        confidence = "low"

    logger.debug(f"Confidence level: {confidence} ({num_disagreements} disagreements)")

    # Aggregate top strengths
    all_strengths = []
    for review in panel_reviews:
        all_strengths.extend(review.top_strengths)

    top_strengths = _deduplicate_strengths_risks(all_strengths)
    logger.debug(f"Aggregated {len(top_strengths)} top strengths")

    # Aggregate top risks
    all_risks = []
    for review in panel_reviews:
        all_risks.extend(review.top_risks)

    top_risks = _deduplicate_strengths_risks(all_risks)
    logger.debug(f"Aggregated {len(top_risks)} top risks")

    # Identify must-have gaps
    must_have_gaps = []
    for category in rubric.categories:
        if category.is_must_have:
            avg_score = _calculate_weighted_average_score(category.name, panel_reviews)
            if avg_score < 3.0:
                gap_description = (
                    f"Must-have category '{category.name}' scored below threshold "
                    f"(avg: {avg_score:.1f}/5.0)"
                )
                must_have_gaps.append(gap_description)
                logger.warning(f"Must-have gap detected: {gap_description}")

    # Determine recommendation
    if overall_fit_score >= 4.0 and not must_have_gaps:
        recommendation = "Hire"
    elif overall_fit_score >= 3.5 and not must_have_gaps:
        recommendation = "Lean hire"
    elif overall_fit_score < 2.5 or must_have_gaps:
        if must_have_gaps:
            recommendation = "No"
        else:
            recommendation = "Lean no"
    else:
        recommendation = None  # Withhold recommendation pending interview

    logger.info(f"Recommendation: {recommendation}")

    # Create decision packet
    decision_packet = DecisionPacket(
        role_title=rubric.role_title,
        overall_fit_score=overall_fit_score,
        confidence=confidence,
        top_strengths=top_strengths,
        top_risks=top_risks,
        must_have_gaps=must_have_gaps,
        recommendation=recommendation,
        disagreements=disagreements
    )

    return decision_packet


def _create_interview_plan(
    rubric: Rubric,
    panel_reviews: List[AgentReview],
    disagreements: List[Disagreement],
    agent_working_memory: Dict[str, WorkingMemory]
) -> InterviewPlan:
    """
    Generate an interview plan with role-specific questions.

    Questions are generated from:
    - Working memory ambiguities
    - Working memory missing information
    - Contradictory cross-references
    - Disagreements between agents

    Args:
        rubric: Evaluation rubric
        panel_reviews: List of agent reviews
        disagreements: List of disagreements
        agent_working_memory: Agent working memory

    Returns:
        InterviewPlan with questions by interviewer
    """
    logger.debug("Creating interview plan")

    # Initialize questions by interviewer
    questions_by_interviewer: Dict[str, List[InterviewQuestion]] = {}

    # Get all agent roles from panel reviews
    agent_roles = [review.agent_role for review in panel_reviews]
    for role in agent_roles:
        questions_by_interviewer[role] = []

    # Track priority areas
    priority_areas = []

    # 1. Generate questions from must-have gaps
    for category in rubric.categories:
        if category.is_must_have:
            avg_score = _calculate_weighted_average_score(category.name, panel_reviews)
            if avg_score < 3.0:
                priority_areas.append(category.name)

                # Assign to most relevant interviewer
                for review in panel_reviews:
                    for score_item in review.category_scores:
                        if score_item.category_name == category.name and score_item.score < 3:
                            question = InterviewQuestion(
                                question=f"This role requires strong {category.name}. Can you walk me through specific examples where you've demonstrated this?",
                                category=category.name,
                                interviewer_role=review.agent_role,
                                what_to_listen_for=["Concrete examples", "Measurable outcomes", "Clear ownership", "Technical depth"],
                                red_flags=["Vague responses", "Lack of specifics", "Team achievements without personal contribution"]
                            )
                            if len(questions_by_interviewer[review.agent_role]) < 7:
                                questions_by_interviewer[review.agent_role].append(question)
                            break

    # 2. Generate questions from disagreements
    for disagreement in disagreements:
        category_name = disagreement.category_name
        priority_areas.append(category_name)

        # Find which agent scored lowest - they should ask the question
        lowest_score = min(disagreement.agent_scores.values())
        lowest_agent = [role for role, score in disagreement.agent_scores.items() if score == lowest_score][0]

        question = InterviewQuestion(
            question=f"Tell me about your experience with {category_name}. What's your approach and what results have you achieved?",
            category=category_name,
            interviewer_role=lowest_agent,
            what_to_listen_for=["Detailed examples", "Specific metrics", "Clear methodology", "Lessons learned"],
            red_flags=["Inconsistent with resume", "Surface-level understanding", "Unable to discuss trade-offs"]
        )

        if len(questions_by_interviewer[lowest_agent]) < 7:
            questions_by_interviewer[lowest_agent].append(question)

    # 3. Generate questions from working memory (ambiguities, gaps, contradictions)
    for agent_role, memory in agent_working_memory.items():
        if agent_role not in questions_by_interviewer:
            continue

        # From ambiguities
        for ambiguity in memory.ambiguities[:2]:  # Limit to 2
            question = InterviewQuestion(
                question=f"Can you clarify: {ambiguity}?",
                category="Clarification",
                interviewer_role=agent_role,
                what_to_listen_for=["Specific examples", "Clear ownership", "Concrete details", "Timeline"],
                red_flags=["Vague answers", "Deflection", "Inconsistency with resume"]
            )
            if len(questions_by_interviewer[agent_role]) < 7:
                questions_by_interviewer[agent_role].append(question)

        # From missing information
        for missing_info in memory.missing_information[:2]:  # Limit to 2
            question = InterviewQuestion(
                question=f"I noticed your resume doesn't mention {missing_info}. Can you speak to your experience in this area?",
                category="Gap Exploration",
                interviewer_role=agent_role,
                what_to_listen_for=["Honest acknowledgment", "Related experience", "Learning approach", "Transferable skills"],
                red_flags=["Defensive response", "Exaggeration", "Avoidance", "Overconfidence"]
            )
            if len(questions_by_interviewer[agent_role]) < 7:
                questions_by_interviewer[agent_role].append(question)

        # From contradictions (using cross_references with contradictory assessment)
        contradictory_refs = [
            ref for ref in memory.cross_references
            if ref.assessment == "contradictory" or (ref.contradictory_evidence and len(ref.contradictory_evidence) > 0)
        ]
        for ref in contradictory_refs[:1]:  # Limit to 1
            question = InterviewQuestion(
                question=f"Your resume states '{ref.claim}'. Can you walk me through specific examples?",
                category="Claim Verification",
                interviewer_role=agent_role,
                what_to_listen_for=["Detailed timeline", "Specific metrics", "Clear outcomes", "Consistency"],
                red_flags=["Lack of specifics", "Timeline mismatch", "Backtracking", "Contradictory details"]
            )
            if len(questions_by_interviewer[agent_role]) < 7:
                questions_by_interviewer[agent_role].append(question)

    # Calculate time estimate (15 minutes per interviewer)
    total_questions = sum(len(questions) for questions in questions_by_interviewer.values())
    time_estimate_minutes = len(questions_by_interviewer) * 15

    logger.info(f"Generated {total_questions} interview questions across {len(questions_by_interviewer)} interviewers")
    logger.debug(f"Estimated interview time: {time_estimate_minutes} minutes")

    # Deduplicate priority areas
    priority_areas = list(set(priority_areas))

    interview_plan = InterviewPlan(
        questions_by_interviewer=questions_by_interviewer,
        priority_areas=priority_areas,
        time_estimate_minutes=time_estimate_minutes
    )

    return interview_plan


def synthesis_node(state: HiringWorkflowState) -> Dict:
    """
    Synthesis node - Final aggregation and decision-making.

    This node:
    1. Detects disagreements between panel agents
    2. Enriches disagreements with working memory context
    3. Creates a decision packet with aggregated scores
    4. Generates an interview plan to resolve ambiguities

    Args:
        state: Current workflow state

    Returns:
        State update with disagreements, decision_packet, and interview_plan
    """
    logger.info("=== Starting Synthesis Node ===")

    try:
        # Extract required fields from state
        rubric = state.get("rubric")
        panel_reviews = state.get("panel_reviews", [])
        agent_working_memory = state.get("agent_working_memory", {})

        # Validate inputs
        if not rubric:
            logger.error("Rubric not found in state")
            raise ValueError("Rubric is required for synthesis")

        if not panel_reviews:
            logger.error("No panel reviews found in state")
            raise ValueError("Panel reviews are required for synthesis")

        if not agent_working_memory:
            logger.warning("No agent working memory found - synthesis will run in degraded mode")

        logger.info(f"Processing {len(panel_reviews)} panel reviews")

        # Step 1: Detect disagreements
        logger.info("Step 1: Detecting disagreements")
        disagreements = _detect_disagreements(panel_reviews, rubric)

        # Step 2: Enrich disagreements with working memory
        logger.info("Step 2: Enriching disagreements with working memory")
        disagreements = _enrich_disagreements_with_memory(disagreements, agent_working_memory)

        # Step 3: Create decision packet
        logger.info("Step 3: Creating decision packet")
        decision_packet = _create_decision_packet(
            rubric,
            panel_reviews,
            disagreements,
            agent_working_memory
        )

        # Step 4: Create interview plan
        logger.info("Step 4: Creating interview plan")
        interview_plan = _create_interview_plan(
            rubric,
            panel_reviews,
            disagreements,
            agent_working_memory
        )

        # Log summary
        logger.info(f"Synthesis complete:")
        logger.info(f"  - Disagreements: {len(disagreements)}")
        logger.info(f"  - Overall fit score: {decision_packet.overall_fit_score}")
        logger.info(f"  - Confidence: {decision_packet.confidence}")
        logger.info(f"  - Recommendation: {decision_packet.recommendation}")
        logger.info(f"  - Interview questions: {sum(len(q) for q in interview_plan.questions_by_interviewer.values())}")

        # Return state update
        return {
            "disagreements": disagreements,
            "decision_packet": decision_packet,
            "interview_plan": interview_plan
        }

    except Exception as e:
        logger.error(f"Error in synthesis node: {str(e)}", exc_info=True)
        raise
