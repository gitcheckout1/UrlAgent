from pathlib import Path

from orchestrator.models import RunState
from orchestrator.policy import safe_write


class Node:
    """A single step in a run. Subclasses set name and implement run()."""

    name: str = ""

    def run(self, state: RunState, run_dir: Path) -> None:
        raise NotImplementedError

    def write_artifact(self, run_dir: Path, relative_path: str, text: str) -> Path:
        path = run_dir / relative_path
        if not safe_write(path):
            raise ValueError(f"policy denies writing to {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path
