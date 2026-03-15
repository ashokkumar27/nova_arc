from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from .contracts import BridgeRequest, BridgeResponse, RuntimeBridge


class BedrockConverseBridge(RuntimeBridge):
    backend_name = "bedrock"

    def __init__(self, model_id: str | None = None, region_name: str | None = None, enabled: bool = False):
        self.model_id = model_id or os.getenv("NOVA_MODEL_ID", "amazon.nova-pro-v1:0")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.enabled = enabled
        self._client = None
        if enabled:
            import boto3  # optional runtime dependency in live mode
            from botocore.config import Config
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.region_name,
                config=Config(connect_timeout=3600, read_timeout=3600, retries={"max_attempts": 1}),
            )

    def invoke(self, request: BridgeRequest) -> BridgeResponse:
        start = time.time()
        if not self.enabled:
            result = self._mock_result(request)
            return BridgeResponse(True, self.backend_name, request.operation, result, latency_ms=int((time.time()-start)*1000))

        if request.operation == "plan":
            system_prompt = request.payload["system_prompt"]
            messages = request.payload["messages"]
            inference_config = request.payload.get("inference_config", {"maxTokens": 1200, "temperature": 0.1, "topP": 0.9})
            response = self._client.converse(
                modelId=self.model_id,
                system=[{"text": system_prompt}],
                messages=messages,
                inferenceConfig=inference_config,
            )
            content = response.get("output", {}).get("message", {}).get("content", [])
            text = "\n".join(block["text"] for block in content if "text" in block).strip()
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = {"raw_text": text}
            return BridgeResponse(True, self.backend_name, request.operation, parsed, latency_ms=int((time.time()-start)*1000))

        return BridgeResponse(False, self.backend_name, request.operation, {}, latency_ms=int((time.time()-start)*1000), error=f"Unsupported operation: {request.operation}")

    def _mock_result(self, request: BridgeRequest) -> Dict[str, Any]:
        if request.operation == "plan":
            state = request.payload["state"]
            pack_id = request.pack_id
            if pack_id == "cold_chain":
                return {
                    "intent": "Protect product integrity and maintain cold-chain compliance",
                    "strategy": "Stabilize storage, isolate inventory, reroute logistics, notify operators",
                    "steps": [
                        {"tool": "start_backup_cooling", "args": {"zone_id": state["signals"]["zone_id"]}, "rationale": "Immediate stabilization is needed.", "expected_effect": "Temperature returns toward acceptable band."},
                        {"tool": "quarantine_batch", "args": {"batch_id": state["signals"]["batch_id"], "reason": "Temperature excursion above threshold"}, "rationale": "Potentially impacted inventory must be isolated.", "expected_effect": "Batch blocked from release."},
                        {"tool": "divert_shipment", "args": {"shipment_id": state["signals"]["shipment_id"], "destination": state["signals"]["destination"]}, "rationale": "Outbound shipment may contain compromised goods.", "expected_effect": "Shipment rerouted."},
                        {"tool": "notify_team", "args": {"channel": "cold-chain-oncall", "message": "Zone-B incident contained. Batch VX-204 quarantined. SHP-884 diverted."}, "rationale": "Operators need awareness.", "expected_effect": "Incident team aligned."},
                    ],
                    "fallback": "Suspend all dispatches from Zone-B and escalate to QA lead",
                }
            return {
                "intent": "Prevent asset destruction and avoid cascading outage",
                "strategy": "Reduce stress, isolate asset, dispatch field response, notify operations",
                "steps": [
                    {"tool": "shed_load", "args": {"feeder_id": state["signals"]["feeder_id"], "percent": state["signals"]["load_shed_percent"]}, "rationale": "Lower thermal and electrical stress.", "expected_effect": "Loading decreases."},
                    {"tool": "isolate_transformer", "args": {"transformer_id": state["signals"]["transformer_id"]}, "rationale": "Prevent cascading damage.", "expected_effect": "Transformer isolated."},
                    {"tool": "dispatch_field_engineer", "args": {"site": state["signals"]["site"], "urgency": "P1"}, "rationale": "Physical inspection required.", "expected_effect": "Engineer mobilized."},
                    {"tool": "notify_team", "args": {"channel": "grid-ops-warroom", "message": "T-17 isolated. Load shed on F-12. P1 engineer dispatched."}, "rationale": "Operations coordination required.", "expected_effect": "War room aligned."},
                ],
                "fallback": "Trigger regional isolation protocol",
            }
        return {"message": "demo"}
