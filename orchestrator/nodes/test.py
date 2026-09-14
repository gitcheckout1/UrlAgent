from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class RunTestsNode(Node):
    name = "test"

    def run(self, state: RunState, run_dir: Path) -> None:
        # Stub only. M4 replaces this with a real pytest invocation.
        self.write_artifact(
            run_dir,
            "test-results.txt",
            "PASS\n\nStub: no tests were executed. M4 runs pytest here.\n",
        )
