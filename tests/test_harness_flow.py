from nova_arc.adapters.perception.runtime_perception import RuntimePerceptionAdapter
from nova_arc.adapters.planning.runtime_planner import RuntimePlannerAdapter
from nova_arc.adapters.surfaces.streamlit_surface import StreamlitSurfaceAdapter
from nova_arc.bridges.router import build_bridge_router
from nova_arc.core.harness import MissionHarness
from nova_arc.core.pack_loader import PackLoader
from nova_arc.testing.factories import build_registry


def build_harness(pack_id: str):
    loader = PackLoader("nova_arc/packs")
    profile = loader.load(pack_id)
    bridges = build_bridge_router(mode="demo")
    return MissionHarness(
        profile=profile,
        perception_adapter=RuntimePerceptionAdapter(bridges.retrieval),
        planner_adapter=RuntimePlannerAdapter(bridges.planner),
        tool_registry=build_registry(bridges.browser),
        surface_adapter=StreamlitSurfaceAdapter(),
        auto_approve=True,
    )


def test_cold_chain_harness_run_success():
    harness = build_harness("cold_chain")
    output = harness.run({"scenario": "cold_chain", "context": "Pharma DC / Vaccine Vault / KL North"})
    assert output["profile"]["pack_id"] == "cold_chain"
    assert output["verification"]["success"] is True
    assert "batch_quarantined" in output["verification"]["achieved_conditions"]
    assert len(output["plan"]["steps"]) == 4


def test_grid_harness_run_success():
    harness = build_harness("grid_ops")
    output = harness.run({"scenario": "grid_ops", "context": "National Grid / Substation East"})
    assert output["profile"]["pack_id"] == "grid_ops"
    assert output["verification"]["success"] is True
    assert "transformer_isolated" in output["verification"]["achieved_conditions"]
