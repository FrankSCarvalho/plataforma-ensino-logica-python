"""Testes da estrutura do schema do banco de dados."""

from app.database.connection import get_connection
from app.database.initialize import SCHEMA_VERSION

TABELAS_ESPERADAS = {
    "alunos",
    "modulos",
    "habilidades",
    "niveis",
    "exercicios",
    "sessoes_estudo",
    "tentativas",
    "progresso_aluno",
}

# Relacionamentos que o schema deve declarar (tabela -> tabelas referenciadas).
RELACIONAMENTOS_ESPERADOS = {
    "habilidades": ["modulos"],
    "niveis": ["habilidades"],
    "exercicios": ["niveis"],
    "sessoes_estudo": ["alunos"],
    "tentativas": ["sessoes_estudo", "alunos", "exercicios"],
    "progresso_aluno": ["alunos", "habilidades", "niveis"],
}


def _nomes_das_tabelas() -> set[str]:
    """Retorna os nomes das tabelas existentes no banco ativo."""
    with get_connection() as connection:
        linhas = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    return {linha["name"] for linha in linhas}


def test_criacao_das_tabelas(banco_de_teste):
    tabelas = _nomes_das_tabelas()
    assert TABELAS_ESPERADAS.issubset(tabelas)


def test_chaves_estrangeiras_ativas(banco_de_teste):
    with get_connection() as connection:
        valor = connection.execute("PRAGMA foreign_keys").fetchone()[0]
    assert valor == 1


def test_relacionamentos_declarados_no_schema(banco_de_teste):
    for tabela, referencias in RELACIONAMENTOS_ESPERADOS.items():
        with get_connection() as connection:
            linhas = connection.execute(
                f"PRAGMA foreign_key_list({tabela})"
            ).fetchall()
        referenciadas = {linha["table"] for linha in linhas}
        assert set(referencias).issubset(referenciadas), (
            f"A tabela {tabela} deveria referenciar {sorted(referencias)}; "
            f"referencia apenas {sorted(referenciadas)}"
        )


def test_versao_do_schema_apos_inicializacao(banco_de_teste):
    with get_connection() as connection:
        versao = connection.execute("PRAGMA user_version").fetchone()[0]
    assert versao == SCHEMA_VERSION