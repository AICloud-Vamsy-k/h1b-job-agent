# src/gap_analyzer_crew.py

from typing import Any, Dict

from crewai import Agent, Task, Crew

from config.settings import DEFAULT_MODEL_NAME
from src.rag.profile_rag import retrieve_relevant_chunks
from src.core.profile_builder import get_or_build_profile_summary


def create_gap_analyzer_crew(
    job_description: str,
    match_result: Dict[str, Any],
) -> Crew:
    """Create a Crew that analyzes gaps and proposes learning + project ideas."""

    gap_agent = Agent(
        role="Gap Analyst and Learning Coach",
        goal=(
            "Analyze the gaps between the candidate's profile and a given job "
            "description, then propose a focused learning plan and 1-2 realistic "
            "mini-project ideas to close the most important gaps."
        ),
        backstory=(
            "You are a senior data/AI engineer and mentor who helps engineers move "
            "from 50-70% fit to 90%+ fit for cloud/data/AI roles. "
            "You think practically about what can be learned in weeks or months, "
            "and you design project ideas that are realistic for one person."
        ),
        llm=DEFAULT_MODEL_NAME,
        verbose=False,
    )

    # Resume-based profile summary and RAG chunks
    profile_summary = get_or_build_profile_summary()

    match_score = match_result.get("match_score")
    strengths = match_result.get("strengths") or []
    gaps = match_result.get("gaps") or []
    summary = match_result.get("summary")

    strengths_text = "\n".join(f"- {s}" for s in strengths)
    gaps_text = "\n".join(f"- {g}" for g in gaps)

    # Use RAG to get the most relevant resume chunks for this JD
    #relevant_chunks = retrieve_relevant_chunks(
    #    query="skills and experience relevant to this job description: " + job_description,
    #    top_k=10,
    #)
    #relevant_chunks_text = "\n\n".join(relevant_chunks) if relevant_chunks else "(no relevant chunks found)"

    # TEMP: disable RAG
    relevant_chunks = []
    relevant_chunks_text = "(RAG disabled for debugging)"

    task_description = f"""
You are helping a senior engineer on H1B in the US improve fit for a specific job.

1) Job description:
-------------------
{job_description}

2) Candidate's profile summary (derived from the current resume):
-----------------------------------------------------------------
{profile_summary or "(no profile summary available; resume may not be set yet)"}

3) Job match analysis:
----------------------
Match score (0-1): {match_score}

Strengths:
{strengths_text}

Gaps:
{gaps_text}

Summary of fit:
{summary}

4) Most relevant resume chunks retrieved for this job (RAG over the current resume):
------------------------------------------------------------------------------------
{relevant_chunks_text}

Your job now:
- Identify the TOP 3-5 missing skills or experience areas that matter most for THIS job.
- For each key gap, propose:
  - What to learn (topics, tools, and concepts).
  - How long it might take at 2 hours/day (rough estimate, in weeks).
- Then propose 1-2 realistic mini-project ideas that:
  - Can be built in 2-4 weeks.
  - Use realistic, public or dummy data.
  - Produce something that can be shown in interviews (GitHub repo, screenshots, small demo).
- Make sure project ideas are aligned with this JD (e.g., cloud data pipelines, ETL, Databricks, Snowflake, leadership, etc., depending on the gaps).
- Prefer using information from the retrieved resume chunks when referring to the candidate's existing strengths and experience.
- Remember: do NOT assume the candidate already has skills that are not in the profile/resume or retrieved chunks; these are learning goals, not current skills.

Output format:
1) Short paragraph: overall view of the gaps.
2) Bullet list: "Key gaps to close".
3) Bullet list: "Learning plan (2 hours/day)" with weeks and topics.
4) Bullet list: "Mini-project ideas" with 2-3 bullets per project.
"""

    gap_task = Task(
        description=task_description,
        expected_output=(
            "Text explanation of gaps, learning plan, and 1-2 concrete mini-project ideas."
        ),
        agent=gap_agent,
    )

    crew = Crew(
        agents=[gap_agent],
        tasks=[gap_task],
        verbose=False,
    )
    return crew


def analyze_gaps_for_learning(
    job_description: str,
    match_result: Dict[str, Any],
) -> str:
    """
    High-level API:
    Given a job description and the match_result dict,
    return a text report with gaps, learning plan, and project ideas.
    """
    crew = create_gap_analyzer_crew(job_description, match_result)
    result = crew.kickoff()

    # result is a CrewOutput / TaskOutput-like object; get its text
    try:
        report_text = result.raw
    except Exception:
        report_text = str(result)

    return report_text
