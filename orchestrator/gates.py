from pathlib import Path

from orchestrator.models import RunState

IMPLEMENT_PREFIX = "implement_"


def can_enter_test(state: RunState) -> bool:
    """True when every implement_* node is DONE. False if there are none."""
    implement_nodes = [name for name in state.nodes if name.startswith(IMPLEMENT_PREFIX)]
    if not implement_nodes:
        return False
    return all(state.is_done(name) for name in implement_nodes)


def can_exit_release(state: RunState) -> bool:
    """Read-only check of the human approval. Never set approvals.release here."""
    return state.approvals.get("release") is True


def ambiguous_requires_answers(run_dir: str | Path) -> bool:
    """True while the human has not written answers.json into the run directory."""
    return not (Path(run_dir) / "answers.json").exists()
