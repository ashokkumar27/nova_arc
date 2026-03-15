from __future__ import annotations

from .execution_engine import ExecutionEngine
from .policy_engine import PolicyEngine
from .replay_store import ReplayStore
from .verifier import Verifier


class MissionHarness:
    def __init__(
        self,
        profile,
        perception_adapter,
        planner_adapter,
        tool_registry,
        surface_adapter,
        auto_approve: bool = True,
    ):
        self.profile = profile
        self.perception = perception_adapter
        self.planner = planner_adapter
        self.tool_registry = tool_registry
        self.surface = surface_adapter
        self.replay = ReplayStore()
        self.policy = PolicyEngine(auto_approve=auto_approve)
        self.executor = ExecutionEngine()
        self.verifier = Verifier()

    def run(self, payload: dict):
        self.replay.log("mission_started", {
            "pack_id": self.profile.pack_id,
            "name": self.profile.name,
            "directive": self.profile.prime_directive,
        })
        state = self.perception.normalize(payload, self.profile)
        self.replay.log("state_normalized", {
            "summary": state.situation_summary,
            "risk_score": state.risk_score,
            "hazards": state.hazards,
        })
        policy_context = self.policy.evaluate_state(self.profile, state)
        self.replay.log("policy_evaluated", policy_context)
        plan = self.planner.plan(state, self.profile, policy_context, self.tool_registry)
        self.replay.log("plan_created", {
            "intent": plan.intent,
            "strategy": plan.strategy,
            "steps": [s.tool for s in plan.steps],
        })
        self.policy.validate_plan(self.profile, plan, self.tool_registry)
        approved = self.policy.approve(plan)
        self.replay.log("approval_result", {"approved": approved})
        if not approved:
            return self.surface.publish_abort(self.profile, state, plan, self.replay.all())
        results = self.executor.execute(plan, self.tool_registry, self.replay)
        verification = self.verifier.verify(self.profile, state, results)
        self.replay.log("verification_completed", {
            "success": verification.success,
            "residual_risk": verification.residual_risk,
            "achieved_conditions": verification.achieved_conditions,
            "missed_conditions": verification.missed_conditions,
        })
        return self.surface.publish(self.profile, state, plan, results, verification, self.replay.all())
