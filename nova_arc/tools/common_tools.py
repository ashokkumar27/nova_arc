from __future__ import annotations

from nova_arc.core.mission_profile import ToolExecutionResult
from .registry import RegisteredTool


def notify_team_tool():
    def _exec(args):
        missing = [key for key in ("channel", "message") if not args.get(key)]
        if missing:
            return ToolExecutionResult(
                tool="notify_team",
                args=args,
                success=False,
                output=f"Missing required args for notify_team: {', '.join(missing)}",
                category="notification",
            )
        channel = args["channel"]
        message = args["message"]
        return ToolExecutionResult(
            tool="notify_team",
            args=args,
            success=True,
            output=f"Notification sent to {channel}: {message}",
            category="notification",
        )
    return RegisteredTool("notify_team", "notification", "Notify the relevant operational response team.", _exec)
