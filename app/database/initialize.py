"""Inicialização do banco de dados SQLite.

Responsável por preparar o banco antes do uso: garante que o diretório
de dados exista e registra a versão atual do esquema.

Nesta fase NÃO são criadas tabelas de negócio (alunos, exercícios,
habilidades etc.); elas serão adicionadas em tarefas futuras.
"""

from contextlib import closing

from app.core import config
from app.database.connection import get_connection

# Versão atual do esquema do banco de dados.
# Quando tabelas de negócio forem criadas nas próximas tarefas, esta
# constante deverá ser incrementada e adicionada a lógica de migração.
SCHEMA_VERSION = 1


def initialize_database() -> None:
    """Cria a estrutura base do banco de dados (sem tabelas de negócio).

    Passos:
      1. Garante que o diretório ``data/`` exista.
      2. Abre a conexão — isso já materializa o arquivo ``.db`` no disco.
      3. Registra a versão do esquema usando ``PRAGMA user_version``,
         um mecanismo nativo do SQLite para versionamento simples.
    """
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    with closing(get_connection()) as connection:
        # PRAGMA não aceita parâmetros ligados; o valor é numérico constante,
        # portanto seguro para uso em f-string.
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()