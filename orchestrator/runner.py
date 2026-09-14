import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from orchestrator.gates import ambiguous_requires_answers, can_enter_test, can_exit_release
from orchestrator.graph import GRAPHS, topological_order
from orchestrator.models import NodeStatus, RunState, Scenario, new_run_state
from orchestrator.nodes import NODE_HANDLERS

RUNS_DIR = Path("runs")

SCENARIO_FIELDS = ("id", "type", "description")
STATE_FILE = "state.json"
TRACE_FILE = "trace.jsonl"
WAIT_RELEASE_FILE = "WAIT_RELEASE.json"
WAIT_ANSWERS_FILE = "WAIT_ANSWERS.json"


class RunStatus(str, Enum):
    COMPLETED = "COMPLETED"
    WAITING_RELEASE = "WAITING_RELEASE"
    WAITING_ANSWERS = "WAITING_ANSWERS"
    FAILED = "FAILED"
    INCOMPLETE = "INCOMPLETE"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load_scenario(scenario_path: str | Path) -> dict[str, str]:
    """Read a flat 'key: value' scenario file. Only id, type, description are used."""
    fields: dict[str, str] = {}
    for line in Path(scenario_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip("\"'")

    missing = [name for name in SCENARIO_FIELDS if not fields.get(name)]
    if missing:
        raise ValueError(f"{scenario_path} is missing required fields: {', '.join(missing)}")
    return {name: fields[name] for name in SCENARIO_FIELDS}


def _state_path(run_dir: Path) -> Path:
    return run_dir / STATE_FILE


def _save_state(run_dir: Path, state: RunState) -> None:
    _state_path(run_dir).write_text(state.model_dump_json(indent=2), encoding="utf-8")


def load_state(run_id: str) -> RunState:
    path = _state_path(RUNS_DIR / run_id)
    if not path.exists():
        raise FileNotFoundError(f"no run state at {path}")
    return RunState.model_validate_json(path.read_text(encoding="utf-8"))


def _append_trace(
    run_dir: Path,
    run_id: str,
    event: str,
    node: str | None = None,
    actor: str = "runner",
) -> None:
    record = {
        "ts": _now().isoformat(),
        "event": event,
        "node": node,
        "actor": actor,
        "run_id": run_id,
    }
    with (run_dir / TRACE_FILE).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def _write_wait_marker(
    run_dir: Path, filename: str, run_id: str, gate: str, node: str, status: RunStatus
) -> None:
    marker = {
        "run_id": run_id,
        "gate": gate,
        "node": node,
        "status": status.value,
        "ts": _now().isoformat(),
    }
    (run_dir / filename).write_text(json.dumps(marker, indent=2), encoding="utf-8")


def run_scenario(scenario_path: str | Path, run_id: str) -> RunStatus:
    scenario_fields = _load_scenario(scenario_path)
    scenario = Scenario(scenario_fields["type"].lower())
    order = topological_order(GRAPHS[scenario])

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Resume an existing run so an approved gate can pick up where it stopped.
    if _state_path(run_dir).exists():
        state = load_state(run_id)
    else:
        state = new_run_state(run_id, scenario, order)
        _save_state(run_dir, state)

    _append_trace(run_dir, run_id, "run_started")

    for node in order:
        if state.is_done(node):
            continue

        if node == "design" and scenario is Scenario.AMBIGUOUS:
            if ambiguous_requires_answers(run_dir) and not state.approvals.get("answers"):
                _write_wait_marker(
                    run_dir,
                    WAIT_ANSWERS_FILE,
                    run_id,
                    "answers",
                    node,
                    RunStatus.WAITING_ANSWERS,
                )
                _append_trace(run_dir, run_id, "waiting_answers", node)
                _save_state(run_dir, state)
                return RunStatus.WAITING_ANSWERS

        if node == "test" and not can_enter_test(state):
            node_state = state.nodes[node]
            node_state.status = NodeStatus.FAILED
            node_state.error = "implement_* nodes are not all DONE"
            _append_trace(run_dir, run_id, "gate_blocked", node)
            _save_state(run_dir, state)
            return RunStatus.FAILED

        if node == "release" and not can_exit_release(state):
            _write_wait_marker(
                run_dir, WAIT_RELEASE_FILE, run_id, "release", node, RunStatus.WAITING_RELEASE
            )
            _append_trace(run_dir, run_id, "waiting_release", node)
            _save_state(run_dir, state)
            return RunStatus.WAITING_RELEASE

        node_state = state.nodes[node]
        try:
            node_state.status = NodeStatus.RUNNING
            node_state.started_at = _now()
            _append_trace(run_dir, run_id, "node_started", node)
            _save_state(run_dir, state)

            handler = NODE_HANDLERS.get(node)
            if handler is None:
                raise KeyError(f"no handler registered for node '{node}'")
            handler.run(state, run_dir)

            node_state.status = NodeStatus.DONE
            node_state.finished_at = _now()
            _append_trace(run_dir, run_id, "node_completed", node)
            _save_state(run_dir, state)
        except Exception as exc:  # noqa: BLE001 - record the failure, then report it
            node_state.status = NodeStatus.FAILED
            node_state.error = str(exc)
            node_state.finished_at = _now()
            _append_trace(run_dir, run_id, "node_failed", node)
            _save_state(run_dir, state)
            return RunStatus.FAILED

    _append_trace(run_dir, run_id, "run_completed")
    return RunStatus.COMPLETED


def approve_gate(run_id: str, gate: str) -> RunState:
    """Record a human approval. This is the only place an approval becomes True."""
    run_dir = RUNS_DIR / run_id
    state = load_state(run_id)
    state.approvals[gate] = True
    _save_state(run_dir, state)
    _append_trace(run_dir, run_id, "gate_approved", gate, actor="human")
    return state


def run_status(run_id: str) -> RunStatus:
    state = load_state(run_id)
    run_dir = RUNS_DIR / run_id

    if any(node.status is NodeStatus.FAILED for node in state.nodes.values()):
        return RunStatus.FAILED
    if all(node.status is NodeStatus.DONE for node in state.nodes.values()):
        return RunStatus.COMPLETED
    # Reuse the same gates the runner uses, so status cannot disagree with a run.
    if (run_dir / WAIT_RELEASE_FILE).exists() and not can_exit_release(state):
        return RunStatus.WAITING_RELEASE
    if (
        (run_dir / WAIT_ANSWERS_FILE).exists()
        and ambiguous_requires_answers(run_dir)
        and not state.approvals.get("answers")
    ):
        return RunStatus.WAITING_ANSWERS
    return RunStatus.INCOMPLETE
