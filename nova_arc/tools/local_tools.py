from __future__ import annotations

from nova_arc.core.mission_profile import ToolExecutionResult
from .registry import RegisteredTool


def start_backup_cooling_tool():
    def _exec(args):
        zone_id = args["zone_id"]
        return ToolExecutionResult(
            tool="start_backup_cooling",
            args=args,
            success=True,
            output=f"Backup cooling engaged for {zone_id}",
            category="facility_control",
        )
    return RegisteredTool("start_backup_cooling", "facility_control", "Engage backup refrigeration for a failed cold-room zone.", _exec)


def shed_load_tool():
    def _exec(args):
        feeder_id = args["feeder_id"]
        percent = args["percent"]
        return ToolExecutionResult(
            tool="shed_load",
            args=args,
            success=True,
            output=f"Load shed {percent}% on feeder {feeder_id}",
            category="grid_control",
        )
    return RegisteredTool("shed_load", "grid_control", "Reduce electrical stress on affected feeder.", _exec)


def dispatch_field_engineer_tool():
    def _exec(args):
        site = args["site"]
        urgency = args["urgency"]
        return ToolExecutionResult(
            tool="dispatch_field_engineer",
            args=args,
            success=True,
            output=f"Engineer dispatched to {site} with urgency={urgency}",
            category="dispatch",
        )
    return RegisteredTool("dispatch_field_engineer", "dispatch", "Dispatch a field engineer for urgent site response.", _exec)
