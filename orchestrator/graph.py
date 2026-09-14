from collections.abc import Mapping

from orchestrator.models import Scenario

# Each graph maps a node to the nodes it depends on.
Graph = Mapping[str, tuple[str, ...]]

GREENFIELD: Graph = {
    "req": (),
    "decompose": ("req",),
    "design": ("decompose",),
    "implement_write": ("design",),
    "implement_redirect": ("design",),
    "implement_analytics": ("design",),
    "join": ("implement_write", "implement_redirect", "implement_analytics"),
    "test": ("join",),
    "docs": ("test",),
    "release": ("docs",),
    "summary": ("release",),
}

# Same as GREENFIELD with impact between design and the implement_* nodes.
BROWNFIELD: Graph = {
    "req": (),
    "decompose": ("req",),
    "design": ("decompose",),
    "impact": ("design",),
    "implement_write": ("impact",),
    "implement_redirect": ("impact",),
    "implement_analytics": ("impact",),
    "join": ("implement_write", "implement_redirect", "implement_analytics"),
    "test": ("join",),
    "docs": ("test",),
    "release": ("docs",),
    "summary": ("release",),
}

# Stops at design: ambiguous requirements need human answers before any build.
AMBIGUOUS: Graph = {
    "req": (),
    "decompose": ("req",),
    "design": ("decompose",),
}

GRAPHS: Mapping[Scenario, Graph] = {
    Scenario.GREENFIELD: GREENFIELD,
    Scenario.BROWNFIELD: BROWNFIELD,
    Scenario.AMBIGUOUS: AMBIGUOUS,
}


def topological_order(graph: Graph) -> list[str]:
    """Dependency order for a graph, keeping declaration order among ready nodes."""
    unmet = {node: set(deps) for node, deps in graph.items()}
    order: list[str] = []
    while unmet:
        ready = [node for node in graph if node in unmet and not unmet[node]]
        if not ready:
            raise ValueError("graph has a cycle or an unknown dependency")
        for node in ready:
            order.append(node)
            del unmet[node]
        for deps in unmet.values():
            deps.difference_update(ready)
    return order
