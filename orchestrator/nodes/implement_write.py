from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class ImplementWriteNode(Node):
    name = "implement_write"

    def run(self, state: RunState, run_dir: Path) -> None:
        self.write_artifact(
            run_dir,
            "verify-write.md",
            "# Verify write\n\n"
            "Stub checklist. Nothing here has been executed.\n\n"
            "- [ ] POST /v1/urls returns 201 with a 7-char code\n"
            "- [ ] javascript:, ftp:, file: rejected with 400\n",
        )
