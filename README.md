# Agentic Hiring Orchestrator

Multi-agent hiring evaluation system using LangGraph for structured, evidence-based candidate assessment.

## Overview

This project implements an intelligent hiring evaluation system that uses multiple specialized AI agents to assess candidates against structured rubrics. The system orchestrates HR, technical, and compliance agents to provide comprehensive, evidence-based evaluations with minimal human bias.

**Key Features:**
- **Multi-Agent Orchestration**: Specialized agents (HR, Technical, Compliance) work in parallel
- **Two-Pass Evaluation**: Agents extract working memory before scoring for better context
- **Evidence-Based Scoring**: All evaluations require citations from application materials
- **Structured Rubrics**: Automated rubric generation from job descriptions
- **Disagreement Detection**: Flags score discrepancies between agents for human review
- **Interview Planning**: Generates targeted interview questions based on evaluation gaps

## Project Structure

```
agentic-hiring-orchestrator/
├── backend/              # Python backend with LangGraph workflows
│   ├── src/             # Application source code
│   ├── tests/           # Test suite
│   ├── notebooks/       # Jupyter notebooks for development
│   ├── examples/        # Example scripts and sample data
│   └── README.md        # Backend-specific documentation
├── prompts/             # Shared prompt templates and examples
└── frontend/            # (Reserved for future UI implementation)
```

## Getting Started

### Backend Setup

The backend contains the core evaluation logic and API. See [backend/README.md](backend/README.md) for detailed setup instructions.

**Quick Start:**

```bash
# Navigate to backend directory
cd backend

# Install dependencies with PDM
pdm install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the system (requires llama.cpp server or OpenAI API key)
pdm run pipeline
```

**LLM Provider Options:**

1. **llama.cpp server (default)**: Run a local llama.cpp server for full privacy and control
   - No API keys required
   - Start server: `./server -m model.gguf -ngl 33 --port 8080`

2. **OpenAI**: Use OpenAI's API for hosted models
   - Set `LLM_PROVIDER=openai` in `.env`
   - Provide `OPENAI_API_KEY`

### Prompts Directory

The `prompts/` directory contains shared prompt templates and few-shot examples used across the system. These prompts are versioned separately to enable rapid iteration and A/B testing.

### Frontend (Future)

The `frontend/` directory is reserved for a future web interface. The current MVP focuses on API-driven workflows accessible via the backend.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Job Description Input              │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │  Orchestrator   │  Generate structured rubric
          └────────┬────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │       Panel Agents (Parallel)     │
    │  ┌──────┐ ┌──────┐ ┌──────────┐ │
    │  │  HR  │ │ Tech │ │Compliance│ │  Two-pass evaluation
    │  └──────┘ └──────┘ └──────────┘ │  with working memory
    └──────────────┬───────────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │   Synthesis     │  Aggregate & detect disagreements
          └────────┬────────┘
                   │
                   ▼
       ┌───────────────────────┐
       │   Decision Packet     │  Scores, reviews, interview plan
       └───────────────────────┘
```

## Use Cases

- **Startup Hiring**: Automate initial candidate screening with consistent evaluation criteria
- **Compliance-Critical Roles**: Ensure regulatory requirements are evaluated systematically
- **High-Volume Recruiting**: Process large applicant pools with structured, evidence-based assessments
- **Interview Preparation**: Generate targeted interview questions based on application gaps

## Technology Stack

- **LangGraph**: Multi-agent workflow orchestration
- **LangChain**: LLM integration and prompt management
- **Pydantic**: Type-safe data validation and settings management
- **FastAPI**: RESTful API endpoints
- **PDM**: Modern Python package management

## Documentation

- [Backend README](backend/README.md) - Backend setup, architecture, and API documentation
- [Prompts Directory](prompts/) - Prompt templates and examples
- Environment Configuration - See `backend/.env.example`

## Development Status

**Current Phase**: MVP Foundation Setup
- [x] Project structure and configuration
- [ ] Core data models (Rubric, Review, Packet, Memory)
- [ ] LangGraph workflow implementation
- [ ] Panel agent nodes (HR, Tech, Compliance)
- [ ] Synthesis and disagreement detection
- [ ] API endpoints
- [ ] Integration tests

## Contributing

This project is in active development. Contributions welcome once the MVP is complete.

## License

MIT License
