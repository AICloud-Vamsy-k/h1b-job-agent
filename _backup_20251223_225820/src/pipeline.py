# src/pipeline.py

from pathlib import Path
import csv
from typing import List, Dict, Any

from src.job_sources import get_candidate_jobs, JobPosting
from src.job_match_crew import evaluate_job
from src.resume_builder_crew import generate_tailored_resume
from src.gap_analyzer_crew import analyze_gaps_for_learning

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_daily_job_pipeline(
    sponsorship_threshold: float = 0.6,
    match_threshold: float = 0.65,
    generate_resumes: bool = False,
) -> Path:
    """
    Load candidate jobs, score them, filter by sponsorship + match score,
    optionally generate tailored resumes and gap plans, and write a CSV report.
    """
    jobs: List[JobPosting] = get_candidate_jobs()

    report_rows: List[Dict[str, Any]] = []

    for job in jobs:
        print(f"\n=== Evaluating job {job.id}: {job.title} at {job.company} ===")
        match_result = evaluate_job(job.description)
        match_score = match_result.get("match_score") or 0.0

        strengths = match_result.get("strengths") or []
        gaps = match_result.get("gaps") or []

        # Join into short strings (truncate for CSV)
        strengths_str = "; ".join(strengths)[:500]
        gaps_str = "; ".join(gaps)[:500]

        print(f"Sponsorship score: {job.sponsorship_score:.2f}")
        print(f"Match score:       {match_score:.2f}")

        # Decide if this job is a "good candidate"
        is_candidate = (
            job.sponsorship_score >= sponsorship_threshold
            and match_score >= match_threshold
        )

        tailored_resume_path = ""
        gap_plan_path = ""

        if is_candidate:
            # Optional: generate tailored resume
            if generate_resumes:
                print("-> Generating tailored resume for this job...")
                resume_result = generate_tailored_resume(job.description, match_result)

                # Save markdown preview
                filename = f"tailored_resume_job_{job.id}.md"
                resume_path = OUTPUT_DIR / filename
                resume_path.write_text(resume_result["markdown_text"], encoding="utf-8")
                tailored_resume_path = str(resume_path)

                # Optionally also copy DOCX next to it if available
                docx_path = resume_result.get("docx_path")
                if docx_path is not None:
                    target_docx = resume_path.with_suffix(".docx")
                    target_docx.write_bytes(docx_path.read_bytes())

            else:
                print("-> Candidate job, but resume generation disabled.")

            # Generate gap analysis + learning plan for this job
            print("-> Generating gap analysis + learning plan for this job...")
            gap_text = analyze_gaps_for_learning(job.description, match_result)
            gap_filename = f"gap_learning_plan_job_{job.id}.md"
            gap_path = OUTPUT_DIR / gap_filename
            gap_path.write_text(gap_text, encoding="utf-8")
            gap_plan_path = str(gap_path)
        else:
            print("-> Job skipped (low sponsorship or match score).")

        report_rows.append(
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "url": job.url,
                "sponsorship_score": job.sponsorship_score,
                "match_score": match_score,
                "is_candidate": is_candidate,
                "resume_path": tailored_resume_path,
                "gap_plan_path": gap_plan_path,
                "strengths": strengths_str,
                "gaps": gaps_str,
            }
        )

    # Write report CSV
    report_path = OUTPUT_DIR / "daily_report.csv"
    with report_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "id",
            "title",
            "company",
            "location",
            "url",
            "sponsorship_score",
            "match_score",
            "is_candidate",
            "resume_path",
            "gap_plan_path",
            "strengths",
            "gaps",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    print(f"\nDaily report written to: {report_path}")
    return report_path
