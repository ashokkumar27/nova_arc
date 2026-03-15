def test_backend_state_updates_for_cooling_quarantine_and_hold(backend_client):
    incident = backend_client.ingest_incident(
        pack_id="cold_chain",
        scenario="cold_chain",
        context="Pharma DC",
        transcript="Zone B temperature is above threshold. Batch VX-204 may be affected. Shipment SHP-884 is loading now.",
    )

    backend_client.start_backup_cooling(pack_id="cold_chain", zone_id="Zone-B", incident_id=incident["incident_id"])
    backend_client.quarantine_batch(
        pack_id="cold_chain",
        batch_id="VX-204",
        reason="Excursion",
        incident_id=incident["incident_id"],
        via="api",
    )
    backend_client.hold_shipment(
        pack_id="cold_chain",
        shipment_id="SHP-884",
        reason="Excursion",
        incident_id=incident["incident_id"],
        via="api",
        disposition="held",
    )

    snapshot = backend_client.get_dashboard("cold_chain", incident["incident_id"])
    assert snapshot["incident"]["status"] == "cooling_started"
    assert snapshot["batches"][0]["status"] == "quarantined"
    assert snapshot["shipments"][0]["status"] == "held"
