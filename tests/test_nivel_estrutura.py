import sqlite3

import pytest

from app.persistencia.migrations import MIGRATIONS
from app.persistencia.migrations.executor import executar_migrations


def criar_banco_migrado() -> sqlite3.Connection:
    """Cria um banco em memória com todas as migrations aplicadas."""
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row
    executar_migrations(conexao, MIGRATIONS)
    return conexao


def criar_habilidade(conexao: sqlite3.Connection) -> int:
    """Insere a cadeia curricular mínima necessária para uma habilidade."""
    materia = conexao.execute(
        """
        INSERT INTO materia (nome, data_criacao, data_atualizacao)
        VALUES ('Lógica', '2024-01-01T10:00:00+00:00', '2024-01-01T10:00:00+00:00')
        """
    )
    modulo = conexao.execute(
        """
        INSERT INTO modulo (materia_id, nome, data_criacao, data_atualizacao)
        VALUES (?, 'Variáveis', '2024-01-02T10:00:00+00:00', '2024-01-02T10:00:00+00:00')
        """,
        (materia.lastrowid,),
    )
    habilidade = conexao.execute(
        """
        INSERT INTO habilidade (modulo_id, nome, data_criacao, data_atualizacao)
        VALUES (?, 'Identificar variáveis', '2024-01-03T10:00:00+00:00', '2024-01-03T10:00:00+00:00')
        """,
        (modulo.lastrowid,),
    )
    conexao.commit()
    return habilidade.lastrowid  # type: ignore


def test_migration_nivel_e_registrada_e_executada_na_ordem_correta() -> None:
    assert [migration.versao for migration in MIGRATIONS] == [1, 2, 3, 4, 5]

    conexao = criar_banco_migrado()
    try:
        assert conexao.execute("PRAGMA user_version").fetchone()[0] == 5
        assert conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'nivel'"
        ).fetchone() is not None
    finally:
        conexao.close()


def test_nivel_possui_exatamente_as_colunas_e_configuracoes_definidas() -> None:
    conexao = criar_banco_migrado()
    try:
        colunas = {
            coluna[1]: coluna for coluna in conexao.execute("PRAGMA table_info(nivel)")
        }

        assert set(colunas) == {
            "id",
            "habilidade_id",
            "nome",
            "descricao",
            "ativa",
            "ordem",
            "data_criacao",
            "data_atualizacao",
        }
        assert colunas["id"][2] == "INTEGER"
        assert colunas["id"][5] == 1
        assert colunas["habilidade_id"][2] == "INTEGER"
        assert colunas["habilidade_id"][3] == 1
        assert colunas["nome"][2] == "TEXT"
        assert colunas["nome"][3] == 1
        assert colunas["descricao"][2] == "TEXT"
        assert colunas["descricao"][3] == 1
        assert colunas["ativa"][2] == "INTEGER"
        assert colunas["ativa"][3] == 1
        assert colunas["ativa"][4] == "1"
        assert colunas["ordem"][2] == "INTEGER"
        assert colunas["ordem"][3] == 1
        assert colunas["ordem"][4] == "0"
        assert colunas["data_criacao"][2] == "TEXT"
        assert colunas["data_criacao"][3] == 1
        assert colunas["data_atualizacao"][2] == "TEXT"
        assert colunas["data_atualizacao"][3] == 1
    finally:
        conexao.close()


def test_nivel_aplica_restricoes_e_defaults_definidos() -> None:
    conexao = criar_banco_migrado()
    try:
        habilidade_id = criar_habilidade(conexao)

        cursor = conexao.execute(
            """
            INSERT INTO nivel (habilidade_id, nome, descricao, data_criacao, data_atualizacao)
            VALUES (?, 'Básico', 'Introdução', '2024-01-04T10:00:00+00:00', '2024-01-04T10:00:00+00:00')
            """,
            (habilidade_id,),
        )
        conexao.commit()
        nivel_id = cursor.lastrowid

        linha = conexao.execute(
            "SELECT ativa, ordem FROM nivel WHERE id = ?", (nivel_id,)
        ).fetchone()
        assert linha["ativa"] == 1
        assert linha["ordem"] == 0

        for nome in (None, "", "   "):
            with pytest.raises(sqlite3.IntegrityError):
                conexao.execute(
                    """
                    INSERT INTO nivel (habilidade_id, nome, descricao, data_criacao, data_atualizacao)
                    VALUES (?, ?, 'Introdução', '2024-01-04T10:00:00+00:00', '2024-01-04T10:00:00+00:00')
                    """,
                    (habilidade_id, nome),
                )

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO nivel (habilidade_id, nome, descricao, ativa, data_criacao, data_atualizacao)
                VALUES (?, 'Avançado', 'Aprofundamento', 2, '2024-01-04T10:00:00+00:00', '2024-01-04T10:00:00+00:00')
                """,
                (habilidade_id,),
            )

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO nivel (habilidade_id, nome, descricao, data_criacao, data_atualizacao)
                VALUES (?, 'Intermediário', NULL, '2024-01-04T10:00:00+00:00', '2024-01-04T10:00:00+00:00')
                """,
                (habilidade_id,),
            )
    finally:
        conexao.close()


def test_nivel_referencia_habilidade_sem_cascade_e_permite_ordem_repetida() -> None:
    conexao = criar_banco_migrado()
    try:
        habilidade_id = criar_habilidade(conexao)
        chaves = conexao.execute("PRAGMA foreign_key_list(nivel)").fetchall()

        assert len(chaves) == 1
        assert chaves[0][2] == "habilidade"
        assert chaves[0][3] == "habilidade_id"
        assert chaves[0][4] == "id"
        assert chaves[0][6].upper() == "NO ACTION"

        ddl = conexao.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'nivel'"
        ).fetchone()[0]
        assert "AUTOINCREMENT" not in ddl.upper()
        assert "ON DELETE CASCADE" not in ddl.upper()

        for nome in ("Básico", "Intermediário"):
            conexao.execute(
                """
                INSERT INTO nivel (habilidade_id, nome, descricao, ordem, data_criacao, data_atualizacao)
                VALUES (?, ?, 'Conteúdo', 1, '2024-01-04T10:00:00+00:00', '2024-01-04T10:00:00+00:00')
                """,
                (habilidade_id, nome),
            )
        conexao.commit()

        assert conexao.execute(
            "SELECT COUNT(*) FROM nivel WHERE habilidade_id = ? AND ordem = 1",
            (habilidade_id,),
        ).fetchone()[0] == 2
    finally:
        conexao.close()


def test_nivel_nao_cria_indices_triggers_ou_views_adicionais() -> None:
    conexao = criar_banco_migrado()
    try:
        assert conexao.execute("PRAGMA index_list(nivel)").fetchall() == []
        assert conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'nivel'"
        ).fetchall() == []
        assert conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view' AND tbl_name = 'nivel'"
        ).fetchall() == []
    finally:
        conexao.close()
