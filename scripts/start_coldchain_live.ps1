$ErrorActionPreference = "Stop"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "uv run uvicorn nova_arc.backend.api:app --host 127.0.0.1 --port 8000"
Start-Sleep -Seconds 2
uv run streamlit run examples/streamlit_app.py
