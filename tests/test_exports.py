from nova_arc.runtime import run_mission
from nova_arc.ui_helpers import default_context, default_transcript


def test_replay_and_report_exports(tmp_path, config):
    from nova_arc.backend.service import CommandCenterBackend

    service = CommandCenterBackend(db_path=str(tmp_path / "exports.db"))
    output = run_mission(
        pack_id="cold_chain",
        scenario="cold_chain",
        transcript=default_transcript("cold_chain"),
        context=default_context("cold_chain"),
        mode="demo",
        config=config,
        service=service,
        use_http_backend=False,
        reset_backend=True,
    )

    assert '"profile"' in output["exports"]["json_report"]
    assert "# Pharma Cold Chain Command Center Replay Report" in output["exports"]["markdown_report"]
    assert len(output["replay"]) > 0
