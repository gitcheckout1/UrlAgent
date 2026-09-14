from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class DecomposeNode(Node):
    name = "decompose"

    def run(self, state: RunState, run_dir: Path) -> None:
        self.write_artifact(
            run_dir,
            "tasks.yaml",
            f"# Stub task breakdown for run {state.run_id}\n"
            f"tasks:\n"
            f"  - implement_write\n"
            f"  - implement_redirect\n"
            f"  - implement_analytics\n",
        )
