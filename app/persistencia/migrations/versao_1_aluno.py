import sqlite3

from app.persistencia.migrations.executor import Migration


VERSAO = 1


def aplicar(conexao: sqlite3.Connection) -> None:
    conexao.execute(
        """
        CREATE TABLE aluno (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL CHECK (length(trim(nome)) > 0)
        )
        """
    )


MIGRATION = Migration(
    versao=VERSAO,
    nome="criar_tabela_aluno",
    aplicar=aplicar,
)