from nova_arc.bridges.bedrock_bridge import BedrockConverseBridge


def test_normalize_plan_from_json():
    bridge = BedrockConverseBridge(enabled=False)
    out = bridge._normalize_plan('{"intent":"Test","strategy":"Do X","steps":[{"tool":"notify_team","args":{"channel":"ops"},"rationale":"Tell ops","expected_effect":"Aligned"}],"fallback":"Escalate"}')
    assert out["intent"] == "Test"
    assert out["strategy"] == "Do X"
    assert out["steps"][0]["tool"] == "notify_team"


def test_normalize_plan_from_codefence():
    bridge = BedrockConverseBridge(enabled=False)
    raw = """```json
{"strategy":"Recover safely","steps":[]}
```"""
    out = bridge._normalize_plan(raw)
    assert out["strategy"] == "Recover safely"


def test_normalize_plan_from_plain_text_falls_back():
    bridge = BedrockConverseBridge(enabled=False)
    out = bridge._normalize_plan("Stabilize first, then notify the team.")
    assert "Stabilize" in out["strategy"]
