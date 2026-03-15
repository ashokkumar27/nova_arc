from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class MissionProfile:
    pack_id: str
    name: str
    prime_directive: str
    objectives: List[str]
    input_modes: List[str]
    allowed_tools: List[str]
    approval_threshold: int
    mandatory_notify_threshold: int
    blocked_tool_categories: List[str]
    success_conditions: List[str]
    residual_risk_target: int
    surface_layout: str
    report_template: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerceivedState:
    mission: str
    context: str
    situation_summary: str
    entities: List[Dict[str, Any]]
    hazards: List[str]
    signals: Dict[str, Any]
    confidence: float
    risk_score: int
    recommended_outcome: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=utc_now)


@dataclass
class ActionStep:
    tool: str
    args: Dict[str, Any]
    rationale: str
    expected_effect: str


@dataclass
class ActionPlan:
    intent: str
    strategy: str
    steps: List[ActionStep]
    requires_approval: bool
    approval_reason: Optional[str]
    fallback: Optional[str]


@dataclass
class ToolExecutionResult:
    tool: str
    args: Dict[str, Any]
    success: bool
    output: str
    category: str
    timestamp: str = field(default_factory=utc_now)


@dataclass
class VerificationResult:
    success: bool
    summary: str
    achieved_conditions: List[str]
    missed_conditions: List[str]
    residual_risk: int
    next_step: Optional[str] = None
