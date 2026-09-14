from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class ReqNode(Node):
    name = "req"

    def run(self, state: RunState, run_dir: Path) -> None:
        self.write_artifact(
            run_dir,
            "00-requirements.md",
            f"# Requirements\n\n"
            f"- run_id: {state.run_id}\n"
            f"- scenario: {state.scenario.value}\n\n"
            f"Stub. Human-authored requirements live in docs/v1-scope.md.\n",
        )
