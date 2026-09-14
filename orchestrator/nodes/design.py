from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class DesignNode(Node):
    name = "design"

    def run(self, state: RunState, run_dir: Path) -> None:
        self.write_artifact(
            run_dir,
            "docs/openapi.yaml",
            "# Stub. Not generated from the live app.\n"
            "openapi: 3.0.0\n"
            "info:\n"
            "  title: UrlAgent\n"
            "  version: 0.1.0\n"
            "paths:\n"
            "  /v1/urls: {}\n"
            "  /{code}: {}\n"
            "  /v1/urls/{code}/stats: {}\n",
        )
