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


def quarantine_batch_tool(browser_bridge, backend_client, pack_id: str):
    def _exec(args):
        if not args.get("batch_id"):
            return _missing_args_result("quarantine_batch", "inventory_control", args, "batch_id")
        workflow_response = browser_bridge.invoke(
            BridgeRequest(
                operation="browser_run",
                pack_id=pack_id,
                payload={
                    "workflow_id": "quarantine_batch_v1",
                    "instruction": "Open the inventory admin portal and quarantine the affected batch.",
                    "parameters": {
                        "batch_id": args["batch_id"],
                        "reason": args.get("reason", "Temperature excursion above threshold"),
                        "incident_id": args.get("incident_id"),
                    },
                },
            )
        )
        if not workflow_response.ok:
            return ToolExecutionResult(
                tool="quarantine_batch",
                args=args,
                success=False,
                output=workflow_response.error or "Nova Act workflow failed.",
                category="inventory_control",
                bridge_label="UI Workflow via Nova Act bridge",
            )
        batch = backend_client.get_dashboard(pack_id=pack_id, incident_id=args.get("incident_id")).get("batches", [])
        return ToolExecutionResult(
            tool="quarantine_batch",
            args=args,
            success=True,
            output=workflow_response.result.get("summary", "Batch quarantined."),
            category="inventory_control",
            details={"workflow": workflow_response.result, "backend_buckets": batch},
            bridge_label="UI Workflow via Nova Act bridge",
        )

    return RegisteredTool(
        "quarantine_batch",
        "inventory_control",
        "Quarantine a suspect batch through the admin portal workflow and persist the backend state. Required args: batch_id, reason.",
        _exec,
        input_schema={
            "type": "object",
            "properties": {
                "batch_id": {"type": "string"},
                "reason": {"type": "string"},
                "incident_id": {"type": "string"},
            },
            "required": ["batch_id", "reason"],
            "additionalProperties": False,
        },
        bridge_label="UI Workflow via Nova Act bridge",
    )


def hold_shipment_tool(browser_bridge, backend_client, pack_id: str):
    def _exec(args):
        if not args.get("shipment_id"):
            return _missing_args_result("hold_shipment", "logistics_control", args, "shipment_id")
        workflow_response = browser_bridge.invoke(
            BridgeRequest(
                operation="browser_run",
                pack_id=pack_id,
                payload={
                    "workflow_id": "hold_shipment_v1",
                    "instruction": "Open the logistics admin portal and hold the outbound shipment.",
                    "parameters": {
                        "shipment_id": args["shipment_id"],
                        "reason": args.get("reason", "Hold shipment pending cold-chain verification"),
                        "incident_id": args.get("incident_id"),
                        "disposition": args.get("disposition", "held"),
                    },
                },
            )
        )
        if not workflow_response.ok:
            return ToolExecutionResult(
                tool="hold_shipment",
                args=args,
                success=False,
                output=workflow_response.error or "Nova Act workflow failed.",
                category="logistics_control",
                bridge_label="UI Workflow via Nova Act bridge",
            )
        shipments = backend_client.get_dashboard(pack_id=pack_id, incident_id=args.get("incident_id")).get("shipments", [])
        return ToolExecutionResult(
            tool="hold_shipment",
            args=args,
            success=True,
            output=workflow_response.result.get("summary", "Shipment held."),
            category="logistics_control",
            details={"workflow": workflow_response.result, "backend_shipments": shipments},
            bridge_label="UI Workflow via Nova Act bridge",
        )

    return RegisteredTool(
        "hold_shipment",
        "logistics_control",
        "Hold or divert an outbound shipment through the admin portal workflow and persist the backend state. Required args: shipment_id, reason.",
        _exec,
        input_schema={
            "type": "object",
            "properties": {
                "shipment_id": {"type": "string"},
                "reason": {"type": "string"},
                "disposition": {"type": "string"},
                "incident_id": {"type": "string"},
            },
            "required": ["shipment_id", "reason"],
            "additionalProperties": False,
        },
        bridge_label="UI Workflow via Nova Act bridge",
    )


def retrieve_evidence_tool(retrieval_bridge, pack_id: str):
    def _exec(args):
        query = args.get("query")
        if not query:
            return _missing_args_result("retrieve_evidence", "retrieval", args, "query")
        response = retrieval_bridge.invoke(
            BridgeRequest(
                operation="search",
                pack_id=pack_id,
                payload={"query": {"type": args.get("input_type", "text"), "content": query, "top_k": args.get("top_k", 4)}},
            )
        )
        if not response.ok:
            return ToolExecutionResult(
                tool="retrieve_evidence",
                args=args,
                success=False,
                output=response.error or "Evidence retrieval failed.",
                category="retrieval",
            )
        matches = response.result.get("matches", [])
        return ToolExecutionResult(
            tool="retrieve_evidence",
            args=args,
            success=True,
            output=f"Retrieved {len(matches)} evidence sources.",
            category="retrieval",
            details=response.result,
            bridge_label="Nova Multimodal Embeddings",
        )

    return RegisteredTool(
        "retrieve_evidence",
        "retrieval",
        "Retrieve relevant multimodal evidence cards for the current incident. Required args: query.",
        _exec,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "input_type": {"type": "string"},
                "top_k": {"type": "integer"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        bridge_label="Nova Multimodal Embeddings",
    )


def isolate_transformer_tool(browser_bridge):
    def _exec(args):
        if not args.get("transformer_id"):
            return _missing_args_result("isolate_transformer", "grid_control", args, "transformer_id")
        response = browser_bridge.invoke(
            BridgeRequest(
                operation="browser_run",
                pack_id="grid_ops",
                payload={
                    "workflow_id": "isolate_transformer_v1",
                    "instruction": "Open grid operations UI and isolate the transformer.",
                    "parameters": args,
                },
            )
        )
        return ToolExecutionResult(
            tool="isolate_transformer",
            args=args,
            success=response.ok,
            output=response.result.get("summary", "Transformer isolated."),
            category="grid_control",
            details=response.result,
            bridge_label="UI Workflow via Nova Act bridge",
        )

    return RegisteredTool(
        "isolate_transformer",
        "grid_control",
        "Isolate a transformer through the bridge workflow. Required args: transformer_id.",
        _exec,
        input_schema={
            "type": "object",
            "properties": {"transformer_id": {"type": "string"}},
            "required": ["transformer_id"],
            "additionalProperties": False,
        },
        bridge_label="UI Workflow via Nova Act bridge",
    )
