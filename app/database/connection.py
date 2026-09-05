"""Conexão com o banco de dados SQLite.

O módulo é responsável apenas por abrir e devolver conexões prontas
para uso. A localização do arquivo do banco vem da camada de
configurações (``app.core.config``).
"""

import sqlite3

from app.core import config


def get_connection() -> sqlite3.Connection:
    """Abre e retorna uma conexão com o banco de dados SQLite.

    A conexão é configurada para:
      - retornar linhas como objetos ``sqlite3.Row`` (acesso por nome);
      - habilitar a restrição de chaves estrangeiras (``foreign_keys``),
        que será útil quando as tabelas de negócio forem criadas.

    O acesso ao banco pode ser feito com ``with get_connection() as conn``:
    o ``sqlite3.Connection`` funciona como um context manager que
    confirma a transação ao sair do bloco.
    """
    connection = sqlite3.connect(str(config.DATABASE_PATH))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection