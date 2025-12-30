"""Batch testing script to run workflow on all sample combinations.

This script tests all combinations of job descriptions and resumes in the
sample_data directory, collecting results and generating a comparison report.

Usage:
    python examples/run_all_samples.py
    python examples/run_all_samples.py --output-dir custom_results
"""

import asyncio
import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import time

# Add parent directory to path for src imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.graph import run_hiring_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_sample_files(sample_dir: Path) -> tuple[List[Path], List[Path]]:
    """Find all job and resume files in sample data directory.

    Args:
        sample_dir: Path to sample_data directory

    Returns:
        Tuple of (job_files, resume_files)
    """
    job_files = sorted(sample_dir.glob("job_*.txt"))
    resume_files = sorted(sample_dir.glob("resume_*.txt"))

    logger.info(f"Found {len(job_files)} job descriptions and {len(resume_files)} resumes")

    return job_files, resume_files


async def run_single_combination(
    job_file: Path,
    resume_file: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """Run workflow for a single job-resume combination.

    Args:
        job_file: Path to job description file
        resume_file: Path to resume file
        output_dir: Directory to save results

    Returns:
        Dictionary with execution results and metadata
    """
    logger.info(f"Running: {job_file.stem} + {resume_file.stem}")

    job_description = job_file.read_text(encoding="utf-8")
    resume = resume_file.read_text(encoding="utf-8")

    start_time = time.time()
    error = None

    try:
        result = await run_hiring_workflow(
            job_description=job_description,
            resume=resume
        )

        duration = time.time() - start_time

        # Extract key metrics
        decision = result["decision_packet"]
        panel_reviews = result["panel_reviews"]

        # Calculate panel score variance
        panel_scores = [
            sum(cat.score for cat in review.category_scores) / len(review.category_scores)
            for review in panel_reviews
        ]
        avg_panel_score = sum(panel_scores) / len(panel_scores)
        panel_variance = sum((s - avg_panel_score) ** 2 for s in panel_scores) / len(panel_scores)

        # Save full results to JSON
        output_file = output_dir / f"{job_file.stem}___{resume_file.stem}.json"
        json_result = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": duration,
                "job_file": job_file.name,
                "resume_file": resume_file.name,
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

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✓ Completed in {duration:.2f}s - {decision.recommendation} ({decision.overall_fit_score:.2f})")

        return {
            "job_file": job_file.name,
            "resume_file": resume_file.name,
            "success": True,
            "duration": duration,
            "overall_fit_score": decision.overall_fit_score,
            "recommendation": decision.recommendation,
            "confidence": decision.confidence,
            "num_disagreements": len(decision.disagreements),
            "num_must_have_gaps": len(decision.must_have_gaps),
            "num_interview_questions": sum(len(questions) for questions in result["interview_plan"].questions_by_interviewer.values()),
            "avg_panel_score": avg_panel_score,
            "panel_variance": panel_variance,
            "error": None
        }

    except Exception as e:
        duration = time.time() - start_time
        error = str(e)
        logger.error(f"  ✗ Failed after {duration:.2f}s: {error}")

        return {
            "job_file": job_file.name,
            "resume_file": resume_file.name,
            "success": False,
            "duration": duration,
            "error": error
        }


async def main():
    """Run workflow on all sample combinations and generate report."""
    parser = argparse.ArgumentParser(description="Run workflow on all sample combinations")
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to save results (relative to examples/)"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("  BATCH TESTING - ALL SAMPLE COMBINATIONS")
    print("="*70 + "\n")

    # Setup directories
    examples_dir = Path(__file__).parent
    sample_dir = examples_dir / "sample_data"
    output_dir = examples_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Output directory: {output_dir}")

    # Load settings
    settings = get_settings()
    logger.info(f"LLM Provider: {settings.llm_provider}")

    # Find all sample files
    job_files, resume_files = find_sample_files(sample_dir)

    if not job_files or not resume_files:
        print("❌ No sample files found. Please check sample_data directory.\n")
        sys.exit(1)

    print(f"Found {len(job_files)} job descriptions:")
    for job_file in job_files:
        print(f"  • {job_file.name}")

    print(f"\nFound {len(resume_files)} resumes:")
    for resume_file in resume_files:
        print(f"  • {resume_file.name}")

    total_combinations = len(job_files) * len(resume_files)
    print(f"\nTotal combinations to test: {total_combinations}\n")

    # Run all combinations
    results = []
    for i, job_file in enumerate(job_files, 1):
        for j, resume_file in enumerate(resume_files, 1):
            combo_num = (i - 1) * len(resume_files) + j
            print(f"[{combo_num}/{total_combinations}] Testing: {job_file.stem} + {resume_file.stem}")

            result = await run_single_combination(job_file, resume_file, output_dir)
            results.append(result)

            # Brief pause to avoid rate limits
            await asyncio.sleep(1)

    # Generate summary CSV
    csv_path = output_dir / "summary.csv"
    fieldnames = [
        "job_file", "resume_file", "success", "duration", "overall_fit_score",
        "recommendation", "confidence", "num_disagreements", "num_must_have_gaps",
        "num_interview_questions", "avg_panel_score", "panel_variance", "error"
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Summary saved to: {csv_path}")

    # Print summary statistics
    print("\n" + "="*70)
    print("  EXECUTION SUMMARY")
    print("="*70 + "\n")

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"Total combinations: {len(results)}")
    print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")

    if successful:
        avg_duration = sum(r["duration"] for r in successful) / len(successful)
        print(f"\nAverage execution time: {avg_duration:.2f}s")

        # Recommendation distribution
        recommendations = {}
        for r in successful:
            rec = r["recommendation"]
            recommendations[rec] = recommendations.get(rec, 0) + 1

        print("\nRecommendation distribution:")
        for rec, count in sorted(recommendations.items()):
            print(f"  {rec}: {count}")

        # Score statistics
        scores = [r["overall_fit_score"] for r in successful]
        print(f"\nScore statistics:")
        print(f"  Min: {min(scores):.2f}")
        print(f"  Max: {max(scores):.2f}")
        print(f"  Average: {sum(scores)/len(scores):.2f}")

        # Disagreement statistics
        total_disagreements = sum(r["num_disagreements"] for r in successful)
        print(f"\nTotal disagreements detected: {total_disagreements}")
        combos_with_disagreements = sum(1 for r in successful if r["num_disagreements"] > 0)
        print(f"Combinations with disagreements: {combos_with_disagreements}/{len(successful)}")

    if failed:
        print("\n❌ Failed combinations:")
        for r in failed:
            print(f"  • {r['job_file']} + {r['resume_file']}")
            print(f"    Error: {r['error']}")

    print(f"\n💾 Results saved to: {output_dir}")
    print(f"📊 Summary CSV: {csv_path}")

    print("\n" + "="*70)
    print("  BATCH TESTING COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
