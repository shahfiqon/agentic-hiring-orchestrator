# Quick Start Guide

This guide will help you get the Agentic Hiring Orchestrator up and running in under 5 minutes.

## Prerequisites

- Python 3.11+
- Node.js 18+
- PDM (Python package manager)
- npm (comes with Node.js)
- An LLM provider (llama.cpp, OpenAI, or Anthropic)

## Step 1: Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pdm install

# Configure environment
cp .env.example .env

# Edit .env and configure your LLM provider
# For llama.cpp (local):
#   LLM_PROVIDER=llamacpp
#   LLAMACPP_BASE_URL=http://localhost:8080
#
# For OpenAI:
#   LLM_PROVIDER=openai
#   OPENAI_API_KEY=your_key_here
#
# For Anthropic:
#   LLM_PROVIDER=anthropic
#   ANTHROPIC_API_KEY=your_key_here

# Start the backend API server
pdm run uvicorn src.api.main:app --reload
```

The backend will be running at http://localhost:8000

**Verify Backend:**
```bash
# In a new terminal
curl http://localhost:8000/health
```

## Step 2: Frontend Setup

```bash
# Navigate to frontend (from project root)
cd frontend

# Install dependencies
npm install

# Configure environment (already set to default values)
# The .env.local file is already created with:
#   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Start the frontend development server
npm run dev
```

The frontend will be running at http://localhost:3000

## Step 3: Use the Application

1. Open your browser to http://localhost:3000
2. You should see the home page with:
   - Backend status indicator (should show "Backend: healthy" in green)
   - Feature highlights
   - "Start Evaluation" button

3. Click "Start Evaluation" to go to the evaluation form

4. Fill in the form:
   - **Job Description**: Paste a job description (minimum 50 characters)
   - **Resume**: Paste a candidate's resume
   - **Company Context** (optional): Add any additional context

5. Click "Start Evaluation"
   - The evaluation will take 1-2 minutes
   - You'll see a loading spinner during processing

6. View the comprehensive results:
   - Decision summary with fit score and recommendation
   - Detailed rubric breakdown
   - Individual agent reviews (HR, Tech, Compliance)
   - Disagreement analysis
   - Interview plan with questions

7. Export results as JSON if needed

## Quick Test with Sample Data

You can test the system using the sample data from the backend:

```bash
# From the backend directory
cat examples/sample_data/job_description.txt
cat examples/sample_data/resume.txt
cat examples/sample_data/company_context.txt
```

Copy these into the frontend form and submit.

## Troubleshooting

### Backend won't start

**Issue**: Port 8000 already in use
```bash
# Use a different port
pdm run uvicorn src.api.main:app --reload --port 8001

# Update frontend .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

**Issue**: LLM provider errors
- Verify your API key is correct in `.env`
- For llama.cpp, ensure the server is running
- Check the backend logs for specific error messages

### Frontend won't start

**Issue**: Port 3000 already in use
```bash
# Next.js will automatically suggest using port 3001
# Or specify a port:
PORT=3001 npm run dev
```

**Issue**: Cannot connect to backend
- Verify backend is running at http://localhost:8000
- Check backend health: `curl http://localhost:8000/health`
- Verify `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local`

### Evaluation fails or times out

**Issue**: Timeout after 5 minutes
- Check backend logs for errors
- Verify your LLM provider is responding
- For llama.cpp, ensure your model is loaded and the server is responsive

**Issue**: Validation errors
- Ensure job description is at least 50 characters
- Ensure resume field is not empty
- Check that all required fields are filled

## Running in Production

### Backend Production Build

```bash
cd backend

# Install production dependencies only
pdm install --prod

# Run with production server
pdm run uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Frontend Production Build

```bash
cd frontend

# Build for production
npm run build

# Start production server
npm start
```

The production build will be optimized and much faster than the development server.

## Next Steps

- Read the [Backend README](backend/README.md) for detailed architecture information
- Read the [Frontend README](frontend/README.md) for component documentation
- Explore the example scripts in `backend/examples/`
- Review the test suite in `backend/tests/`
- Customize prompts in the `prompts/` directory (future feature)

## Development Workflow

**Backend Development:**
```bash
cd backend

# Run tests
pdm run pytest

# Run tests with coverage
pdm run pytest --cov=src --cov-report=html

# Format code
pdm run black src tests

# Type checking
pdm run mypy src
```

**Frontend Development:**
```bash
cd frontend

# Run linter
npm run lint

# Build and check for errors
npm run build
```

## Getting Help

- Check the documentation in `README.md`
- Review backend docs in `backend/README.md`
- Review frontend docs in `frontend/README.md`
- Look at example code in `backend/examples/`

## Summary

You now have a fully functional hiring evaluation system with:
- Backend API running at http://localhost:8000
- Frontend UI running at http://localhost:3000
- Multi-agent evaluation pipeline
- Comprehensive results display
- Export capabilities

Start evaluating candidates through the web interface at http://localhost:3000!
