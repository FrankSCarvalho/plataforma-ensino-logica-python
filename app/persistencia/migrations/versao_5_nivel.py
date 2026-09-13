import sqlite3

from app.persistencia.migrations.executor import Migration


# Cada migration possui um número de versão único e crescente.
VERSAO = 5


def aplicar(conexao: sqlite3.Connection) -> None:
    """Cria a tabela 'nivel' na base de dados."""
    conexao.execute(
        """
        CREATE TABLE nivel (
            id INTEGER PRIMARY KEY,
            habilidade_id INTEGER NOT NULL,
            nome TEXT NOT NULL CHECK (length(trim(nome)) > 0),
            descricao TEXT NOT NULL,
            ativa INTEGER NOT NULL DEFAULT 1 CHECK (ativa IN (0, 1)),
            ordem INTEGER NOT NULL DEFAULT 0,
            data_criacao TEXT NOT NULL,
            data_atualizacao TEXT NOT NULL,
            FOREIGN KEY (habilidade_id) REFERENCES habilidade(id)
        )
        """
    )


MIGRATION = Migration(
    versao=VERSAO,
    nome="criar_tabela_nivel",
    aplicar=aplicar,
)
