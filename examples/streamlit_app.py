from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nova_arc.config import AppConfig, load_environment
from nova_arc.runtime import run_mission
from nova_arc.ui_helpers import classify_error, default_context, default_transcript, risk_delta, risk_status


load_environment()
CONFIG = AppConfig.from_env()

st.set_page_config(page_title="Nova A.R.C. ColdChain Live", page_icon="N", layout="wide")

CUSTOM_CSS = """
<style>
:root {
  --ink: #f6f8fc;
  --muted: #a9bfd7;
  --soft-ink: #d7e6f5;
  --bg0: #04111f;
  --bg1: #0c2340;
  --bg2: #173d5e;
  --glass: rgba(9, 25, 43, 0.78);
  --line: rgba(169, 191, 215, 0.18);
  --accent: #8ef0cf;
  --warn: #ffb266;
  --danger: #ff7d7d;
  --sidebar-ink: #e7f0fa;
  --sidebar-muted: #9bb5cf;
  --input-bg: rgba(231, 240, 250, 0.96);
  --input-ink: #14314d;
}
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at top right, rgba(40, 101, 164, 0.35), transparent 30%),
    radial-gradient(circle at bottom left, rgba(142, 240, 207, 0.18), transparent 28%),
    linear-gradient(180deg, var(--bg0) 0%, #081827 36%, #0a1d31 100%);
  color: var(--ink);
}
header[data-testid="stHeader"] {
  background: linear-gradient(180deg, rgba(4, 17, 31, 0.96), rgba(4, 17, 31, 0.62));
  border-bottom: 1px solid rgba(169, 191, 215, 0.12);
}
[data-testid="stDecoration"] {
  background: linear-gradient(90deg, rgba(142, 240, 207, 0.95), rgba(78, 167, 255, 0.95));
}
[data-testid="stStatusWidget"] *,
[data-testid="stToolbar"] * {
  color: var(--soft-ink) !important;
}
.main .block-container {
  padding-top: 1.1rem;
  padding-bottom: 1rem;
  max-width: 1440px;
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(8, 23, 39, 0.98), rgba(10, 32, 54, 0.98));
  border-right: 1px solid rgba(169, 191, 215, 0.12);
}
[data-testid="stSidebar"] .block-container {
  padding-top: 2rem;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-baseweb="checkbox"] span,
[data-testid="stSidebar"] [data-baseweb="radio"] span {
  color: var(--sidebar-ink) !important;
}
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  color: var(--sidebar-muted) !important;
}
[data-testid="stSidebar"] a {
  color: #7fc4ff !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
  background: var(--input-bg) !important;
  color: var(--input-ink) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  box-shadow: none !important;
}
[data-testid="stSidebar"] textarea::placeholder,
[data-testid="stSidebar"] input::placeholder {
  color: rgba(20, 49, 77, 0.65) !important;
}
[data-testid="stSidebar"] svg {
  fill: rgba(20, 49, 77, 0.8) !important;
}
[data-testid="stSidebar"] .stButton > button {
  background: linear-gradient(135deg, #8ef0cf 0%, #58c4ef 100%) !important;
  color: #082032 !important;
  border: none !important;
  font-weight: 800 !important;
  box-shadow: 0 10px 24px rgba(88, 196, 239, 0.2);
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: linear-gradient(135deg, #a6f7db 0%, #74d3f4 100%) !important;
  color: #04111f !important;
}
[data-testid="stSidebar"] .stButton > button:disabled {
  background: rgba(148, 163, 184, 0.18) !important;
  color: rgba(231, 240, 250, 0.45) !important;
  border: 1px solid rgba(169, 191, 215, 0.12) !important;
}
[data-testid="stSidebar"] [data-baseweb="switch"] > div {
  background-color: rgba(147, 197, 253, 0.26) !important;
}
[data-testid="stSidebar"] [data-baseweb="switch"] input:checked + div,
[data-testid="stSidebar"] [data-baseweb="switch"] div[aria-checked="true"] {
  background-color: rgba(142, 240, 207, 0.5) !important;
}
.hero {
  background:
    linear-gradient(120deg, rgba(7, 18, 31, 0.96), rgba(20, 61, 94, 0.92)),
    radial-gradient(circle at top right, rgba(142, 240, 207, 0.2), transparent 20%);
  border: 1px solid var(--line);
  border-radius: 28px;
  padding: 28px;
  box-shadow: 0 20px 70px rgba(0, 0, 0, 0.24);
}
.badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(142, 240, 207, 0.35);
  color: var(--accent);
  background: rgba(142, 240, 207, 0.08);
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.glass {
  background: var(--glass);
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 18px;
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.18);
}
.metric {
  background: linear-gradient(180deg, rgba(10, 24, 40, 0.92), rgba(7, 19, 31, 0.92));
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 18px;
}
.metric .label { color: var(--muted); font-size: 0.92rem; }
.metric .value { color: var(--ink); font-size: 2.05rem; font-weight: 800; margin-top: 8px; }
.card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 16px;
  margin-bottom: 12px;
}
.card h4 { margin: 0 0 10px 0; color: var(--ink); }
.meta { color: var(--muted); font-size: 0.9rem; }
.status-pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  margin-right: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  background: rgba(142, 240, 207, 0.1);
  color: var(--accent);
}
.danger-pill { background: rgba(255, 125, 125, 0.12); color: var(--danger); }
.warning-pill { background: rgba(255, 178, 102, 0.12); color: var(--warn); }
.section-title {
  font-size: 1.04rem;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 12px;
}
.stTabs [data-baseweb="tab-list"] {
  gap: 10px;
}
.stTabs [data-baseweb="tab"] {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(169, 191, 215, 0.14);
  border-radius: 999px;
  color: var(--soft-ink);
  font-weight: 700;
  padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
  background: rgba(142, 240, 207, 0.12) !important;
  color: var(--accent) !important;
  border-color: rgba(142, 240, 207, 0.28) !important;
}
.stAlert,
.stSuccess,
.stWarning,
.stError,
.stInfo {
  color: var(--ink) !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricLabel"],
[data-testid="stMetricDelta"] {
  color: var(--ink) !important;
}
[data-testid="stDataFrame"] {
  border-radius: 18px;
  overflow: hidden;
}
.stJson {
  border-radius: 16px;
}
.divider {
  height: 1px;
  background: var(--line);
  margin: 16px 0;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


PACKS = {
    "Nova A.R.C. ColdChain Live": {"pack_id": "cold_chain", "scenario": "cold_chain"},
    "Grid Ops Proof": {"pack_id": "grid_ops", "scenario": "grid_ops"},
}


def render_bridge_health(bridge_health: dict):
    cards = []
    for name, item in bridge_health.items():
        pill_class = "status-pill" if item.get("ok") else "status-pill danger-pill"
        cards.append(
            f"""
            <div class="card">
              <div class="{pill_class}">{name.replace('_', ' ').title()}</div>
              <div class="meta">{item.get('detail', 'ready')}</div>
              <div style="margin-top:8px;color:var(--ink);font-weight:700;">{item.get('model_id', item.get('portal_url', ''))}</div>
            </div>
            """
        )
    st.markdown("".join(cards), unsafe_allow_html=True)


def render_evidence_cards(evidence: list[dict]):
    for item in evidence:
        st.markdown(
            f"""
            <div class="card">
              <div class="status-pill">{item.get('source_label', item.get('modality', 'Evidence'))}</div>
              <h4>{item.get('title', 'Evidence')}</h4>
              <div class="meta">Score: {item.get('score', 'n/a')} | Path: {item.get('path', '')}</div>
              <p style="margin-top:10px;">{item.get('snippet', '')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_plan_steps(steps: list[dict]):
    for index, step in enumerate(steps, start=1):
        st.markdown(
            f"""
            <div class="card">
              <div class="status-pill">Step {index}</div>
              <h4>{step['tool']}</h4>
              <div class="meta">Expected effect: {step['expected_effect']}</div>
              <p style="margin-top:10px;"><strong>Rationale:</strong> {step['rationale']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.json(step["args"])


def render_results(results: list[dict]):
    for result in results:
        pill_class = "status-pill" if result["success"] else "status-pill danger-pill"
        bridge_label = result.get("bridge_label") or result["category"]
        st.markdown(
            f"""
            <div class="card">
              <div class="{pill_class}">{'Completed' if result['success'] else 'Failed'}</div>
              <div class="status-pill warning-pill">{bridge_label}</div>
              <h4>{result['tool']}</h4>
              <div class="meta">{result['output']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if result.get("details"):
            st.json(result["details"])


def render_error_panel(error_payload: dict):
    st.markdown(
        f"""
        <div class="glass" style="border-color: rgba(255, 125, 125, 0.35);">
          <div class="status-pill danger-pill">{error_payload['title']}</div>
          <h3 style="color: var(--ink); margin-top: 10px;">Mission execution did not complete</h3>
          <p>{error_payload['detail']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown("## Mission Controls")
    pack_name = st.selectbox("Pack", list(PACKS.keys()), index=0)
    mode = st.selectbox("Runtime Mode", ["demo", "live_bedrock", "live_bridge"], index=0)
    pack = PACKS[pack_name]
    context = st.text_input("Mission Context", value=default_context(pack["pack_id"]))
    transcript = st.text_area("Voice / Transcript Intake", value=default_transcript(pack["pack_id"]), height=140)
    show_debug = st.toggle("Show debug drawer", value=True)
    run = st.button("Run Mission", use_container_width=True, type="primary")
    st.caption(f"Backend: {CONFIG.backend_url}")
    st.caption(f"Planner model: {CONFIG.nova_model_id}")

if "mission_output" not in st.session_state:
    st.session_state.mission_output = None
    st.session_state.mission_error = None

if run:
    try:
        st.session_state.mission_output = run_mission(
            pack_id=pack["pack_id"],
            scenario=pack["scenario"],
            transcript=transcript,
            context=context,
            mode=mode,
            config=CONFIG,
            use_http_backend=True,
            reset_backend=True,
        )
        st.session_state.mission_error = None
    except Exception as exc:
        st.session_state.mission_output = None
        st.session_state.mission_error = classify_error(str(exc))

output = st.session_state.mission_output
error = st.session_state.mission_error

if output is None and error is None:
    st.markdown(
        """
        <div class="hero">
          <div class="badge">Amazon Nova Command Center</div>
          <h1 style="margin: 12px 0 12px 0; color: var(--ink);">Nova A.R.C. ColdChain Live</h1>
          <p style="max-width: 860px; color: var(--muted); font-size: 1.03rem;">
            A filmable incident command surface where a spoken warehouse issue is grounded with multimodal evidence,
            planned with Amazon Nova, executed through real tools, verified against backend state, and replayed as a premium mission timeline.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    a, b, c = st.columns(3)
    with a:
        st.markdown(
            """
            <div class="glass">
              <div class="section-title">Voice + Evidence</div>
              <p>Voice ingress is framed through Nova 2 Sonic and grounded with SOP, dashboard, log, and prior incident evidence.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b:
        st.markdown(
            """
            <div class="glass">
              <div class="section-title">Agentic Tooling</div>
              <p>Amazon Nova planning is constrained by pack-scoped tools, including a real local Nova Act-style admin workflow.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c:
        st.markdown(
            """
            <div class="glass">
              <div class="section-title">Replayable By Design</div>
              <p>Every stage is logged, verified, exportable, and ready to show in a 3-minute hackathon demo.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

if error is not None:
    render_error_panel(error)

if output is not None:
    profile = output["profile"]
    state = output["state"]
    verification = output["verification"]

    st.markdown(
        f"""
        <div class="hero">
          <div class="badge">{output['runtime_mode'].replace('_', ' ').title()}</div>
          <div class="badge">Voice Ingress: Nova 2 Sonic</div>
          <h1 style="margin: 12px 0 8px 0; color: var(--ink);">{profile['name']}</h1>
          <p style="color: var(--muted); max-width: 920px;">
            <strong>Prime directive:</strong> {profile['prime_directive']}<br/>
            <strong>Context:</strong> {state['context']}<br/>
            <strong>Planner model:</strong> {output['runtime']['planner_model_id']}
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    for column, label, value, note in [
        (k1, "Current Risk", state["risk_score"], risk_status(state["risk_score"])),
        (k2, "Residual Risk", verification["residual_risk"], risk_status(verification["residual_risk"])),
        (k3, "Risk Reduced", risk_delta(state["risk_score"], verification["residual_risk"]), "Containment effect"),
        (k4, "Confidence", f"{int(state['confidence'] * 100)}%", "Grounded mission confidence"),
    ]:
        with column:
            st.markdown(
                f"""
                <div class="metric">
                  <div class="label">{label}</div>
                  <div class="value">{value}</div>
                  <div class="meta">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    left, right = st.columns([1.7, 1])
    with left:
        st.markdown(
            f"""
            <div class="glass">
              <div class="section-title">Mission Header</div>
              <div class="status-pill">{profile['pack_id']}</div>
              <div class="status-pill warning-pill">{output['runtime_mode']}</div>
              <p style="margin-top:12px;"><strong>Summary:</strong> {state['situation_summary']}</p>
              <p><strong>Transcript:</strong> {state['source_transcript']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown("<div class='glass'><div class='section-title'>Bridge Health</div>", unsafe_allow_html=True)
        render_bridge_health(output["bridge_health"])
        st.markdown("</div>", unsafe_allow_html=True)

    tabs = st.tabs(
        [
            "Situation Overview",
            "Evidence Grounding",
            "Planned Intervention",
            "Action Execution",
            "Verification",
            "Replay Timeline",
            "Exports",
        ]
    )

    with tabs[0]:
        a, b = st.columns([1.1, 1])
        with a:
            st.markdown("<div class='glass'><div class='section-title'>Incident Summary</div>", unsafe_allow_html=True)
            st.write(state["situation_summary"])
            st.write("**Hazards**")
            for hazard in state["hazards"]:
                st.write(f"- {hazard}")
            st.write("**Signals**")
            st.json(state["signals"])
            st.markdown("</div>", unsafe_allow_html=True)
        with b:
            st.markdown("<div class='glass'><div class='section-title'>Entities And Backend State</div>", unsafe_allow_html=True)
            st.dataframe(output["tables"]["entities_df"], use_container_width=True)
            snapshot = state.get("backend_snapshot", {})
            if snapshot.get("batches"):
                st.write("**Batches**")
                st.dataframe(snapshot["batches"], use_container_width=True)
            if snapshot.get("shipments"):
                st.write("**Shipments**")
                st.dataframe(snapshot["shipments"], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown("<div class='glass'><div class='section-title'>Evidence Grounding</div>", unsafe_allow_html=True)
        render_evidence_cards(state["evidence"])
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        plan = output["plan"]
        meta1, meta2, meta3 = st.columns(3)
        meta1.metric("Intent", plan["intent"])
        meta2.metric("Approval", "Required" if plan["requires_approval"] else "Auto")
        meta3.metric("Fallback", "Ready" if plan["fallback"] else "None")
        st.markdown("<div class='glass'><div class='section-title'>Planner Strategy</div>", unsafe_allow_html=True)
        st.write(plan["strategy"])
        if plan["sanitization_notes"]:
            for note in plan["sanitization_notes"]:
                st.warning(note)
        render_plan_steps(plan["steps"])
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        st.markdown("<div class='glass'><div class='section-title'>Action Execution</div>", unsafe_allow_html=True)
        render_results(output["results"])
        if not output["tables"]["actions_df"].empty:
            st.write("**Backend Action Log**")
            st.dataframe(output["tables"]["actions_df"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]:
        st.markdown("<div class='glass'><div class='section-title'>Verification</div>", unsafe_allow_html=True)
        if verification["success"]:
            st.success(verification["summary"])
        else:
            st.error(verification["summary"])
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Achieved Conditions**")
            for item in verification["achieved_conditions"]:
                st.write(f"- {item}")
        with c2:
            st.write("**Missed Conditions**")
            if verification["missed_conditions"]:
                for item in verification["missed_conditions"]:
                    st.write(f"- {item}")
            else:
                st.write("- none")
        if verification.get("next_step"):
            st.warning(verification["next_step"])
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[5]:
        st.markdown("<div class='glass'><div class='section-title'>Replay Timeline</div>", unsafe_allow_html=True)
        st.dataframe(output["tables"]["timeline_df"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[6]:
        st.markdown("<div class='glass'><div class='section-title'>Exports</div>", unsafe_allow_html=True)
        st.download_button(
            label="Download JSON Report",
            data=output["exports"]["json_report"],
            file_name=f"{profile['pack_id']}_command_report.json",
            mime="application/json",
            use_container_width=True,
        )
        st.download_button(
            label="Download Markdown Replay",
            data=output["exports"]["markdown_report"],
            file_name=f"{profile['pack_id']}_command_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if show_debug:
        with st.expander("Debug Drawer", expanded=False):
            st.write("**Planner Raw Output**")
            st.code(str(output["debug"]["planner_raw_output"]), language="text")
            st.write("**Planner Request**")
            st.json(output["debug"]["planner_request"])
            st.write("**Voice Bridge Response**")
            st.json(output["debug"]["voice_response"])
            st.write("**Retrieval Trace**")
            st.json(state["retrieval_trace"])
            st.write("**Bridge Responses**")
            st.json(output["bridge_health"])
