from __future__ import annotations

from nova_arc.bridges.contracts import BridgeRequest
from nova_arc.core.mission_profile import ToolExecutionResult
from .registry import RegisteredTool


def _missing_args_result(tool_name, category, args, *required):
    missing = [key for key in required if not args.get(key)]
    return ToolExecutionResult(
        tool=tool_name,
        args=args,
        success=False,
        output=f"Missing required args for {tool_name}: {', '.join(missing)}",
        category=category,
    )


def quarantine_batch_tool(browser_bridge):
    def _exec(args):
        if not args.get("batch_id"):
            return _missing_args_result("quarantine_batch", "inventory_control", args, "batch_id")
        response = browser_bridge.invoke(BridgeRequest(operation="browser_run", payload={
            "workflow_id": "quarantine_batch_v1",
            "instruction": "Open inventory portal and quarantine batch",
            "parameters": args,
        }))
        return ToolExecutionResult(
            tool="quarantine_batch",
            args=args,
            success=response.ok,
            output=response.result.get("summary", "Batch quarantined"),
            category="inventory_control",
        )
    return RegisteredTool(
        "quarantine_batch",
        "inventory_control",
        "Prevent suspect inventory from being released. Required args: batch_id.",
        _exec,
    )


def divert_shipment_tool(browser_bridge):
    def _exec(args):
        if not args.get("shipment_id") or not args.get("destination"):
            return _missing_args_result("divert_shipment", "logistics_control", args, "shipment_id", "destination")
        response = browser_bridge.invoke(BridgeRequest(operation="browser_run", payload={
            "workflow_id": "divert_shipment_v1",
            "instruction": "Open logistics portal and divert shipment",
            "parameters": args,
        }))
        return ToolExecutionResult(
            tool="divert_shipment",
            args=args,
            success=response.ok,
            output=response.result.get("summary", "Shipment diverted"),
            category="logistics_control",
        )
    return RegisteredTool(
        "divert_shipment",
        "logistics_control",
        "Reroute outbound logistics to a safe destination. Required args: shipment_id, destination.",
        _exec,
    )


def isolate_transformer_tool(browser_bridge):
    def _exec(args):
        if not args.get("transformer_id"):
            return _missing_args_result("isolate_transformer", "grid_control", args, "transformer_id")
        response = browser_bridge.invoke(BridgeRequest(operation="browser_run", payload={
            "workflow_id": "isolate_transformer_v1",
            "instruction": "Open grid operations UI and isolate transformer",
            "parameters": args,
        }))
        return ToolExecutionResult(
            tool="isolate_transformer",
            args=args,
            success=response.ok,
            output=response.result.get("summary", "Transformer isolated"),
            category="grid_control",
        )
    return RegisteredTool(
        "isolate_transformer",
        "grid_control",
        "Isolate a high-risk transformer from the active network. Required args: transformer_id.",
        _exec,
    )
