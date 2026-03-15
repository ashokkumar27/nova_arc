from __future__ import annotations

from nova_arc.bridges.contracts import BridgeRequest
from nova_arc.core.mission_profile import PerceivedState

from .base import PerceptionAdapter


class RuntimePerceptionAdapter(PerceptionAdapter):
    def __init__(self, retrieval_bridge, backend_client, voice_bridge):
        self.retrieval_bridge = retrieval_bridge
        self.backend_client = backend_client
        self.voice_bridge = voice_bridge
        self.last_voice_response = {}
        self.last_retrieval_response = {}

    def normalize(self, payload: dict, profile):
        scenario = payload["scenario"]
        transcript = payload.get("transcript") or payload.get("context", "")

        voice_response = self.voice_bridge.invoke(
            BridgeRequest(
                operation="ingest_transcript",
                pack_id=profile.pack_id,
                payload={"text": transcript},
            )
        )
        self.last_voice_response = voice_response.result if voice_response.ok else {}

        incident = self.backend_client.ingest_incident(
            pack_id=profile.pack_id,
            scenario=scenario,
            context=payload.get("context", ""),
            transcript=transcript,
        )

        evidence_response = self.retrieval_bridge.invoke(
            BridgeRequest(
                operation="search",
                payload={"query": {"type": payload.get("input_type", "text"), "content": transcript, "top_k": 4}},
                pack_id=profile.pack_id,
            )
        )
        self.last_retrieval_response = evidence_response.result if evidence_response.ok else {}
        evidence = evidence_response.result.get("matches", []) if evidence_response.ok else []
        snapshot = self.backend_client.get_dashboard(profile.pack_id, incident_id=incident["incident_id"])

        if scenario == "cold_chain":
            return PerceivedState(
                mission=profile.pack_id,
                context=payload.get("context", ""),
                situation_summary=incident["summary"],
                entities=[
                    {"type": "zone", "id": incident["signals"]["zone_id"], "status": "critical"},
                    {"type": "batch", "id": incident["signals"]["batch_id"], "status": snapshot["batches"][0]["status"] if snapshot["batches"] else "at_risk"},
                    {"type": "shipment", "id": incident["signals"]["shipment_id"], "status": snapshot["shipments"][0]["status"] if snapshot["shipments"] else "loading"},
                ],
                hazards=incident["hazards"],
                signals=incident["signals"],
                confidence=incident["confidence"],
                risk_score=incident["risk_score"],
                recommended_outcome="Protect inventory integrity and compliance",
                evidence=evidence,
                incident_id=incident["incident_id"],
                source_transcript=self.last_voice_response.get("text", transcript),
                voice_events=self.last_voice_response.get("events", []),
                backend_snapshot=snapshot,
                retrieval_trace=self.last_retrieval_response.get("trace", {}),
            )

        return PerceivedState(
            mission=profile.pack_id,
            context=payload.get("context", ""),
            situation_summary=incident["summary"],
            entities=[
                {"type": "transformer", "id": incident["signals"]["transformer_id"], "status": "critical"},
                {"type": "feeder", "id": incident["signals"]["feeder_id"], "status": "stressed"},
                {"type": "site", "id": incident["signals"]["site"], "status": "watch"},
            ],
            hazards=incident["hazards"],
            signals=incident["signals"],
            confidence=incident["confidence"],
            risk_score=incident["risk_score"],
            recommended_outcome="Prevent transformer failure and cascading outage",
            evidence=evidence,
            incident_id=incident["incident_id"],
            source_transcript=self.last_voice_response.get("text", transcript),
            voice_events=self.last_voice_response.get("events", []),
            backend_snapshot=snapshot,
            retrieval_trace=self.last_retrieval_response.get("trace", {}),
        )
