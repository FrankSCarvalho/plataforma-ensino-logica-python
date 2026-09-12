import sqlite3

import pytest

from app.persistencia.migrations import MIGRATIONS
from app.persistencia.migrations.executor import executar_migrations


def criar_banco_migrado() -> sqlite3.Connection:
    """Cria um banco em memória com todas as migrations já aplicadas."""
    conexao = sqlite3.connect(":memory:")
    executar_migrations(conexao, MIGRATIONS)
    return conexao


def test_aluno_possui_id_como_chave_primaria() -> None:
    # PRAGMA table_info(aluno) devolve a definição das colunas da tabela.
    conexao = criar_banco_migrado()
    try:
        colunas = conexao.execute("PRAGMA table_info(aluno)").fetchall()

        coluna_id = next(coluna for coluna in colunas if coluna[1] == "id")

        assert coluna_id[2] == "INTEGER"  # tipo da coluna
        assert coluna_id[5] == 1  # flag 'pk' = 1  -> é chave primária
    finally:
        conexao.close()


def test_aluno_possui_nome_obrigatorio_no_banco() -> None:
    conexao = criar_banco_migrado()
    try:
        colunas = conexao.execute("PRAGMA table_info(aluno)").fetchall()

        coluna_nome = next(coluna for coluna in colunas if coluna[1] == "nome")

        assert coluna_nome[2] == "TEXT"  # tipo da coluna
        assert coluna_nome[3] == 1  # flag 'notnull' = 1 -> não aceita NULL
    finally:
        conexao.close()


def test_banco_permite_dois_alunos_com_mesmo_nome() -> None:
    # Não existe UNIQUE na coluna nome: inserir dois registros iguais
    # deve ser permitido, cada um com id próprio.
    conexao = criar_banco_migrado()
    try:
        conexao.execute("INSERT INTO aluno (nome) VALUES (?)", ("Ana",))
        conexao.execute("INSERT INTO aluno (nome) VALUES (?)", ("Ana",))
        conexao.commit()

        ids = [
            linha[0]
            for linha in conexao.execute(
                "SELECT id FROM aluno WHERE nome = ? ORDER BY id",
                ("Ana",),
            ).fetchall()
        ]

        assert len(ids) == 2
        assert ids[0] != ids[1]  # ids distintos mesmo com nomes repetidos
    finally:
        conexao.close()


def test_banco_rejeita_identificador_duplicado() -> None:
    # A chave primaria é única: inserir um id já existente viola essa regra.
    conexao = criar_banco_migrado()
    try:
        conexao.execute(
            "INSERT INTO aluno (id, nome) VALUES (?, ?)",
            (1, "Ana"),
        )
        conexao.commit()

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                "INSERT INTO aluno (id, nome) VALUES (?, ?)",
                (1, "Bruno"),
            )
    finally:
        conexao.close()


def test_banco_rejeita_nome_nulo() -> None:
    # A restrição NOT NULL na coluna nome bloqueia a inserção de NULL.
    conexao = criar_banco_migrado()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute("INSERT INTO aluno (nome) VALUES (NULL)")
    finally:
        conexao.close()


def test_banco_rejeita_nome_vazio() -> None:
    conexao = criar_banco_migrado()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute("INSERT INTO aluno (nome) VALUES (?)", ("",))
    finally:
        conexao.close()


def test_banco_rejeita_nome_formado_apenas_por_espacos() -> None:
    # A CHECK com trim() impede que "   " (só espaços) seja considerado válido.
    conexao = criar_banco_migrado()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute("INSERT INTO aluno (nome) VALUES (?)", ("   ",))
    finally:
        conexao.close()


def test_aluno_nao_possui_chaves_estrangeiras_antecipadas() -> None:
    # Garantia estrutural: a tabela 'aluno' ainda não deve ter FK (foreign keys),
    # porque no estado atual do modelo não há relações com outras tabelas.
    conexao = criar_banco_migrado()
    try:
        chaves_estrangeiras = conexao.execute(
            "PRAGMA foreign_key_list(aluno)"
        ).fetchall()

        assert chaves_estrangeiras == []
    finally:
        conexao.close()


def test_aluno_nao_possui_indices_adicionais_sem_justificativa() -> None:
    # Evita índices "órfãos" criados por engano; índices extra só devem
    # existir quando haja uma justificativa real de performance.
    conexao = criar_banco_migrado()
    try:
        indices = conexao.execute("PRAGMA index_list(aluno)").fetchall()

        assert indices == []
    finally:
        conexao.close()


def test_migrations_reexecutadas_nao_alteram_o_schema() -> None:
    # Idempotência estrutural: rodar migrations de novo sobre o mesmo banco
    # não pode alterar o conjunto de tabelas/índices nem duplicar nada.
    conexao = sqlite3.connect(":memory:")
    try:
        # Primeira execução em banco vazio: aplica TODAS as migrations
        # registradas (v1 aluno + v2 materia + v3 modulo) e devolve a versão 3.
        assert executar_migrations(conexao, MIGRATIONS) == 3

        schema_antes = conexao.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE type IN ('table', 'index') ORDER BY type, name"
        ).fetchall()

        assert executar_migrations(conexao, MIGRATIONS) == 3

        schema_depois = conexao.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE type IN ('table', 'index') ORDER BY type, name"
        ).fetchall()

        assert schema_depois == schema_antes  # nenhuma alteração na 2ª execução
        assert conexao.execute("PRAGMA user_version").fetchone()[0] == 3
    finally:
        conexao.close()


def test_schema_final_e_reproduzivel_a_partir_de_banco_vazio() -> None:
    # Desde um banco zerado (versão 0), as migrations devem construir o schema
    # final completo de forma determinística e reproduzível.
    conexao = sqlite3.connect(":memory:")
    try:
        assert conexao.execute("PRAGMA user_version").fetchone()[0] == 0

        versao_final = executar_migrations(conexao, MIGRATIONS)

        assert versao_final == 3
        assert conexao.execute("PRAGMA user_version").fetchone()[0] == 3
        assert conexao.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'aluno'"
        ).fetchone() is not None
    finally:
        conexao.close()
