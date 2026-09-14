from pathlib import Path

from orchestrator.models import RunState
from orchestrator.nodes.base import Node


class SummaryNode(Node):
    name = "summary"

    def run(self, state: RunState, run_dir: Path) -> None:
        # Deferred import: runner imports this package, so a module-level import would cycle.
        from orchestrator.runner import collect_metrics

        metrics = collect_metrics(state, run_dir)
        mttr = "N/A" if metrics["mttr_s"] is None else metrics["mttr_s"]

        lines = [
            "# Summary",
            "",
            f"- run_id: {state.run_id}",
            f"- scenario: {state.scenario.value}",
            f"- approvals: {state.approvals}",
            "",
            "## Metrics",
            "",
            f"- duration_s: {metrics['duration_s']}",
            f"- retry_count: {metrics['retry_count']}",
            f"- rollback_count: {metrics['rollback_count']}",
            f"- success: {'true' if metrics['success'] else 'false'}",
            f"- mttr_s: {mttr}",
            "",
            "duration_s is runner wall clock only. Time parked at a human gate is excluded,",
            "and human gate wait is NOT MTTR: mttr_s measures first test FAIL to next test PASS.",
            "",
            "## Nodes",
            "",
        ]
        for name, node in state.nodes.items():
            lines.append(f"- {name}: {node.status.value}")
        lines.append("")
        self.write_artifact(run_dir, "SUMMARY.md", "\n".join(lines))
