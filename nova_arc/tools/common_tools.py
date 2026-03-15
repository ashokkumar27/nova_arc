from __future__ import annotations

from email.message import EmailMessage
import json
import smtplib
from urllib import request as urllib_request

from nova_arc.core.mission_profile import ToolExecutionResult

from .registry import RegisteredTool


def _post_json(url: str, payload: dict) -> None:
    req = urllib_request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(req):
        return None


def _dispatch_notification(config, provider: str, channel: str, message: str) -> dict:
    provider = (provider or config.notification_provider or "slack").lower()

    if provider == "slack" and config.slack_webhook_url:
        _post_json(config.slack_webhook_url, {"text": f"[{channel}] {message}"})
        return {"provider": "slack", "external_status": "sent"}

    if provider == "teams" and config.teams_webhook_url:
        _post_json(config.teams_webhook_url, {"text": f"[{channel}] {message}"})
        return {"provider": "teams", "external_status": "sent"}

    if provider == "telegram" and config.telegram_bot_token and config.telegram_chat_id:
        telegram_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
        _post_json(telegram_url, {"chat_id": config.telegram_chat_id, "text": f"[{channel}] {message}"})
        return {"provider": "telegram", "external_status": "sent"}

    if provider == "email" and config.smtp_host and config.email_from and config.email_to:
        email_message = EmailMessage()
        email_message["Subject"] = f"Nova A.R.C. Alert | {channel}"
        email_message["From"] = config.email_from
        email_message["To"] = config.email_to
        email_message.set_content(message)
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            if config.smtp_username:
                server.starttls()
                server.login(config.smtp_username, config.smtp_password)
            server.send_message(email_message)
        return {"provider": "email", "external_status": "sent"}

    return {"provider": provider or "local_audit", "external_status": "stored_locally"}


def notify_team_tool(backend_client, config, pack_id: str):
    def _exec(args):
        missing = [key for key in ("channel", "message") if not args.get(key)]
        if missing:
            return ToolExecutionResult(
                tool="notify_team",
                args=args,
                success=False,
                output=f"Missing required args for notify_team: {', '.join(missing)}",
                category="notification",
            )

        provider = args.get("provider") or config.notification_provider
        try:
            delivery = _dispatch_notification(config, provider, args["channel"], args["message"])
            backend_result = backend_client.record_notification(
                pack_id=pack_id,
                channel=args["channel"],
                provider=delivery["provider"],
                message=args["message"],
                incident_id=args.get("incident_id"),
                external_status=delivery["external_status"],
            )
            return ToolExecutionResult(
                tool="notify_team",
                args=args,
                success=True,
                output=f"Notification processed via {delivery['provider']} with status {delivery['external_status']}.",
                category="notification",
                details={**delivery, **backend_result},
            )
        except Exception as exc:
            return ToolExecutionResult(
                tool="notify_team",
                args=args,
                success=False,
                output=f"Notification failed: {type(exc).__name__}: {exc}",
                category="notification",
            )

    return RegisteredTool(
        "notify_team",
        "notification",
        "Notify the incident response team through a configured webhook or email path. Required args: channel, message.",
        _exec,
        input_schema={
            "type": "object",
            "properties": {
                "channel": {"type": "string"},
                "message": {"type": "string"},
                "provider": {"type": "string"},
                "incident_id": {"type": "string"},
            },
            "required": ["channel", "message"],
            "additionalProperties": False,
        },
    )
