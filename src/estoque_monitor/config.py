from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


def _csv_env(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def sqlalchemy_url(self) -> str:
        user = quote_plus(self.user)
        password = quote_plus(self.password)
        host = self.host
        database = quote_plus(self.database)
        return f"mysql+pymysql://{user}:{password}@{host}:{self.port}/{database}?charset=utf8mb4"


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str
    recipients: list[str]
    use_tls: bool


@dataclass(frozen=True)
class WhatsAppConfig:
    api_url: str
    token: str
    recipients: list[str]


@dataclass(frozen=True)
class AppConfig:
    database: DatabaseConfig
    smtp: SmtpConfig
    whatsapp: WhatsAppConfig
    alert_channels: list[str]
    alert_repeat_hours: int
    max_alert_items: int
    dry_run: bool
    powerbi_export_dir: Path


def load_config(env_file: str | Path = ".env") -> AppConfig:
    load_dotenv(env_file)

    return AppConfig(
        database=DatabaseConfig(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=_int_env("MYSQL_PORT", 3306),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "estoque_monitor"),
        ),
        smtp=SmtpConfig(
            host=os.getenv("SMTP_HOST", ""),
            port=_int_env("SMTP_PORT", 587),
            username=os.getenv("SMTP_USERNAME", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            sender=os.getenv("SMTP_FROM", os.getenv("SMTP_USERNAME", "")),
            recipients=_csv_env("SMTP_TO"),
            use_tls=_bool_env("SMTP_USE_TLS", True),
        ),
        whatsapp=WhatsAppConfig(
            api_url=os.getenv("WHATSAPP_API_URL", ""),
            token=os.getenv("WHATSAPP_TOKEN", ""),
            recipients=_csv_env("WHATSAPP_TO"),
        ),
        alert_channels=[channel.lower() for channel in _csv_env("ALERT_CHANNELS", "smtp")],
        alert_repeat_hours=_int_env("ALERT_REPEAT_HOURS", 24),
        max_alert_items=_int_env("MAX_ALERT_ITEMS", 25),
        dry_run=_bool_env("DRY_RUN", False),
        powerbi_export_dir=Path(os.getenv("POWERBI_EXPORT_DIR", "powerbi/data")),
    )
