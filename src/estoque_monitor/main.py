from __future__ import annotations

import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.engine import Engine

from estoque_monitor.config import load_config
from estoque_monitor.db import DatabaseConnectionError, check_connection, create_mysql_engine
from estoque_monitor.inventory import build_alert_message, fetch_low_stock, filter_recent_alerts
from estoque_monitor.notifier import AlertResult, Notifier, has_successful_delivery


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "monitor.log"


def configure_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def record_alert_history(
    engine: Engine,
    product_ids: list[int],
    message: str,
    results: list[AlertResult],
) -> None:
    if not product_ids or not results:
        return

    insert_statement = text(
        """
        INSERT INTO alert_history
          (product_id, channel, recipient, status, message, error_message, sent_at)
        VALUES
          (:product_id, :channel, :recipient, :status, :message, :error_message, NOW())
        """
    )

    rows = [
        {
            "product_id": int(product_id),
            "channel": result.channel,
            "recipient": result.recipient,
            "status": result.status,
            "message": message,
            "error_message": result.error_message,
        }
        for product_id in product_ids
        for result in results
    ]

    with engine.begin() as connection:
        connection.execute(insert_statement, rows)


def run() -> int:
    configure_logging()
    config = load_config()
    engine = create_mysql_engine(config.database)
    try:
        check_connection(engine, config.database)
    except DatabaseConnectionError as exc:
        logging.error("%s", exc)
        return 2

    low_stock = fetch_low_stock(engine)
    logging.info("Produtos abaixo do minimo encontrados: %s", len(low_stock))

    pending_alerts = filter_recent_alerts(
        engine=engine,
        products=low_stock,
        repeat_hours=config.alert_repeat_hours,
    )
    logging.info("Produtos pendentes de alerta: %s", len(pending_alerts))

    if pending_alerts.empty:
        logging.info("Nenhum alerta novo para enviar.")
        return 0

    subject = f"Alerta de estoque baixo ({len(pending_alerts)} produto(s))"
    message = build_alert_message(pending_alerts, max_items=config.max_alert_items)
    if config.dry_run:
        logging.info("DRY_RUN ativo. Mensagem que seria enviada:\n%s", message)

    notifier = Notifier(config)
    results = notifier.send(subject=subject, body=message)

    for result in results:
        if result.status in {"sent", "dry_run"}:
            logging.info("Alerta %s para %s via %s", result.status, result.recipient, result.channel)
        else:
            logging.error(
                "Falha no alerta para %s via %s: %s",
                result.recipient,
                result.channel,
                result.error_message,
            )

    if has_successful_delivery(results):
        record_alert_history(
            engine=engine,
            product_ids=pending_alerts["product_id"].astype(int).tolist(),
            message=message,
            results=results,
        )
        logging.info("Historico de alertas atualizado.")
        return 0

    logging.error("Nenhum canal conseguiu entregar o alerta.")
    return 2


if __name__ == "__main__":
    raise SystemExit(run())
