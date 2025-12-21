# src/resume_builder_crew.py

from pathlib import Path
from typing import Any, Dict

from crewai import Agent, Task, Crew

from src.config import DEFAULT_MODEL_NAME
from src.job_match_crew import load_profile_text  # you already have this


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_base_resume() -> str:
    """Load the base resume text from data/base_resume.md."""
    resume_path = DATA_DIR / "base_resume.md"
    if not resume_path.exists():
        raise FileNotFoundError(f"Base resume not found at {resume_path}")
    return resume_path.read_text(encoding="utf-8")


def create_resume_editor_crew(
    job_description: str,
    match_result: Dict[str, Any],
    base_resume_text: str,
    profile_text: str,
) -> Crew:
    """Create a CrewAI crew that tailors the resume for a specific job."""
    # 1) Define the agent
    resume_agent = Agent(
        role="Resume Tailor and ATS-Aware Writer",
        goal=(
            "Rewrite and tailor the candidate's resume for the given job "
            "so it sounds human-written, highlights true relevant strengths, "
            "and stays 100% honest with no fake skills, companies, or dates."
        ),
        backstory=(
            "You are a senior technical recruiter and resume writer who "
            "specializes in software/data/AI roles. "
            "You know how ATS keyword filters work and how human hiring "
            "managers read resumes. You never fabricate experience."
        ),
        llm=DEFAULT_MODEL_NAME,
        verbose=False,
    )

    # 2) Build a detailed task description
    match_score = match_result.get("match_score")
    strengths = match_result.get("strengths")
    gaps = match_result.get("gaps")
    summary = match_result.get("summary")

    # Turn strengths/gaps into simple bullet text for the prompt
    strengths_text = "\n".join(f"- {s}" for s in strengths or [])
    gaps_text = "\n".join(f"- {g}" for g in gaps or [])

    task_description = f"""
You are given:

1) The job description:
-----------------------
{job_description}

2) The candidate's profile summary (from a separate profile file):
------------------------------------------------------------------
{profile_text}

3) The candidate's current base resume:
--------------------------------------
{base_resume_text}

4) An analysis of how well the candidate matches this job:
----------------------------------------------------------
Match score (0-1): {match_score}

Strengths:
{strengths_text}

Gaps:
{gaps_text}

Summary of fit:
{summary}

Your job:
- Produce a fully tailored resume for THIS specific job.
- Keep all facts honest: do NOT invent companies, dates, degrees, or tools the candidate does not already have.
- You MAY:
  - Reorder sections or bullets.
  - Rewrite sentences to better match the job wording.
  - Emphasize the most relevant projects/skills for this JD.
  - Add specific metrics or impact ONLY if they are clearly implied by the existing resume/profile.
- You MUST:
  - Make the result look like it was carefully written by a human.
  - Avoid obvious AI phrases (e.g., "As an AI language model", generic buzzword walls).
  - Keep a clean, simple structure: Summary, Skills, Experience, Education, Certifications.
  - Use bullet points under Experience.

Output:
Return ONLY the final tailored resume as Markdown or plain text.
"""

    resume_task = Task(
        description=task_description,
        expected_output=(
            "A complete, human-sounding, tailored resume text for this job, "
            "with sections: Summary, Skills, Experience, Education, Certifications."
        ),
        agent=resume_agent,
    )

    crew = Crew(
        agents=[resume_agent],
        tasks=[resume_task],
        verbose=False,
    )
    return crew


def generate_tailored_resume(job_description: str, match_result: Dict[str, Any]) -> str:
    """High-level API: given JD + match_result, return tailored resume text."""
    profile_text = load_profile_text()
    base_resume_text = load_base_resume()

    crew = create_resume_editor_crew(
        job_description=job_description,
        match_result=match_result,
        base_resume_text=base_resume_text,
        profile_text=profile_text,
    )

    result = crew.kickoff()
    # result is usually a TaskOutput; get its raw text
    # If your CrewAI version returns plain string, this will still work.
    try:
        tailored_resume = str(result)
    except Exception:
        tailored_resume = result  # fallback

    return tailored_resume
