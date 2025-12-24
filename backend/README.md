# Agentic Hiring Orchestrator - Backend

Multi-agent hiring evaluation system using LangGraph for structured candidate assessment.

## Overview

This backend implements a multi-agent workflow orchestrator that evaluates candidates through structured rubrics, panel-based reviews, and automated synthesis. The system uses LangGraph for workflow orchestration and supports both local llama.cpp servers and OpenAI as LLM providers.

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PDM (Python Development Master) for package management
- llama.cpp server running locally (default) OR OpenAI API key

### Installation

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pdm install

# Install with optional dependencies (development, notebooks, visualization)
pdm install -G dev -G notebooks -G viz

# Copy environment template and configure
cp .env.example .env
# Edit .env with your settings (API keys, model configuration, etc.)
```

### Configuration

The system uses environment variables for configuration. See `.env.example` for all available options.

**Default Setup (llama.cpp server):**
```bash
# Ensure llama.cpp server is running
# Example: ./server -m /path/to/model.gguf -ngl 33 --port 8080

# The default .env.example is pre-configured for llama.cpp server
# No API keys needed - just start your server and run
```

**Alternative Setup (OpenAI):**
```bash
# In your .env file:
LLM_PROVIDER=openai
OPENAI_API_KEY=your_actual_api_key_here
```

### Running the System

```bash
# Run the evaluation pipeline (once implemented)
pdm run pipeline

# Start the API server
pdm run api

# Launch Jupyter notebooks for interactive development
pdm run notebook

# Run tests
pytest

# Lint code
pdm run lint
```

## Project Structure

```
backend/
├── src/                          # Application source code
│   ├── models/                   # Pydantic data models
│   │   ├── rubric.py            # Rubric schemas
│   │   ├── review.py            # Review schemas
│   │   ├── packet.py            # Decision packet schemas
│   │   ├── interview.py         # Interview plan schemas
│   │   └── memory.py            # Working memory schemas
│   ├── nodes/                    # LangGraph node implementations
│   │   ├── orchestrator.py      # Rubric generation node
│   │   ├── hr_agent.py          # HR panel agent
│   │   ├── tech_agent.py        # Technical panel agent
│   │   ├── compliance_agent.py  # Compliance panel agent
│   │   └── synthesis.py         # Decision synthesis node
│   ├── prompts/                  # LLM prompt templates
│   │   └── examples/            # Few-shot examples
│   ├── utils/                    # Shared utilities
│   ├── graph/                    # LangGraph workflow definitions
│   ├── api/                      # FastAPI endpoints
│   ├── config.py                 # Centralized configuration
│   └── state.py                  # Workflow state definitions
├── tests/                        # Test suite
│   ├── test_models/             # Model validation tests
│   ├── test_nodes/              # Node logic tests
│   ├── test_graph/              # Workflow integration tests
│   ├── test_api/                # API endpoint tests
│   └── fixtures/                # Test data and fixtures
├── notebooks/                    # Jupyter notebooks
│   ├── testing_workflow.ipynb   # Workflow testing
│   ├── prompt_engineering.ipynb # Prompt development
│   └── data_exploration.ipynb   # Data analysis
├── examples/                     # Example scripts
│   ├── run_pipeline.py          # Pipeline execution example
│   └── sample_data/             # Sample input data
├── pyproject.toml               # Project metadata and dependencies
├── .env.example                 # Environment variable template
└── README.md                    # This file
```

## Architecture

The system follows a multi-agent orchestration pattern:

```
┌─────────────────┐
│  Orchestrator   │  Generates structured rubrics from job descriptions
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│          Panel Agents                    │
│  ┌──────┐  ┌──────┐  ┌────────────┐    │
│  │  HR  │  │ Tech │  │ Compliance │    │  Two-pass evaluation with
│  └──────┘  └──────┘  └────────────┘    │  working memory extraction
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Synthesis     │  Aggregates reviews into decision packet
└─────────────────┘
```

**Key Components:**

- **Orchestrator**: Generates evaluation rubrics from job descriptions
- **Panel Agents**: Specialized agents (HR, Technical, Compliance) that perform two-pass evaluations:
  - Pass 1: Extract working memory (key observations, concerns, strengths)
  - Pass 2: Score against rubric using working memory context
- **Synthesis**: Aggregates panel reviews, detects disagreements, generates interview plans

**Workflow Features:**

- **Parallel Execution**: Panel agents execute concurrently (fan-out/fan-in pattern)
- **Working Memory**: Two-pass evaluation captures context before scoring
- **Evidence-Based**: All scores require evidence citations from application materials
- **Disagreement Detection**: Flags significant score deltas between agents
- **Structured Outputs**: Pydantic models ensure type safety and validation

## Development

### Environment Variables

All configuration is managed through environment variables. Key settings:

- `LLM_PROVIDER`: Choose between `llamacpp-server` (default) or `openai`
- `LLAMACPP_BASE_URL`: llama.cpp server endpoint (default: http://localhost:8080/v1)
- `OPENAI_API_KEY`: Required only if using OpenAI provider
- `ENABLE_WORKING_MEMORY`: Toggle two-pass evaluation (default: true)
- `ENABLE_PRODUCT_AGENT`: Toggle product agent in panel (default: false)
- `RUBRIC_CATEGORIES_COUNT`: Number of rubric categories (default: 5)
- `LANGCHAIN_TRACING_V2`: Enable LangSmith tracing for debugging

See `.env.example` for complete documentation.

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test module
pytest tests/test_models/test_rubric.py

# Run tests in parallel
pytest -n auto
```

### Code Quality

```bash
# Lint code
pdm run lint

# Format code
ruff check --fix src/ tests/

# Type checking
mypy src/
```

## API Endpoints

The FastAPI server provides the following endpoints (once implemented):

- `POST /evaluate`: Submit candidate application for evaluation
  - Input: Job description, resume, cover letter, work samples
  - Output: Decision packet with scores, reviews, interview plan

## Contributing

This project follows standard Python development practices:

- Use type hints for all function signatures
- Write tests for new features
- Follow PEP 8 style guidelines (enforced by ruff)
- Document complex logic with docstrings
- Keep functions focused and modular

## License

MIT License
