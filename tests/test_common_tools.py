from nova_arc.tools.common_tools import notify_team_tool


def test_notify_team_tool_returns_failed_result_when_required_args_missing(backend_client, config):
    result = notify_team_tool(backend_client=backend_client, config=config, pack_id="cold_chain").execute({"message": "Investigate now"})

    assert result.success is False
    assert result.category == "notification"
    assert "channel" in result.output


def test_notify_team_tool_records_local_notification_when_no_webhook_configured(backend_client, config):
    incident = backend_client.ingest_incident(
        pack_id="cold_chain",
        scenario="cold_chain",
        context="Pharma DC",
        transcript="Zone B temperature is above threshold.",
    )
    result = notify_team_tool(backend_client=backend_client, config=config, pack_id="cold_chain").execute(
        {"channel": "ops", "message": "Investigate now", "incident_id": incident["incident_id"]}
    )

    assert result.success is True
    assert result.details["external_status"] == "stored_locally"
