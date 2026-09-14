from pathlib import Path, PurePosixPath

ALLOWED_ROOTS = ("app", "tests", "docs", "scenarios", "runs")


def safe_write(path: str | Path) -> bool:
    """True if policy permits writing to path (a repo-relative path). Does not write."""
    raw = str(path).replace("\\", "/")
    if not raw or raw.startswith("/"):
        return False

    parts = PurePosixPath(raw).parts
    if not parts:
        return False
    if any(part == ".." for part in parts):
        return False
    if any(part.startswith(".env") for part in parts):
        return False

    return parts[0] in ALLOWED_ROOTS
