import sqlite3

import pytest

from app.persistencia.migrations import MIGRATIONS
from app.persistencia.migrations.executor import executar_migrations


def criar_banco_migrado() -> sqlite3.Connection:
    conexao = sqlite3.connect(":memory:")
    executar_migrations(conexao, MIGRATIONS)
    return conexao


def test_aluno_possui_id_como_chave_primaria() -> None:
    conexao = criar_banco_migrado()
    try:
        colunas = conexao.execute("PRAGMA table_info(aluno)").fetchall()

        coluna_id = next(coluna for coluna in colunas if coluna[1] == "id")

        assert coluna_id[2] == "INTEGER"
        assert coluna_id[5] == 1
    finally:
        conexao.close()


def test_aluno_possui_nome_obrigatorio_no_banco() -> None:
    conexao = criar_banco_migrado()
    try:
        colunas = conexao.execute("PRAGMA table_info(aluno)").fetchall()

        coluna_nome = next(coluna for coluna in colunas if coluna[1] == "nome")

        assert coluna_nome[2] == "TEXT"
        assert coluna_nome[3] == 1
    finally:
        conexao.close()


def test_banco_permite_dois_alunos_com_mesmo_nome() -> None:
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
        assert ids[0] != ids[1]
    finally:
        conexao.close()


def test_banco_rejeita_identificador_duplicado() -> None:
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
    conexao = criar_banco_migrado()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute("INSERT INTO aluno (nome) VALUES (?)", ("   ",))
    finally:
        conexao.close()


def test_aluno_nao_possui_chaves_estrangeiras_antecipadas() -> None:
    conexao = criar_banco_migrado()
    try:
        chaves_estrangeiras = conexao.execute(
            "PRAGMA foreign_key_list(aluno)"
        ).fetchall()

        assert chaves_estrangeiras == []
    finally:
        conexao.close()


def test_aluno_nao_possui_indices_adicionais_sem_justificativa() -> None:
    conexao = criar_banco_migrado()
    try:
        indices = conexao.execute("PRAGMA index_list(aluno)").fetchall()

        assert indices == []
    finally:
        conexao.close()


def test_migrations_reexecutadas_nao_alteram_o_schema() -> None:
    conexao = sqlite3.connect(":memory:")
    try:
        assert executar_migrations(conexao, MIGRATIONS) == 1

        schema_antes = conexao.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE type IN ('table', 'index') ORDER BY type, name"
        ).fetchall()

        assert executar_migrations(conexao, MIGRATIONS) == 1

        schema_depois = conexao.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE type IN ('table', 'index') ORDER BY type, name"
        ).fetchall()

        assert schema_depois == schema_antes
        assert conexao.execute("PRAGMA user_version").fetchone()[0] == 1
    finally:
        conexao.close()


def test_schema_final_e_reproduzivel_a_partir_de_banco_vazio() -> None:
    conexao = sqlite3.connect(":memory:")
    try:
        assert conexao.execute("PRAGMA user_version").fetchone()[0] == 0

        versao_final = executar_migrations(conexao, MIGRATIONS)

        assert versao_final == 1
        assert conexao.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conexao.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'aluno'"
        ).fetchone() is not None
    finally:
        conexao.close()