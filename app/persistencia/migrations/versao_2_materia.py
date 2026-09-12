import sqlite3

from app.persistencia.migrations.executor import Migration


# Cada migração tem um número de versão único e crescente.
# O executor usa esse número para saber se ela já foi aplicada.
VERSAO = 2


def aplicar(conexao: sqlite3.Connection) -> None:
    """Cria a tabela 'materia' na base de dados."""
    # Executamos o SQL "cru" contra a conexão. Detalhes da tabela:
    #  - id INTEGER PRIMARY KEY              -> chave primária inteira e autoincrementável
    #                                          (mesma estratégia usada em 'aluno')
    #  - nome TEXT NOT NULL CHECK(...)        -> obrigatório e não pode ser vazio ou só espaços
    #  - descricao TEXT                       -> texto livre (explicação do que a matéria abrange)
    #  - ativa INTEGER NOT NULL DEFAULT 1     -> 1 = ativa / 0 = inativa (booleano padrão SQLite)
    #    CHECK (ativa IN (0, 1))              -> garante que só aceite os dois estados válidos
    #  - ordem INTEGER NOT NULL DEFAULT 0     -> posição da matéria (não é derivada do id)
    #  - data_criacao TEXT NOT NULL           -> momento técnico de criação (ISO 8601 em UTC)
    #  - data_atualizacao TEXT NOT NULL       -> momento técnico da última atualização
    conexao.execute(
        """
        CREATE TABLE materia (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL CHECK (length(trim(nome)) > 0),
            descricao TEXT,
            ativa INTEGER NOT NULL DEFAULT 1 CHECK (ativa IN (0, 1)),
            ordem INTEGER NOT NULL DEFAULT 0,
            data_criacao TEXT NOT NULL,
            data_atualizacao TEXT NOT NULL
        )
        """
    )


# Instância "registrável": o pacote migrations (__init__.py) a coleta
# para que o executor possa aplicá-la na ordem correta.
MIGRATION = Migration(
    versao=VERSAO,
    nome="criar_tabela_materia",
    aplicar=aplicar,
)