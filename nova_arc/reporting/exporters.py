from __future__ import annotations

from typing import Any, Dict
import json


def _strip_tables(output: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in output.items() if key != "tables"}


def build_json_report(output: Dict[str, Any]) -> str:
    return json.dumps(_strip_tables(output), indent=2, default=str)


def build_markdown_report(output: Dict[str, Any]) -> str:
    profile = output["profile"]
    state = output.get("state", {})
    plan = output.get("plan", {})
    verification = output.get("verification", {})

    lines = [
        f"# {profile['name']} Replay Report",
        "",
        f"- Pack: `{profile['pack_id']}`",
        f"- Prime directive: {profile['prime_directive']}",
        f"- Runtime mode: `{output.get('runtime_mode', 'demo')}`",
        f"- Planner model: `{output.get('runtime', {}).get('planner_model_id', 'demo')}`",
        "",
        "## Situation",
        "",
        state.get("situation_summary", "Mission aborted before a full situation summary was published."),
        "",
        f"- Risk score: {state.get('risk_score', 'n/a')}",
        f"- Confidence: {state.get('confidence', 'n/a')}",
        f"- Hazards: {', '.join(state.get('hazards', []))}",
        "",
        "## Evidence",
        "",
    ]

    for evidence in state.get("evidence", []):
        lines.append(
            f"- {evidence['title']} ({evidence['source_label']}, score {evidence['score']}): {evidence['snippet']}"
        )

    lines.extend(
        [
            "",
            "## Plan",
            "",
            f"- Intent: {plan.get('intent', 'n/a')}",
            f"- Strategy: {plan.get('strategy', 'n/a')}",
        ]
    )
    for idx, step in enumerate(plan.get("steps", []), start=1):
        lines.append(
            f"- Step {idx}: `{step['tool']}` -> {step['expected_effect']} | rationale: {step['rationale']}"
        )

    lines.extend(
        [
            "",
            "## Verification",
            "",
            f"- Success: {verification.get('success', 'n/a')}",
            f"- Residual risk: {verification.get('residual_risk', 'n/a')}",
            f"- Achieved: {', '.join(verification.get('achieved_conditions', [])) or 'none'}",
            f"- Missed: {', '.join(verification.get('missed_conditions', [])) or 'none'}",
            "",
            "## Replay",
            "",
        ]
    )
    for event in output.get("replay", []):
        lines.append(f"- {event['time']} | {event['type']} | {event['payload']}")

    return "\n".join(lines)


def build_export_bundle(output: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "json_report": build_json_report(output),
        "markdown_report": build_markdown_report(output),
    }
