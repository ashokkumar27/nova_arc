from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
SAMPLE_DATA_DIR = PACKAGE_DIR / "sample_data"
DEFAULT_DB_PATH = REPO_ROOT / "data" / "nova_arc.db"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_or_default(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value


def load_environment() -> None:
    load_dotenv(REPO_ROOT / ".env", override=False)


@dataclass(frozen=True)
class AppConfig:
    runtime_mode: str
    aws_region: str
    nova_model_id: str
    nova_sonic_model_id: str
    nova_embeddings_model_id: str
    bedrock_timeout_seconds: int
    backend_url: str
    backend_db_path: str
    admin_portal_base_url: str
    notification_provider: str
    resend_api_key: str
    resend_from_email: str
    resend_to_email: str
    slack_webhook_url: str
    teams_webhook_url: str
    telegram_bot_token: str
    telegram_chat_id: str
    email_from: str
    email_to: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    enable_live_embeddings: bool

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_environment()
        return cls(
            runtime_mode=_env_or_default("NOVA_RUNTIME_MODE", "demo"),
            aws_region=_env_or_default("AWS_REGION", "us-east-1"),
            nova_model_id=_env_or_default("NOVA_MODEL_ID", "us.amazon.nova-2-lite-v1:0"),
            nova_sonic_model_id=_env_or_default("NOVA_SONIC_MODEL_ID", "amazon.nova-sonic-v1:0"),
            nova_embeddings_model_id=_env_or_default("NOVA_EMBEDDINGS_MODEL_ID", "amazon.nova-2-multimodal-embeddings-v1:0"),
            bedrock_timeout_seconds=int(os.getenv("NOVA_BEDROCK_TIMEOUT_SECONDS", "3600")),
            backend_url=_env_or_default("BACKEND_URL", "http://127.0.0.1:8000"),
            backend_db_path=_env_or_default("BACKEND_DB_PATH", str(DEFAULT_DB_PATH)),
            admin_portal_base_url=_env_or_default("ADMIN_PORTAL_BASE_URL", "http://127.0.0.1:8000/admin"),
            notification_provider=_env_or_default("NOTIFICATION_PROVIDER", "slack"),
            resend_api_key=os.getenv("RESEND_API_KEY", ""),
            resend_from_email=os.getenv("RESEND_FROM_EMAIL", os.getenv("EMAIL_FROM", "")),
            resend_to_email=os.getenv("RESEND_TO_EMAIL", os.getenv("EMAIL_TO", "")),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
            teams_webhook_url=os.getenv("TEAMS_WEBHOOK_URL", ""),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            email_from=os.getenv("EMAIL_FROM", ""),
            email_to=os.getenv("EMAIL_TO", ""),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            enable_live_embeddings=_as_bool(os.getenv("ENABLE_LIVE_EMBEDDINGS"), default=False),
        )
