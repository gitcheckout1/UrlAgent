import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from orchestrator.gates import can_enter_test
from orchestrator.graph import GRAPHS, topological_order
from orchestrator.models import NodeStatus, Scenario, new_run_state
from orchestrator.nodes import test as node_test
from orchestrator.runner import RunStatus, load_state, run_scenario

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


def test_join_gate_blocks_test_until_implements_done():
    """join itself is symbolic (a no-op fan-in). can_enter_test is what actually gates."""
    order = topological_order(GRAPHS[Scenario.GREENFIELD])
    state = new_run_state("gatecheck", Scenario.GREENFIELD, order)

    assert can_enter_test(state) is False

    implements = [name for name in state.nodes if name.startswith("implement_")]
    for name in implements[:-1]:
        state.nodes[name].status = NodeStatus.DONE
    assert can_enter_test(state) is False

    state.nodes[implements[-1]].status = NodeStatus.DONE
    assert can_enter_test(state) is True


def test_rollback_restores_app_on_forced_test_fail(tmp_path, monkeypatch):
    # Run against a throwaway tree so a real rollback never touches the repo's app/.
    monkeypatch.chdir(tmp_path)
    marker = tmp_path / "app" / "marker.py"
    marker.parent.mkdir()
    marker.write_text("original", encoding="utf-8")

    def failing_pytest():
        # Stand in for a bad implement step: corrupt app/, then report failure.
        marker.write_text("broken", encoding="utf-8")
        return subprocess.CompletedProcess(
            args=["pytest"], returncode=1, stdout="forced failure", stderr=""
        )

    monkeypatch.setattr(node_test, "run_pytest", failing_pytest)

    status = run_scenario(REPO_ROOT / "scenarios" / "greenfield.yaml", "test_rollback")

    assert status is RunStatus.STOPPED
    assert marker.read_text(encoding="utf-8") == "original"

    state = load_state("test_rollback")
    assert state.rollback_count == 2
    assert state.retry_count == 1

    summary = (tmp_path / "runs" / "test_rollback" / "SUMMARY.md").read_text(encoding="utf-8")
    assert "success: false" in summary
