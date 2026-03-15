import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nova_arc.adapters.perception.runtime_perception import RuntimePerceptionAdapter
from nova_arc.adapters.planning.runtime_planner import RuntimePlannerAdapter
from nova_arc.adapters.surfaces.streamlit_surface import StreamlitSurfaceAdapter
from nova_arc.bridges.router import build_bridge_router
from nova_arc.core.harness import MissionHarness
from nova_arc.core.pack_loader import PackLoader
from nova_arc.testing.factories import build_registry


def run(pack_id: str, scenario: str, context: str):
    loader = PackLoader("nova_arc/packs")
    profile = loader.load(pack_id)
    bridges = build_bridge_router(mode="demo")
    harness = MissionHarness(
        profile=profile,
        perception_adapter=RuntimePerceptionAdapter(bridges.retrieval),
        planner_adapter=RuntimePlannerAdapter(bridges.planner),
        tool_registry=build_registry(bridges.browser),
        surface_adapter=StreamlitSurfaceAdapter(),
        auto_approve=True,
    )
    return harness.run({"scenario": scenario, "context": context})


if __name__ == "__main__":
    for pack_id, scenario, context in [
        ("cold_chain", "cold_chain", "Pharma DC / Vaccine Vault / KL North"),
        ("grid_ops", "grid_ops", "National Grid / Substation East"),
    ]:
        output = run(pack_id, scenario, context)
        print(f"\n=== {output['profile']['name']} ===")
        print(output["state"]["situation_summary"])
        print(output["plan"]["intent"])
        print(output["verification"]["summary"])
