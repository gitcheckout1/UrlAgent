from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class ImplementRedirectNode(Node):
    name = "implement_redirect"

    def run(self, state: RunState, run_dir: Path) -> None:
        self.write_artifact(
            run_dir,
            "verify-redirect.md",
            "# Verify redirect\n\n"
            "Stub checklist. Nothing here has been executed.\n\n"
            "- [ ] GET /{code} returns 302 to the stored URL\n"
            "- [ ] unknown code returns 404\n"
            "- [ ] clicks increment on each hit\n",
        )
