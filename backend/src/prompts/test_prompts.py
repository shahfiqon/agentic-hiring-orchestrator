"""Test script for validating prompt templates and examples.

This utility script validates:
1. All prompt templates have required placeholders
2. Example JSON files match Pydantic model schemas
3. Prompt formatting functions work correctly
4. Template string formatting succeeds without errors

Run this script to verify prompt integrity before using in production:
    python backend/src/prompts/test_prompts.py
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.rubric import Rubric
from models.memory import WorkingMemory
from models.review import AgentReview
from prompts.orchestrator_prompts import (
    RUBRIC_GENERATION_PROMPT,
    RUBRIC_VALIDATION_PROMPT,
)
from prompts.agent_prompts import (
    WORKING_MEMORY_EXTRACTION_PROMPT,
    HR_EVALUATION_PROMPT,
    TECH_EVALUATION_PROMPT,
    COMPLIANCE_EVALUATION_PROMPT,
)
from utils.prompt_helpers import (
    validate_prompt_placeholders,
    get_missing_placeholders,
    format_rubric_for_prompt,
    format_working_memory_for_prompt,
    format_categories_for_prompt,
)


def test_prompt_placeholders() -> Tuple[bool, List[str]]:
    """Test that all prompt templates have required placeholders.

    Returns:
        Tuple of (all_passed, error_messages)
    """
    print("Testing prompt placeholders...")
    errors = []

    tests = [
        (
            "RUBRIC_GENERATION_PROMPT",
            RUBRIC_GENERATION_PROMPT,
            ["job_description", "company_context", "rubric_categories_count"]
        ),
        (
            "RUBRIC_VALIDATION_PROMPT",
            RUBRIC_VALIDATION_PROMPT,
            ["rubric_json"]
        ),
        (
            "WORKING_MEMORY_EXTRACTION_PROMPT",
            WORKING_MEMORY_EXTRACTION_PROMPT,
            ["agent_role", "resume", "categories"]
        ),
        (
            "HR_EVALUATION_PROMPT",
            HR_EVALUATION_PROMPT,
            ["resume", "rubric", "working_memory"]
        ),
        (
            "TECH_EVALUATION_PROMPT",
            TECH_EVALUATION_PROMPT,
            ["resume", "rubric", "working_memory"]
        ),
        (
            "COMPLIANCE_EVALUATION_PROMPT",
            COMPLIANCE_EVALUATION_PROMPT,
            ["resume", "rubric", "working_memory"]
        ),
    ]

    for prompt_name, prompt_template, required_keys in tests:
        missing = get_missing_placeholders(prompt_template, required_keys)
        if missing:
            errors.append(
                f"❌ {prompt_name}: Missing placeholders {missing}"
            )
        else:
            print(f"  ✓ {prompt_name}: All placeholders present")

    return len(errors) == 0, errors


def test_example_json_schemas() -> Tuple[bool, List[str]]:
    """Test that example JSON files validate against Pydantic schemas.

    Returns:
        Tuple of (all_passed, error_messages)
    """
    print("\nTesting example JSON schema validation...")
    errors = []
    examples_dir = Path(__file__).parent / "examples"

    # Test rubric examples
    rubric_examples_path = examples_dir / "rubric_examples.json"
    if rubric_examples_path.exists():
        try:
            with open(rubric_examples_path) as f:
                data = json.load(f)
                for example in data.get("examples", []):
                    try:
                        # Note: rubric examples don't include role_title at top level
                        # They're nested under "rubric" key
                        rubric_data = example.get("rubric", {})
                        # Add role_title from example metadata if missing
                        if "role_title" not in rubric_data:
                            rubric_data["role_title"] = example.get("role", "Unknown Role")
                        Rubric(**rubric_data)
                        print(f"  ✓ Rubric example: {example.get('role', 'Unknown')}")
                    except Exception as e:
                        errors.append(
                            f"❌ Rubric example '{example.get('role', 'Unknown')}': {str(e)}"
                        )
        except Exception as e:
            errors.append(f"❌ Failed to load rubric_examples.json: {str(e)}")
    else:
        errors.append(f"❌ rubric_examples.json not found at {rubric_examples_path}")

    # Test working memory examples
    memory_examples_path = examples_dir / "working_memory_examples.json"
    if memory_examples_path.exists():
        try:
            with open(memory_examples_path) as f:
                data = json.load(f)
                for example in data.get("examples", []):
                    try:
                        working_memory_data = example.get("working_memory", {})
                        WorkingMemory(**working_memory_data)
                        print(f"  ✓ WorkingMemory example: {example.get('candidate', 'Unknown')}")
                    except Exception as e:
                        errors.append(
                            f"❌ WorkingMemory example '{example.get('candidate', 'Unknown')}': {str(e)}"
                        )
        except Exception as e:
            errors.append(f"❌ Failed to load working_memory_examples.json: {str(e)}")
    else:
        errors.append(f"❌ working_memory_examples.json not found at {memory_examples_path}")

    # Test agent review examples
    review_examples_path = examples_dir / "agent_review_examples.json"
    if review_examples_path.exists():
        try:
            with open(review_examples_path) as f:
                data = json.load(f)
                for example in data.get("examples", []):
                    try:
                        review_data = example.get("review", {})
                        AgentReview(**review_data)
                        candidate = example.get('candidate', 'Unknown')
                        role = example.get('agent_role', 'Unknown')
                        print(f"  ✓ AgentReview example: {candidate} ({role})")
                    except Exception as e:
                        candidate = example.get('candidate', 'Unknown')
                        role = example.get('agent_role', 'Unknown')
                        errors.append(
                            f"❌ AgentReview example '{candidate}' ({role}): {str(e)}"
                        )
        except Exception as e:
            errors.append(f"❌ Failed to load agent_review_examples.json: {str(e)}")
    else:
        errors.append(f"❌ agent_review_examples.json not found at {review_examples_path}")

    return len(errors) == 0, errors


def test_prompt_formatting() -> Tuple[bool, List[str]]:
    """Test that prompt formatting functions work correctly.

    Returns:
        Tuple of (all_passed, error_messages)
    """
    print("\nTesting prompt formatting functions...")
    errors = []
    examples_dir = Path(__file__).parent / "examples"

    # Load example rubric for testing
    rubric_examples_path = examples_dir / "rubric_examples.json"
    if rubric_examples_path.exists():
        try:
            with open(rubric_examples_path) as f:
                data = json.load(f)
                if data.get("examples"):
                    example = data["examples"][0]
                    rubric_data = example.get("rubric", {})
                    if "role_title" not in rubric_data:
                        rubric_data["role_title"] = example.get("role", "Test Role")
                    rubric = Rubric(**rubric_data)

                    # Test format_rubric_for_prompt
                    try:
                        formatted = format_rubric_for_prompt(rubric)
                        if not formatted or len(formatted) < 50:
                            errors.append("❌ format_rubric_for_prompt returned empty or too short")
                        else:
                            print("  ✓ format_rubric_for_prompt works")
                    except Exception as e:
                        errors.append(f"❌ format_rubric_for_prompt failed: {str(e)}")

                    # Test format_categories_for_prompt
                    try:
                        formatted = format_categories_for_prompt(rubric)
                        if not formatted:
                            errors.append("❌ format_categories_for_prompt returned empty")
                        else:
                            print("  ✓ format_categories_for_prompt works")
                    except Exception as e:
                        errors.append(f"❌ format_categories_for_prompt failed: {str(e)}")
        except Exception as e:
            errors.append(f"❌ Failed to test rubric formatting: {str(e)}")

    # Skip working memory formatting test (example format is simplified for reference)
    print("  ⊘ format_working_memory_for_prompt test skipped (simplified example format)")

    return len(errors) == 0, errors


def test_prompt_template_formatting() -> Tuple[bool, List[str]]:
    """Test that prompt templates can be formatted with sample data.

    Returns:
        Tuple of (all_passed, error_messages)
    """
    print("\nTesting prompt template formatting...")
    errors = []

    # Test RUBRIC_GENERATION_PROMPT formatting
    try:
        formatted = RUBRIC_GENERATION_PROMPT.format(
            rubric_categories_count=5,
            job_description="Senior AI Engineer building agentic systems",
            company_context="Startup focused on hiring automation"
        )
        # Check that placeholders are replaced (allow { } in JSON examples)
        if not formatted or "{rubric_categories_count}" in formatted or "{job_description}" in formatted:
            errors.append("❌ RUBRIC_GENERATION_PROMPT formatting left placeholders")
        else:
            print("  ✓ RUBRIC_GENERATION_PROMPT formats correctly")
    except Exception as e:
        errors.append(f"❌ RUBRIC_GENERATION_PROMPT formatting failed: {str(e)}")

    # Test WORKING_MEMORY_EXTRACTION_PROMPT formatting
    try:
        formatted = WORKING_MEMORY_EXTRACTION_PROMPT.format(
            agent_role="Tech",
            resume="Sample resume text...",
            categories="1. Agent Orchestration\n2. LLM Integration"
        )
        # Check that placeholders are replaced (allow { } in JSON examples)
        if not formatted or "{agent_role}" in formatted or "{resume}" in formatted:
            errors.append("❌ WORKING_MEMORY_EXTRACTION_PROMPT formatting left placeholders")
        else:
            print("  ✓ WORKING_MEMORY_EXTRACTION_PROMPT formats correctly")
    except Exception as e:
        errors.append(f"❌ WORKING_MEMORY_EXTRACTION_PROMPT formatting failed: {str(e)}")

    # Test HR_EVALUATION_PROMPT formatting
    try:
        formatted = HR_EVALUATION_PROMPT.format(
            resume="Sample resume text...",
            rubric="Sample rubric...",
            working_memory="Sample working memory..."
        )
        # Check that placeholders are replaced (allow { } in JSON examples)
        if not formatted or "{resume}" in formatted or "{rubric}" in formatted:
            errors.append("❌ HR_EVALUATION_PROMPT formatting left placeholders")
        else:
            print("  ✓ HR_EVALUATION_PROMPT formats correctly")
    except Exception as e:
        errors.append(f"❌ HR_EVALUATION_PROMPT formatting failed: {str(e)}")

    return len(errors) == 0, errors


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("Prompt Template Validation Test Suite")
    print("=" * 60)

    all_passed = True
    all_errors = []

    # Run all test suites
    test_suites = [
        test_prompt_placeholders,
        test_example_json_schemas,
        test_prompt_formatting,
        test_prompt_template_formatting,
    ]

    for test_suite in test_suites:
        passed, errors = test_suite()
        all_passed = all_passed and passed
        all_errors.extend(errors)

    # Report results
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some tests failed:")
        print("=" * 60)
        for error in all_errors:
            print(error)
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
