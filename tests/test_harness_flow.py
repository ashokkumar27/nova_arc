from nova_arc.backend.service import CommandCenterBackend
from nova_arc.runtime import run_mission
from nova_arc.ui_helpers import default_context, default_transcript


def build_service(tmp_path):
    service = CommandCenterBackend(db_path=str(tmp_path / "mission.db"))
    return service


def test_cold_chain_harness_run_success(tmp_path, config):
    service = build_service(tmp_path)
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

    assert output["profile"]["pack_id"] == "cold_chain"
    assert output["verification"]["success"] is True
    assert "batch_quarantined" in output["verification"]["achieved_conditions"]
    assert len(output["plan"]["steps"]) == 4


def test_grid_harness_run_success(tmp_path, config):
    service = build_service(tmp_path)
    output = run_mission(
        pack_id="grid_ops",
        scenario="grid_ops",
        transcript=default_transcript("grid_ops"),
        context=default_context("grid_ops"),
        mode="demo",
        config=config,
        service=service,
        use_http_backend=False,
        reset_backend=True,
    )

    assert output["profile"]["pack_id"] == "grid_ops"
    assert output["verification"]["success"] is True
    assert "transformer_isolated" in output["verification"]["achieved_conditions"]
