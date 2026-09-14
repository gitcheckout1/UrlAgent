from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class ImplementAnalyticsNode(Node):
    name = "implement_analytics"

    def run(self, state: RunState, run_dir: Path) -> None:
        self.write_artifact(
            run_dir,
            "verify-analytics.md",
            "# Verify analytics\n\n"
            "Stub checklist. Nothing here has been executed.\n\n"
            "- [ ] GET /v1/urls/{code}/stats reports clicks and last_clicked_at\n"
            "- [ ] unknown code returns 404\n",
        )
