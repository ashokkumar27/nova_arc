from nova_arc.core.execution_engine import ExecutionEngine
from nova_arc.core.mission_profile import ActionPlan, ActionStep
from nova_arc.core.replay_store import ReplayStore
from nova_arc.tools.registry import RegisteredTool, ToolRegistry


def test_execution_engine_converts_tool_exceptions_to_failed_results():
    registry = ToolRegistry()
    registry.register(
        RegisteredTool(
            name="broken_tool",
            category="ops",
            description="Raises during execution.",
            executor=lambda args: args["missing"],
        )
    )
    plan = ActionPlan(
        intent="Test",
        strategy="Run broken tool",
        steps=[ActionStep(tool="broken_tool", args={}, rationale="Test", expected_effect="None")],
        requires_approval=False,
        approval_reason=None,
        fallback=None,
    )

    results = ExecutionEngine().execute(plan, registry, ReplayStore())

    assert len(results) == 1
    assert results[0].tool == "broken_tool"
    assert results[0].success is False
    assert "Tool execution failed: KeyError" in results[0].output
