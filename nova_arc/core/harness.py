from .replay_store import ReplayStore
from .policy_engine import PolicyEngine
from .execution_engine import ExecutionEngine
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
        self.verifier = Verifier(getattr(perception_adapter, "backend_client", None))

    def _sanitize_plan(self, plan):
        allowed = set(self.profile.allowed_tools)
        filtered_steps = [step for step in plan.steps if step.tool in allowed]
        removed = [step.tool for step in plan.steps if step.tool not in allowed]

        if removed:
            note = f"Removed forbidden tools: {', '.join(removed)}"
            plan.sanitization_notes.append(note)
            self.replay.log("plan_sanitized", {
                "removed_forbidden_tools": removed,
                "allowed_tools": sorted(allowed),
            })

        plan.steps = filtered_steps
        return plan

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
            "incident_id": state.incident_id,
        })
        self.replay.log("evidence_grounded", {
            "incident_id": state.incident_id,
            "evidence_ids": [item.get("id") for item in state.evidence],
            "trace": state.retrieval_trace,
        })

        policy_context = self.policy.evaluate_state(self.profile, state)
        self.replay.log("policy_evaluated", policy_context)

        allowed_tool_registry = self.tool_registry.subset(self.profile.allowed_tools)

        plan = self.planner.plan(state, self.profile, policy_context, allowed_tool_registry)
        plan = self._sanitize_plan(plan)

        self.replay.log("plan_created", {
            "intent": plan.intent,
            "strategy": plan.strategy,
            "steps": [s.tool for s in plan.steps],
            "sanitization_notes": plan.sanitization_notes,
        })

        if not plan.steps:
            raise ValueError(
                f"Planner produced no valid steps for pack '{self.profile.pack_id}'. "
                f"Allowed tools were: {self.profile.allowed_tools}"
            )

        self.policy.validate_plan(self.profile, plan, allowed_tool_registry)

        approved = self.policy.approve(plan)
        self.replay.log("approval_result", {"approved": approved})

        if not approved:
            return self.surface.publish_abort(self.profile, state, plan, self.replay.all())

        results = self.executor.execute(plan, allowed_tool_registry, self.replay)

        verification = self.verifier.verify(self.profile, state, results)
        self.replay.log("verification_completed", {
            "success": verification.success,
            "residual_risk": verification.residual_risk,
            "achieved_conditions": verification.achieved_conditions,
            "missed_conditions": verification.missed_conditions,
            "details": verification.details,
        })

        return self.surface.publish(
            self.profile,
            state,
            plan,
            results,
            verification,
            self.replay.all(),
        )
