"""
Rubric validation utilities for quality assurance.

This module provides validation functions to ensure generated rubrics
meet quality standards beyond basic structural validation.
"""

from typing import List, Tuple
from ..models.rubric import Rubric, RubricCategory


def validate_rubric_quality(rubric: Rubric) -> Tuple[bool, List[str]]:
    """
    Validate the overall quality of rubric content.

    Checks:
    - Category names are descriptive and specific
    - Scoring criteria descriptions are detailed
    - Each scoring criteria has at least 2 indicators
    - Indicators are specific and observable

    Args:
        rubric: The rubric to validate

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Generic category names to avoid
    generic_names = {"skills", "experience", "qualifications", "requirements",
                     "background", "competencies", "abilities", "knowledge"}

    for category in rubric.categories:
        # Check category name specificity
        if category.name.lower() in generic_names:
            issues.append(
                f"Category '{category.name}' is too generic. "
                "Use more specific names like 'Python Backend Development' "
                "instead of 'Skills'."
            )

        # Check each scoring criteria in the category
        for criteria in category.scoring_criteria:
            # Check description length
            if len(criteria.description) < 20:
                issues.append(
                    f"Scoring criteria description for score {criteria.score_value} in "
                    f"'{category.name}' is too brief (< 20 chars). "
                    "Provide detailed descriptions."
                )

            # Check indicator count
            if len(criteria.indicators) < 2:
                issues.append(
                    f"Scoring criteria for score {criteria.score_value} in '{category.name}' "
                    f"has only {len(criteria.indicators)} indicator(s). "
                    "Provide at least 2 indicators."
                )

            # Check indicator specificity
            vague_terms = {"good", "bad", "some", "many", "few", "experience"}
            for indicator in criteria.indicators:
                if any(term in indicator.lower() for term in vague_terms):
                    if len(indicator) < 15:  # Short and vague is problematic
                        issues.append(
                            f"Indicator '{indicator}' in '{category.name}' "
                            "appears vague. Use specific, observable criteria."
                        )

    return (len(issues) == 0, issues)


def validate_scoring_criteria_differentiation(category: RubricCategory) -> Tuple[bool, List[str]]:
    """
    Validate that scoring criteria show clear progression.

    Checks:
    - Higher scores have more/better indicators than lower scores
    - Descriptions are distinct and not overlapping
    - Clear progression from 0 → 3 → 5

    Args:
        category: The rubric category to validate

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Extract score values from the list of ScoringCriteria
    score_values = sorted([sc.score_value for sc in category.scoring_criteria])

    if score_values != [0, 3, 5]:
        issues.append(
            f"Category '{category.name}' has invalid score levels {score_values}. "
            "Expected [0, 3, 5]."
        )
        return (False, issues)

    # Build an index by score_value for easy lookup
    criteria_by_score = {sc.score_value: sc for sc in category.scoring_criteria}

    # Check indicator count progression
    indicator_counts = {
        score: len(criteria_by_score[score].indicators)
        for score in score_values
    }

    # Higher scores should generally have more indicators
    if indicator_counts[5] < indicator_counts[0]:
        issues.append(
            f"Category '{category.name}': Score 5 has fewer indicators "
            f"({indicator_counts[5]}) than score 0 ({indicator_counts[0]}). "
            "Higher scores should demonstrate more criteria."
        )

    # Check description distinctness
    descriptions = [
        criteria_by_score[score].description.lower()
        for score in score_values
    ]

    # Simple overlap check: descriptions shouldn't be too similar
    for i, desc1 in enumerate(descriptions):
        for j, desc2 in enumerate(descriptions[i+1:], start=i+1):
            # Check if descriptions are too similar (> 70% common words)
            words1 = set(desc1.split())
            words2 = set(desc2.split())
            if len(words1) > 0 and len(words2) > 0:
                overlap = len(words1 & words2) / max(len(words1), len(words2))
                if overlap > 0.7:
                    issues.append(
                        f"Category '{category.name}': Scoring descriptions "
                        f"for levels {score_values[i]} and {score_values[j]} are too similar. "
                        "Ensure clear differentiation."
                    )

    return (len(issues) == 0, issues)


def validate_weight_distribution(rubric: Rubric) -> Tuple[bool, List[str]]:
    """
    Validate that category weights are appropriately distributed.

    Checks:
    - Must-have categories have appropriate weights (0.20-0.35)
    - Non-must-have categories don't dominate (≤ 0.25)
    - No single category dominates (≤ 0.40)

    Args:
        rubric: The rubric to validate

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    for category in rubric.categories:
        # Check if single category dominates
        if category.weight > 0.40:
            issues.append(
                f"Category '{category.name}' has weight {category.weight:.2f} "
                "which is too high (> 0.40). Distribute weights more evenly."
            )

        # Check must-have category weights
        if category.is_must_have:
            if category.weight < 0.20:
                issues.append(
                    f"Must-have category '{category.name}' has weight "
                    f"{category.weight:.2f} which is too low (< 0.20). "
                    "Must-have categories should have significant weight."
                )
            elif category.weight > 0.35:
                issues.append(
                    f"Must-have category '{category.name}' has weight "
                    f"{category.weight:.2f} which is very high (> 0.35). "
                    "Consider if this weight is appropriate."
                )
        else:
            # Check non-must-have category weights
            if category.weight > 0.25:
                issues.append(
                    f"Non-must-have category '{category.name}' has weight "
                    f"{category.weight:.2f} which is high (> 0.25). "
                    "Consider if this should be a must-have category."
                )

    return (len(issues) == 0, issues)


def validate_rubric_completeness(rubric: Rubric) -> Tuple[bool, List[str]]:
    """
    Validate structural completeness of the rubric.

    Checks:
    - All categories have unique names
    - At least one category is marked as must-have
    - Rubric has 3-10 categories

    Args:
        rubric: The rubric to validate

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Check category count
    category_count = len(rubric.categories)
    if category_count < 3:
        issues.append(
            f"Rubric has only {category_count} category/categories. "
            "Minimum is 3 for comprehensive evaluation."
        )
    elif category_count > 10:
        issues.append(
            f"Rubric has {category_count} categories. "
            "Maximum is 10 to avoid complexity."
        )

    # Check unique category names
    category_names = [cat.name for cat in rubric.categories]
    if len(category_names) != len(set(category_names)):
        duplicates = [name for name in category_names if category_names.count(name) > 1]
        issues.append(
            f"Rubric has duplicate category names: {set(duplicates)}. "
            "All categories must have unique names."
        )

    # Check at least one must-have category exists
    must_have_count = sum(1 for cat in rubric.categories if cat.is_must_have)
    if must_have_count == 0:
        issues.append(
            "Rubric has no must-have categories. "
            "At least one category should be marked as must-have."
        )

    return (len(issues) == 0, issues)
