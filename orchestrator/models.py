from collections.abc import Iterable
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Scenario(str, Enum):
    GREENFIELD = "greenfield"
    BROWNFIELD = "brownfield"
    AMBIGUOUS = "ambiguous"


class NodeStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class NodeState(BaseModel):
    name: str
    status: NodeStatus = NodeStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


class RunState(BaseModel):
    run_id: str
    scenario: Scenario
    nodes: dict[str, NodeState] = Field(default_factory=dict)
    # Human-only gates, keyed by gate name. Only an explicit human approve
    # command may set one to True; never default or infer them.
    approvals: dict[str, bool] = Field(default_factory=dict)

    def status_of(self, name: str) -> NodeStatus | None:
        node = self.nodes.get(name)
        return None if node is None else node.status

    def is_done(self, name: str) -> bool:
        return self.status_of(name) is NodeStatus.DONE


def new_run_state(run_id: str, scenario: Scenario, node_names: Iterable[str]) -> RunState:
    return RunState(
        run_id=run_id,
        scenario=scenario,
        nodes={name: NodeState(name=name) for name in node_names},
    )
