# src/resume_parser.py

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple
from docx import Document  # from python-docx
from pypdf import PdfReader  # or from PyPDF2 import PdfReader

def _parse_docx_to_text(path: Path) -> str:
    """
    Extract text from a DOCX file.
    Returns paragraphs joined by newlines.
    """
    doc = Document(str(path))

    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        paragraphs.append(text)

    # You can add more logic later to include table content if needed.
    return "\n".join(paragraphs)

def _parse_pdf_to_text(path: Path) -> str:
    """
    Extract text from a PDF file using pypdf.
    Best-effort; quality depends on the PDF structure.
    """
    reader = PdfReader(str(path))
    parts: List[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_text = page_text.strip()
        if page_text:
            parts.append(page_text)

    return "\n".join(parts)

def parse_resume_to_text(path: Path, resume_type: str) -> str:
    """
    Unified entry point.
    resume_type: 'docx' or 'pdf'.
    """
    if resume_type == "docx":
        return _parse_docx_to_text(path)
    elif resume_type == "pdf":
        return _parse_pdf_to_text(path)
    else:
        raise ValueError(f"Unsupported resume type for parsing: {resume_type}")

def _chunk_text_by_length(
    text: str,
    max_chars: int = 1200,
    overlap: int = 200,
) -> List[str]:
    """
    Simple sliding-window chunking by character length.
    Not semantic, but good enough as a start.
    """
    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap  # step back for overlap
        if start < 0:
            start = 0

        if start >= n:
            break

    return chunks

def parse_resume_to_chunks(path: Path, resume_type: str) -> List[Dict]:
    """
    Convert the resume into a list of chunk dicts for RAG.
    Each chunk: {'id': str, 'text': str, 'section': str, 'order': int}
    """
    full_text = parse_resume_to_text(path, resume_type)
    if not full_text:
        return []

    raw_chunks = _chunk_text_by_length(full_text)

    chunks: List[Dict] = []
    for idx, chunk_text in enumerate(raw_chunks):
        chunk_id = f"resume_chunk_{idx}"
        chunks.append(
            {
                "id": chunk_id,
                "text": chunk_text,
                "section": "resume",  # can add finer sections later
                "order": idx,
            }
        )

    return chunks


