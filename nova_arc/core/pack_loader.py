from __future__ import annotations

from pathlib import Path

import yaml

from .mission_profile import MissionProfile


class PackLoader:
    def __init__(self, packs_root: str):
        self.packs_root = Path(packs_root)

    def load(self, pack_id: str) -> MissionProfile:
        manifest_path = self.packs_root / pack_id / "manifest.yaml"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Pack manifest not found: {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return MissionProfile(
            pack_id=data["pack_id"],
            name=data["name"],
            prime_directive=data["directive"]["prime_directive"],
            objectives=data["directive"]["objectives"],
            input_modes=data["perception"]["adapters"],
            allowed_tools=data["tools"]["allowlist"],
            approval_threshold=data["policy"]["approval_threshold"],
            mandatory_notify_threshold=data["policy"]["mandatory_notify_threshold"],
            blocked_tool_categories=data["policy"]["blocked_tool_categories"],
            success_conditions=data["verification"]["success_conditions"],
            residual_risk_target=data["verification"]["residual_risk_target"],
            surface_layout=data["surface"]["layout"],
            report_template=data["reporting"]["template"],
            metadata=data,
        )
