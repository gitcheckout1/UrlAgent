from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class SummaryNode(Node):
    name = "summary"

    def run(self, state: RunState, run_dir: Path) -> None:
        lines = [
            "# Summary",
            "",
            f"- run_id: {state.run_id}",
            f"- scenario: {state.scenario.value}",
            f"- approvals: {state.approvals}",
            "",
            "## Nodes",
            "",
        ]
        for name, node in state.nodes.items():
            lines.append(f"- {name}: {node.status.value}")
        lines.append("")
        self.write_artifact(run_dir, "SUMMARY.md", "\n".join(lines))
