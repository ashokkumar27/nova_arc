import json
import os
import sys

import streamlit as st
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nova_arc.adapters.perception.runtime_perception import RuntimePerceptionAdapter
from nova_arc.adapters.planning.runtime_planner import RuntimePlannerAdapter
from nova_arc.adapters.surfaces.streamlit_surface import StreamlitSurfaceAdapter
from nova_arc.bridges.router import build_bridge_router
from nova_arc.core.harness import MissionHarness
from nova_arc.core.pack_loader import PackLoader
from nova_arc.testing.factories import build_registry

load_dotenv()

st.set_page_config(page_title="Nova A.R.C. Command Center", page_icon="⚡", layout="wide")

CUSTOM_CSS = """
<style>
[data-testid="stAppViewContainer"] {background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);} 
.main .block-container {padding-top: 1.1rem; padding-bottom: 1rem; max-width: 1320px;}
.hero {background: linear-gradient(135deg,#0f172a 0%,#111827 50%,#1d4ed8 100%); color:white; border-radius:24px; padding:24px; box-shadow:0 18px 50px rgba(15,23,42,0.25);}
.glass {background: rgba(255,255,255,0.88); backdrop-filter: blur(10px); border:1px solid rgba(255,255,255,0.6); border-radius:20px; padding:18px; box-shadow:0 10px 32px rgba(15,23,42,0.08);} 
.metric-shell {background: linear-gradient(180deg,#111827 0%,#0f172a 100%); color:white; border-radius:20px; padding:18px; box-shadow:0 12px 30px rgba(15,23,42,0.18);} 
.section-title {font-size: 1.05rem; font-weight: 700; margin-bottom: 0.55rem;}
.small-muted {color: #6b7280; font-size: 0.92rem;}
.kpi {font-size: 2rem; font-weight: 800; margin: 0.1rem 0;}
.badge {display:inline-block; padding:6px 10px; border-radius:999px; background:#dbeafe; color:#1d4ed8; font-weight:700; font-size:.8rem;}
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


def risk_delta(score: int, residual: int):
    return score - residual


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
    output = harness.run({"scenario": scenario, "context": context, "input_type": "voice" if mode == "live_bridge" else "text"})
    output["bridge_health"] = bridges.health()
    output["runtime_mode"] = mode
    return output


with st.sidebar:
    st.header("Mission Controls")
    mode = st.selectbox("Runtime Mode", ["demo", "live_bedrock", "live_bridge"], index=0)
    pack_choice = st.selectbox("Choose Command Center Pack", ["Pharma Cold Chain", "Grid Operations"])
    default_context = "Pharma DC / Vaccine Vault / KL North" if pack_choice == "Pharma Cold Chain" else "National Grid / Substation East"
    context = st.text_input("Mission Context", value=default_context)
    show_debug = st.toggle("Show debug panels", value=False)
    run = st.button("Run Mission", use_container_width=True, type="primary")
    st.divider()
    st.caption("Live Bedrock requires boto3 plus working Bedrock permissions/model access.")

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
    st.markdown("<div class='hero'><div class='badge'>Agentic Harness Engineering</div><h1 style='margin:0.35rem 0 0.5rem 0;'>Nova A.R.C. Command Center</h1><p style='font-size:1.03rem;max-width:860px;'>A close-to-real command-center runtime that loads a mission pack, normalizes an incident, plans safe interventions, executes approved tools, verifies outcomes, and renders a replay trail in one surface.</p></div>", unsafe_allow_html=True)
    a,b,c = st.columns(3)
    with a:
        st.markdown("<div class='glass'><div class='section-title'>Pack-driven</div><p>Cold chain and grid operations use the same harness core with different directives, tools, and success conditions.</p></div>", unsafe_allow_html=True)
    with b:
        st.markdown("<div class='glass'><div class='section-title'>Live-ready</div><p>Bedrock planning path is wired through the bridge layer. Sonic and Nova Act remain seamless bridge targets.</p></div>", unsafe_allow_html=True)
    with c:
        st.markdown("<div class='glass'><div class='section-title'>Replayable</div><p>Every mission step is logged into a timeline for verification, debugging, and auditability.</p></div>", unsafe_allow_html=True)
else:
    profile = output["profile"]
    state = output["state"]
    plan = output["plan"]
    verification = output["verification"]
    health = output.get("bridge_health", {})

    st.markdown(f"<div class='hero'><div class='badge'>{output.get('runtime_mode','demo').replace('_',' ').title()}</div><h1 style='margin:0.35rem 0 0.5rem 0;'>{profile['name']}</h1><p style='font-size:1.03rem;max-width:920px;'><strong>Prime Directive:</strong> {profile['prime_directive']}<br/><span style='opacity:0.9'>Context: {state['context']}</span></p></div>", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"<div class='metric-shell'><div class='small-muted'>Initial Risk</div><div class='kpi'>{state['risk_score']}</div><div>{risk_status(state['risk_score'])}</div></div>", unsafe_allow_html=True)
    with k2:
        st.markdown(f"<div class='metric-shell'><div class='small-muted'>Residual Risk</div><div class='kpi'>{verification['residual_risk']}</div><div>{risk_status(verification['residual_risk'])}</div></div>", unsafe_allow_html=True)
    with k3:
        st.markdown(f"<div class='metric-shell'><div class='small-muted'>Risk Reduced</div><div class='kpi'>{risk_delta(state['risk_score'], verification['residual_risk'])}</div><div>Containment effect</div></div>", unsafe_allow_html=True)
    with k4:
        st.markdown(f"<div class='metric-shell'><div class='small-muted'>Confidence</div><div class='kpi'>{int(state['confidence']*100)}%</div><div>{'Success' if verification['success'] else 'Escalation needed'}</div></div>", unsafe_allow_html=True)

    s1, s2 = st.columns([1.6, 1])
    with s1:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("Operational Situation")
        st.info(state["situation_summary"])
        st.write("**Recommended Outcome**")
        st.success(state["recommended_outcome"])
        st.write("**Mission Objectives**")
        for obj in profile["objectives"]:
            st.write(f"- {obj}")
        st.markdown("</div>", unsafe_allow_html=True)
    with s2:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("Bridge Health")
        for name, item in health.items():
            status = "🟢" if item.get("ok") else "🔴"
            st.write(f"{status} **{name.title()}** — {item.get('detail','ready')}")
            extra = {k:v for k,v in item.items() if k not in {'ok','backend','detail'}}
            if extra:
                st.caption(str(extra))
        st.markdown("</div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Situation", "Plan", "Execution", "Verification", "Replay", "Debug"])

    with tab1:
        a, b = st.columns([1.25, 1])
        with a:
            st.markdown("### Hazards & Signals")
            for h in state["hazards"]:
                st.write(f"- {h}")
            st.write("")
            st.json(state["signals"])
        with b:
            st.markdown("### Entities")
            st.dataframe(output["tables"]["entities_df"], use_container_width=True)
            st.markdown("### Evidence Grounding")
            st.dataframe(output["tables"]["evidence_df"], use_container_width=True)

    with tab2:
        st.markdown("### Planned Intervention")
        st.write(f"**Intent:** {plan['intent']}")
        st.write(f"**Strategy:** {plan['strategy']}")
        meta1, meta2, meta3 = st.columns(3)
        meta1.metric("Steps", len(plan["steps"]))
        meta2.metric("Approval", "Required" if plan["requires_approval"] else "Not required")
        meta3.metric("Fallback", "Ready" if plan["fallback"] else "None")
        if plan["approval_reason"]:
            st.warning(f"Approval Reason: {plan['approval_reason']}")
        for i, step in enumerate(plan["steps"], 1):
            with st.expander(f"Step {i}: {step['tool']}", expanded=True):
                left, right = st.columns([1.5,1])
                with left:
                    st.write(f"**Rationale:** {step['rationale']}")
                    st.write(f"**Expected Effect:** {step['expected_effect']}")
                with right:
                    st.json(step["args"])
        if plan["fallback"]:
            st.info(f"Fallback: {plan['fallback']}")

    with tab3:
        st.markdown("### Execution Results")
        st.dataframe(output["tables"]["results_df"], use_container_width=True)

    with tab4:
        v1, v2 = st.columns([1.3,1])
        with v1:
            if verification["success"]:
                st.success(verification["summary"])
            else:
                st.error(verification["summary"])
            st.metric("Residual Risk", verification["residual_risk"])
            if verification["next_step"]:
                st.warning(f"Next Step: {verification['next_step']}")
        with v2:
            st.write("**Achieved Conditions**")
            for item in verification["achieved_conditions"]:
                st.write(f"- {item}")
            st.write("**Missed Conditions**")
            if verification["missed_conditions"]:
                for item in verification["missed_conditions"]:
                    st.write(f"- {item}")
            else:
                st.write("- None")

    with tab5:
        st.markdown("### Replay Timeline")
        st.dataframe(output["tables"]["timeline_df"], use_container_width=True)
        st.download_button(
            label="Download incident report JSON",
            data=json.dumps(output, default=str, indent=2),
            file_name=f"{profile['pack_id']}_incident_report.json",
            mime="application/json",
            use_container_width=True,
        )

    with tab6:
        if show_debug:
            st.markdown("### Planner Debug")
            st.write("**Planner usage**")
            st.json(output.get("debug", {}).get("planner_usage", {}))
            st.write("**Planner raw output**")
            raw = output.get("debug", {}).get("planner_raw_output")
            if isinstance(raw, str):
                st.code(raw, language="text")
            else:
                st.json(raw or {})
            if output.get("debug", {}).get("planner_error"):
                st.error(output["debug"]["planner_error"])
        else:
            st.info("Enable 'Show debug panels' in the sidebar to inspect raw live planner output.")
