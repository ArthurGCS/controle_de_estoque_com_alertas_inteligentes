from __future__ import annotations

import socket

from pymysql.err import OperationalError as PyMySQLOperationalError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError
from sqlalchemy.engine import Engine

from estoque_monitor.config import DatabaseConfig


class DatabaseConnectionError(RuntimeError):
    """Raised when the monitor cannot reach MySQL."""


def create_mysql_engine(config: DatabaseConfig) -> Engine:
    return create_engine(config.sqlalchemy_url, pool_pre_ping=True, future=True)


def check_connection(engine: Engine, config: DatabaseConfig) -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyOperationalError as exc:
        message = (
            "Nao foi possivel conectar ao MySQL.\n"
            f"Host configurado: {config.host}:{config.port}\n"
            f"Banco configurado: {config.database}\n\n"
            "Verifique se o MySQL esta instalado e iniciado, se a porta esta correta "
            "e se as credenciais no arquivo .env batem com o seu ambiente."
        )
        if _is_connection_refused(exc):
            message += (
                "\n\nNo Windows, procure um servico chamado MySQL ou MySQL80 e inicie-o, "
                "ou instale o MySQL Server se ele ainda nao existir."
            )
        raise DatabaseConnectionError(message) from exc


def _is_connection_refused(exc: SQLAlchemyOperationalError) -> bool:
    current: BaseException | None = exc
    while current is not None:
        if isinstance(current, ConnectionRefusedError):
            return True
        if isinstance(current, PyMySQLOperationalError):
            return any("10061" in str(arg) or "Connection refused" in str(arg) for arg in current.args)
        if isinstance(current, socket.error) and getattr(current, "winerror", None) == 10061:
            return True
        current = current.__cause__ or current.__context__
    return False
