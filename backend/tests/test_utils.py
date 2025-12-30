"""
Test utility functions for creating valid test data and assertions.

This module provides helper functions for generating test objects with
configurable parameters and assertion utilities for comparing Pydantic models.
"""

from typing import List, Optional, Dict, Any
from src.models.rubric import Rubric, RubricCategory, ScoringCriteria
from src.models.review import AgentReview, CategoryScore, Evidence
from src.models.memory import WorkingMemory, KeyObservation, CrossReference


def create_valid_rubric(
    num_categories: int = 4,
    must_have_count: int = 2,
    ensure_weights_sum: bool = True,
) -> Rubric:
    """
    Create a valid rubric with configurable parameters.

    Args:
        num_categories: Number of rubric categories to create
        must_have_count: Number of must-have categories
        ensure_weights_sum: Whether to ensure weights sum to 1.0

    Returns:
        Valid Rubric object
    """
    if must_have_count > num_categories:
        raise ValueError("must_have_count cannot exceed num_categories")

    # Create scoring criteria
    scoring_criteria = [
        ScoringCriteria(score=i, description=f"Level {i} performance")
        for i in range(6)
    ]

    # Calculate weights
    if ensure_weights_sum:
        base_weight = 1.0 / num_categories
        weights = [base_weight] * num_categories
        # Adjust for floating point precision
        weights[-1] = 1.0 - sum(weights[:-1])
    else:
        weights = [0.25] * num_categories

    # Create categories
    categories = []
    for i in range(num_categories):
        category = RubricCategory(
            name=f"Category {i+1}",
            description=f"Description for category {i+1}",
            weight=weights[i],
            is_must_have=(i < must_have_count),
            scoring_criteria=scoring_criteria,
        )
        categories.append(category)

    return Rubric(categories=categories)


def create_valid_agent_review(
    agent_role: str = "hr_agent",
    category_names: Optional[List[str]] = None,
    scores: Optional[List[int]] = None,
    confidence: str = "high",
) -> AgentReview:
    """
    Create a valid agent review with configurable parameters.

    Args:
        agent_role: Role of the agent ("hr_agent", "tech_agent", "compliance_agent")
        category_names: List of category names to score
        scores: List of scores (must match length of category_names)
        confidence: Confidence level for all scores

    Returns:
        Valid AgentReview object
    """
    if category_names is None:
        category_names = ["Category 1", "Category 2", "Category 3"]

    if scores is None:
        scores = [4] * len(category_names)

    if len(scores) != len(category_names):
        raise ValueError("scores and category_names must have same length")

    category_scores = []
    for name, score in zip(category_names, scores):
        evidence = Evidence(
            text=f"Evidence for {name} with score {score}",
            interpretation=f"Interpretation of evidence for {name}",
        )
        category_score = CategoryScore(
            category_name=name,
            score=score,
            evidence=[evidence],
            confidence=confidence,
        )
        category_scores.append(category_score)

    return AgentReview(
        agent_role=agent_role,
        category_scores=category_scores,
        expected_rubric_categories=category_names,
    )


def create_valid_working_memory(
    agent_role: str = "hr_agent",
    num_observations: int = 5,
    num_cross_references: int = 2,
    num_ambiguities: int = 1,
    category_names: Optional[List[str]] = None,
) -> WorkingMemory:
    """
    Create valid working memory with configurable parameters.

    Args:
        agent_role: Role of the agent
        num_observations: Number of observations to create (3-15)
        num_cross_references: Number of cross-references
        num_ambiguities: Number of ambiguities
        category_names: List of category names for observations

    Returns:
        Valid WorkingMemory object
    """
    if not (3 <= num_observations <= 15):
        raise ValueError("num_observations must be between 3 and 15")

    if category_names is None:
        category_names = ["Category 1", "Category 2", "Category 3"]

    # Create observations
    observations = []
    for i in range(num_observations):
        category = category_names[i % len(category_names)]
        obs_type = "strength" if i % 2 == 0 else "gap"
        observation = KeyObservation(
            category_name=category,
            observation=f"Observation {i+1} for {category}",
            observation_type=obs_type,
        )
        observations.append(observation)

    # Create cross-references
    cross_references = []
    for i in range(num_cross_references):
        cross_ref = CrossReference(
            claim=f"Claim {i+1}",
            supporting_evidence=[f"Evidence A{i}", f"Evidence B{i}"],
            contradicting_evidence=[],
            assessment="strong_corroboration",
        )
        cross_references.append(cross_ref)

    # Create ambiguities
    ambiguities = [f"Ambiguity {i+1}" for i in range(num_ambiguities)]

    return WorkingMemory(
        agent_role=agent_role,
        observations=observations,
        cross_references=cross_references,
        ambiguities=ambiguities,
    )


def assert_rubric_equal(rubric1: Rubric, rubric2: Rubric, check_order: bool = False):
    """
    Assert that two rubrics are equal.

    Args:
        rubric1: First rubric
        rubric2: Second rubric
        check_order: Whether to check category order
    """
    assert len(rubric1.categories) == len(rubric2.categories)

    if check_order:
        categories1 = rubric1.categories
        categories2 = rubric2.categories
    else:
        categories1 = sorted(rubric1.categories, key=lambda c: c.name)
        categories2 = sorted(rubric2.categories, key=lambda c: c.name)

    for cat1, cat2 in zip(categories1, categories2):
        assert cat1.name == cat2.name
        assert cat1.description == cat2.description
        assert abs(cat1.weight - cat2.weight) < 0.001  # Floating point tolerance
        assert cat1.is_must_have == cat2.is_must_have
        assert len(cat1.scoring_criteria) == len(cat2.scoring_criteria)


def assert_agent_review_equal(review1: AgentReview, review2: AgentReview, check_order: bool = False):
    """
    Assert that two agent reviews are equal.

    Args:
        review1: First review
        review2: Second review
        check_order: Whether to check category score order
    """
    assert review1.agent_role == review2.agent_role
    assert len(review1.category_scores) == len(review2.category_scores)

    if check_order:
        scores1 = review1.category_scores
        scores2 = review2.category_scores
    else:
        scores1 = sorted(review1.category_scores, key=lambda s: s.category_name)
        scores2 = sorted(review2.category_scores, key=lambda s: s.category_name)

    for score1, score2 in zip(scores1, scores2):
        assert score1.category_name == score2.category_name
        assert score1.score == score2.score
        assert score1.confidence == score2.confidence
        assert len(score1.evidence) == len(score2.evidence)


def assert_working_memory_equal(memory1: WorkingMemory, memory2: WorkingMemory, check_order: bool = False):
    """
    Assert that two working memory objects are equal.

    Args:
        memory1: First memory
        memory2: Second memory
        check_order: Whether to check observation order
    """
    assert memory1.agent_role == memory2.agent_role
    assert len(memory1.observations) == len(memory2.observations)
    assert len(memory1.cross_references) == len(memory2.cross_references)
    assert len(memory1.ambiguities) == len(memory2.ambiguities)

    if not check_order:
        # Sort observations by category and observation text
        obs1 = sorted(memory1.observations, key=lambda o: (o.category_name, o.observation))
        obs2 = sorted(memory2.observations, key=lambda o: (o.category_name, o.observation))

        for o1, o2 in zip(obs1, obs2):
            assert o1.category_name == o2.category_name
            assert o1.observation == o2.observation
            assert o1.observation_type == o2.observation_type


def get_category_score_by_name(review: AgentReview, category_name: str) -> Optional[CategoryScore]:
    """
    Get a category score by name from an agent review.

    Args:
        review: Agent review to search
        category_name: Name of category to find

    Returns:
        CategoryScore if found, None otherwise
    """
    for score in review.category_scores:
        if score.category_name == category_name:
            return score
    return None


def get_observations_for_category(memory: WorkingMemory, category_name: str) -> List[KeyObservation]:
    """
    Get all observations for a specific category from working memory.

    Args:
        memory: Working memory to search
        category_name: Name of category to filter by

    Returns:
        List of observations for the category
    """
    return [obs for obs in memory.observations if obs.category_name == category_name]


def calculate_average_score(reviews: List[AgentReview], category_name: str) -> float:
    """
    Calculate average score across all reviews for a specific category.

    Args:
        reviews: List of agent reviews
        category_name: Name of category to average

    Returns:
        Average score for the category
    """
    scores = []
    for review in reviews:
        score = get_category_score_by_name(review, category_name)
        if score:
            scores.append(score.score)

    if not scores:
        raise ValueError(f"No scores found for category: {category_name}")

    return sum(scores) / len(scores)


def validate_state_structure(state: Dict[str, Any], expected_keys: List[str]):
    """
    Validate that a state dictionary has the expected keys.

    Args:
        state: State dictionary to validate
        expected_keys: List of keys that should be present

    Raises:
        AssertionError if any expected keys are missing
    """
    for key in expected_keys:
        assert key in state, f"Missing expected key: {key}"


def validate_review_coverage(review: AgentReview, rubric: Rubric):
    """
    Validate that an agent review covers all rubric categories.

    Args:
        review: Agent review to validate
        rubric: Rubric to check against

    Raises:
        AssertionError if any categories are missing
    """
    rubric_categories = {cat.name for cat in rubric.categories}
    review_categories = {score.category_name for score in review.category_scores}

    missing = rubric_categories - review_categories
    assert not missing, f"Review missing categories: {missing}"

    extra = review_categories - rubric_categories
    assert not extra, f"Review has extra categories: {extra}"
