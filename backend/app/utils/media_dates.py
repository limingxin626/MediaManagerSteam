import os
import sys
from datetime import datetime
from typing import Optional


def clean_taken_at(value: Optional[datetime]) -> Optional[datetime]:
    """Discard invalid Unix-epoch-day capture timestamps."""
    if value is not None and value.date().isoformat() == "1970-01-01":
        return None
    return value


def get_file_created_at(file_path: str, platform: Optional[str] = None) -> Optional[datetime]:
    """Return a real filesystem creation/birth time when the platform exposes one."""
    try:
        stat_result = os.stat(file_path)
    except OSError:
        return None

    current_platform = platform or sys.platform
    if current_platform == "win32":
        timestamp = stat_result.st_ctime
    elif current_platform == "darwin" or "bsd" in current_platform:
        timestamp = getattr(stat_result, "st_birthtime", None)
        if timestamp is None:
            return None
    else:
        return None

    try:
        return datetime.fromtimestamp(timestamp)
    except (OSError, OverflowError, ValueError):
        return None
