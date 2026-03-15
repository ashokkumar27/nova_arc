from __future__ import annotations

from nova_arc.tools.registry import ToolRegistry
from nova_arc.tools.common_tools import notify_team_tool
from nova_arc.tools.local_tools import start_backup_cooling_tool, shed_load_tool, dispatch_field_engineer_tool
from nova_arc.tools.bridge_tools import quarantine_batch_tool, divert_shipment_tool, isolate_transformer_tool


def build_registry(browser_bridge):
    registry = ToolRegistry()
    registry.register(notify_team_tool())
    registry.register(start_backup_cooling_tool())
    registry.register(quarantine_batch_tool(browser_bridge))
    registry.register(divert_shipment_tool(browser_bridge))
    registry.register(shed_load_tool())
    registry.register(isolate_transformer_tool(browser_bridge))
    registry.register(dispatch_field_engineer_tool())
    return registry
