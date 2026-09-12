import sqlite3

from app.persistencia.migrations.executor import Migration


# Cada migração tem um número de versão único e crescente.
# O executor usa esse número para saber se ela já foi aplicada.
VERSAO = 1


def aplicar(conexao: sqlite3.Connection) -> None:
    """Cria a tabela 'aluno' na base de dados."""
    # Executamos o SQL "cru" contra a conexão. Detalhes da tabela:
    #  - id INTEGER PRIMARY KEY            -> chave primária inteira e autoincrementable
    #  - nome TEXT NOT NULL                -> campo obrigatório (não aceita NULL)
    #  - CHECK(length(trim(nome)) > 0)     -> proíbe nome vazio ou composto só por espaços
    conexao.execute(
        """
        CREATE TABLE aluno (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL CHECK (length(trim(nome)) > 0)
        )
        """
    )


# Instância "registrável": o pacote migrations (__init__.py) a coleta
# para que o executor possa aplicá-la na ordem correta.
MIGRATION = Migration(
    versao=VERSAO,
    nome="criar_tabela_aluno",
    aplicar=aplicar,
)