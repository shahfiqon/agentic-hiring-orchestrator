"""Example pipeline execution script.

This script demonstrates how to run the agentic hiring evaluation pipeline
with sample candidate data.

Usage:
    pdm run pipeline
    # or
    python examples/run_pipeline.py
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for src imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Run the hiring evaluation pipeline with sample data."""
    logger.info("Starting Agentic Hiring Orchestrator pipeline")

    # Load settings
    settings = get_settings()
    logger.info(f"Using LLM provider: {settings.llm_provider}")
    logger.info(f"Working memory enabled: {settings.enable_working_memory}")
    logger.info(f"Parallel execution: {settings.parallel_execution}")

    # Sample candidate data
    sample_candidate = {
        "name": "Jane Doe",
        "role": "Senior Backend Engineer",
        "resume": "Sample resume content...",
        "experience_years": 5,
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]
    }

    logger.info(f"Evaluating candidate: {sample_candidate['name']}")
    logger.info(f"Position: {sample_candidate['role']}")

    # TODO: Initialize and run the graph when implemented
    # For now, just demonstrate configuration is working
    logger.info("Pipeline configuration validated successfully")
    logger.info("Graph execution will be implemented in src/graph/")

    # Output sample result
    result = {
        "candidate": sample_candidate["name"],
        "status": "ready",
        "message": "Pipeline is configured and ready to execute when graph is implemented"
    }

    logger.info(f"Result: {json.dumps(result, indent=2)}")
    return result


if __name__ == "__main__":
    asyncio.run(main())
