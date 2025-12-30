"""Example pipeline execution script.

This script demonstrates how to run the agentic hiring evaluation pipeline
with sample candidate data.

Usage:
    pdm run pipeline
    # or
    python examples/run_pipeline.py

    # With custom files
    python examples/run_pipeline.py --job sample_data/job_backend_engineer.txt --resume sample_data/resume_moderate_candidate.txt

    # Verbose mode
    python examples/run_pipeline.py --verbose

    # Save to JSON
    python examples/run_pipeline.py --output-json results/output.json
"""

import asyncio
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime

# Add parent directory to path for src imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.graph import run_hiring_workflow
from src.utils.output_formatters import (
    format_workflow_results,
    format_execution_metadata,
    format_validation_summary
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pipeline_execution.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_sample_data(job_file: str, resume_file: str) -> Tuple[str, str]:
    """Load job description and resume from sample data files.

    Args:
        job_file: Path to job description file (relative to sample_data directory)
        resume_file: Path to resume file (relative to sample_data directory)

    Returns:
        Tuple of (job_description, resume) as strings

    Raises:
        FileNotFoundError: If files don't exist
    """
    base_dir = Path(__file__).parent / "sample_data"

    job_path = base_dir / job_file
    resume_path = base_dir / resume_file

    if not job_path.exists():
        raise FileNotFoundError(f"Job description not found: {job_path}")
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume not found: {resume_path}")

    job_description = job_path.read_text(encoding="utf-8")
    resume = resume_path.read_text(encoding="utf-8")

    logger.info(f"Loaded job description from: {job_file}")
    logger.info(f"Loaded resume from: {resume_file}")

    return job_description, resume


def validate_workflow_output(result: Dict[str, Any]) -> bool:
    """Check that all expected fields are present in workflow output.

    Args:
        result: Workflow output dictionary

    Returns:
        True if all required fields present
    """
    required_fields = ["rubric", "panel_reviews", "decision_packet", "interview_plan"]
    missing = [field for field in required_fields if field not in result]

    if missing:
        logger.warning(f"Missing required fields: {missing}")
        return False

    logger.info("✓ All required fields present")
    return True


def validate_panel_consistency(result: Dict[str, Any]) -> bool:
    """Verify panel_reviews and agent_working_memory have matching agent roles.

    Args:
        result: Workflow output dictionary

    Returns:
        True if panel is consistent
    """
    if "panel_reviews" not in result:
        return False

    review_agents = {review.agent_role for review in result["panel_reviews"]}

    if "agent_working_memory" in result:
        memory_agents = set(result["agent_working_memory"].keys())
        if review_agents != memory_agents:
            logger.warning(f"Agent mismatch - Reviews: {review_agents}, Memory: {memory_agents}")
            return False

    expected_agents = {"HR", "Tech", "Compliance"}
    if review_agents != expected_agents:
        logger.warning(f"Unexpected agent set: {review_agents}, expected: {expected_agents}")
        return False

    logger.info(f"✓ Panel consistency verified ({len(review_agents)} agents)")
    return True


def check_disagreements_detected(result: Dict[str, Any]) -> bool:
    """Confirm disagreements are properly identified when score deltas exist.

    Args:
        result: Workflow output dictionary

    Returns:
        True if disagreement detection working correctly
    """
    if "decision_packet" not in result or "panel_reviews" not in result:
        return False

    decision = result["decision_packet"]

    # Calculate actual score deltas across categories
    category_scores = {}
    for review in result["panel_reviews"]:
        for cat_score in review.category_scores:
            cat_name = cat_score.category_name
            if cat_name not in category_scores:
                category_scores[cat_name] = []
            category_scores[cat_name].append(cat_score.score)

    # Check for significant deltas (>1.0 difference)
    has_significant_delta = False
    for cat_name, scores in category_scores.items():
        if max(scores) - min(scores) > 1.0:
            has_significant_delta = True
            logger.info(f"  Significant delta in {cat_name}: {scores}")

    has_disagreements = bool(decision.disagreements)

    if has_significant_delta and not has_disagreements:
        logger.warning("⚠  Score deltas detected but no disagreements recorded")
        return False

    if has_disagreements:
        logger.info(f"✓ Disagreements detected ({len(decision.disagreements)} total)")
    else:
        logger.info("✓ No disagreements (panel aligned)")

    return True


def validate_decision_packet(result: Dict[str, Any]) -> bool:
    """Verify decision packet has valid recommendation and confidence.

    Args:
        result: Workflow output dictionary

    Returns:
        True if decision packet is valid
    """
    if "decision_packet" not in result:
        return False

    decision = result["decision_packet"]

    valid_recommendations = {"Hire", "Lean hire", "Lean no", "No", None}
    if decision.recommendation not in valid_recommendations:
        logger.warning(f"Invalid recommendation: {decision.recommendation}")
        return False

    valid_confidence = {"high", "medium", "low"}
    if decision.confidence not in valid_confidence:
        logger.warning(f"Invalid confidence: {decision.confidence}")
        return False

    if not (0.0 <= decision.overall_fit_score <= 5.0):
        logger.warning(f"Invalid overall_fit_score: {decision.overall_fit_score}")
        return False

    logger.info(f"✓ Decision packet valid (recommendation: {decision.recommendation}, confidence: {decision.confidence})")
    return True


async def main():
    """Run the hiring evaluation pipeline with sample data."""
    parser = argparse.ArgumentParser(description="Run agentic hiring workflow")
    parser.add_argument(
        "--job",
        default="job_senior_ai_engineer.txt",
        help="Job description file (relative to sample_data/)"
    )
    parser.add_argument(
        "--resume",
        default="resume_strong_candidate.txt",
        help="Resume file (relative to sample_data/)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output including working memories"
    )
    parser.add_argument(
        "--output-json",
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--company-context",
        help="Optional company context string"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("  AGENTIC HIRING ORCHESTRATOR - WORKFLOW EXECUTION")
    print("="*70 + "\n")

    # Load settings
    settings = get_settings()
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Working Memory: {settings.enable_working_memory}")
    logger.info(f"Parallel Execution: {settings.parallel_execution}")

    # Load sample data
    try:
        job_description, resume = load_sample_data(args.job, args.resume)
    except FileNotFoundError as e:
        logger.error(f"Error loading files: {e}")
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)

    # Display execution metadata
    start_time = time.time()
    timestamp = datetime.now()

    job_preview = job_description.replace('\n', ' ')[:150]
    resume_preview = resume.replace('\n', ' ')[:150]

    print(format_execution_metadata(
        duration_seconds=0,
        timestamp=timestamp,
        job_desc_preview=job_preview,
        resume_preview=resume_preview
    ))

    # Execute workflow
    try:
        logger.info("Invoking run_hiring_workflow...")
        print("🚀 Executing workflow (this may take 1-2 minutes)...\n")

        result = await run_hiring_workflow(
            job_description=job_description,
            resume=resume,
            company_context=args.company_context
        )

        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"Workflow completed in {duration:.2f} seconds")
        print(f"✅ Workflow completed in {duration:.2f} seconds\n")

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        print(f"\n❌ Workflow execution failed: {e}\n")
        print("Check pipeline_execution.log for full stack trace\n")
        sys.exit(1)

    # Display formatted results
    print(format_workflow_results(result, verbose=args.verbose))

    # Run validation checks
    print("\n" + "="*70)
    print("  VALIDATION CHECKS")
    print("="*70 + "\n")

    has_all_fields = validate_workflow_output(result)
    panel_consistent = validate_panel_consistency(result)
    disagreements_ok = check_disagreements_detected(result)
    decision_valid = validate_decision_packet(result)

    print(format_validation_summary(
        has_all_fields=has_all_fields,
        panel_consistent=panel_consistent,
        disagreements_detected=disagreements_ok,
        decision_valid=decision_valid
    ))

    # Save to JSON if requested
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Pydantic models to dicts for JSON serialization
        json_result = {
            "metadata": {
                "timestamp": timestamp.isoformat(),
                "duration_seconds": duration,
                "job_file": args.job,
                "resume_file": args.resume,
            },
            "rubric": result["rubric"].model_dump(),
            "panel_reviews": [r.model_dump() for r in result["panel_reviews"]],
            "decision_packet": result["decision_packet"].model_dump(),
            "interview_plan": result["interview_plan"].model_dump(),
        }

        if "agent_working_memory" in result:
            json_result["agent_working_memory"] = {
                k: v.model_dump() for k, v in result["agent_working_memory"].items()
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to: {output_path}")
        print(f"💾 Results saved to: {output_path}\n")

    print("="*70)
    print("  EXECUTION COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
