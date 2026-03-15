import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova_arc.backend.client import BackendClient
from nova_arc.backend.service import CommandCenterBackend
from nova_arc.config import AppConfig


@pytest.fixture
def config() -> AppConfig:
    return AppConfig(
        runtime_mode="demo",
        aws_region="us-east-1",
        nova_model_id="us.amazon.nova-2-lite-v1:0",
        nova_sonic_model_id="amazon.nova-sonic-v1:0",
        nova_embeddings_model_id="amazon.nova-2-multimodal-embeddings-v1:0",
        bedrock_timeout_seconds=3600,
        backend_url="http://127.0.0.1:8000",
        backend_db_path="",
        admin_portal_base_url="http://127.0.0.1:8000/admin",
        notification_provider="slack",
        resend_api_key="",
        resend_from_email="",
        resend_to_email="",
        slack_webhook_url="",
        teams_webhook_url="",
        telegram_bot_token="",
        telegram_chat_id="",
        email_from="",
        email_to="",
        smtp_host="",
        smtp_port=587,
        smtp_username="",
        smtp_password="",
        enable_live_embeddings=False,
    )


@pytest.fixture
def backend_service(tmp_path) -> CommandCenterBackend:
    service = CommandCenterBackend(db_path=str(tmp_path / "nova_arc_test.db"))
    service.bootstrap(reset=True)
    return service


@pytest.fixture
def backend_client(backend_service) -> BackendClient:
    return BackendClient(service=backend_service)
