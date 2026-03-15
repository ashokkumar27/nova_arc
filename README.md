# Nova A.R.C. Command Center — Close-to-Real Build

A pack-driven agentic harness for future command centers.

## What this build improves
- stronger Streamlit UI/UX
- stricter live Bedrock planner parsing
- `.env` loading through `python-dotenv`
- bridge health shown in the UI
- raw planner output available in debug mode
- tests for bridge parsing and harness flow

## Run with uv
```bash
uv venv
uv pip install -r requirements.txt
uv run streamlit run examples/streamlit_app.py
```

## Run with live Bedrock
Create a `.env` file from `.env.example` and set either:
- `AWS_BEARER_TOKEN_BEDROCK`, or
- standard `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`

Then switch the UI to `live_bedrock`.

## Test
```bash
uv run pytest -q
```

## Notes
- Bedrock live planner path is real-ready.
- Nova Act and Nova 2 Sonic stay behind bridge contracts for clean integration.
