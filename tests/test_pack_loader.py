from nova_arc.core.pack_loader import PackLoader


def test_pack_loader_cold_chain():
    loader = PackLoader("nova_arc/packs")
    profile = loader.load("cold_chain")
    assert profile.pack_id == "cold_chain"
    assert "quarantine_batch" in profile.allowed_tools
    assert "hold_shipment" in profile.allowed_tools
    assert profile.approval_threshold == 80
