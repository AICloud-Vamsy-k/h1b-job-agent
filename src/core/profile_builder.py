# src/core/profile_builder.py  # ✅ RENAMED from profile_summary.py

from pathlib import Path
from typing import Optional

from openai import OpenAI
from config.settings import DEFAULT_MODEL_NAME, OPENAI_API_KEY, OPENAI_API_BASE
from src.rag.profile_rag import _load_latest_resume_text  # ✅ UPDATED: Uses new RAG resume loader

PROFILE_SUMMARY_PATH = Path("data/profile_summary.txt")

_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE or None,
)

def call_chat_model(prompt: str) -> str:
    resp = _client.chat.completions.create(
        model=DEFAULT_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content

def get_or_build_profile_summary() -> Optional[str]:
    """
    Return a short profile summary derived from the **latest uploaded resume**.
    If not cached, generate once via LLM and store.
    """
    if PROFILE_SUMMARY_PATH.exists():
        return PROFILE_SUMMARY_PATH.read_text(encoding="utf-8")

    # ✅ UPDATED: Load from latest uploaded DOCX (matches RAG)
    try:
        resume_text = _load_latest_resume_text()
    except FileNotFoundError:
        return None  # No resume uploaded yet

    # Use only a snippet to avoid huge prompts (same logic)
    resume_snippet = resume_text[:8000]

    prompt = (
        "You are summarizing a candidate's resume.\n"
        "Given the resume text below, write a concise 5-7 line professional summary "
        "highlighting key skills, domains, and experience.\n\n"
        f"RESUME:\n{resume_snippet}\n"
    )

    summary = call_chat_model(prompt)
    PROFILE_SUMMARY_PATH.write_text(summary, encoding="utf-8")
    return summary
