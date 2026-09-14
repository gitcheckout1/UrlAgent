from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class ImpactNode(Node):
    name = "impact"

    def run(self, state: RunState, run_dir: Path) -> None:
        self.write_artifact(
            run_dir,
            "impact.md",
            "# Impact\n\n"
            "Stub list of files a brownfield change (expiry, rate limits) would touch:\n\n"
            "- app/models.py\n"
            "- app/shared/store_protocol.py\n"
            "- app/shared/memory_store.py\n"
            "- app/write/api.py\n"
            "- app/redirect/api.py\n"
            "- tests/test_app.py\n",
        )
