# src/resume_docx_renderer.py

from pathlib import Path
from typing import Dict, Optional

from docxtpl import DocxTemplate

from src.resume_source import get_resume_template_path


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def render_resume_docx_from_template(
    context: Dict[str, str],
    output_filename: str = "tailored_resume.docx",
) -> Optional[Path]:
    """
    Render the template DOCX with the given context (section content).

    Args:
        context: dict with keys like 'SUMMARY', 'SKILLS', 'EXPERIENCE', etc.
                 Values should be plain text or markdown-like strings.
        output_filename: name of the output file (saved in output/).

    Returns:
        Path to the generated DOCX, or None if no template available.
    """
    template_path = get_resume_template_path()
    if template_path is None:
        return None

    try:
        # Load the template
        doc = DocxTemplate(str(template_path))

        # Render with context (replaces {{KEY}} with context['KEY'])
        doc.render(context)

        # Save to output
        output_path = OUTPUT_DIR / output_filename
        doc.save(str(output_path))

        return output_path
    except Exception as e:
        print(f"Error rendering resume DOCX: {e}")
        return None
