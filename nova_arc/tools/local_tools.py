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


def start_backup_cooling_tool():
    def _exec(args):
        zone_id = args.get("zone_id")
        if not zone_id:
            return _missing_args_result("start_backup_cooling", "facility_control", args, "zone_id")
        return ToolExecutionResult(
            tool="start_backup_cooling",
            args=args,
            success=True,
            output=f"Backup cooling engaged for {zone_id}",
            category="facility_control",
        )
    return RegisteredTool(
        "start_backup_cooling",
        "facility_control",
        "Engage backup refrigeration for a failed cold-room zone. Required args: zone_id.",
        _exec,
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
            output=f"Load shed {percent}% on feeder {feeder_id}",
            category="grid_control",
        )
    return RegisteredTool(
        "shed_load",
        "grid_control",
        "Reduce electrical stress on affected feeder. Required args: feeder_id, percent.",
        _exec,
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
            output=f"Engineer dispatched to {site} with urgency={urgency}",
            category="dispatch",
        )
    return RegisteredTool(
        "dispatch_field_engineer",
        "dispatch",
        "Dispatch a field engineer for urgent site response. Required args: site, urgency.",
        _exec,
    )
