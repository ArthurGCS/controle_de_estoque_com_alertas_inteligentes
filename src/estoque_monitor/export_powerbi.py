from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from estoque_monitor.config import load_config
from estoque_monitor.db import DatabaseConnectionError, check_connection, create_mysql_engine


EXPORTS = {
    "inventory_status": "SELECT * FROM v_inventory_status",
    "stock_movements": "SELECT * FROM v_stock_movements_enriched",
    "alerts_history": "SELECT * FROM alert_history",
    "products": "SELECT * FROM products",
}


def export_table(name: str, query: str, output_dir: Path, engine) -> Path:
    data = pd.read_sql(query, engine)
    output_path = output_dir / f"{name}.csv"
    data.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def run() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = load_config()
    output_dir = config.powerbi_export_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    engine = create_mysql_engine(config.database)
    try:
        check_connection(engine, config.database)
    except DatabaseConnectionError as exc:
        logging.error("%s", exc)
        return 2

    for name, query in EXPORTS.items():
        path = export_table(name, query, output_dir, engine)
        logging.info("Exportado: %s", path)

    excel_path = output_dir / "dashboard_dataset.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for name, query in EXPORTS.items():
            data = pd.read_sql(query, engine)
            data.to_excel(writer, sheet_name=name[:31], index=False)
    logging.info("Exportado: %s", excel_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
