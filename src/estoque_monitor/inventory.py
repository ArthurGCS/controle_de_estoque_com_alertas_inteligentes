from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


LOW_STOCK_QUERY = text(
    """
    SELECT
      product_id,
      sku,
      product_name,
      category_name,
      supplier_name,
      unit,
      current_stock,
      minimum_stock,
      target_stock,
      suggested_reorder_qty,
      unit_cost,
      stock_value,
      stock_status,
      snapshot_at
    FROM v_inventory_status
    WHERE is_active = 1
      AND current_stock <= minimum_stock
    ORDER BY
      CASE stock_status
        WHEN 'CRITICO' THEN 1
        WHEN 'BAIXO' THEN 2
        ELSE 3
      END,
      suggested_reorder_qty DESC,
      product_name ASC
    """
)

LAST_ALERT_QUERY = text(
    """
    SELECT
      product_id,
      MAX(sent_at) AS last_sent_at
    FROM alert_history
    WHERE status = 'sent'
    GROUP BY product_id
    """
)


def fetch_low_stock(engine: Engine) -> pd.DataFrame:
    return pd.read_sql(LOW_STOCK_QUERY, engine)


def filter_recent_alerts(
    engine: Engine,
    products: pd.DataFrame,
    repeat_hours: int,
    now: datetime | None = None,
) -> pd.DataFrame:
    if products.empty:
        return products.copy()

    last_alerts = pd.read_sql(LAST_ALERT_QUERY, engine)
    if last_alerts.empty:
        return products.copy()

    current_time = now or datetime.now()
    cutoff = current_time - timedelta(hours=repeat_hours)
    last_alerts["last_sent_at"] = pd.to_datetime(last_alerts["last_sent_at"])

    merged = products.merge(last_alerts, on="product_id", how="left")
    pending = merged[
        merged["last_sent_at"].isna() | (merged["last_sent_at"] < pd.Timestamp(cutoff))
    ].copy()
    return pending.drop(columns=["last_sent_at"])


def build_alert_message(products: pd.DataFrame, max_items: int = 25) -> str:
    if products.empty:
        return "Nenhum produto com estoque baixo."

    limited = products.head(max_items)
    lines = [
        f"Alerta de estoque baixo: {len(products)} produto(s) precisam de atencao.",
        "",
        "SKU | Produto | Atual | Minimo | Repor | Status",
        "--- | --- | ---: | ---: | ---: | ---",
    ]

    for row in limited.itertuples(index=False):
        lines.append(
            (
                f"{row.sku} | {row.product_name} | "
                f"{row.current_stock:g} {row.unit} | "
                f"{row.minimum_stock:g} {row.unit} | "
                f"{row.suggested_reorder_qty:g} {row.unit} | "
                f"{row.stock_status}"
            )
        )

    remaining = len(products) - len(limited)
    if remaining > 0:
        lines.extend(["", f"... e mais {remaining} produto(s)."])

    lines.extend(["", "Acesse o dashboard Power BI para analisar categorias e fornecedores."])
    return "\n".join(lines)
