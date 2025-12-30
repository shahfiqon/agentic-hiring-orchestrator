"""
Unit tests for rubric models (Rubric, RubricCategory, ScoringCriteria).

Tests cover validation logic, edge cases, helper methods, and serialization.
"""

import pytest
from pydantic import ValidationError

from src.models.rubric import Rubric, RubricCategory, ScoringCriteria
from tests.test_utils import create_valid_rubric


class TestScoringCriteria:
    """Tests for ScoringCriteria model."""

    def test_valid_scoring_criteria(self):
        """Test creating valid scoring criteria."""
        criteria = ScoringCriteria(
            score_value=3,
            description="Solid experience, can work independently",
            indicators=["Independent work", "Production experience"],
        )
        assert criteria.score_value == 3
        assert "Solid experience" in criteria.description

    def test_score_range_validation(self):
        """Test that scores must be in range 0-5."""
        # Valid scores
        for score in range(6):
            criteria = ScoringCriteria(score_value=score, description=f"Level {score}", indicators=[f"Indicator {score}"])
            assert criteria.score_value == score

        # Invalid scores
        with pytest.raises(ValidationError) as exc_info:
            ScoringCriteria(score_value=-1, description="Invalid")
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ScoringCriteria(score_value=6, description="Invalid")
        assert "less than or equal to 5" in str(exc_info.value)

    def test_non_empty_description(self):
        """Test that description cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            ScoringCriteria(score_value=3, description="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        criteria = ScoringCriteria(score_value=4, description="Expert level", indicators=["Mentorship", "Advanced implementations"])
        json_data = criteria.model_dump()

        assert json_data["score_value"] == 4
        assert json_data["description"] == "Expert level"

        # Deserialize
        criteria_copy = ScoringCriteria(**json_data)
        assert criteria_copy.score_value == criteria.score_value
        assert criteria_copy.description == criteria.description


class TestRubricCategory:
    """Tests for RubricCategory model."""

    def test_valid_rubric_category(self, sample_scoring_criteria):
        """Test creating valid rubric category."""
        category = RubricCategory(
            name="LLM Agent Frameworks",
            description="Experience with agentic orchestration",
            weight=0.3,
            is_must_have=True,
            scoring_criteria=sample_scoring_criteria,
        )
        assert category.name == "LLM Agent Frameworks"
        assert category.weight == 0.3
        assert category.is_must_have is True
        assert len(category.scoring_criteria) == 6

    def test_weight_range_validation(self, sample_scoring_criteria):
        """Test that weight must be in range 0-1."""
        # Valid weights
        for weight in [0.0, 0.25, 0.5, 0.75, 1.0]:
            category = RubricCategory(
                name="Test",
                description="Test category",
                weight=weight,
                is_must_have=False,
                scoring_criteria=sample_scoring_criteria,
            )
            assert category.weight == weight

        # Invalid weights
        with pytest.raises(ValidationError) as exc_info:
            RubricCategory(
                name="Test",
                description="Test",
                weight=-0.1,
                is_must_have=False,
                scoring_criteria=sample_scoring_criteria,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            RubricCategory(
                name="Test",
                description="Test",
                weight=1.1,
                is_must_have=False,
                scoring_criteria=sample_scoring_criteria,
            )
        assert "less than or equal to 1" in str(exc_info.value)

    def test_scoring_criteria_count_validation(self, sample_scoring_criteria):
        """Test that category must have at least 3 scoring criteria."""
        # Valid: multiple criteria
        category = RubricCategory(
            name="Test",
            description="Test",
            weight=0.5,
            is_must_have=False,
            scoring_criteria=sample_scoring_criteria,
        )
        assert len(category.scoring_criteria) == 6

        # Invalid: less than 3 criteria
        with pytest.raises(ValidationError) as exc_info:
            RubricCategory(
                name="Test",
                description="Test",
                weight=0.5,
                is_must_have=False,
                scoring_criteria=[
                    ScoringCriteria(score_value=0, description="Level 0", indicators=["None"]),
                    ScoringCriteria(score_value=3, description="Level 3", indicators=["Some"]),
                ],
            )
        assert "at least 3" in str(exc_info.value).lower() and "scoring" in str(exc_info.value).lower()

    def test_unique_score_values_validation(self):
        """Test that scoring criteria must have unique score values."""
        # Valid: unique scores
        unique_criteria = [
            ScoringCriteria(score_value=0, description="Level 0", indicators=["Indicator 0"]),
            ScoringCriteria(score_value=1, description="Level 1", indicators=["Indicator 1"]),
            ScoringCriteria(score_value=2, description="Level 2", indicators=["Indicator 2"]),
        ]
        category = RubricCategory(
            name="Test",
            description="Test",
            weight=0.5,
            is_must_have=False,
            scoring_criteria=unique_criteria,
        )
        assert len(category.scoring_criteria) == 3

        # Invalid: duplicate scores
        duplicate_criteria = [
            ScoringCriteria(score_value=0, description="Level 0", indicators=["Indicator 0"]),
            ScoringCriteria(score_value=1, description="Level 1", indicators=["Indicator 1"]),
            ScoringCriteria(score_value=1, description="Duplicate Level 1", indicators=["Duplicate indicator"]),
        ]
        with pytest.raises(ValidationError) as exc_info:
            RubricCategory(
                name="Test",
                description="Test",
                weight=0.5,
                is_must_have=False,
                scoring_criteria=duplicate_criteria,
            )
        assert "duplicate score values" in str(exc_info.value).lower()

    def test_json_serialization(self, sample_scoring_criteria):
        """Test JSON serialization and deserialization."""
        category = RubricCategory(
            name="Technical Skills",
            description="Core technical competencies",
            weight=0.4,
            is_must_have=True,
            scoring_criteria=sample_scoring_criteria,
        )
        json_data = category.model_dump()

        assert json_data["name"] == "Technical Skills"
        assert json_data["weight"] == 0.4
        assert json_data["is_must_have"] is True
        assert len(json_data["scoring_criteria"]) == 6

        # Deserialize
        category_copy = RubricCategory(**json_data)
        assert category_copy.name == category.name
        assert category_copy.weight == category.weight


class TestRubric:
    """Tests for Rubric model."""

    def test_valid_rubric(self, sample_rubric):
        """Test creating valid rubric."""
        assert len(sample_rubric.categories) == 4
        total_weight = sum(cat.weight for cat in sample_rubric.categories)
        assert abs(total_weight - 1.0) < 0.001  # Floating point tolerance

    def test_weights_sum_validation(self, sample_scoring_criteria):
        """Test that category weights must sum to 1.0."""
        # Valid: weights sum to 1.0
        valid_categories = [
            RubricCategory(
                name="Cat1", description="D1", weight=0.5,
                is_must_have=True, scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Cat2", description="D2", weight=0.5,
                is_must_have=False, scoring_criteria=sample_scoring_criteria,
            ),
        ]
        rubric = Rubric(role_title="Test Role", categories=valid_categories)
        assert len(rubric.categories) == 2

        # Invalid: weights sum to 0.9
        invalid_categories = [
            RubricCategory(
                name="Cat1", description="D1", weight=0.4,
                is_must_have=True, scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Cat2", description="D2", weight=0.5,
                is_must_have=False, scoring_criteria=sample_scoring_criteria,
            ),
        ]
        with pytest.raises(ValidationError) as exc_info:
            Rubric(role_title="Test Role", categories=invalid_categories)
        assert "Category weights must sum to 1.0" in str(exc_info.value)

        # Invalid: weights sum to 1.1
        invalid_categories2 = [
            RubricCategory(
                name="Cat1", description="D1", weight=0.6,
                is_must_have=True, scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Cat2", description="D2", weight=0.5,
                is_must_have=False, scoring_criteria=sample_scoring_criteria,
            ),
        ]
        with pytest.raises(ValidationError) as exc_info:
            Rubric(role_title="Test Role", categories=invalid_categories2)
        assert "Category weights must sum to 1.0" in str(exc_info.value)

    def test_must_have_validation(self, sample_scoring_criteria):
        """Test that rubric must have at least one must-have category."""
        # Valid: has must-have categories
        valid_categories = [
            RubricCategory(
                name="Cat1", description="D1", weight=0.5,
                is_must_have=True, scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Cat2", description="D2", weight=0.5,
                is_must_have=False, scoring_criteria=sample_scoring_criteria,
            ),
        ]
        rubric = Rubric(role_title="Test Role", categories=valid_categories)
        assert any(cat.is_must_have for cat in rubric.categories)

        # Invalid: no must-have categories
        invalid_categories = [
            RubricCategory(
                name="Cat1", description="D1", weight=0.5,
                is_must_have=False, scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Cat2", description="D2", weight=0.5,
                is_must_have=False, scoring_criteria=sample_scoring_criteria,
            ),
        ]
        with pytest.raises(ValidationError) as exc_info:
            Rubric(role_title="Test Role", categories=invalid_categories)
        assert "must" in str(exc_info.value).lower() and "have" in str(exc_info.value).lower()

    def test_get_category_by_name(self, sample_rubric):
        """Test get_category_by_name helper method."""
        # Find existing category
        category = sample_rubric.get_category_by_name("LLM Agent Frameworks")
        assert category is not None
        assert category.name == "LLM Agent Frameworks"
        assert category.is_must_have is True

        # Try to find non-existent category
        missing = sample_rubric.get_category_by_name("Non-existent Category")
        assert missing is None

    def test_unique_category_names_validation(self, sample_scoring_criteria):
        """Test that category names should be unique (currently not enforced)."""
        # Valid: unique names
        valid_categories = [
            RubricCategory(
                name="Cat1", description="D1", weight=0.5,
                is_must_have=True, scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Cat2", description="D2", weight=0.5,
                is_must_have=False, scoring_criteria=sample_scoring_criteria,
            ),
        ]
        rubric = Rubric(role_title="Test Role", categories=valid_categories)
        assert len(rubric.categories) == 2

        # Note: The Rubric model currently doesn't enforce unique category names
        # This is by design - duplicates are allowed but not recommended
        # If duplicate validation is needed in the future, add a model_validator
        duplicate_categories = [
            RubricCategory(
                name="Cat1", description="D1", weight=0.5,
                is_must_have=True, scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Cat1", description="D2", weight=0.5,
                is_must_have=False, scoring_criteria=sample_scoring_criteria,
            ),
        ]
        # Currently this doesn't raise an error - duplicates are allowed
        rubric2 = Rubric(role_title="Test Role", categories=duplicate_categories)
        assert len(rubric2.categories) == 2

    def test_json_serialization(self, sample_rubric):
        """Test JSON serialization and deserialization."""
        json_data = sample_rubric.model_dump()

        assert len(json_data["categories"]) == 4
        assert all("name" in cat for cat in json_data["categories"])
        assert all("weight" in cat for cat in json_data["categories"])

        # Deserialize
        rubric_copy = Rubric(**json_data)
        assert len(rubric_copy.categories) == len(sample_rubric.categories)

    def test_floating_point_weight_tolerance(self, sample_scoring_criteria):
        """Test that weights with floating point errors are accepted."""
        # Weights that sum to ~1.0 due to floating point arithmetic
        categories = [
            RubricCategory(
                name="Cat1", description="D1", weight=0.333333,
                is_must_have=True, scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Cat2", description="D2", weight=0.333333,
                is_must_have=False, scoring_criteria=sample_scoring_criteria,
            ),
            RubricCategory(
                name="Cat3", description="D3", weight=0.333334,
                is_must_have=False, scoring_criteria=sample_scoring_criteria,
            ),
        ]
        # Should accept weights that sum to 1.0 within tolerance
        rubric = Rubric(role_title="Test Role", categories=categories)
        assert len(rubric.categories) == 3

    def test_edge_case_single_category(self, sample_scoring_criteria):
        """Test rubric with single category."""
        single_category = [
            RubricCategory(
                name="Only Category", description="The one and only",
                weight=1.0, is_must_have=True,
                scoring_criteria=sample_scoring_criteria,
            ),
        ]
        rubric = Rubric(role_title="Test Role", categories=single_category)
        assert len(rubric.categories) == 1
        assert rubric.categories[0].weight == 1.0
