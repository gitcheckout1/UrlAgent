import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "test1"
RUN_DIR = REPO_ROOT / "runs" / RUN_ID


def orchestrator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "orchestrator", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


@pytest.fixture(autouse=True)
def fresh_run_dir():
    # Clean before only, so the run artifacts stay on disk for inspection.
    shutil.rmtree(RUN_DIR, ignore_errors=True)


def test_greenfield_waits_for_release_then_completes_after_approval():
    first = orchestrator("run", "scenarios/greenfield.yaml", "--run-id", RUN_ID)
    assert first.returncode == 2, first.stderr
    assert "WAITING_RELEASE" in first.stdout
    assert (RUN_DIR / "WAIT_RELEASE.json").exists()
    assert not (RUN_DIR / "release.txt").exists()

    approved = orchestrator("approve", "--gate", "release", "--run-id", RUN_ID)
    assert approved.returncode == 0, approved.stderr

    second = orchestrator("run", "scenarios/greenfield.yaml", "--run-id", RUN_ID)
    assert second.returncode == 0, second.stderr
    assert "COMPLETED" in second.stdout
    assert (RUN_DIR / "release.txt").exists()
    assert (RUN_DIR / "SUMMARY.md").exists()
