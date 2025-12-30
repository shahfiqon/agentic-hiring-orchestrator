##  Testing Guide

Comprehensive testing documentation for the agentic hiring orchestrator.

## Test Structure

The test suite is organized into three main categories:

```
tests/
├── conftest.py                    # Shared fixtures and test utilities
├── test_utils.py                  # Helper functions for test data creation
├── test_models/                   # Unit tests for Pydantic models
│   ├── test_rubric.py            # Rubric, RubricCategory, ScoringCriteria
│   ├── test_review.py            # AgentReview, CategoryScore, Evidence
│   ├── test_packet.py            # DecisionPacket, Disagreement
│   ├── test_interview.py         # InterviewPlan, InterviewQuestion
│   └── test_memory.py            # WorkingMemory, KeyObservation, CrossReference
├── test_nodes/                    # Unit tests for workflow nodes
│   ├── test_orchestrator.py      # Orchestrator node (rubric generation)
│   ├── test_hr_agent.py          # HR agent two-pass evaluation
│   ├── test_tech_agent.py        # Tech agent two-pass evaluation
│   ├── test_compliance_agent.py  # Compliance agent two-pass evaluation
│   └── test_synthesis.py         # Synthesis node (aggregation, disagreements)
└── test_graph/                    # Integration tests
    ├── test_workflow_integration.py  # End-to-end workflow tests
    └── test_state_validation.py      # State validation between nodes
```

## Running Tests

### All Tests

```bash
pdm run pytest
```

### With Coverage

```bash
pdm run pytest --cov=src --cov-report=html --cov-report=term
```

This generates:
- Terminal coverage report
- HTML coverage report in `htmlcov/index.html`

### Specific Test Files

```bash
# Run specific test file
pdm run pytest tests/test_models/test_rubric.py

# Run specific test function
pdm run pytest tests/test_models/test_rubric.py::test_rubric_weights_sum_validation
```

### By Test Category

```bash
# Model unit tests
pdm run pytest tests/test_models/

# Node unit tests
pdm run pytest tests/test_nodes/

# Integration tests
pdm run pytest tests/test_graph/
```

### Verbose Output

```bash
pdm run pytest -v
pdm run pytest -vv  # Extra verbose
```

### Filter by Test Name

```bash
# Run all tests with "validation" in the name
pdm run pytest -k validation

# Run all tests for rubric
pdm run pytest -k rubric
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

### Sample Data Fixtures

- `sample_job_description`: Senior AI Engineer job posting
- `sample_resume_strong`: Strong candidate resume
- `sample_resume_moderate`: Moderate candidate with gaps
- `sample_company_context`: Company evaluation priorities

### Model Fixtures

- `sample_rubric`: Complete rubric with 4 categories
- `sample_hr_review`: HR agent review with scores
- `sample_tech_review`: Tech agent review with scores
- `sample_working_memory`: Working memory with observations
- `sample_decision_packet`: Decision packet with recommendation
- `sample_interview_plan`: Interview plan with questions

### State Fixtures

- `sample_state_initial`: Initial state with job description + resume
- `sample_state_with_rubric`: State after orchestrator execution
- `sample_state_with_reviews`: State after panel agent execution

### Mock LLM Fixtures

- `mock_llm_rubric`: Returns sample rubric
- `mock_llm_review`: Returns sample agent review
- `mock_llm_memory`: Returns sample working memory

## Test Utilities

Helper functions in `test_utils.py`:

### Data Creation

```python
from tests.test_utils import create_valid_rubric, create_valid_agent_review

# Create rubric with custom parameters
rubric = create_valid_rubric(num_categories=5, must_have_count=3)

# Create agent review
review = create_valid_agent_review(
    agent_role="hr_agent",
    category_names=["Cat1", "Cat2"],
    scores=[4, 5]
)
```

### Assertion Helpers

```python
from tests.test_utils import assert_rubric_equal, validate_review_coverage

# Compare rubrics
assert_rubric_equal(rubric1, rubric2)

# Validate review covers all rubric categories
validate_review_coverage(review, rubric)
```

## Writing New Tests

### Model Tests

Model tests verify Pydantic validation logic:

```python
import pytest
from pydantic import ValidationError
from src.models.rubric import Rubric

def test_rubric_weights_must_sum_to_one(sample_scoring_criteria):
    """Test that category weights must sum to 1.0."""
    categories = [
        RubricCategory(
            name="Cat1",
            description="Test",
            weight=0.4,  # Only 0.9 total
            is_must_have=True,
            scoring_criteria=sample_scoring_criteria,
        ),
        RubricCategory(
            name="Cat2",
            description="Test",
            weight=0.5,
            is_must_have=False,
            scoring_criteria=sample_scoring_criteria,
        ),
    ]

    with pytest.raises(ValidationError) as exc_info:
        Rubric(categories=categories)
    assert "must sum to 1.0" in str(exc_info.value)
```

### Node Tests

Node tests mock LLM calls to test node logic:

```python
from unittest.mock import Mock, patch
from src.nodes.orchestrator import orchestrator_node

@patch("src.nodes.orchestrator.get_structured_llm")
def test_orchestrator_success(mock_get_llm, sample_state_initial, sample_rubric):
    """Test successful rubric generation."""
    # Setup mock
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=sample_rubric)
    mock_get_llm.return_value = mock_llm

    # Execute
    result = orchestrator_node(sample_state_initial)

    # Verify
    assert "rubric" in result
    assert isinstance(result["rubric"], Rubric)
    mock_llm.invoke.assert_called_once()
```

### Integration Tests

Integration tests verify end-to-end workflows:

```python
@patch("src.nodes.orchestrator.get_structured_llm")
@patch("src.nodes.hr_agent.get_structured_llm")
def test_workflow_execution(
    mock_hr_llm,
    mock_orchestrator_llm,
    sample_job_description,
    sample_resume_strong,
):
    """Test complete workflow from inputs to outputs."""
    # Mock all LLM calls
    # ...

    # Execute workflow
    final_state = run_hiring_workflow(
        job_description=sample_job_description,
        resume=sample_resume_strong,
    )

    # Verify outputs
    assert "decision_packet" in final_state
    assert "interview_plan" in final_state
```

## Mocking Strategy

### Why Mock LLMs?

- **Speed**: Tests run in seconds instead of minutes
- **Cost**: Avoid API charges during testing
- **Reliability**: No dependency on external services
- **Determinism**: Consistent test results

### How to Mock

Use `unittest.mock.patch` to replace LLM calls:

```python
from unittest.mock import Mock, patch

@patch("src.nodes.orchestrator.get_structured_llm")
def test_function(mock_get_llm):
    # Create mock LLM
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=expected_output)
    mock_get_llm.return_value = mock_llm

    # Test will use mock instead of real LLM
```

### Mock Multiple Nodes

For integration tests, mock all LLM calls:

```python
@patch("src.nodes.orchestrator.get_structured_llm")
@patch("src.nodes.hr_agent.get_structured_llm")
@patch("src.nodes.tech_agent.get_structured_llm")
def test_integration(mock_tech, mock_hr, mock_orch):
    # Setup all mocks
    # Execute workflow
    # Verify results
```

## Coverage Goals

Target coverage by module:

| Module | Target | Current |
|--------|--------|---------|
| `src/models/` | 95%+ | TBD |
| `src/nodes/` | 85%+ | TBD |
| `src/state.py` | 90%+ | TBD |
| `src/graph.py` | 80%+ | TBD |
| `src/utils/` | 75%+ | TBD |

**Overall Target**: 80%+ coverage

## Testing Best Practices

### DO

- ✅ Use fixtures from `conftest.py` for reusable test data
- ✅ Mock all LLM calls to avoid API costs and ensure speed
- ✅ Test both success and failure paths
- ✅ Use descriptive test names that explain what's being tested
- ✅ Test edge cases and boundary conditions
- ✅ Verify validation error messages contain expected text

### DON'T

- ❌ Make real LLM API calls in tests
- ❌ Depend on external services or files
- ❌ Write tests that depend on specific execution order
- ❌ Use hardcoded IDs or timestamps
- ❌ Test implementation details - focus on behavior

## Continuous Integration

Tests run automatically on:
- Every commit to `main`
- Every pull request
- Pre-commit hooks (optional)

CI configuration:
- Runs full test suite with coverage
- Fails if coverage drops below 80%
- Generates coverage badge for README

## Debugging Failed Tests

### View Full Traceback

```bash
pdm run pytest --tb=long
```

### Run Single Failing Test

```bash
pdm run pytest tests/test_models/test_rubric.py::test_failing_test -v
```

### Print Debug Output

Add `print()` statements or use `pytest`'s `-s` flag:

```bash
pdm run pytest -s  # Show print() output
```

### Drop into Debugger

```python
def test_something():
    # Add breakpoint
    import pdb; pdb.set_trace()

    # Test code
```

## Common Test Patterns

### Testing Validation Errors

```python
with pytest.raises(ValidationError) as exc_info:
    Model(invalid_field="bad_value")
assert "expected error message" in str(exc_info.value)
```

### Testing State Updates

```python
result = node_function(state)
assert "expected_key" in result
assert result["expected_key"] == expected_value
```

### Parametrized Tests

```python
@pytest.mark.parametrize("score,expected", [
    (0, "No evidence"),
    (3, "Solid experience"),
    (5, "Expert level"),
])
def test_score_descriptions(score, expected):
    criteria = ScoringCriteria(score=score, description=expected)
    assert criteria.description == expected
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock guide](https://docs.python.org/3/library/unittest.mock.html)
- [Pydantic testing guide](https://docs.pydantic.dev/latest/concepts/testing/)
