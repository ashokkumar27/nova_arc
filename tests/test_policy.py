from nova_arc.core.mission_profile import ActionPlan, ActionStep
from nova_arc.core.pack_loader import PackLoader
from nova_arc.core.policy_engine import PolicyEngine
from nova_arc.tools.registry import RegisteredTool, ToolRegistry


def test_policy_blocks_disallowed_tool():
    loader = PackLoader("nova_arc/packs")
    profile = loader.load("cold_chain")
    plan = ActionPlan(
        intent="Test",
        strategy="Test",
        requires_approval=False,
        approval_reason=None,
        fallback=None,
        steps=[ActionStep(tool="forbidden_tool", args={}, rationale="x", expected_effect="y")],
    )
    registry = ToolRegistry()
    registry.register(RegisteredTool(name="forbidden_tool", category="forbidden", description="Nope", executor=lambda args: None))
    policy = PolicyEngine(auto_approve=True)
    try:
        policy.validate_plan(profile, plan, registry)
        assert False, "Expected PermissionError"
    except PermissionError:
        assert True
