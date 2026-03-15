from __future__ import annotations

from nova_arc.bridges.contracts import BridgeRequest
from nova_arc.core.mission_profile import PerceivedState

from .base import PerceptionAdapter


class RuntimePerceptionAdapter(PerceptionAdapter):
    def __init__(self, retrieval_bridge):
        self.retrieval_bridge = retrieval_bridge

    def normalize(self, payload: dict, profile):
        scenario = payload["scenario"]
        evidence_response = self.retrieval_bridge.invoke(
            BridgeRequest(
                operation="search",
                payload={"query": {"type": payload.get("input_type", "text"), "content": payload.get("context", "")}},
                pack_id=profile.pack_id,
            )
        )
        evidence = evidence_response.result.get("matches", []) if evidence_response.ok else []

        if scenario == "cold_chain":
            return PerceivedState(
                mission=profile.pack_id,
                context=payload["context"],
                situation_summary=(
                    "Cold-room Zone B temperature rose to 11.8C for 14 minutes. "
                    "Compressor vibration abnormal. Vaccine batch VX-204 at spoilage risk. "
                    "Outbound shipment SHP-884 is in active loading window."
                ),
                entities=[
                    {"type": "zone", "id": "Zone-B", "status": "critical"},
                    {"type": "batch", "id": "VX-204", "status": "at-risk"},
                    {"type": "shipment", "id": "SHP-884", "status": "loading"},
                ],
                hazards=["temperature_excursion", "inventory_spoilage_risk", "regulatory_non_compliance"],
                signals={
                    "zone_id": "Zone-B",
                    "batch_id": "VX-204",
                    "shipment_id": "SHP-884",
                    "destination": "Hub-2",
                    "temperature_c": 11.8,
                    "duration_minutes": 14,
                },
                confidence=0.96,
                risk_score=82,
                recommended_outcome="Protect inventory integrity and compliance",
                evidence=evidence,
            )

        if scenario == "grid_ops":
            return PerceivedState(
                mission=profile.pack_id,
                context=payload["context"],
                situation_summary=(
                    "Transformer T-17 oil temperature reached 149C. Acoustic pattern suggests internal arcing risk. "
                    "Feeder F-12 is under stress and failure may cascade to Substation East."
                ),
                entities=[
                    {"type": "transformer", "id": "T-17", "status": "critical"},
                    {"type": "feeder", "id": "F-12", "status": "loaded"},
                    {"type": "site", "id": "Substation-East", "status": "watch"},
                ],
                hazards=["thermal_failure", "arc_fault_risk", "cascading_outage"],
                signals={
                    "transformer_id": "T-17",
                    "feeder_id": "F-12",
                    "site": "Substation-East",
                    "load_shed_percent": "20",
                },
                confidence=0.94,
                risk_score=91,
                recommended_outcome="Prevent transformer failure and cascading outage",
                evidence=evidence,
            )

        raise ValueError(f"Unknown scenario: {scenario}")
