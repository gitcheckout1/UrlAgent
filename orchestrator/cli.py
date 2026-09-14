import argparse
import json
import sys

from orchestrator.runner import RunStatus, approve_gate, load_state, run_scenario, run_status

EXIT_CODES = {
    RunStatus.COMPLETED: 0,
    RunStatus.WAITING_RELEASE: 2,
    RunStatus.WAITING_ANSWERS: 2,
    RunStatus.FAILED: 1,
    RunStatus.STOPPED: 1,
    RunStatus.INCOMPLETE: 1,
}

GATES = ("release", "answers")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="orchestrator")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run = subcommands.add_parser("run", help="run a scenario")
    run.add_argument("scenario", help="path to a scenario file")
    run.add_argument("--run-id", required=True)

    status = subcommands.add_parser("status", help="show run state")
    status.add_argument("--run-id", required=True)

    approve = subcommands.add_parser("approve", help="record a human approval")
    approve.add_argument("--gate", required=True, choices=GATES)
    approve.add_argument("--run-id", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        if args.command == "run":
            status = run_scenario(args.scenario, args.run_id)
            print(status.value)
            return EXIT_CODES[status]

        if args.command == "status":
            state = load_state(args.run_id)
            status = run_status(args.run_id)
            print(
                json.dumps(
                    {
                        "run_id": state.run_id,
                        "scenario": state.scenario.value,
                        "status": status.value,
                        "approvals": state.approvals,
                        "nodes": {
                            name: node.status.value for name, node in state.nodes.items()
                        },
                    },
                    indent=2,
                )
            )
            return EXIT_CODES[status]

        if args.command == "approve":
            state = approve_gate(args.run_id, args.gate)
            print(f"approved {args.gate} for {state.run_id}")
            return 0
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 1
