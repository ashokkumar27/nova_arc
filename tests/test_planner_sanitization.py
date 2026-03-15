from nova_arc.adapters.perception.runtime_perception import RuntimePerceptionAdapter
from nova_arc.adapters.surfaces.streamlit_surface import StreamlitSurfaceAdapter
from nova_arc.bridges.router import build_bridge_router
from nova_arc.core.harness import MissionHarness
from nova_arc.core.pack_loader import PackLoader
from nova_arc.testing.factories import build_registry


class ForbiddenPlanner:
    def __init__(self):
        self.last_raw_output = None
        self.last_error = None
        self.last_usage = {}

    def plan(self, state, profile, policy_context, tool_registry):
        from nova_arc.core.mission_profile import ActionPlan, ActionStep

        return ActionPlan(
            intent="Test",
            strategy="Try everything",
            steps=[
                ActionStep(tool="forbidden_tool", args={}, rationale="No", expected_effect="No"),
                ActionStep(tool="start_backup_cooling", args={"zone_id": "Zone-B", "incident_id": state.incident_id}, rationale="Yes", expected_effect="Cool"),
            ],
            requires_approval=False,
            approval_reason=None,
            fallback=None,
        )


def test_planner_sanitizes_forbidden_tools(backend_client, config):
    profile = PackLoader("nova_arc/packs").load("cold_chain")
    bridges = build_bridge_router(mode="demo", config=config, backend_client=backend_client)
    harness = MissionHarness(
        profile=profile,
        perception_adapter=RuntimePerceptionAdapter(bridges.retrieval, backend_client=backend_client, voice_bridge=bridges.voice),
        planner_adapter=ForbiddenPlanner(),
        tool_registry=build_registry(backend_client=backend_client, pack_id="cold_chain", config=config, browser_bridge=bridges.browser, retrieval_bridge=bridges.retrieval),
        surface_adapter=StreamlitSurfaceAdapter(),
        auto_approve=True,
    )

    output = harness.run(
        {
            "scenario": "cold_chain",
            "context": "Pharma DC",
            "transcript": "Zone B temperature is above threshold. Batch VX-204 may be affected. Shipment SHP-884 is loading now.",
            "input_type": "voice",
        }
    )

    assert output["plan"]["steps"][0]["tool"] == "start_backup_cooling"
    assert output["plan"]["sanitization_notes"]
