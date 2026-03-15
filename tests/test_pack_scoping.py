from nova_arc.testing.factories import build_registry


def test_pack_scoped_tool_exposure(backend_client, config):
    registry = build_registry(backend_client=backend_client, pack_id="cold_chain", config=config)
    cold_tools = registry.subset(["retrieve_evidence", "start_backup_cooling", "quarantine_batch", "hold_shipment", "notify_team"]).names()
    assert "hold_shipment" in cold_tools
    assert "shed_load" not in cold_tools
