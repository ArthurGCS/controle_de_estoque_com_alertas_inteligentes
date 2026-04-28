from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable

import requests

from estoque_monitor.config import AppConfig


@dataclass(frozen=True)
class AlertResult:
    channel: str
    recipient: str
    status: str
    error_message: str | None = None


class Notifier:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def send(self, subject: str, body: str) -> list[AlertResult]:
        results: list[AlertResult] = []
        channels = list(dict.fromkeys(self.config.alert_channels))

        if self.config.dry_run:
            return [
                AlertResult(channel=channel, recipient="dry-run", status="dry_run")
                for channel in channels
            ]

        if "smtp" in channels:
            results.extend(self._send_smtp(subject, body))

        if "whatsapp" in channels:
            results.extend(self._send_whatsapp(body))

        if not results:
            results.append(
                AlertResult(
                    channel="none",
                    recipient="none",
                    status="failed",
                    error_message="No alert channel configured.",
                )
            )
        return results

    def _send_smtp(self, subject: str, body: str) -> list[AlertResult]:
        smtp = self.config.smtp
        if not smtp.host or not smtp.sender or not smtp.recipients:
            return [
                AlertResult(
                    channel="smtp",
                    recipient=",".join(smtp.recipients) or "none",
                    status="failed",
                    error_message="SMTP_HOST, SMTP_FROM and SMTP_TO are required.",
                )
            ]

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = smtp.sender
        message["To"] = ", ".join(smtp.recipients)
        message.set_content(body)

        try:
            with smtplib.SMTP(smtp.host, smtp.port, timeout=30) as server:
                if smtp.use_tls:
                    server.starttls()
                if smtp.username:
                    server.login(smtp.username, smtp.password)
                server.send_message(message)
        except Exception as exc:  # noqa: BLE001
            return [
                AlertResult(
                    channel="smtp",
                    recipient=recipient,
                    status="failed",
                    error_message=str(exc),
                )
                for recipient in smtp.recipients
            ]

        return [
            AlertResult(channel="smtp", recipient=recipient, status="sent")
            for recipient in smtp.recipients
        ]

    def _send_whatsapp(self, body: str) -> list[AlertResult]:
        whatsapp = self.config.whatsapp
        if not whatsapp.api_url or not whatsapp.token or not whatsapp.recipients:
            return [
                AlertResult(
                    channel="whatsapp",
                    recipient=",".join(whatsapp.recipients) or "none",
                    status="failed",
                    error_message="WHATSAPP_API_URL, WHATSAPP_TOKEN and WHATSAPP_TO are required.",
                )
            ]

        return [
            self._post_whatsapp_message(whatsapp.api_url, whatsapp.token, recipient, body)
            for recipient in whatsapp.recipients
        ]

    @staticmethod
    def _post_whatsapp_message(
        api_url: str,
        token: str,
        recipient: str,
        body: str,
    ) -> AlertResult:
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            return AlertResult(
                channel="whatsapp",
                recipient=recipient,
                status="failed",
                error_message=str(exc),
            )

        return AlertResult(channel="whatsapp", recipient=recipient, status="sent")


def has_successful_delivery(results: Iterable[AlertResult]) -> bool:
    return any(result.status in {"sent", "dry_run"} for result in results)
