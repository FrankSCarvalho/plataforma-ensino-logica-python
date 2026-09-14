import sqlite3

import pytest

from app.persistencia.migrations.executor import executar_migrations


def criar_conexao() -> sqlite3.Connection:
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_banco_com_migrations() -> sqlite3.Connection:
    conexao = criar_conexao()
    executar_migrations(conexao)
    return conexao


def test_tabela_exercicio_existe():
    conexao = criar_banco_com_migrations()

    resultado = conexao.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'exercicio'
        """
    ).fetchone()

    assert resultado is not None


def test_tabela_exercicio_possui_colunas_esperadas():
    conexao = criar_banco_com_migrations()

    colunas = conexao.execute(
        "PRAGMA table_info(exercicio)"
    ).fetchall()

    nomes = [coluna["name"] for coluna in colunas]

    assert nomes == [
        "id",
        "nivel_id",
        "enunciado",
        "tipo",
        "dados_exercicio",
        "ativa",
        "ordem",
        "data_criacao",
        "data_atualizacao",
    ]


def test_nivel_id_e_obrigatorio():
    conexao = criar_banco_com_migrations()

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute(
            """
            INSERT INTO exercicio (
                nivel_id,
                enunciado,
                tipo,
                dados_exercicio,
                data_criacao,
                data_atualizacao
            )
            VALUES (
                NULL,
                'Exercício de teste',
                'completar_lacunas',
                '{}',
                '2026-09-13T00:00:00',
                '2026-09-13T00:00:00'
            )
            """
        )


def test_enunciado_nao_aceita_vazio():
    conexao = criar_banco_com_migrations()

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute(
            """
            INSERT INTO exercicio (
                nivel_id,
                enunciado,
                tipo,
                dados_exercicio,
                data_criacao,
                data_atualizacao
            )
            VALUES (
                1,
                '   ',
                'completar_lacunas',
                '{}',
                '2026-09-13T00:00:00',
                '2026-09-13T00:00:00'
            )
            """
        )


def test_ativa_tem_valor_padrao_e_restringe_valores():
    conexao = criar_banco_com_migrations()

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute(
            """
            INSERT INTO exercicio (
                nivel_id,
                enunciado,
                tipo,
                dados_exercicio,
                data_criacao,
                data_atualizacao,
                ativa
            )
            VALUES (
                1,
                'Exercício de teste',
                'completar_lacunas',
                '{}',
                '2026-09-13T00:00:00',
                '2026-09-13T00:00:00',
                2
            )
            """
        )


def test_ordem_tem_valor_padrao_zero():
    conexao = criar_banco_com_migrations()

    conexao.execute(
        """
        INSERT INTO exercicio (
            nivel_id,
            enunciado,
            tipo,
            dados_exercicio,
            data_criacao,
            data_atualizacao
        )
        VALUES (
            1,
            'Exercício de teste',
            'completar_lacunas',
            '{}',
            '2026-09-13T00:00:00',
            '2026-09-13T00:00:00'
        )
        """
    )

    resultado = conexao.execute(
        "SELECT ordem, ativa FROM exercicio"
    ).fetchone()

    assert resultado["ordem"] == 0
    assert resultado["ativa"] == 1


def test_campos_de_data_sao_obrigatorios():
    conexao = criar_banco_com_migrations()

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute(
            """
            INSERT INTO exercicio (
                nivel_id,
                enunciado,
                tipo,
                dados_exercicio,
                data_criacao,
                data_atualizacao
            )
            VALUES (
                1,
                'Exercício de teste',
                'completar_lacunas',
                '{}',
                NULL,
                NULL
            )
            """
        )


def test_exercicio_pode_referenciar_nivel_existente_e_rejeita_nivel_inexistente():
    conexao = criar_banco_com_migrations()

    conexao.execute(
        """
        INSERT INTO materia (
            nome,
            descricao,
            ativa,
            data_criacao,
            data_atualizacao
        )
        VALUES (
            'Python',
            'Matéria de teste',
            1,
            '2026-09-13T00:00:00',
            '2026-09-13T00:00:00'
        )
        """
    )

    materia_id = conexao.execute(
        "SELECT id FROM materia"
    ).fetchone()["id"]

    conexao.execute(
        """
        INSERT INTO modulo (
            materia_id,
            nome,
            descricao,
            ativa,
            ordem,
            data_criacao,
            data_atualizacao
        )
        VALUES (
            ?,
            'Módulo de teste',
            'Módulo de teste',
            1,
            0,
            '2026-09-13T00:00:00',
            '2026-09-13T00:00:00'
        )
        """,
        (materia_id,),
    )

    modulo_id = conexao.execute(
        "SELECT id FROM modulo"
    ).fetchone()["id"]

    conexao.execute(
        """
        INSERT INTO habilidade (
            modulo_id,
            nome,
            descricao,
            ativa,
            ordem,
            data_criacao,
            data_atualizacao
        )
        VALUES (
            ?,
            'Habilidade de teste',
            'Habilidade de teste',
            1,
            0,
            '2026-09-13T00:00:00',
            '2026-09-13T00:00:00'
        )
        """,
        (modulo_id,),
    )

    habilidade_id = conexao.execute(
        "SELECT id FROM habilidade"
    ).fetchone()["id"]

    conexao.execute(
        """
        INSERT INTO nivel (
            habilidade_id,
            nome,
            descricao,
            ativa,
            ordem,
            data_criacao,
            data_atualizacao
        )
        VALUES (
            ?,
            'Nível de teste',
            'Nível de teste',
            1,
            0,
            '2026-09-13T00:00:00',
            '2026-09-13T00:00:00'
        )
        """,
        (habilidade_id,),
    )

    nivel_id = conexao.execute(
        "SELECT id FROM nivel"
    ).fetchone()["id"]

    conexao.execute(
        """
        INSERT INTO exercicio (
            nivel_id,
            enunciado,
            tipo,
            dados_exercicio,
            data_criacao,
            data_atualizacao
        )
        VALUES (
            ?,
            'Exercício de teste',
            'completar_lacunas',
            '{}',
            '2026-09-13T00:00:00',
            '2026-09-13T00:00:00'
        )
        """,
        (nivel_id,),
    )

    assert conexao.execute(
        "SELECT COUNT(*) FROM exercicio"
    ).fetchone()[0] == 1

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute(
            """
            INSERT INTO exercicio (
                nivel_id,
                enunciado,
                tipo,
                dados_exercicio,
                data_criacao,
                data_atualizacao
            )
            VALUES (
                999999,
                'Exercício inválido',
                'completar_lacunas',
                '{}',
                '2026-09-13T00:00:00',
                '2026-09-13T00:00:00'
            )
            """
        )