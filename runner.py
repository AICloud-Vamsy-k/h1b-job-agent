"""
H1B Job Agent - Unified Entry Point
Combines all features from old src/runner.py + new runner.py
"""
import sys
from pathlib import Path
from textwrap import dedent

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def show_menu():
    print("\n" + "="*70)
    print("  H1B JOB AGENT - Main Menu")
    print("="*70)
    print("\n1. Run sample job match example")
    print("2. Paste JD and evaluate match")
    print("3. Paste JD and generate tailored resume")
    print("4. Paste JD and get gap analysis + learning plan")
    print("5. Run H1B Job Finder (real-time job scraping)")
    print("6. Run Daily Pipeline (batch process jobs_sample.csv)")
    print("7. Launch Streamlit UI")
    print("8. Exit")
    print("="*70)

def run_sample_job_match():
    """Option 1: Run built-in sample"""
    from src.crews.job_match_crew import run_job_match_example
    run_job_match_example()

def evaluate_pasted_jd():
    """Option 2: Evaluate pasted JD"""
    from src.crews.job_match_crew import evaluate_job
    
    print("\nPaste job description below.")
    print("Finish with a line containing only 'END':")
    
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    
    job_text = dedent("\n".join(lines))
    
    print("\n=== Evaluating Job ===\n")
    result = evaluate_job(job_text)
    
    print("\n=== Results ===")
    print(f"Match score: {result.get('match_score')}")
    print(f"Strengths: {result.get('strengths')}")
    print(f"Gaps: {result.get('gaps')}")
    print(f"Summary: {result.get('summary')}")

def generate_tailored_resume_interactive():
    """Option 3: Generate tailored resume"""
    from src.crews.job_match_crew import evaluate_job
    from src.crews.resume_builder_crew import generate_tailored_resume
    
    print("\nPaste job description below.")
    print("Finish with a line containing only 'END':")
    
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    
    job_text = dedent("\n".join(lines))
    
    print("\n=== Evaluating Job ===\n")
    match_result = evaluate_job(job_text)
    
    print(f"Match score: {match_result.get('match_score')}")
    print(f"Strengths: {match_result.get('strengths')}")
    print(f"Gaps: {match_result.get('gaps')}")
    
    confirm = input("\nGenerate tailored resume? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    print("\nGenerating tailored resume...")
    resume_result = generate_tailored_resume(job_text, match_result)
    
    # Save resume
    OUTPUT_DIR = Path(__file__).parent / "output" / "resumes"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    md_path = OUTPUT_DIR / "tailored_resume.md"
    md_path.write_text(resume_result["markdown_text"], encoding="utf-8")
    
    print(f"\n✅ Resume saved to: {md_path}")
    
    if resume_result.get("docx_path"):
        print(f"✅ DOCX saved to: {resume_result['docx_path']}")

def generate_gap_analysis_interactive():
    """Option 4: Gap analysis"""
    from src.crews.job_match_crew import evaluate_job
    from src.crews.gap_analyzer_crew import analyze_gaps_for_learning
    
    print("\nPaste job description below.")
    print("Finish with a line containing only 'END':")
    
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    
    job_text = dedent("\n".join(lines))
    
    print("\n=== Evaluating Job ===\n")
    match_result = evaluate_job(job_text)
    
    print(f"Match score: {match_result.get('match_score')}")
    print(f"Gaps: {match_result.get('gaps')}")
    
    confirm = input("\nGenerate gap analysis + learning plan? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    print("\nGenerating gap analysis...")
    report_text = analyze_gaps_for_learning(job_text, match_result)
    
    OUTPUT_DIR = Path(__file__).parent / "output" / "plans"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    out_path = OUTPUT_DIR / "gap_learning_plan.md"
    out_path.write_text(report_text, encoding="utf-8")
    
    print(f"\n✅ Gap analysis saved to: {out_path}")

def run_h1b_finder():
    """Option 5: H1B Job Finder"""
    from src.pipelines.h1b_pipeline import run_h1b_job_finder
    run_h1b_job_finder()

def run_daily_pipeline():
    """Option 6: Daily pipeline"""
    from src.pipelines.daily_pipeline import run_daily_job_pipeline
    
    confirm = input("Generate tailored resumes for candidate jobs? (y/n): ").strip().lower()
    generate_resumes = (confirm == 'y')
    
    run_daily_job_pipeline(
        sponsorship_threshold=0.6,
        match_threshold=0.65,
        generate_resumes=generate_resumes
    )

def launch_streamlit():
    """Option 7: Launch Streamlit"""
    import os
    os.system('streamlit run streamlit_app.py')

def main():
    """Main entry point"""
    while True:
        show_menu()
        choice = input("\nSelect (1-8): ").strip()
        
        if choice == '1':
            run_sample_job_match()
        elif choice == '2':
            evaluate_pasted_jd()
        elif choice == '3':
            generate_tailored_resume_interactive()
        elif choice == '4':
            generate_gap_analysis_interactive()
        elif choice == '5':
            run_h1b_finder()
        elif choice == '6':
            run_daily_pipeline()
        elif choice == '7':
            launch_streamlit()
        elif choice == '8':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")
        
        if choice in ['1', '2', '3', '4', '5', '6']:
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
