from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from .resume_parser import parse_resume_to_text, parse_resume_to_chunks



# Paths (adapt if your structure differs)
DATA_DIR = Path("data")
UPLOADS_DIR = DATA_DIR / "uploads"
CONFIG_PATH = DATA_DIR / "current_resume.json"
RESUME_TEMPLATE_PATH = DATA_DIR / "current_resume_template.docx"

# Ensure uploads directory exists
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class CurrentResumeConfig:
    path: Path
    type: str          # "docx" or "pdf"
    uploaded_at: datetime

    @classmethod
    def from_dict(cls, d: dict) -> "CurrentResumeConfig":
        return cls(
            path=Path(d["path"]),
            type=d["type"],
            uploaded_at=datetime.fromisoformat(d["uploaded_at"]),
        )

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "type": self.type,
            "uploaded_at": self.uploaded_at.isoformat(),
        }

def _load_config() -> Optional[CurrentResumeConfig]:
    """Load current resume config from JSON, if it exists."""
    if not CONFIG_PATH.exists():
        return None

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return CurrentResumeConfig.from_dict(data)


def _save_config(cfg: CurrentResumeConfig) -> None:
    """Save current resume config to JSON."""
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg.to_dict(), f, indent=2)

def get_current_resume_config() -> Optional[CurrentResumeConfig]:
    """
    Return the current resume configuration, or None if no resume has been set.
    """
    cfg = _load_config()
    if cfg is None:
        return None
    # If file was deleted/moved, treat as None
    if not cfg.path.exists():
        return None
    return cfg

def get_current_resume_path() -> Optional[Path]:
    """
    Return Path to the current resume file, or None if not configured.
    """
    cfg = get_current_resume_config()
    return cfg.path if cfg is not None else None


def get_current_resume_type() -> Optional[str]:
    """
    Return 'docx' or 'pdf' for the current resume, or None.
    """
    cfg = get_current_resume_config()
    return cfg.type if cfg is not None else None

def set_current_resume(uploaded_bytes: bytes, original_filename: str) -> CurrentResumeConfig:
    """
    Save an uploaded resume into data/uploads/, update JSON config,
    and if it's a DOCX, also copy it as the template for DOCX output.
    """
    # Determine extension and type
    suffix = Path(original_filename).suffix.lower()
    if suffix not in [".docx", ".pdf"]:
        raise ValueError(f"Unsupported resume type: {suffix}")

    resume_type = "docx" if suffix == ".docx" else "pdf"

    # Build a timestamped filename to avoid collisions
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    new_filename = f"resume_{timestamp}{suffix}"
    new_path = UPLOADS_DIR / new_filename

    # Write bytes to disk
    new_path.write_bytes(uploaded_bytes)

    # If DOCX, also copy as template for output
    if resume_type == "docx":
        RESUME_TEMPLATE_PATH.write_bytes(uploaded_bytes)

    # Create and save config
    cfg = CurrentResumeConfig(
        path=new_path,
        type=resume_type,
        uploaded_at=datetime.utcnow(),
    )
    _save_config(cfg)
    return cfg


def get_resume_template_path() -> Path | None:
    """
    Return path to the current resume DOCX template, or None if no DOCX set.
    """
    if RESUME_TEMPLATE_PATH.exists():
        return RESUME_TEMPLATE_PATH
    return None


def get_resume_text() -> Optional[str]:
    """
    Return the full text of the current resume, or None if not set.
    """
    cfg = get_current_resume_config()
    if cfg is None:
        return None

    return parse_resume_to_text(cfg.path, cfg.type)

def get_resume_chunks() -> List[Dict]:
    """
    Return a list of chunk dicts for RAG, based on the current resume.
    Each chunk can have: {'id': str, 'text': str, 'section': str, 'order': int}
    Returns empty list if no resume is set.
    """
    cfg = get_current_resume_config()
    if cfg is None:
        return []

    return parse_resume_to_chunks(cfg.path, cfg.type)

