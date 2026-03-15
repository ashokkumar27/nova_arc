from __future__ import annotations

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nova_arc.backend.service import CommandCenterBackend
from nova_arc.config import AppConfig
from nova_arc.runtime import run_mission
from nova_arc.ui_helpers import default_context, default_transcript


def run(pack_id: str, scenario: str, mode: str = "demo"):
    config = AppConfig.from_env()
    service = CommandCenterBackend(db_path=config.backend_db_path)
    return run_mission(
        pack_id=pack_id,
        scenario=scenario,
        transcript=default_transcript(pack_id),
        context=default_context(pack_id),
        mode=mode,
        config=config,
        service=service,
        use_http_backend=False,
        reset_backend=True,
    )


if __name__ == "__main__":
    for pack_id, scenario in [("cold_chain", "cold_chain"), ("grid_ops", "grid_ops")]:
        output = run(pack_id, scenario)
        print(f"\n=== {output['profile']['name']} ===")
        print(output["state"]["situation_summary"])
        print(output["plan"]["strategy"])
        print(output["verification"]["summary"])
