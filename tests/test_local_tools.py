from nova_arc.tools.local_tools import shed_load_tool


def test_shed_load_tool_accepts_load_shed_percent_alias():
    result = shed_load_tool().execute({"feeder_id": "F-12", "load_shed_percent": "20"})

    assert result.success is True
    assert result.args["percent"] == "20"
    assert result.output == "Load shed 20% on feeder F-12"


def test_shed_load_tool_returns_failed_result_when_percent_missing():
    result = shed_load_tool().execute({"feeder_id": "F-12"})

    assert result.success is False
    assert "percent" in result.output
