"""
Unit tests for interview models (InterviewPlan, InterviewQuestion).

Tests cover validation logic, edge cases, and helper methods.
"""

import pytest
from pydantic import ValidationError

from src.models.interview import InterviewPlan, InterviewQuestion


class TestInterviewQuestion:
    """Tests for InterviewQuestion model."""

    def test_valid_interview_question(self, sample_interview_question):
        """Test creating valid interview question."""
        assert "bias mitigation" in sample_interview_question.question
        assert sample_interview_question.category == "AI Safety & Compliance"
        assert sample_interview_question.interviewer_role == "Tech"

    def test_non_empty_question(self):
        """Test that question cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            InterviewQuestion(
                question="",
                category="Test Category",
                interviewer_role="Tech",
                what_to_listen_for=["Key point 1"],
            )
        # Pydantic validation happens before custom validator, so we get the string length error
        assert "string should have at least 1 character" in str(exc_info.value).lower()

    def test_non_empty_category(self):
        """Test that category cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            InterviewQuestion(
                question="What is your experience with LangGraph?",
                category="",
                interviewer_role="Tech",
                what_to_listen_for=["LangGraph knowledge"],
            )
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_valid_interviewer_roles(self):
        """Test that interviewer_role must be a valid role."""
        valid_roles = ["HR", "Tech", "Product", "Compliance"]

        for role in valid_roles:
            question = InterviewQuestion(
                question="Test question?",
                category="Test Category",
                interviewer_role=role,
                what_to_listen_for=["Point 1"],
            )
            assert question.interviewer_role == role

        # Invalid role
        with pytest.raises(ValidationError) as exc_info:
            InterviewQuestion(
                question="Test question?",
                category="Test Category",
                interviewer_role="invalid_role",
                what_to_listen_for=["Point 1"],
            )
        assert "Input should be 'HR', 'Tech', 'Product' or 'Compliance'" in str(exc_info.value)

    def test_what_to_listen_for_required(self):
        """Test that what_to_listen_for must have at least one item."""
        # Valid: with items
        question = InterviewQuestion(
            question="Test?",
            category="Test Category",
            interviewer_role="Tech",
            what_to_listen_for=["Key point"],
        )
        assert len(question.what_to_listen_for) >= 1

        # Invalid: empty list
        with pytest.raises(ValidationError) as exc_info:
            InterviewQuestion(
                question="Test?",
                category="Test Category",
                interviewer_role="Tech",
                what_to_listen_for=[],
            )
        assert "List should have at least 1 item" in str(exc_info.value)

    def test_json_serialization(self, sample_interview_question):
        """Test JSON serialization and deserialization."""
        json_data = sample_interview_question.model_dump()

        assert "question" in json_data
        assert "category" in json_data
        assert "interviewer_role" in json_data
        assert "what_to_listen_for" in json_data

        # Deserialize
        question_copy = InterviewQuestion(**json_data)
        assert question_copy.question == sample_interview_question.question
        assert question_copy.category == sample_interview_question.category


class TestInterviewPlan:
    """Tests for InterviewPlan model."""

    def test_valid_interview_plan(self, sample_interview_plan):
        """Test creating valid interview plan."""
        assert len(sample_interview_plan.priority_areas) >= 1
        assert len(sample_interview_plan.questions_by_interviewer) >= 1
        assert "Tech" in sample_interview_plan.questions_by_interviewer
        assert "Compliance" in sample_interview_plan.questions_by_interviewer

    def test_valid_interviewer_roles_in_questions(self):
        """Test that all questions have valid interviewer roles."""
        questions_by_interviewer = {
            "Tech": [
                InterviewQuestion(
                    question="Question 1?",
                    category="Category 1",
                    interviewer_role="Tech",
                    what_to_listen_for=["Point 1"],
                ),
            ],
            "Compliance": [
                InterviewQuestion(
                    question="Question 2?",
                    category="Category 2",
                    interviewer_role="Compliance",
                    what_to_listen_for=["Point 2"],
                ),
            ],
            "HR": [
                InterviewQuestion(
                    question="Question 3?",
                    category="Category 3",
                    interviewer_role="HR",
                    what_to_listen_for=["Point 3"],
                ),
            ],
        }
        plan = InterviewPlan(
            questions_by_interviewer=questions_by_interviewer,
            priority_areas=["Area 1", "Area 2"],
        )
        assert len(plan.questions_by_interviewer) == 3
        assert plan.questions_by_interviewer["Tech"][0].interviewer_role == "Tech"
        assert plan.questions_by_interviewer["Compliance"][0].interviewer_role == "Compliance"
        assert plan.questions_by_interviewer["HR"][0].interviewer_role == "HR"

    def test_role_matching_validation(self):
        """Test that questions match their suggested interviewer roles."""
        # Valid: tech questions for Tech
        tech_questions = {
            "Tech": [
                InterviewQuestion(
                    question="Explain your LangGraph architecture?",
                    category="Technical Skills",
                    interviewer_role="Tech",
                    what_to_listen_for=["LangGraph knowledge"],
                ),
            ]
        }
        plan = InterviewPlan(
            questions_by_interviewer=tech_questions,
            priority_areas=["Technical Skills"],
        )
        assert plan.questions_by_interviewer["Tech"][0].interviewer_role == "Tech"

        # Valid: compliance questions for Compliance
        compliance_questions = {
            "Compliance": [
                InterviewQuestion(
                    question="How do you handle PII in your systems?",
                    category="AI Safety & Compliance",
                    interviewer_role="Compliance",
                    what_to_listen_for=["PII handling knowledge"],
                ),
            ]
        }
        plan2 = InterviewPlan(
            questions_by_interviewer=compliance_questions,
            priority_areas=["AI Safety & Compliance"],
        )
        assert plan2.questions_by_interviewer["Compliance"][0].interviewer_role == "Compliance"

    def test_priority_areas_requirement(self):
        """Test that at least one priority area is required."""
        questions = {
            "Tech": [
                InterviewQuestion(
                    question="Test?",
                    category="Test",
                    interviewer_role="Tech",
                    what_to_listen_for=["Test"],
                ),
            ]
        }

        # Valid: with priority areas
        plan = InterviewPlan(
            questions_by_interviewer=questions,
            priority_areas=["Area 1"],
        )
        assert len(plan.priority_areas) == 1

        # Invalid: empty priority areas
        with pytest.raises(ValidationError) as exc_info:
            InterviewPlan(
                questions_by_interviewer=questions,
                priority_areas=[],
            )
        assert "list should have at least 1 item" in str(exc_info.value).lower()

    def test_questions_requirement(self):
        """Test that at least one question is required."""
        # Valid: with questions
        plan = InterviewPlan(
            questions_by_interviewer={
                "Tech": [
                    InterviewQuestion(
                        question="Test?",
                        category="Test",
                        interviewer_role="Tech",
                        what_to_listen_for=["Test"],
                    ),
                ]
            },
            priority_areas=["Area 1"],
        )
        assert len(plan.questions_by_interviewer["Tech"]) == 1

        # Invalid: empty questions dict
        with pytest.raises(ValidationError) as exc_info:
            InterviewPlan(
                questions_by_interviewer={},
                priority_areas=["Area 1"],
            )
        # The validator message says "at least one question"
        assert ("at least one question" in str(exc_info.value).lower() or "must include" in str(exc_info.value).lower())

    def test_get_questions_for_role(self, sample_interview_plan):
        """Test get_questions_for_role helper method."""
        # Get Tech questions
        tech_questions = sample_interview_plan.get_questions_for_role("Tech")
        assert len(tech_questions) == 1
        assert "AI safety framework" in tech_questions[0].question

        # Get Compliance questions
        compliance_questions = sample_interview_plan.get_questions_for_role("Compliance")
        assert len(compliance_questions) == 1
        assert "PII detection" in compliance_questions[0].question

        # Get questions for role with no questions
        hr_questions = sample_interview_plan.get_questions_for_role("HR")
        assert len(hr_questions) == 0

    def test_total_questions_method(self, sample_interview_plan):
        """Test total_questions helper method."""
        assert sample_interview_plan.total_questions() == 2

        # Test with more questions
        questions_by_interviewer = {
            "Tech": [
                InterviewQuestion(
                    question=f"Question {i}?",
                    category="Category",
                    interviewer_role="Tech",
                    what_to_listen_for=[f"Point {i}"],
                )
                for i in range(5)
            ]
        }
        plan = InterviewPlan(
            questions_by_interviewer=questions_by_interviewer,
            priority_areas=["Area 1"],
        )
        assert plan.total_questions() == 5

    def test_question_distribution_warning(self):
        """Test warning for uneven question distribution (70%+ skew)."""
        # Create plan with 10 questions, 8 for Tech (80% skew)
        tech_questions = [
            InterviewQuestion(
                question=f"Tech question {i}?",
                category="Technical",
                interviewer_role="Tech",
                what_to_listen_for=["Tech point"],
            )
            for i in range(8)
        ]
        compliance_questions = [
            InterviewQuestion(
                question=f"Compliance question {i}?",
                category="Compliance",
                interviewer_role="Compliance",
                what_to_listen_for=["Compliance point"],
            )
            for i in range(2)
        ]

        # Should not raise error, but would log warning in production
        plan = InterviewPlan(
            questions_by_interviewer={
                "Tech": tech_questions,
                "Compliance": compliance_questions,
            },
            priority_areas=["Technical Skills"],
        )
        assert plan.total_questions() == 10
        tech_q = plan.get_questions_for_role("Tech")
        assert len(tech_q) == 8

    def test_json_serialization(self, sample_interview_plan):
        """Test JSON serialization and deserialization."""
        json_data = sample_interview_plan.model_dump()

        assert "priority_areas" in json_data
        assert "questions_by_interviewer" in json_data
        assert len(json_data["questions_by_interviewer"]) >= 1

        # Deserialize
        plan_copy = InterviewPlan(**json_data)
        assert len(plan_copy.priority_areas) == len(sample_interview_plan.priority_areas)
        assert len(plan_copy.questions_by_interviewer) == len(sample_interview_plan.questions_by_interviewer)

    def test_edge_case_single_priority_area(self):
        """Test interview plan with single priority area."""
        plan = InterviewPlan(
            questions_by_interviewer={
                "HR": [
                    InterviewQuestion(
                        question="Single question?",
                        category="Category",
                        interviewer_role="HR",
                        what_to_listen_for=["Point"],
                    ),
                ]
            },
            priority_areas=["Only Area"],
        )
        assert len(plan.priority_areas) == 1
        assert plan.total_questions() == 1

    def test_multiple_priority_areas(self):
        """Test interview plan with multiple priority areas."""
        plan = InterviewPlan(
            questions_by_interviewer={
                "Tech": [
                    InterviewQuestion(
                        question="Question 1?",
                        category="Cat1",
                        interviewer_role="Tech",
                        what_to_listen_for=["Point 1"],
                    ),
                ],
                "Compliance": [
                    InterviewQuestion(
                        question="Question 2?",
                        category="Cat2",
                        interviewer_role="Compliance",
                        what_to_listen_for=["Point 2"],
                    ),
                ],
            },
            priority_areas=[
                "Technical Skills",
                "AI Safety & Compliance",
                "Production Experience",
                "Leadership & Communication",
            ],
        )
        assert len(plan.priority_areas) == 4
        assert plan.total_questions() == 2

    def test_all_interviewer_roles_represented(self):
        """Test interview plan with all possible interviewer roles."""
        questions_by_interviewer = {
            "HR": [
                InterviewQuestion(
                    question="HR question?",
                    category="HR Category",
                    interviewer_role="HR",
                    what_to_listen_for=["HR point"],
                ),
            ],
            "Tech": [
                InterviewQuestion(
                    question="Tech question?",
                    category="Tech Category",
                    interviewer_role="Tech",
                    what_to_listen_for=["Tech point"],
                ),
            ],
            "Compliance": [
                InterviewQuestion(
                    question="Compliance question?",
                    category="Compliance Category",
                    interviewer_role="Compliance",
                    what_to_listen_for=["Compliance point"],
                ),
            ],
            "Product": [
                InterviewQuestion(
                    question="Product question?",
                    category="Product Category",
                    interviewer_role="Product",
                    what_to_listen_for=["Product point"],
                ),
            ],
        }
        plan = InterviewPlan(
            questions_by_interviewer=questions_by_interviewer,
            priority_areas=["Comprehensive Assessment"],
        )
        assert plan.total_questions() == 4

        # Verify each role has exactly one question
        assert len(plan.get_questions_for_role("HR")) == 1
        assert len(plan.get_questions_for_role("Tech")) == 1
        assert len(plan.get_questions_for_role("Compliance")) == 1
        assert len(plan.get_questions_for_role("Product")) == 1

    def test_invalid_interviewer_role_in_dict(self):
        """Test that invalid interviewer roles in dict are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InterviewPlan(
                questions_by_interviewer={
                    "invalid_role": [
                        InterviewQuestion(
                            question="Test?",
                            category="Test",
                            interviewer_role="Tech",
                            what_to_listen_for=["Test"],
                        ),
                    ]
                },
                priority_areas=["Test"],
            )
        assert "Invalid interviewer roles" in str(exc_info.value)

    def test_question_role_mismatch(self):
        """Test that questions must match their assigned role."""
        with pytest.raises(ValidationError) as exc_info:
            InterviewPlan(
                questions_by_interviewer={
                    "Tech": [
                        InterviewQuestion(
                            question="Test?",
                            category="Test",
                            interviewer_role="HR",  # Mismatch!
                            what_to_listen_for=["Test"],
                        ),
                    ]
                },
                priority_areas=["Test"],
            )
        assert "interviewer_role mismatch" in str(exc_info.value)
