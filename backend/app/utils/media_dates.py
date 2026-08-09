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
    """Return the earliest valid filesystem creation/birth or modification time."""
    try:
        stat_result = os.stat(file_path)
    except OSError:
        return None

    current_platform = platform or sys.platform
    timestamps = [getattr(stat_result, "st_mtime", None)]
    if current_platform == "win32":
        timestamps.append(getattr(stat_result, "st_ctime", None))
    elif current_platform == "darwin" or "bsd" in current_platform:
        timestamps.append(getattr(stat_result, "st_birthtime", None))

    values = []
    for timestamp in timestamps:
        if timestamp is None:
            continue
        try:
            values.append(datetime.fromtimestamp(timestamp))
        except (OSError, OverflowError, TypeError, ValueError):
            continue
    return min(values) if values else None
