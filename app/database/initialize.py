"""Inicialização do banco de dados SQLite.

Responsável por preparar o banco antes do uso: garante que o diretório
de dados exista e aplica as migrações de schema pendentes.

A versão atual do esquema fica registrada no próprio banco através de
``PRAGMA user_version``. Um banco já atualizado não é alterado — a
inicialização é segura para bancos existentes.
"""

from contextlib import closing

from app.core import config
from app.database.connection import get_connection
from app.database.migrations import MIGRACOES

# Versão mais recente do esquema, derivada das migrações disponíveis.
SCHEMA_VERSION = max(MIGRACOES)


def _versao_atual(connection) -> int:
    """Lê a versão do esquema registrada no banco."""
    linha = connection.execute("PRAGMA user_version").fetchone()
    return linha[0]


def _aplicar_migracoes_pendentes(connection, versao_atual: int) -> None:
    """Aplica, em ordem e de forma atômica, as migrações pendentes.

    Toda a sequência é executada dentro de uma única transação: se
    qualquer comando falhar, o banco permanece exatamente como estava.
    """
    connection.execute("BEGIN")
    try:
        for versao in range(versao_atual + 1, SCHEMA_VERSION + 1):
            for script in MIGRACOES[versao]:
                connection.execute(script)
            # PRAGMA não aceita parâmetros ligados; o valor é um número
            # constante do mapa de migrações, portanto seguro na string.
            connection.execute(f"PRAGMA user_version = {versao}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def initialize_database() -> None:
    """Prepara o banco de dados sem destruir dados existentes.

    Passos:
      1. Garante que o diretório ``data/`` exista.
      2. Abre a conexão — isso materializa o arquivo ``.db`` no disco.
      3. Se o banco estiver desatualizado, aplica apenas as migrações
         pendentes; bancos já na versão mais recente não são tocados.
    """
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    with closing(get_connection()) as connection:
        versao_atual = _versao_atual(connection)

        if versao_atual < SCHEMA_VERSION:
            _aplicar_migracoes_pendentes(connection, versao_atual)