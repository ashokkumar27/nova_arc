import pytest

from nova_arc.bridges.bedrock_bridge import BedrockConverseBridge


def test_normalize_plan_from_json(config):
    bridge = BedrockConverseBridge(config=config, enabled=False)
    out = bridge._normalize_plan(
        '{"intent":"Test","strategy":"Do X","steps":[{"tool":"notify_team","args":{"channel":"ops"},"rationale":"Tell ops","expected_effect":"Aligned"}],"fallback":"Escalate"}',
        strict=True,
    )
    assert out["intent"] == "Test"
    assert out["strategy"] == "Do X"
    assert out["steps"][0]["tool"] == "notify_team"


def test_normalize_plan_from_tool_use_blocks(config):
    bridge = BedrockConverseBridge(config=config, enabled=False)
    out = bridge._normalize_plan(
        [{"toolUse": {"name": "start_backup_cooling", "input": {"zone_id": "Zone-B"}}}],
        strict=True,
    )
    assert out["steps"][0]["tool"] == "start_backup_cooling"
    assert out["steps"][0]["args"]["zone_id"] == "Zone-B"


def test_normalize_plan_invalid_json_raises_in_strict_mode(config):
    bridge = BedrockConverseBridge(config=config, enabled=False)
    with pytest.raises(ValueError):
        bridge._normalize_plan("Stabilize first, then notify the team.", strict=True)
