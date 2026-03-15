import os
import sys
from pathlib import Path

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nova_arc.adapters.perception.runtime_perception import RuntimePerceptionAdapter
from nova_arc.adapters.planning.runtime_planner import RuntimePlannerAdapter
from nova_arc.adapters.surfaces.streamlit_surface import StreamlitSurfaceAdapter
from nova_arc.bridges.router import build_bridge_router
from nova_arc.core.harness import MissionHarness
from nova_arc.core.pack_loader import PackLoader
from nova_arc.testing.factories import build_registry

st.set_page_config(page_title="Nova A.R.C. Command Center", page_icon="⚡", layout="wide")

CUSTOM_CSS = """
<style>
.main .block-container {padding-top: 1.2rem; padding-bottom: 1rem; max-width: 1200px;}
.metric-card {background: linear-gradient(135deg, #101828 0%, #1f2937 100%); color: white; padding: 18px; border-radius: 18px; box-shadow: 0 8px 24px rgba(0,0,0,0.15);}
.panel {background: #ffffff; border: 1px solid #e5e7eb; border-radius: 18px; padding: 18px; box-shadow: 0 10px 30px rgba(15,23,42,0.06);}
.small-muted {color: #667085; font-size: 0.92rem;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def risk_status(score: int):
    if score >= 85:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 40:
        return "Moderate"
    return "Low"


def run_pack(pack_id: str, scenario: str, context: str, mode: str):
    loader = PackLoader("nova_arc/packs")
    profile = loader.load(pack_id)
    bridges = build_bridge_router(mode=mode, enable_bedrock=(mode != "demo"))
    harness = MissionHarness(
        profile=profile,
        perception_adapter=RuntimePerceptionAdapter(bridges.retrieval),
        planner_adapter=RuntimePlannerAdapter(bridges.planner),
        tool_registry=build_registry(bridges.browser),
        surface_adapter=StreamlitSurfaceAdapter(),
        auto_approve=True,
    )
    return harness.run({"scenario": scenario, "context": context, "input_type": "voice" if mode == "live_bridge" else "text"})


with st.sidebar:
    st.header("Mission Controls")
    mode = st.selectbox("Runtime Mode", ["demo", "live_bedrock", "live_bridge"], index=0)
    pack_choice = st.selectbox("Choose Command Center Pack", ["Pharma Cold Chain", "Grid Operations"])
    default_context = "Pharma DC / Vaccine Vault / KL North" if pack_choice == "Pharma Cold Chain" else "National Grid / Substation East"
    context = st.text_input("Mission Context", value=default_context)
    run = st.button("Run Mission", use_container_width=True)

if "output" not in st.session_state:
    st.session_state.output = None

if run:
    st.session_state.output = run_pack(
        pack_id="cold_chain" if pack_choice == "Pharma Cold Chain" else "grid_ops",
        scenario="cold_chain" if pack_choice == "Pharma Cold Chain" else "grid_ops",
        context=context,
        mode=mode,
    )

output = st.session_state.output

if output is None:
    st.title("Nova A.R.C. Command Center")
    st.caption("Seamless, pack-driven agentic harness for future command centers")
    st.write("Choose a pack and run the mission.")
else:
    profile = output["profile"]
    state = output["state"]
    plan = output["plan"]
    verification = output["verification"]

    st.title("Nova A.R.C. Command Center")
    st.caption("Prime Directive in. Pack loaded. Command center live.")

    c1, c2, c3 = st.columns([2.4, 1.2, 1.2])
    with c1:
        st.markdown(f"<div class='panel'><h3 style='margin-top:0'>{profile['name']}</h3><div class='small-muted'>Prime Directive</div><p>{profile['prime_directive']}</p><div class='small-muted'>Context</div><p>{state['context']}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><div>Risk Score</div><h2>{state['risk_score']}</h2><div>{risk_status(state['risk_score'])}</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><div>Confidence</div><h2>{int(state['confidence']*100)}%</h2><div>Planner grounded</div></div>", unsafe_allow_html=True)

    st.markdown("## Judge-Friendly Summary")
    st.markdown(f"- Same harness core loaded the **{profile['name']}** pack.\n- It interpreted the situation, generated a **{len(plan['steps'])}-step** plan, executed approved tools, and reduced residual risk to **{verification['residual_risk']}**.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Situation", "Plan", "Execution", "Verification", "Replay"])

    with tab1:
        col_a, col_b = st.columns([2,1])
        with col_a:
            st.markdown("### Situation Overview")
            st.info(state["situation_summary"])
            st.write("**Hazards**")
            for h in state["hazards"]:
                st.write(f"- {h}")
            st.write("**Signals**")
            for k, v in state["signals"].items():
                st.write(f"- **{k}**: {v}")
        with col_b:
            st.markdown("### Recommended Outcome")
            st.success(state["recommended_outcome"])
            st.write("**Entities**")
            st.dataframe(output["tables"]["entities_df"], use_container_width=True)
        st.markdown("### Evidence Grounding")
        st.dataframe(output["tables"]["evidence_df"], use_container_width=True)

    with tab2:
        st.markdown("### Planned Intervention")
        st.write(f"**Intent:** {plan['intent']}")
        st.write(f"**Strategy:** {plan['strategy']}")
        if plan["approval_reason"]:
            st.warning(f"Approval Reason: {plan['approval_reason']}")
        for i, step in enumerate(plan["steps"], 1):
            with st.expander(f"Step {i}: {step['tool']}", expanded=True):
                st.write(f"**Rationale:** {step['rationale']}")
                st.write(f"**Expected Effect:** {step['expected_effect']}")
                st.json(step["args"])
        if plan["fallback"]:
            st.write(f"**Fallback:** {plan['fallback']}")

    with tab3:
        st.markdown("### Execution Results")
        st.dataframe(output["tables"]["results_df"], use_container_width=True)

    with tab4:
        k1, k2, k3 = st.columns(3)
        k1.metric("Mission Success", "Yes" if verification["success"] else "No")
        k2.metric("Residual Risk", verification["residual_risk"])
        k3.metric("Achieved Conditions", len(verification["achieved_conditions"]))
        if verification["success"]:
            st.success(verification["summary"])
        else:
            st.error(verification["summary"])
        left, right = st.columns(2)
        with left:
            st.write("**Achieved Conditions**")
            for item in verification["achieved_conditions"]:
                st.write(f"- {item}")
        with right:
            st.write("**Missed Conditions**")
            if verification["missed_conditions"]:
                for item in verification["missed_conditions"]:
                    st.write(f"- {item}")
            else:
                st.write("- None")
        if verification["next_step"]:
            st.warning(f"Next Step: {verification['next_step']}")

    with tab5:
        st.markdown("### Replay Timeline")
        st.dataframe(output["tables"]["timeline_df"], use_container_width=True)
        st.download_button(
            label="Download incident report JSON",
            data=__import__('json').dumps(output, default=str, indent=2),
            file_name=f"{profile['pack_id']}_incident_report.json",
            mime="application/json",
            use_container_width=True,
        )
