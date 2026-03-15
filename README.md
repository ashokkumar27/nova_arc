# Nova A.R.C. ColdChain Live

Nova A.R.C. ColdChain Live is a pack-driven incident command center built for a filmable Amazon Nova hackathon submission. It grounds a spoken cold-chain incident with multimodal evidence, plans a policy-aware response with Amazon Bedrock Converse, executes real tools against a SQLite-backed FastAPI service, verifies backend outcomes, and exports a replayable mission report.

## What is in this branch

- `Amazon Bedrock Runtime` planner bridge using `boto3.client("bedrock-runtime")` and `Converse` with a `read_timeout` of `3600`
- `Nova 2 Sonic` voice ingress bridge with a transcript-first event contract
- `Nova Multimodal Embeddings` retrieval bridge over:
  - SOP PDF
  - dashboard screenshot
  - incident log CSV
  - prior incident note
- `Nova Act` local admin-portal workflow bridge for:
  - batch quarantine
  - shipment hold
- FastAPI backend with SQLite persistence for:
  - `incidents`
  - `batches`
  - `shipments`
  - `action_log`
  - `evidence_sources`
- Premium Streamlit command center UI with:
  - Situation Overview
  - Evidence Grounding
  - Planned Intervention
  - Action Execution
  - Verification
  - Replay Timeline
  - Exports
- Secondary `Grid Ops` pack on the same harness
- Automated tests for planner parsing, sanitization, bridge routing, backend state changes, exports, pack scoping, and UI helpers

## Key paths

- Streamlit UI: [`examples/streamlit_app.py`](/c:/Users/user/nova_arc/examples/streamlit_app.py)
- Demo runner: [`examples/demo.py`](/c:/Users/user/nova_arc/examples/demo.py)
- FastAPI backend: [`nova_arc/backend/api.py`](/c:/Users/user/nova_arc/nova_arc/backend/api.py)
- Runtime assembly: [`nova_arc/runtime.py`](/c:/Users/user/nova_arc/nova_arc/runtime.py)
- Cold-chain pack: [`nova_arc/packs/cold_chain/manifest.yaml`](/c:/Users/user/nova_arc/nova_arc/packs/cold_chain/manifest.yaml)
- Sample evidence: [`nova_arc/sample_data/cold_chain/evidence/manifest.json`](/c:/Users/user/nova_arc/nova_arc/sample_data/cold_chain/evidence/manifest.json)
- One-click-ish Windows launcher: [`scripts/start_coldchain_live.ps1`](/c:/Users/user/nova_arc/scripts/start_coldchain_live.ps1)

## Setup

1. Create a `.env` from `.env.example`.
2. Set `AWS_REGION` and `NOVA_MODEL_ID`.
3. Add either:
   - `AWS_BEARER_TOKEN_BEDROCK`, or
   - standard AWS credentials
4. Optionally set `SLACK_WEBHOOK_URL` for a real notification path.

## Run with uv

```bash
uv venv
uv pip install -r requirements.txt
uv run uvicorn nova_arc.backend.api:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
uv run streamlit run examples/streamlit_app.py
```

## Windows shortcut

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_coldchain_live.ps1
```

## Demo flow

1. Open the Streamlit command center.
2. Keep the default cold-chain transcript:
   - `Zone B temperature is above threshold. Batch VX-204 may be affected. Shipment SHP-884 is loading now.`
3. Click `Run Mission`.
4. Show:
   - evidence cards
   - Nova-generated strategy
   - action execution
   - backend state changes
   - verification
   - JSON and Markdown exports
5. Switch the pack to `Grid Ops Proof` for the universality pass.

## Runtime modes

- `demo`: deterministic planner with local retrieval and local admin workflow bridge
- `live_bedrock`: Bedrock Converse planner with local Sonic contract and local Nova Act workflow bridge
- `live_bridge`: Bedrock planner plus the live-labeled bridge contracts for Sonic and Nova Act

## Environment variables

See [`.env.example`](/c:/Users/user/nova_arc/.env.example) for the full list. The most important ones are:

- `AWS_REGION`
- `NOVA_MODEL_ID`
- `NOVA_SONIC_MODEL_ID`
- `NOVA_EMBEDDINGS_MODEL_ID`
- `AWS_BEARER_TOKEN_BEDROCK`
- `BACKEND_URL`
- `SLACK_WEBHOOK_URL`

## Tests

```bash
uv run pytest -q
```

## Notes

- The backend and Streamlit surface are split on purpose so tool actions produce durable visible state changes.
- The cold-chain planner is pack-scoped and sanitizes forbidden tools before execution.
- If Bedrock access is unavailable, the UI shows a targeted error card for IAM or model-access failures.
