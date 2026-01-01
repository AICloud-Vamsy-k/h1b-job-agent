from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional

def filter_by_date(jobs: List[Dict], posted_after: Optional[datetime]) -> List[Dict]:
    if not posted_after:
        return jobs
    filtered: List[Dict] = []
    for job in jobs:
        dt = job.get("posted_at")
        if isinstance(dt, datetime) and dt >= posted_after:
            filtered.append(job)
    return filtered