from nova_arc.tools.common_tools import notify_team_tool


def test_notify_team_tool_returns_failed_result_when_required_args_missing():
    result = notify_team_tool().execute({"message": "Investigate now"})

    assert result.success is False
    assert result.category == "notification"
    assert "channel" in result.output


def test_notify_team_tool_succeeds_with_required_args():
    result = notify_team_tool().execute({"channel": "ops", "message": "Investigate now"})

    assert result.success is True
    assert result.output == "Notification sent to ops: Investigate now"
