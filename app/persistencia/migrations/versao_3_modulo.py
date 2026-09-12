import sqlite3

from app.persistencia.migrations.executor import Migration


# Cada migração tem um número de versão único e crescente.
# O executor usa esse número para saber se ela já foi aplicada.
VERSAO = 3


def aplicar(conexao: sqlite3.Connection) -> None:
    """Cria a tabela 'modulo' na base de dados."""
    # Executamos o SQL "cru" contra a conexão. Detalhes da tabela:
    #  - id INTEGER PRIMARY KEY               -> chave primária inteira (sem AUTOINCREMENT explícito)
    #  - materia_id INTEGER NOT NULL          -> referência obrigatória à matéria dona
    #    FOREIGN KEY (materia_id) REFERENCES materia(id) -> sem ON DELETE CASCADE
    #  - nome TEXT NOT NULL CHECK(...)         -> obrigatório e não pode ser vazio ou só espaços
    #  - descricao TEXT                        -> texto livre (pode ser NULL)
    #  - ativa INTEGER NOT NULL DEFAULT 1      -> 1 = ativo / 0 = inativo (booleano padrão SQLite)
    #    CHECK (ativa IN (0, 1))               -> garante que só aceite os dois estados válidos
    #  - ordem INTEGER NOT NULL DEFAULT 0      -> posição do módulo (sem UNIQUE)
    #  - data_criacao TEXT NOT NULL            -> momento técnico de criação (ISO 8601 em UTC)
    #  - data_atualizacao TEXT NOT NULL        -> momento técnico da última atualização
    conexao.execute(
        """
        CREATE TABLE modulo (
            id INTEGER PRIMARY KEY,
            materia_id INTEGER NOT NULL,
            nome TEXT NOT NULL CHECK (length(trim(nome)) > 0),
            descricao TEXT,
            ativa INTEGER NOT NULL DEFAULT 1 CHECK (ativa IN (0, 1)),
            ordem INTEGER NOT NULL DEFAULT 0,
            data_criacao TEXT NOT NULL,
            data_atualizacao TEXT NOT NULL,
            FOREIGN KEY (materia_id) REFERENCES materia(id)
        )
        """
    )


# Instância "registrável": o pacote migrations (__init__.py) a coleta
# para que o executor possa aplicá-la na ordem correta.
MIGRATION = Migration(
    versao=VERSAO,
    nome="criar_tabela_modulo",
    aplicar=aplicar,
)
