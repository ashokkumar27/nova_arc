from __future__ import annotations

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


def start_backup_cooling_tool(backend_client, pack_id: str):
    def _exec(args):
        zone_id = args.get("zone_id")
        if not zone_id:
            return _missing_args_result("start_backup_cooling", "facility_control", args, "zone_id")
        backend_result = backend_client.start_backup_cooling(
            pack_id=pack_id,
            zone_id=zone_id,
            incident_id=args.get("incident_id"),
        )
        return ToolExecutionResult(
            tool="start_backup_cooling",
            args=args,
            success=True,
            output=f"Cooling started for {zone_id}. Incident status is cooling_started.",
            category="facility_control",
            details=backend_result,
        )

    return RegisteredTool(
        "start_backup_cooling",
        "facility_control",
        "Start backup cooling and persist the incident status to cooling_started. Required args: zone_id.",
        _exec,
        input_schema={
            "type": "object",
            "properties": {
                "zone_id": {"type": "string", "description": "Affected cold-room zone identifier."},
                "incident_id": {"type": "string"},
            },
            "required": ["zone_id"],
            "additionalProperties": False,
        },
    )


def shed_load_tool():
    def _exec(args):
        feeder_id = args.get("feeder_id")
        percent = args.get("percent") or args.get("load_shed_percent") or args.get("percentage")
        if not feeder_id or not percent:
            return _missing_args_result("shed_load", "grid_control", args, "feeder_id", "percent")
        return ToolExecutionResult(
            tool="shed_load",
            args={**args, "percent": percent},
            success=True,
            output=f"Load shed {percent}% on feeder {feeder_id}.",
            category="grid_control",
            details={"feeder_id": feeder_id, "percent": percent},
        )

    return RegisteredTool(
        "shed_load",
        "grid_control",
        "Reduce load on an affected feeder. Required args: feeder_id, percent.",
        _exec,
        input_schema={
            "type": "object",
            "properties": {
                "feeder_id": {"type": "string"},
                "percent": {"type": "string"},
            },
            "required": ["feeder_id", "percent"],
            "additionalProperties": True,
        },
    )


def dispatch_field_engineer_tool():
    def _exec(args):
        site = args.get("site")
        urgency = args.get("urgency")
        if not site or not urgency:
            return _missing_args_result("dispatch_field_engineer", "dispatch", args, "site", "urgency")
        return ToolExecutionResult(
            tool="dispatch_field_engineer",
            args=args,
            success=True,
            output=f"Engineer dispatched to {site} with urgency {urgency}.",
            category="dispatch",
            details={"site": site, "urgency": urgency},
        )

    return RegisteredTool(
        "dispatch_field_engineer",
        "dispatch",
        "Dispatch an engineer to inspect the affected site. Required args: site, urgency.",
        _exec,
        input_schema={
            "type": "object",
            "properties": {
                "site": {"type": "string"},
                "urgency": {"type": "string"},
            },
            "required": ["site", "urgency"],
            "additionalProperties": False,
        },
    )
