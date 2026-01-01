from __future__ import annotations
from datetime import datetime, timedelta, timezone
import re
from typing import Optional

UTC = timezone.utc


def parse_relative_date(text: str) -> Optional[datetime]:
    """
    Handle strings like:
    - '7 hours ago'
    - '3 days ago'
    - '2 weeks ago'
    - '44d ago'

    Returns a naive UTC datetime (tzinfo removed) or None.
    """
    if not text:
        return None

    s = text.strip().lower()

    # e.g. "44d ago"
    m = re.match(r"(\d+)\s*d\s*ago", s)
    if m:
        days = int(m.group(1))
        dt = datetime.now(UTC) - timedelta(days=days)
        return dt.replace(tzinfo=None)

    # e.g. "7 hours ago"
    m = re.match(r"(\d+)\s*hour[s]?\s*ago", s)
    if m:
        hours = int(m.group(1))
        dt = datetime.now(UTC) - timedelta(hours=hours)
        return dt.replace(tzinfo=None)

    # e.g. "3 days ago"
    m = re.match(r"(\d+)\s*day[s]?\s*ago", s)
    if m:
        days = int(m.group(1))
        dt = datetime.now(UTC) - timedelta(days=days)
        return dt.replace(tzinfo=None)

    # e.g. "2 weeks ago"
    m = re.match(r"(\d+)\s*week[s]?\s*ago", s)
    if m:
        weeks = int(m.group(1))
        dt = datetime.now(UTC) - timedelta(weeks=weeks)
        return dt.replace(tzinfo=None)

    return None


def parse_any_posted_date(text: str) -> Optional[datetime]:
    """
    Generic parser for:
    - '2024-12-31'
    - '2024-12-31T10:15:00Z'
    - '44d ago', '7 hours ago', '2 weeks ago', etc.

    Returns a **naive** UTC datetime (no tzinfo) or None.
    """
    if not text:
        return None

    s = text.strip()

    # Normalize trailing Z
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    # Try ISO-like formats
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(s, fmt)
            # Convert to UTC and drop tzinfo so we compare naive datetimes everywhere
            return dt.astimezone(UTC).replace(tzinfo=None)
        except Exception:
            pass

    # Try relative formats
    rel = parse_relative_date(text)
    if rel:
        return rel  # already naive UTC

    return None
