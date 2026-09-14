import subprocess
import sys
from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node

REPO_ROOT = Path(__file__).resolve().parents[2]

# Scoped to the app suite on purpose: a bare "pytest -q" would collect
# tests/test_orchestrator.py, which launches the orchestrator, which lands back here.
PYTEST_TARGET = "tests/test_app.py"


class TestsFailed(Exception):
    """Raised when the pytest subprocess exits non-zero, so the runner can roll back."""


def run_pytest() -> subprocess.CompletedProcess[str]:
    """Seam for tests: monkeypatch this to force a failing run."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", PYTEST_TARGET],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


class RunTestsNode(Node):
    name = "test"

    def run(self, state: RunState, run_dir: Path) -> None:
        result = run_pytest()
        verdict = "PASS" if result.returncode == 0 else "FAIL"
        self.write_artifact(
            run_dir,
            "test-results.txt",
            f"{verdict}\n"
            f"command: pytest -q {PYTEST_TARGET}\n"
            f"exit_code: {result.returncode}\n"
            f"attempt_rollbacks_so_far: {state.rollback_count}\n\n"
            f"{result.stdout}\n{result.stderr}\n",
        )
        if result.returncode != 0:
            raise TestsFailed(f"pytest exited {result.returncode}")
