from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class JoinNode(Node):
    name = "join"

    def run(self, state: RunState, run_dir: Path) -> None:
        """No-op. Exists so the implement_* fan-out has a single successor."""
