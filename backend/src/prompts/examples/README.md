# Prompt Examples

This directory contains reference examples for prompt engineering, testing, and validation of the agentic hiring orchestrator.

## Files

### `rubric_examples.json`

Complete rubric examples for different roles demonstrating:
- **Proper category weighting**: All weights sum to exactly 1.0
- **Well-defined scoring criteria**: Clear 0/3/5 levels with specific indicators
- **Must-have vs. nice-to-have**: Mix of critical and secondary categories
- **Role-specific focus**: Different competencies for different roles (AI Engineer vs. Product Manager)

**Usage**:
- Reference when designing new rubric generation prompts
- Use as few-shot examples in `RUBRIC_GENERATION_PROMPT`
- Validate Pydantic `Rubric` model schema against these examples
- Test rubric generation LLM calls

### `working_memory_examples.json`

WorkingMemory extraction examples showing:
- **Key observations**: 5-8 observations per rubric category with specific evidence
- **Cross-references**: Well-supported, partially-supported, contradictory, and unverifiable assessments
- **Timeline analysis**: Career progression patterns (steady growth, pivots, tenure issues)
- **Missing information**: Expected details absent from resumes
- **Ambiguities**: Vague claims requiring clarification

**Usage**:
- Reference when designing `WORKING_MEMORY_EXTRACTION_PROMPT`
- Test working memory extraction LLM calls
- Validate Pydantic `WorkingMemory` model schema
- Train agents on what constitutes good observations vs. superficial notes

### `agent_review_examples.json`

Complete AgentReview examples for each agent role (HR, Tech, Compliance) demonstrating:
- **Category scores with evidence**: Each score cites specific working memory observations
- **Role-specific focus**: HR emphasizes seniority/trajectory, Tech emphasizes production signals, Compliance emphasizes privacy/bias risks
- **Top strengths and risks**: Specific evidence citations from working memory
- **Follow-up questions**: Derived from ambiguities and gaps in working memory

**Usage**:
- Reference when designing agent evaluation prompts (`HR_EVALUATION_PROMPT`, `TECH_EVALUATION_PROMPT`, `COMPLIANCE_EVALUATION_PROMPT`)
- Test agent evaluation LLM calls
- Validate Pydantic `AgentReview` model schema
- Ensure agents properly leverage working memory in their evaluations

## How to Use These Examples

### 1. Prompt Engineering Iteration

When refining prompts, compare LLM outputs against these reference examples:
- Does the LLM output match the structure and quality of the examples?
- Are observations specific enough (like in `working_memory_examples.json`)?
- Do category scores include proper evidence citations (like in `agent_review_examples.json`)?

### 2. Testing Structured Outputs

Use these examples to test Pydantic model validation:

```python
import json
from backend.src.models.review import Rubric, AgentReview
from backend.src.models.memory import WorkingMemory

# Test Rubric schema
with open('backend/src/prompts/examples/rubric_examples.json') as f:
    data = json.load(f)
    for example in data['examples']:
        rubric = Rubric(**example['rubric'])
        print(f"✓ Validated rubric for {example['role']}")

# Test WorkingMemory schema
with open('backend/src/prompts/examples/working_memory_examples.json') as f:
    data = json.load(f)
    for example in data['examples']:
        memory = WorkingMemory(**example['working_memory'])
        print(f"✓ Validated working memory for {example['candidate']}")

# Test AgentReview schema
with open('backend/src/prompts/examples/agent_review_examples.json') as f:
    data = json.load(f)
    for example in data['examples']:
        review = AgentReview(**example['review'])
        print(f"✓ Validated {example['agent_role']} review for {example['candidate']}")
```

### 3. Few-Shot Learning in Prompts

Include these examples directly in prompts to guide LLM behavior:

```python
# Example: Using rubric examples in few-shot prompt
from backend.src.prompts.orchestrator_prompts import RUBRIC_GENERATION_PROMPT

prompt = RUBRIC_GENERATION_PROMPT.format(
    rubric_categories_count=5,
    job_description="Senior Backend Engineer role...",
    company_context="Startup building developer tools..."
)
# The prompt already contains few-shot examples from rubric_examples.json
```

### 4. Validation of Pydantic Models

If you update Pydantic models, re-validate these examples to ensure backward compatibility:

```bash
# Run validation script (if created)
python backend/src/prompts/test_prompts.py
```

## Adding New Examples

When adding new examples:

1. **Ensure JSON validity**: Use a JSON validator before committing
2. **Match Pydantic schemas**: All examples must pass Pydantic validation
3. **Provide diverse scenarios**: Cover different roles, experience levels, edge cases
4. **Document intent**: Add comments explaining what each example demonstrates
5. **Test with LLM**: Verify that examples improve LLM output quality when used as few-shot learning

## Example Quality Guidelines

Good examples should:
- ✅ Be specific and concrete (not vague or generic)
- ✅ Include realistic details (names, numbers, timelines)
- ✅ Show both positive and negative signals (strengths and gaps)
- ✅ Demonstrate proper evidence citations
- ✅ Match the intended output schema exactly

Bad examples:
- ❌ Vague observations: "Candidate has good experience"
- ❌ Missing evidence: Scores without justification
- ❌ Unrealistic perfection: All scores are 5/5
- ❌ Schema mismatches: Missing required fields or wrong types

## Version History

- **v1.0** (2025-01-XX): Initial examples created
  - 2 rubric examples (AI Engineer, Product Manager)
  - 2 working memory examples
  - 3 agent review examples (HR, Tech, Compliance)
