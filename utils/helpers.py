"""
utils/helpers.py — Formatting and utility functions.
"""

from typing import Optional


def fmt_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    if size_bytes <= 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def safe_filename(name: str, max_len: int = 200) -> str:
    """Sanitize and truncate a filename."""
    if not name:
        return "unnamed_file"
    import re
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = name.strip(". ")
    if len(name) > max_len:
        ext = ""
        base = name
        dot = name.rfind(".")
        if dot > 0:
            ext = name[dot:]
            base = name[:dot]
        base = base[: max_len - len(ext)]
        name = base + ext
    return name or "unnamed_file"


def chunk_text(text: str, size: int = 4096):
    """Split text into chunks."""
    for i in range(0, len(text), size):
        yield text[i: i + size]