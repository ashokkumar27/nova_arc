from nova_arc.tools.local_tools import shed_load_tool, start_backup_cooling_tool


def test_shed_load_tool_accepts_load_shed_percent_alias():
    result = shed_load_tool().execute({"feeder_id": "F-12", "load_shed_percent": "20"})

    assert result.success is True
    assert result.args["percent"] == "20"
    assert result.output == "Load shed 20% on feeder F-12."


def test_start_backup_cooling_persists_backend_state(backend_client):
    incident = backend_client.ingest_incident(
        pack_id="cold_chain",
        scenario="cold_chain",
        context="Pharma DC",
        transcript="Zone B temperature is above threshold. Batch VX-204 may be affected.",
    )
    result = start_backup_cooling_tool(backend_client=backend_client, pack_id="cold_chain").execute(
        {"zone_id": "Zone-B", "incident_id": incident["incident_id"]}
    )

    updated = backend_client.get_dashboard("cold_chain", incident["incident_id"])["incident"]
    assert result.success is True
    assert updated["status"] == "cooling_started"
