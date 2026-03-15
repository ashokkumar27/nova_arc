from nova_arc.adapters.surfaces.streamlit_surface import StreamlitSurfaceAdapter
from nova_arc.testing.factories import build_profile, build_state, build_plan, build_results, build_verification


def test_surface_publish_has_tables():
    surface = StreamlitSurfaceAdapter()
    out = surface.publish(build_profile(), build_state(), build_plan(), build_results(), build_verification(), [])
    assert "tables" in out
    assert set(out["tables"].keys()) >= {"results_df", "timeline_df", "entities_df", "evidence_df"}
