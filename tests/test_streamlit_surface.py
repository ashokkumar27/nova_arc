from nova_arc.adapters.surfaces.streamlit_surface import StreamlitSurfaceAdapter
from nova_arc.testing.factories import build_plan, build_profile, build_results, build_state, build_verification
from nova_arc.ui_helpers import classify_error, risk_status


def test_surface_publish_has_tables_and_exports():
    surface = StreamlitSurfaceAdapter()
    out = surface.publish(build_profile(), build_state(), build_plan(), build_results(), build_verification(), [])

    assert "tables" in out
    assert set(out["tables"].keys()) >= {"results_df", "timeline_df", "entities_df", "evidence_df"}
    assert "exports" in out
    assert "markdown_report" in out["exports"]


def test_ui_helpers_format_risk_and_error():
    assert risk_status(88) == "Critical"
    assert classify_error("AccessDeniedException: no model access")["title"] == "IAM Or Model Access Failure"
