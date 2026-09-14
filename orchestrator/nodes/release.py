from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class ReleaseNode(Node):
    name = "release"

    def run(self, state: RunState, run_dir: Path) -> None:
        # The runner only reaches this node after can_exit_release passes.
        # This node reads the approval and never sets it.
        self.write_artifact(
            run_dir,
            "release.txt",
            f"run_id: {state.run_id}\n"
            f"release gate: approved by human\n"
            f"approvals: {state.approvals}\n",
        )
