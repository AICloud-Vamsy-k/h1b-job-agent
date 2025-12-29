# src/resume_builder_crew.py

from pathlib import Path
from typing import Any, Dict
import re
import json
from crewai import Agent, Task, Crew

from config.settings import DEFAULT_MODEL_NAME
from src.rag.profile_rag import retrieve_relevant_chunks, build_or_refresh_profile_index
from src.core.profile_builder import get_or_build_profile_summary
from src.core.resume_renderer import render_resume_docx_from_template

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

def create_resume_editor_crew(
    job_description: str,
    match_result: Dict[str, Any],
) -> Crew:
    """
    Create a CrewAI crew that tailors the resume for a specific job.

    Uses:
    - Profile summary derived from the current resume.
    - Resume-based RAG chunks from Chroma.
    """
    # BUILD INDEX FROM UPLOADED RESUME
    build_or_refresh_profile_index()

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

    # 2) Extract analysis fields
    match_score = match_result.get("match_score")
    strengths = match_result.get("strengths")
    gaps = match_result.get("gaps")
    summary = match_result.get("summary")

    strengths_text = "\n".join(f"- {s}" for s in strengths or [])
    gaps_text = "\n".join(f"- {g}" for g in gaps or [])

    # 3) Resume-based profile summary + RAG chunks
    profile_summary = get_or_build_profile_summary()
    relevant_chunks = retrieve_relevant_chunks(
        query="experience and skills relevant to this job description: " + job_description,
        top_k=10,
    )
    relevant_chunks_text = (
        "\n\n".join(relevant_chunks) if relevant_chunks else "(no relevant chunks found)"
    )

    # 4) Build detailed task description
    task_description = f"""
You are given:

1) The job description:
-----------------------
{job_description}

2) The candidate's profile summary (derived from the current resume):
--------------------------------------------------------------------
{profile_summary or "(no profile summary available; resume may not be set yet)"}

3) An analysis of how well the candidate matches this job:
----------------------------------------------------------
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

Your job:
- Produce tailored content for THIS specific job.
- Keep all facts honest: do NOT invent companies, dates, degrees, tools, or certifications the candidate does not already have.
- Prefer using information from the retrieved resume chunks when writing detailed bullets or project descriptions.
- You MAY:
  - Reorder sections or bullets.
  - Rewrite sentences to better match the job wording.
  - Emphasize the most relevant projects/skills for this JD.
  - Add specific metrics or impact ONLY if they are clearly implied by the existing resume, profile summary, or retrieved chunks.
- You MUST:
  - Make the result look like it was carefully written by a human.
  - Avoid obvious AI phrases (e.g., "As an AI language model", generic buzzword walls).

Output format:
Return ONLY a JSON object with these keys (all values are plain text strings):
{{
  "summary": "2-3 sentences professional summary tailored to this job",
  "skills": "Comma-separated or bulleted list of relevant skills (one per line, no extra formatting)",
  "experience": "Bullet-point list of relevant experience bullets (use '- ' prefix for each bullet)",
  "education": "Degrees, schools (one per line, use '- ' prefix)",
  "certifications": "Any certifications or credentials (one per line, use '- ' prefix, or empty string if none)"
}}

Only output the JSON object, nothing else. Ensure all double quotes are escaped properly.
"""

    resume_task = Task(
        description=task_description,
        expected_output=(
            "A JSON object with keys: summary, skills, experience, education, certifications. "
            "Each value is plain text suitable for Word document sections."
        ),
        agent=resume_agent,
    )

    crew = Crew(
        agents=[resume_agent],
        tasks=[resume_task],
        verbose=False,
    )
    return crew

def _json_to_markdown(json_content: Dict[str, Any]) -> str:
    """Convert JSON content to markdown for UI preview."""
    parts: list[str] = []

    if json_content.get("summary"):
        parts.append("## Professional Summary\n")
        parts.append(json_content["summary"])

    if json_content.get("skills"):
        parts.append("\n## Skills\n")
        parts.append(json_content["skills"])

    if json_content.get("experience"):
        parts.append("\n## Experience\n")
        parts.append(json_content["experience"])

    if json_content.get("education"):
        parts.append("\n## Education\n")
        parts.append(json_content["education"])

    if json_content.get("certifications"):
        parts.append("\n## Certifications\n")
        parts.append(json_content["certifications"])

    return "\n".join(parts)

def generate_tailored_resume(job_description: str, match_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    High-level API: given JD + match_result, generate a tailored resume.

    Returns:
        {
          "docx_path": Path or None,
          "markdown_text": str,
          "json_content": dict or None,
          "raw": str,
        }
    """
    crew = create_resume_editor_crew(
        job_description=job_description,
        match_result=match_result,        
    )

    result = crew.kickoff()

    try:
        raw_text = result.raw  # CrewOutput.raw if available
    except Exception:
        raw_text = str(result)

    json_content: Dict[str, Any] | None = None
    docx_path: Path | None = None

    # Try to parse JSON from agent output
    try:
        json_content = json.loads(raw_text)

        context = {
            "SUMMARY": json_content.get("summary", ""),
            "SKILLS": json_content.get("skills", ""),
            "EXPERIENCE": json_content.get("experience", ""),
            "EDUCATION": json_content.get("education", ""),
            "CERTIFICATIONS": json_content.get("certifications", ""),
        }

        # Render DOCX from template; may return None if no template
        docx_path = render_resume_docx_from_template(context)

    except json.JSONDecodeError:
        print("Warning: Resume agent output is not valid JSON; using raw text only.")

    markdown_text = _json_to_markdown(json_content) if json_content else raw_text

    return {
        "docx_path": docx_path,
        "markdown_text": markdown_text,
        "json_content": json_content,
        "raw": raw_text,
    }
