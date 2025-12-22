from textwrap import dedent
from pathlib import Path
from .job_match_crew import run_job_match_example, evaluate_job
from .resume_builder_crew import generate_tailored_resume
from .gap_analyzer_crew import analyze_gaps_for_learning
from .pipeline import run_daily_job_pipeline




def run_daily_pipeline():
    """
    Menu:
    1 = run the built-in sample job match example
    2 = paste a job description and evaluate match
    3 = paste a job description, evaluate match, and generate a tailored resume
    """
    choice = input(
        "Choose mode:\n"
        "1 = Run sample job match example\n"
        "2 = Paste a job description and evaluate\n"
        "3 = Paste a job description and generate tailored resume\n"
        "4 = Paste a job description and get gap analysis + learning plan\n"
        "5 = Run daily pipeline on jobs_sample.csv\n"
        "Enter 1, 2, 3, 4 or 5: "
    ).strip()

    if choice == "1":
        # Existing sample job evaluation
        run_job_match_example()

    elif choice == "2":
        # Evaluate a pasted JD
        print(
            "Paste the job description below.\n"
            "Finish input with a single line containing only 'END':"
        )
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)

        job_text = "\n".join(lines)
        job_text = dedent(job_text)

        print("\n=== Evaluating pasted job description ===\n")
        result = evaluate_job(job_text)
        print("=== Job Match Crew Result ===")
        print(result)

    elif choice == "3":
        # Evaluate + generate tailored resume
        print(
            "Paste the job description below.\n"
            "Finish input with a single line containing only 'END':"
        )
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)

        job_text = "\n".join(lines)
        job_text = dedent(job_text)

        print("\n=== Evaluating pasted job description ===\n")
        match_result = evaluate_job(job_text)
        print("=== Job Match Crew Result ===")
        print("Match score:", match_result.get("match_score"))
        print("Strengths:", match_result.get("strengths"))
        print("Gaps:", match_result.get("gaps"))
        print("Summary:", match_result.get("summary"))
        print()

        confirm = input(
            "Generate tailored resume for this job using the base resume? (y/n): "
        ).strip().lower()
        if confirm != "y":
            print("Cancelled. No resume generated.")
            return

        print("\nGenerating tailored resume... This may take a few seconds.\n")
        tailored_resume = generate_tailored_resume(job_text, match_result)

        # Ensure output directory exists
        OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        out_path = OUTPUT_DIR / "tailored_resume.md"
        out_path.write_text(tailored_resume, encoding="utf-8")

        print(f"Tailored resume saved to: {out_path}")

    elif choice == "4":
        # Gap analysis + learning ideas
        print(
            "Paste the job description below.\n"
            "Finish input with a single line containing only 'END':"
        )
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)

        job_text = "\n".join(lines)
        job_text = dedent(job_text)

        print("\n=== Evaluating pasted job description ===\n")
        match_result = evaluate_job(job_text)
        print("Match score:", match_result.get("match_score"))
        print("Strengths:", match_result.get("strengths"))
        print("Gaps:", match_result.get("gaps"))
        print("Summary:", match_result.get("summary"))
        print()

        confirm = input(
            "Generate gap analysis + learning plan + project ideas for this job? (y/n): "
        ).strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return

        print("\nGenerating gap analysis and learning plan...\n")
        report_text = analyze_gaps_for_learning(job_text, match_result)

        OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "gap_learning_plan.md"
        out_path.write_text(report_text, encoding="utf-8")

        print(f"Gap analysis + learning plan saved to: {out_path}")

    elif choice == "5":
        print("Running daily pipeline on data/jobs_sample.csv ...")
        confirm_resumes = input(
            "Generate tailored resumes for candidate jobs as well? (y/n): "
        ).strip().lower()
        generate_resumes = confirm_resumes == "y"

        run_daily_job_pipeline(
            sponsorship_threshold=0.6,
            match_threshold=0.65,
            generate_resumes=generate_resumes,
        )

    else:
        print("Invalid choice. Please run again and enter 1, 2 or 3.")


if __name__ == "__main__":
    run_daily_pipeline()
