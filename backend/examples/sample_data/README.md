# Sample Data for Hiring Workflow Testing

This directory contains synthetic sample data for testing and demonstrating the agentic hiring orchestrator workflow. All data is fictional and created specifically for validation and development purposes.

## Files Overview

### Job Descriptions

**`job_senior_ai_engineer.txt`**
- Role: Senior AI Engineer focused on agentic systems and multi-agent orchestration
- Key requirements: LangGraph, production LLM integration, 5+ years experience
- Emphasis on: Multi-agent systems, state management, prompt engineering, production deployment
- Use case: Tests the workflow's ability to evaluate deep technical expertise in AI/agent domains

**`job_backend_engineer.txt`**
- Role: Senior Backend Engineer for platform and infrastructure
- Key requirements: Python/FastAPI, system design, 5+ years experience
- Emphasis on: Scalable APIs, distributed systems, database optimization
- Use case: Tests the workflow with traditional backend engineering requirements

### Resumes

**`resume_strong_candidate.txt`**
- Profile: Alex Chen - 6 years experience with strong LangGraph and multi-agent background
- Strengths:
  - Direct production experience with LangGraph and agent orchestration
  - Quantified achievements (50K conversations/month, 60% cost reduction)
  - Open-source contributions and thought leadership
  - Strong technical breadth across the stack
- Potential gaps:
  - Less experience with model training infrastructure
  - Still learning RLHF and fine-tuning techniques
- Expected score range: 4.0-4.5 / 5.0 when matched with AI Engineer role
- Use case: Tests workflow's ability to recognize strong matches and identify appropriate interview focus areas

**`resume_moderate_candidate.txt`**
- Profile: Jordan Martinez - 3.5 years experience with basic LLM integration
- Strengths:
  - Practical chatbot and OpenAI API experience
  - Eagerness to learn and self-awareness
  - Basic LangChain and RAG knowledge
- Gaps:
  - Limited production multi-agent experience
  - Smaller scale systems (thousands vs millions of requests)
  - More theoretical than hands-on with advanced frameworks
  - Junior-level experience overall
- Expected score range: 2.5-3.5 / 5.0 when matched with Senior AI Engineer role
- Use case: Tests workflow's ability to identify experience gaps, detect ambiguities, and generate targeted interview questions

## Usage Examples

### Basic Execution
```bash
python backend/examples/run_pipeline.py
```
This runs the default configuration (AI Engineer job + strong candidate resume).

### Specify Custom Files
```bash
python backend/examples/run_pipeline.py \
  --job sample_data/job_backend_engineer.txt \
  --resume sample_data/resume_moderate_candidate.txt
```

### Verbose Mode (Show Working Memories)
```bash
python backend/examples/run_pipeline.py --verbose
```

### Save Results to JSON
```bash
python backend/examples/run_pipeline.py --output-json results/output.json
```

### Run All Combinations
```bash
python backend/examples/run_all_samples.py
```

## Expected Workflow Behaviors

### Strong Candidate + AI Engineer Role
- **Panel Agreement**: Should see general alignment on technical competency (scores 4.0-4.5)
- **Potential Disagreements**: Compliance agent might flag gaps in model training infrastructure vs technical agent focusing on strong agent experience
- **Interview Focus**: Deep dive on specific LangGraph implementations, architecture decisions, scaling challenges
- **Decision**: Likely "strong_yes" or "yes" with high confidence

### Moderate Candidate + AI Engineer Role
- **Panel Disagreements**: Technical agent might score lower (2.5-3.0) due to lack of production multi-agent experience, while HR agent might score higher (3.5-4.0) based on enthusiasm and growth potential
- **Missing Information**: Many ambiguous claims ("basic LangChain", "some Docker experience") should trigger follow-up questions
- **Interview Focus**: Probe depth of understanding, validate claims about agent workflows, assess learning ability
- **Decision**: Likely "maybe" or "no" with moderate confidence, depending on role requirements

### Moderate Candidate + Backend Engineer Role
- **Better Alignment**: More suitable for backend role given API and database experience
- **Panel Scores**: More consistent across agents (3.0-3.5 range)
- **Decision**: Likely "maybe" with questions about scale and system design experience

## Testing Objectives

1. **Rubric Extraction**: Verify that job descriptions produce comprehensive rubrics with appropriate categories and weights
2. **Disagreement Detection**: Confirm that ambiguous candidates trigger panel disagreements
3. **Interview Question Quality**: Ensure questions target specific gaps and ambiguities
4. **Working Memory**: Validate that agents track cross-references and identify missing information
5. **Decision Consistency**: Check that decision packet reasoning aligns with panel reviews

## Data Characteristics

- **Realistic Detail**: Includes specific technologies, metrics, and timelines
- **Balanced Profiles**: Both strengths and weaknesses to trigger nuanced evaluation
- **Ambiguous Claims**: Intentional vagueness to test interview question generation
- **Varied Writing Styles**: Different formats (bullet points, paragraphs, summaries)
- **Scale Indicators**: Different levels of system scale to test experience assessment

## Extending Sample Data

To add new test cases:

1. Create new job description or resume file in this directory
2. Follow naming convention: `job_[role].txt` or `resume_[profile].txt`
3. Include realistic details with both strengths and gaps
4. Add entry to this README describing expected workflow behavior
5. Test with `run_pipeline.py` to validate results

## Notes

- All names, companies, and details are entirely fictional
- Sample data designed to exercise different workflow paths and edge cases
- Realistic but exaggerated to clearly demonstrate workflow capabilities
- Not intended to represent ideal resume or job description formats
