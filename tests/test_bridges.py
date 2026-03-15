from nova_arc.bridges.contracts import BridgeRequest
from nova_arc.bridges.router import build_bridge_router


def test_embedding_bridge_search_returns_evidence_cards(backend_client, config):
    router = build_bridge_router(mode="demo", config=config, backend_client=backend_client)
    resp = router.retrieval.invoke(
        BridgeRequest(operation="search", payload={"query": {"type": "text", "content": "Zone B temperature batch VX-204"}}, pack_id="cold_chain")
    )

    assert resp.ok
    assert len(resp.result["matches"]) == 4
    assert resp.result["matches"][0]["source_label"] in {"SOP PDF", "Dashboard Screenshot", "Incident Log", "Prior Incident"}


def test_nova_act_bridge_runs_local_admin_workflow(backend_client, config):
    incident = backend_client.ingest_incident(
        pack_id="cold_chain",
        scenario="cold_chain",
        context="Pharma DC",
        transcript="Zone B temperature is above threshold. Batch VX-204 may be affected. Shipment SHP-884 is loading now.",
    )
    router = build_bridge_router(mode="demo", config=config, backend_client=backend_client)
    resp = router.browser.invoke(
        BridgeRequest(
            operation="browser_run",
            pack_id="cold_chain",
            payload={"workflow_id": "quarantine_batch_v1", "parameters": {"batch_id": "VX-204", "reason": "Test", "incident_id": incident["incident_id"]}},
        )
    )

    assert resp.ok
    assert resp.result["status"] == "completed"
    snapshot = backend_client.get_dashboard("cold_chain", incident["incident_id"])
    assert snapshot["batches"][0]["status"] == "quarantined"


def test_router_behaviour_changes_by_mode(backend_client, config):
    demo_router = build_bridge_router(mode="demo", config=config, backend_client=backend_client)
    live_router = build_bridge_router(mode="live_bridge", config=config, backend_client=backend_client)

    assert demo_router.planner.enabled is False
    assert live_router.planner.enabled is True
    assert demo_router.voice.enabled is False
    assert live_router.voice.enabled is True
