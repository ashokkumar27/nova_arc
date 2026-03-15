from nova_arc.tools.registry import RegisteredTool, ToolRegistry


def test_registry_describes_registered_tools():
    registry = ToolRegistry()
    registry.register(
        RegisteredTool(
            name="notify_team",
            category="notification",
            description="Notify the relevant operational response team. Required args: channel, message.",
            executor=lambda args: args,
        )
    )

    assert registry.describe_all() == [
        {
            "name": "notify_team",
            "category": "notification",
            "description": "Notify the relevant operational response team. Required args: channel, message.",
        }
    ]
    assert registry.get("notify_team").execute({"channel": "ops"}) == {"channel": "ops"}


def test_registered_tool_supports_legacy_constructor():
    tool = RegisteredTool("legacy_tool", "ops", lambda args: {"ok": True, **args})

    assert tool.description == ""
    assert tool.execute({"ticket": "INC-1"}) == {"ok": True, "ticket": "INC-1"}
