from __future__ import annotations

from nova_arc.bridges.embedding_bridge import MultimodalEmbeddingBridge
from nova_arc.bridges.nova_act_bridge import NovaActBridge
from nova_arc.config import AppConfig

from .bridge_tools import hold_shipment_tool, isolate_transformer_tool, quarantine_batch_tool, retrieve_evidence_tool
from .common_tools import notify_team_tool
from .local_tools import dispatch_field_engineer_tool, shed_load_tool, start_backup_cooling_tool
from .registry import ToolRegistry


def build_registry(
    backend_client,
    pack_id: str,
    config: AppConfig | None = None,
    browser_bridge=None,
    retrieval_bridge=None,
) -> ToolRegistry:
    config = config or AppConfig.from_env()
    retrieval_bridge = retrieval_bridge or MultimodalEmbeddingBridge(backend_client=backend_client, config=config, enabled=False)
    browser_bridge = browser_bridge or NovaActBridge(backend_client=backend_client, config=config)

    registry = ToolRegistry()
    registry.register(notify_team_tool(backend_client=backend_client, config=config, pack_id=pack_id))
    registry.register(start_backup_cooling_tool(backend_client=backend_client, pack_id=pack_id))
    registry.register(quarantine_batch_tool(browser_bridge=browser_bridge, backend_client=backend_client, pack_id=pack_id))
    registry.register(hold_shipment_tool(browser_bridge=browser_bridge, backend_client=backend_client, pack_id=pack_id))
    registry.register(retrieve_evidence_tool(retrieval_bridge=retrieval_bridge, pack_id=pack_id))
    registry.register(shed_load_tool())
    registry.register(isolate_transformer_tool(browser_bridge))
    registry.register(dispatch_field_engineer_tool())
    return registry
