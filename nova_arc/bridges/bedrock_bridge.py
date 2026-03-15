from __future__ import annotations

from typing import Any, Dict, Iterator, List
import json
import re
import time

from nova_arc.config import AppConfig

from .contracts import BridgeRequest, BridgeResponse, RuntimeBridge


class BedrockConverseBridge(RuntimeBridge):
    backend_name = "bedrock-runtime"

    def __init__(self, config: AppConfig, enabled: bool = False):
        self.config = config
        self.model_id = config.nova_model_id
        self.region_name = config.aws_region
        self.enabled = enabled
        self._client = None
        self.auth_mode = "disabled"
        if enabled:
            import boto3
            from botocore.config import Config

            self.auth_mode = "bearer" if self._has_bearer_auth() else "standard"
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.region_name,
                config=Config(
                    connect_timeout=config.bedrock_timeout_seconds,
                    read_timeout=config.bedrock_timeout_seconds,
                    retries={"max_attempts": 1},
                ),
            )

    def _has_bearer_auth(self) -> bool:
        import os

        return bool(os.getenv("AWS_BEARER_TOKEN_BEDROCK"))

    def health(self) -> dict:
        if not self.enabled:
            return {
                "ok": True,
                "backend": self.backend_name,
                "detail": "demo planner active",
                "model_id": self.model_id,
            }
        return {
            "ok": self._client is not None,
            "backend": self.backend_name,
            "detail": f"Converse planner active ({self.auth_mode})",
            "model_id": self.model_id,
        }

    def invoke(self, request: BridgeRequest) -> BridgeResponse:
        start = time.time()
        if not self.enabled:
            result = self._mock_result(request)
            return BridgeResponse(True, self.backend_name, request.operation, result, latency_ms=int((time.time() - start) * 1000))

        try:
            if request.operation != "plan":
                return BridgeResponse(
                    False,
                    self.backend_name,
                    request.operation,
                    {},
                    latency_ms=int((time.time() - start) * 1000),
                    error=f"Unsupported operation: {request.operation}",
                )

            payload = request.payload
            response = self._client.converse(
                modelId=self.model_id,
                system=[{"text": payload["system_prompt"]}],
                messages=payload["messages"],
                inferenceConfig=payload.get("inference_config", {"maxTokens": 1400, "temperature": 0.1, "topP": 0.9}),
                toolConfig=payload.get("tool_config"),
            )
            content = response.get("output", {}).get("message", {}).get("content", [])
            parsed = self._normalize_plan(content, strict=payload.get("strict_json", True))
            usage = response.get("usage", {}) or {}
            parsed["raw_content"] = content
            return BridgeResponse(True, self.backend_name, request.operation, parsed, usage=usage, latency_ms=int((time.time() - start) * 1000))
        except Exception as exc:
            return BridgeResponse(
                False,
                self.backend_name,
                request.operation,
                {},
                latency_ms=int((time.time() - start) * 1000),
                error=f"{type(exc).__name__}: {exc}",
            )

    def stream(self, request: BridgeRequest) -> Iterator[dict]:
        if not self.enabled:
            yield {"event_type": "planner_text", "data": {"text": "Demo planner active"}}
            return
        response = self._client.converse_stream(
            modelId=self.model_id,
            system=[{"text": request.payload["system_prompt"]}],
            messages=request.payload["messages"],
            inferenceConfig=request.payload.get("inference_config", {"maxTokens": 1400, "temperature": 0.1, "topP": 0.9}),
            toolConfig=request.payload.get("tool_config"),
        )
        stream = response.get("stream", [])
        for event in stream:
            yield event

    @staticmethod
    def _extract_json_block(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        match = re.search(r"\{.*\}", text, flags=re.S)
        return match.group(0) if match else text

    def _normalize_plan(self, content: List[Dict[str, Any]] | str, strict: bool = False) -> Dict[str, Any]:
        text_blocks = []
        tool_steps = []

        if isinstance(content, str):
            text_blocks = [content]
        else:
            for block in content:
                if "text" in block:
                    text_blocks.append(block["text"])
                if "toolUse" in block:
                    tool_use = block["toolUse"]
                    tool_steps.append(
                        {
                            "tool": tool_use.get("name"),
                            "args": tool_use.get("input", {}),
                            "rationale": "Selected through Bedrock Converse tool use.",
                            "expected_effect": "Execute the requested operational intervention.",
                        }
                    )

        raw_text = "\n".join(text_blocks).strip()
        if tool_steps and not raw_text:
            return {
                "intent": "Contain incident",
                "strategy": "Use Bedrock tool selections to execute the approved interventions.",
                "steps": tool_steps,
                "fallback": "Escalate to human operations lead",
                "raw_text": raw_text,
            }

        candidate = self._extract_json_block(raw_text) if raw_text else "{}"
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            if strict:
                raise ValueError(f"Planner returned invalid JSON: {exc}") from exc
            parsed = {"strategy": raw_text, "steps": tool_steps}

        steps_in = parsed.get("steps") or tool_steps
        steps = []
        for idx, step in enumerate(steps_in):
            if not isinstance(step, dict):
                continue
            tool = step.get("tool") or step.get("name")
            if not tool:
                continue
            steps.append(
                {
                    "tool": str(tool),
                    "args": step.get("args") or step.get("input") or {},
                    "rationale": step.get("rationale") or step.get("reason") or f"Planner step {idx + 1}",
                    "expected_effect": step.get("expected_effect") or step.get("expected") or "Reduce operational risk",
                }
            )

        intent = str(parsed.get("intent") or "Contain incident")
        strategy = parsed.get("strategy")
        if not strategy and strict:
            raise ValueError("Planner returned no strategy")
        return {
            "intent": intent,
            "strategy": str(strategy or raw_text[:500] or "Assess and intervene safely"),
            "steps": steps,
            "fallback": parsed.get("fallback") or "Escalate to human operations lead",
            "raw_text": raw_text,
        }

    def _mock_result(self, request: BridgeRequest) -> Dict[str, Any]:
        state = request.payload["state"]
        if request.pack_id == "cold_chain":
            return {
                "intent": "Protect product integrity and patient safety",
                "strategy": "Stabilize the chamber, quarantine the batch, hold the shipment, and notify on-call.",
                "steps": [
                    {
                        "tool": "start_backup_cooling",
                        "args": {"zone_id": state["signals"]["zone_id"], "incident_id": state.get("incident_id")},
                        "rationale": "The chamber needs active cooling before inventory can be cleared.",
                        "expected_effect": "Temperature trend reverses toward the safe band.",
                    },
                    {
                        "tool": "quarantine_batch",
                        "args": {
                            "batch_id": state["signals"]["batch_id"],
                            "reason": "Temperature excursion above threshold in the affected zone.",
                            "incident_id": state.get("incident_id"),
                        },
                        "rationale": "Potentially exposed inventory must be isolated before release.",
                        "expected_effect": "Batch VX-204 is blocked from release.",
                    },
                    {
                        "tool": "hold_shipment",
                        "args": {
                            "shipment_id": state["signals"]["shipment_id"],
                            "reason": "Hold pending chamber stabilization and QA disposition.",
                            "incident_id": state.get("incident_id"),
                            "disposition": "held",
                        },
                        "rationale": "The outbound shipment must not leave while product integrity is uncertain.",
                        "expected_effect": "Shipment SHP-884 is held at the dock.",
                    },
                    {
                        "tool": "notify_team",
                        "args": {
                            "channel": "coldchain-oncall",
                            "message": "Zone B excursion contained. Backup cooling started, VX-204 quarantined, SHP-884 held.",
                            "incident_id": state.get("incident_id"),
                        },
                        "rationale": "On-call coordination is required for QA and warehouse leadership.",
                        "expected_effect": "The incident response team is aligned on the response.",
                    },
                ],
                "fallback": "Escalate to the warehouse incident commander and suspend all dispatches from Zone B.",
                "raw_text": "mock",
            }

        return {
            "intent": "Prevent asset loss and avoid cascading outage",
            "strategy": "Shed feeder load, isolate the transformer, dispatch a field engineer, and notify the war room.",
            "steps": [
                {
                    "tool": "shed_load",
                    "args": {"feeder_id": state["signals"]["feeder_id"], "percent": state["signals"]["load_shed_percent"]},
                    "rationale": "Reduce electrical stress before the fault spreads.",
                    "expected_effect": "Feeder loading drops immediately.",
                },
                {
                    "tool": "isolate_transformer",
                    "args": {"transformer_id": state["signals"]["transformer_id"]},
                    "rationale": "Prevent a cascading transformer failure.",
                    "expected_effect": "The transformer is isolated from service.",
                },
                {
                    "tool": "dispatch_field_engineer",
                    "args": {"site": state["signals"]["site"], "urgency": "P1"},
                    "rationale": "A physical inspection is required for safe restoration.",
                    "expected_effect": "A field engineer is en route.",
                },
                {
                    "tool": "notify_team",
                    "args": {"channel": "grid-ops-warroom", "message": "T-17 isolated, feeder load shed, P1 engineer dispatched."},
                    "rationale": "Operations leadership needs a coordinated status update.",
                    "expected_effect": "The war room is aligned on the next actions.",
                },
            ],
            "fallback": "Trigger regional isolation protocol and escalate to the control room lead.",
            "raw_text": "mock",
        }
