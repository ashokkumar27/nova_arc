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
            result = tool.execute(step.args)
            replay_store.log("tool_invocation_completed", {
                "tool": result.tool,
                "success": result.success,
                "output": result.output,
            })
            results.append(result)
            if not result.success:
                replay_store.log("execution_halted", {"reason": f"Tool failure on {result.tool}"})
                break
        return results
