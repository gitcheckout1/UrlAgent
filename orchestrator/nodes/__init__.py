from orchestrator.nodes.base import Node
from orchestrator.nodes.decompose import DecomposeNode
from orchestrator.nodes.design import DesignNode
from orchestrator.nodes.docs import DocsNode
from orchestrator.nodes.impact import ImpactNode
from orchestrator.nodes.implement_analytics import ImplementAnalyticsNode
from orchestrator.nodes.implement_redirect import ImplementRedirectNode
from orchestrator.nodes.implement_write import ImplementWriteNode
from orchestrator.nodes.join import JoinNode
from orchestrator.nodes.release import ReleaseNode
from orchestrator.nodes.req import ReqNode
from orchestrator.nodes.summary import SummaryNode
from orchestrator.nodes.test import RunTestsNode

NODE_HANDLERS: dict[str, Node] = {
    handler.name: handler
    for handler in (
        ReqNode(),
        DecomposeNode(),
        DesignNode(),
        ImpactNode(),
        ImplementWriteNode(),
        ImplementRedirectNode(),
        ImplementAnalyticsNode(),
        JoinNode(),
        RunTestsNode(),
        DocsNode(),
        ReleaseNode(),
        SummaryNode(),
    )
}
