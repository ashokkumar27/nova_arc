from nova_arc.tools.registry import RegisteredTool, ToolRegistry


def test_registry_describes_registered_tools_with_schema():
    registry = ToolRegistry()
    registry.register(
        RegisteredTool(
            name="notify_team",
            category="notification",
            description="Notify the relevant operational response team.",
            executor=lambda args: args,
            input_schema={"type": "object", "properties": {"channel": {"type": "string"}}},
            bridge_label="Webhook",
        )
    )

    assert registry.describe_all() == [
        {
            "name": "notify_team",
            "category": "notification",
            "description": "Notify the relevant operational response team.",
            "input_schema": {"type": "object", "properties": {"channel": {"type": "string"}}},
            "bridge_label": "Webhook",
        }
    ]


def test_registered_tool_supports_legacy_constructor():
    tool = RegisteredTool("legacy_tool", "ops", lambda args: {"ok": True, **args})

    assert tool.description == ""
    assert tool.execute({"ticket": "INC-1"}) == {"ok": True, "ticket": "INC-1"}
