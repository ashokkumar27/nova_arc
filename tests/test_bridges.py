from nova_arc.bridges.contracts import BridgeRequest
from nova_arc.bridges.router import build_bridge_router


def test_embedding_bridge_search():
    router = build_bridge_router(mode="demo")
    resp = router.retrieval.invoke(BridgeRequest(operation="search", payload={"query": {"type": "text", "content": "cold room"}}, pack_id="cold_chain"))
    assert resp.ok
    assert len(resp.result["matches"]) >= 1


def test_nova_act_bridge():
    router = build_bridge_router(mode="demo")
    resp = router.browser.invoke(BridgeRequest(operation="browser_run", payload={"workflow_id": "test", "parameters": {"id": "X"}}))
    assert resp.ok
    assert resp.result["status"] == "completed"
