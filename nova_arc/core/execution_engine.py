from __future__ import annotations

from typing import List

from .mission_profile import ActionPlan, ToolExecutionResult


class ExecutionEngine:
    def execute(self, plan: ActionPlan, tool_registry, replay_store) -> List[ToolExecutionResult]:
        results: List[ToolExecutionResult] = []
        for step in plan.steps:
            tool = tool_registry.get(step.tool)
            replay_store.log("tool_invocation_requested", {
                "tool": step.tool,
                "args": step.args,
                "rationale": step.rationale,
            })
            try:
                result = tool.execute(step.args)
            except Exception as exc:
                result = ToolExecutionResult(
                    tool=step.tool,
                    args=step.args,
                    success=False,
                    output=f"Tool execution failed: {type(exc).__name__}: {exc}",
                    category=getattr(tool, "category", "unknown"),
                )
            replay_store.log("tool_invocation_completed", {
                "tool": result.tool,
                "success": result.success,
                "output": result.output,
                "details": result.details,
                "bridge_label": result.bridge_label,
            })
            results.append(result)
            if not result.success:
                replay_store.log("execution_halted", {"reason": f"Tool failure on {result.tool}"})
                break
        return results
