import sqlite3

from app.persistencia.migrations.executor import Migration

VERSAO = 6

def aplicar(conexao: sqlite3.Connection) -> None:
    conexao.execute(
        """
        CREATE TABLE exercicio (
            id INTEGER PRIMARY KEY,
            nivel_id INTEGER NOT NULL,
            enunciado TEXT NOT NULL CHECK (length(trim(enunciado)) > 0),
            tipo TEXT NOT NULL,
            dados_exercicio TEXT NOT NULL,
            ativa INTEGER NOT NULL DEFAULT 1 CHECK (ativa IN (0, 1)),
            ordem INTEGER NOT NULL DEFAULT 0,
            data_criacao TEXT NOT NULL,
            data_atualizacao TEXT NOT NULL,
            FOREIGN KEY (nivel_id) REFERENCES nivel(id)
        )
        """
    )

MIGRATION = Migration(
    versao=VERSAO,
    nome="criar_tabela_exercicio",
    aplicar=aplicar,
)