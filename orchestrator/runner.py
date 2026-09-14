import json
import shutil
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from orchestrator.gates import (
    IMPLEMENT_PREFIX,
    ambiguous_requires_answers,
    can_enter_test,
    can_exit_release,
)
from orchestrator.graph import GRAPHS, topological_order
from orchestrator.models import NodeStatus, RunState, Scenario, new_run_state
from orchestrator.nodes import NODE_HANDLERS
from orchestrator.nodes.test import TestsFailed
from orchestrator.policy import safe_write

RUNS_DIR = Path("runs")
APP_DIR = Path("app")

SCENARIO_FIELDS = ("id", "type", "description")
STATE_FILE = "state.json"
TRACE_FILE = "trace.jsonl"
WAIT_RELEASE_FILE = "WAIT_RELEASE.json"
WAIT_ANSWERS_FILE = "WAIT_ANSWERS.json"
SNAPSHOT_SUBDIR = "snapshot"

# Total pytest attempts per invocation: the first run plus one retry, then STOPPED.
MAX_TEST_ATTEMPTS = 2

# Reset together on a retry, since the whole implement path is re-run.
RETRY_RESET_NODES = ("join", "test")


class RunStatus(str, Enum):
    COMPLETED = "COMPLETED"
    WAITING_RELEASE = "WAITING_RELEASE"
    WAITING_ANSWERS = "WAITING_ANSWERS"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    INCOMPLETE = "INCOMPLETE"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _guard_write(path: Path) -> Path:
    """Every write under the repo goes through policy.safe_write first."""
    if not safe_write(path):
        raise ValueError(f"policy denies writing to {path}")
    return path


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
    path = _guard_write(_state_path(run_dir))
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")


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
    fields: dict | None = None,
) -> None:
    record = {
        "ts": _now().isoformat(),
        "event": event,
        "node": node,
        "actor": actor,
        "run_id": run_id,
    }
    if fields:
        record.update(fields)
    path = _guard_write(run_dir / TRACE_FILE)
    with path.open("a", encoding="utf-8") as handle:
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
    path = _guard_write(run_dir / filename)
    path.write_text(json.dumps(marker, indent=2), encoding="utf-8")


def _snapshot_path(run_dir: Path) -> Path:
    return run_dir / SNAPSHOT_SUBDIR / APP_DIR.name


def _snapshot_app(run_dir: Path) -> Path:
    """Copy app/ into the run dir so a failing test can be rolled back."""
    destination = _guard_write(_snapshot_path(run_dir))
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(APP_DIR, destination, ignore=shutil.ignore_patterns("__pycache__"))
    return destination


def _restore_app(run_dir: Path) -> None:
    """Replace app/ with the snapshot. Refuses to delete app/ without a usable snapshot."""
    source = _snapshot_path(run_dir)
    if not source.is_dir() or not any(source.iterdir()):
        raise FileNotFoundError(f"no usable snapshot at {source}; refusing to touch {APP_DIR}")
    _guard_write(APP_DIR)
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(source, APP_DIR)


def _reset_implement_path(state: RunState, order: list[str]) -> None:
    for name in order:
        if not (name.startswith(IMPLEMENT_PREFIX) or name in RETRY_RESET_NODES):
            continue
        node_state = state.nodes[name]
        node_state.status = NodeStatus.PENDING
        node_state.started_at = None
        node_state.finished_at = None
        node_state.error = None


def _read_trace(run_dir: Path) -> list[dict]:
    path = run_dir / TRACE_FILE
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _active_duration_s(records: list[dict]) -> float:
    """Wall clock inside run segments only, so time parked at a human gate is excluded.

    Each invocation opens a segment with run_started. The gap between one segment's last
    event and the next run_started is human wait time and is not counted.
    """
    total = 0.0
    segment_start: datetime | None = None
    last_ts: datetime | None = None

    for record in records:
        ts = datetime.fromisoformat(record["ts"])
        if record["event"] == "run_started":
            if segment_start is not None and last_ts is not None:
                total += (last_ts - segment_start).total_seconds()
            segment_start = ts
        last_ts = ts

    if segment_start is not None and last_ts is not None:
        total += (last_ts - segment_start).total_seconds()
    return round(total, 3)


def _mttr_s(records: list[dict]) -> float | None:
    """Seconds from the first test failure to the next test pass. None if tests never failed."""
    first_failure: datetime | None = None
    for record in records:
        if record["event"] == "test_failed" and first_failure is None:
            first_failure = datetime.fromisoformat(record["ts"])
        elif record["event"] == "test_passed" and first_failure is not None:
            recovered = datetime.fromisoformat(record["ts"])
            return round((recovered - first_failure).total_seconds(), 3)
    return None


def collect_metrics(state: RunState, run_dir: Path) -> dict:
    records = _read_trace(run_dir)
    return {
        "duration_s": _active_duration_s(records),
        "retry_count": state.retry_count,
        "rollback_count": state.rollback_count,
        "success": not any(node.status is NodeStatus.FAILED for node in state.nodes.values()),
        "mttr_s": _mttr_s(records),
    }


def _emit_summary_metrics(run_dir: Path, run_id: str, state: RunState) -> None:
    _append_trace(
        run_dir,
        run_id,
        "summary_metrics",
        "summary",
        fields=collect_metrics(state, run_dir),
    )


def _finish_stopped(run_dir: Path, run_id: str, state: RunState) -> RunStatus:
    """Retries exhausted. Still write SUMMARY.md so a failed run reports metrics."""
    _append_trace(run_dir, run_id, "run_stopped", "test")
    handler = NODE_HANDLERS.get("summary")
    if handler is not None:
        handler.run(state, run_dir)
    _emit_summary_metrics(run_dir, run_id, state)
    _save_state(run_dir, state)
    return RunStatus.STOPPED


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

    snapshot_taken = False
    test_attempts = 0
    retry_requested = True

    while retry_requested:
        retry_requested = False

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

            if node.startswith(IMPLEMENT_PREFIX) and not snapshot_taken:
                _snapshot_app(run_dir)
                _append_trace(run_dir, run_id, "snapshot_created", node)
                snapshot_taken = True

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

                if node == "test":
                    _append_trace(run_dir, run_id, "test_passed", node)

                node_state.status = NodeStatus.DONE
                node_state.finished_at = _now()
                _append_trace(run_dir, run_id, "node_completed", node)
                _save_state(run_dir, state)
            except TestsFailed as exc:
                test_attempts += 1
                _append_trace(run_dir, run_id, "test_failed", node)

                _restore_app(run_dir)
                state.rollback_count += 1
                _append_trace(run_dir, run_id, "rollback", node)

                if test_attempts >= MAX_TEST_ATTEMPTS:
                    node_state.status = NodeStatus.FAILED
                    node_state.error = str(exc)
                    node_state.finished_at = _now()
                    _save_state(run_dir, state)
                    return _finish_stopped(run_dir, run_id, state)

                state.retry_count += 1
                _reset_implement_path(state, order)
                _append_trace(run_dir, run_id, "retry", node)
                _save_state(run_dir, state)
                retry_requested = True
                break
            except Exception as exc:  # noqa: BLE001 - record the failure, then report it
                node_state.status = NodeStatus.FAILED
                node_state.error = str(exc)
                node_state.finished_at = _now()
                _append_trace(run_dir, run_id, "node_failed", node)
                _save_state(run_dir, state)
                return RunStatus.FAILED

    _append_trace(run_dir, run_id, "run_completed")
    _emit_summary_metrics(run_dir, run_id, state)
    _save_state(run_dir, state)
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
