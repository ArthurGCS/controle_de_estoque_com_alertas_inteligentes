from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from estoque_monitor.config import load_config
from estoque_monitor.db import DatabaseConnectionError, check_connection, create_mysql_engine


INVENTORY_QUERY = "SELECT * FROM v_inventory_status"
MOVEMENTS_QUERY = "SELECT * FROM v_stock_movements_enriched"
ALERTS_QUERY = "SELECT * FROM alert_history"

STATUS_ORDER = ["CRITICO", "BAIXO", "ATENCAO", "OK"]
LOW_STOCK_STATUS = {"CRITICO", "BAIXO"}


def main() -> None:
    st.set_page_config(
        page_title="Dashboard de Estoque",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_style()

    st.title("Dashboard de Estoque")

    config = load_config()
    source = st.sidebar.radio(
        "Fonte de dados",
        ["MySQL ao vivo", "CSV exportado"],
        help=(
            "Use MySQL para dados em tempo real ou CSV para visualizar "
            "o ultimo export."
        ),
    )

    try:
        inventory, movements, alerts = load_data(source, config.powerbi_export_dir)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        st.info("Use a fonte 'CSV exportado' se quiser abrir o dashboard sem o MySQL ativo.")
        st.stop()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.info("Rode `python -m estoque_monitor.export_powerbi` para gerar os CSVs.")
        st.stop()

    if inventory.empty:
        st.warning("Nenhum produto encontrado na fonte selecionada.")
        st.stop()

    inventory = prepare_inventory(inventory)
    movements = prepare_movements(movements)
    alerts = prepare_alerts(alerts)

    filtered_inventory = render_filters(inventory)
    render_kpis(filtered_inventory, alerts)
    render_charts(filtered_inventory, movements)
    render_tables(filtered_inventory, alerts)


@st.cache_data(ttl=60)
def load_data(source: str, export_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if source == "MySQL ao vivo":
        return load_from_mysql()
    return load_from_csv(export_dir)


def load_from_mysql() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    config = load_config()
    engine = create_mysql_engine(config.database)
    check_connection(engine, config.database)
    return (
        pd.read_sql(INVENTORY_QUERY, engine),
        pd.read_sql(MOVEMENTS_QUERY, engine),
        pd.read_sql(ALERTS_QUERY, engine),
    )


def load_from_csv(export_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    files = {
        "inventory_status": export_dir / "inventory_status.csv",
        "stock_movements": export_dir / "stock_movements.csv",
        "alerts_history": export_dir / "alerts_history.csv",
    }
    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Arquivos de dashboard nao encontrados: " + ", ".join(missing))

    return (
        pd.read_csv(files["inventory_status"]),
        pd.read_csv(files["stock_movements"]),
        pd.read_csv(files["alerts_history"]),
    )


def prepare_inventory(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    numeric_columns = [
        "current_stock",
        "minimum_stock",
        "target_stock",
        "suggested_reorder_qty",
        "unit_cost",
        "stock_value",
    ]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0)
    if "snapshot_at" in data.columns:
        data["snapshot_at"] = pd.to_datetime(data["snapshot_at"], errors="coerce")
    if "is_active" in data.columns:
        data["is_active"] = data["is_active"].astype(str).str.lower().isin({"1", "true", "yes"})
    return data


def prepare_movements(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    if data.empty:
        return data
    for column in ["quantity", "signed_quantity", "unit_cost"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0)
    if "movement_at" in data.columns:
        data["movement_at"] = pd.to_datetime(data["movement_at"], errors="coerce")
    return data


def prepare_alerts(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    if data.empty:
        return data
    if "sent_at" in data.columns:
        data["sent_at"] = pd.to_datetime(data["sent_at"], errors="coerce")
    return data


def render_filters(inventory: pd.DataFrame) -> pd.DataFrame:
    data = inventory.copy()

    categories = sorted(data["category_name"].dropna().unique().tolist())
    suppliers = sorted(data["supplier_name"].dropna().unique().tolist())
    statuses = [status for status in STATUS_ORDER if status in set(data["stock_status"].dropna())]

    selected_categories = st.sidebar.multiselect("Categorias", categories, default=categories)
    selected_suppliers = st.sidebar.multiselect("Fornecedores", suppliers, default=suppliers)
    selected_statuses = st.sidebar.multiselect("Status", statuses, default=statuses)

    if selected_categories:
        data = data[data["category_name"].isin(selected_categories)]
    if selected_suppliers:
        data = data[data["supplier_name"].isin(selected_suppliers)]
    if selected_statuses:
        data = data[data["stock_status"].isin(selected_statuses)]

    return data


def render_kpis(inventory: pd.DataFrame, alerts: pd.DataFrame) -> None:
    active_products = int(inventory.get("is_active", pd.Series([True] * len(inventory))).sum())
    low_stock = int(inventory["stock_status"].isin(LOW_STOCK_STATUS).sum())
    stock_value = float(inventory["stock_value"].sum())
    reorder_qty = float(inventory["suggested_reorder_qty"].sum())
    sent_alerts = int(alerts["status"].eq("sent").sum()) if "status" in alerts.columns else 0

    cols = st.columns(5)
    cols[0].metric("Produtos ativos", f"{active_products}")
    cols[1].metric("Baixo estoque", f"{low_stock}")
    cols[2].metric("Valor em estoque", format_currency(stock_value))
    cols[3].metric("Qtd. a repor", format_number(reorder_qty))
    cols[4].metric("Alertas enviados", f"{sent_alerts}")


def render_charts(inventory: pd.DataFrame, movements: pd.DataFrame) -> None:
    left, right = st.columns([1, 1])

    status_counts = (
        inventory["stock_status"]
        .value_counts()
        .reindex(
            [
                status
                for status in STATUS_ORDER
                if status in inventory["stock_status"].unique()
            ]
        )
        .dropna()
        .astype(int)
        .rename_axis("status")
        .reset_index(name="produtos")
    )
    left.subheader("Produtos por status")
    left.bar_chart(
        status_counts,
        x="status",
        y="produtos",
        color="#2f6f73",
        use_container_width=True,
    )

    reorder = (
        inventory.sort_values("suggested_reorder_qty", ascending=False)
        .head(10)[["product_name", "suggested_reorder_qty"]]
        .rename(columns={"product_name": "produto", "suggested_reorder_qty": "repor"})
    )
    right.subheader("Reposicao sugerida")
    right.bar_chart(
        reorder,
        x="produto",
        y="repor",
        color="#b85c38",
        use_container_width=True,
    )

    st.subheader("Movimentacoes por dia")
    if movements.empty or "movement_at" not in movements.columns:
        st.caption("Sem movimentacoes para exibir.")
        return

    daily = (
        movements.dropna(subset=["movement_at"])
        .assign(day=lambda frame: frame["movement_at"].dt.date)
        .pivot_table(
            index="day",
            columns="movement_type",
            values="signed_quantity",
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
    )
    st.line_chart(daily, use_container_width=True)


def render_tables(inventory: pd.DataFrame, alerts: pd.DataFrame) -> None:
    low_stock = inventory[inventory["stock_status"].isin(LOW_STOCK_STATUS)].copy()
    low_stock = low_stock.sort_values(
        ["stock_status", "suggested_reorder_qty"],
        ascending=[True, False],
    )

    st.subheader("Produtos que precisam de reposicao")
    st.dataframe(
        low_stock[
            [
                "sku",
                "product_name",
                "category_name",
                "supplier_name",
                "current_stock",
                "minimum_stock",
                "suggested_reorder_qty",
                "stock_status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    tabs = st.tabs(["Estoque completo", "Historico de alertas"])
    with tabs[0]:
        st.dataframe(inventory, use_container_width=True, hide_index=True)
    with tabs[1]:
        if alerts.empty:
            st.caption("Nenhum alerta registrado.")
        else:
            st.dataframe(
                alerts.sort_values("sent_at", ascending=False),
                use_container_width=True,
                hide_index=True,
            )


def format_currency(value: float) -> str:
    formatted = f"R$ {value:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value: float) -> str:
    if value.is_integer():
        return f"{int(value)}"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _apply_style() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        [data-testid="stMetric"] {
            border: 1px solid #d9e1e2;
            border-radius: 6px;
            padding: 14px 16px;
            background: #ffffff;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.45rem;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
