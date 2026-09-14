from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class DocsNode(Node):
    name = "docs"

    def run(self, state: RunState, run_dir: Path) -> None:
        lines = ["# HITL graph", "", f"Run {state.run_id} ({state.scenario.value}) node order:", ""]
        for name in state.nodes:
            marker = "  <-- human gate" if name == "release" else ""
            lines.append(f"- {name}{marker}")
        lines += ["", "Stub. release requires a human approval before it runs.", ""]
        self.write_artifact(run_dir, "hitl-graph.md", "\n".join(lines))
