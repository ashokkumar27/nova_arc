# Nova A.R.C. Seamless Harness

A pack-driven, agentic harness for future command center use cases.

This repo keeps one stable runtime and swaps capabilities through bridges:
- Bedrock Converse for planning/reasoning
- Nova 2 Sonic bridge for voice streaming
- Nova Multimodal Embeddings bridge for grounding/retrieval
- Nova Act bridge for browser automation

## Modes
- `demo`: deterministic local behavior for reliable demos
- `live_bedrock`: real Bedrock planning/reasoning with safe local fallbacks for the rest
- `live_bridge`: route planning, retrieval, voice, and browser execution through bridge interfaces

## Run
```bash
python -m pip install -r requirements.txt
streamlit run examples/streamlit_app.py
```

## Test
```bash
pytest -q
```

## Structure
- `nova_arc/core`: harness core
- `nova_arc/bridges`: stable bridge contracts and adapters
- `nova_arc/adapters`: perception, planning, and surface layers
- `nova_arc/tools`: bridge-backed and local tools
- `nova_arc/packs`: mission packs
- `tests`: automated tests

## Notes
- The bridge interfaces are designed to be swapped with your real backend services without changing the harness.
- The Bedrock bridge includes a real boto3 integration path when credentials are configured.
- Sonic and Nova Act are modeled as clean bridge contracts so your integration team can plug them in seamlessly.
