import sqlite3

import pytest

from app.persistencia.migrations.executor import (
    Migration,
    executar_migrations,
    obter_versao_schema,
)


def criar_conexao() -> sqlite3.Connection:
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row
    return conexao


def test_banco_novo_inicia_na_versao_zero():
    with criar_conexao() as conexao:
        assert obter_versao_schema(conexao) == 0


def test_aplica_primeira_migration_e_atualiza_versao():
    def aplicar(conexao: sqlite3.Connection) -> None:
        conexao.execute("CREATE TABLE teste (id INTEGER PRIMARY KEY)")

    migration = Migration(1, "primeira", aplicar)

    with criar_conexao() as conexao:
        versao = executar_migrations(conexao, [migration])

        assert versao == 1
        assert obter_versao_schema(conexao) == 1
        assert conexao.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'teste'"
        ).fetchone() is not None


def test_multiplas_migrations_sao_aplicadas_em_ordem():
    ordem = []

    def aplicar_2(conexao: sqlite3.Connection) -> None:
        ordem.append(2)
        conexao.execute("CREATE TABLE segundo (id INTEGER PRIMARY KEY)")

    def aplicar_1(conexao: sqlite3.Connection) -> None:
        ordem.append(1)
        conexao.execute("CREATE TABLE primeiro (id INTEGER PRIMARY KEY)")

    migrations = [
        Migration(2, "segunda", aplicar_2),
        Migration(1, "primeira", aplicar_1),
    ]

    with criar_conexao() as conexao:
        versao = executar_migrations(conexao, migrations)

        assert ordem == [1, 2]
        assert versao == 2


def test_banco_ja_atualizado_nao_reexecuta_migrations():
    quantidade_execucoes = 0

    def aplicar(conexao: sqlite3.Connection) -> None:
        nonlocal quantidade_execucoes
        quantidade_execucoes += 1
        conexao.execute("CREATE TABLE teste (id INTEGER PRIMARY KEY)")

    migration = Migration(1, "primeira", aplicar)

    with criar_conexao() as conexao:
        assert executar_migrations(conexao, [migration]) == 1
        assert executar_migrations(conexao, [migration]) == 1
        assert quantidade_execucoes == 1


def test_banco_parcialmente_atualizado_recebe_somente_pendentes():
    ordem = []

    def aplicar_1(conexao: sqlite3.Connection) -> None:
        ordem.append(1)
        conexao.execute("CREATE TABLE primeiro (id INTEGER PRIMARY KEY)")

    def aplicar_2(conexao: sqlite3.Connection) -> None:
        ordem.append(2)
        conexao.execute("CREATE TABLE segundo (id INTEGER PRIMARY KEY)")

    migration_1 = Migration(1, "primeira", aplicar_1)
    migration_2 = Migration(2, "segunda", aplicar_2)

    with criar_conexao() as conexao:
        assert executar_migrations(conexao, [migration_1]) == 1
        assert executar_migrations(conexao, [migration_1, migration_2]) == 2
        assert ordem == [1, 2]


def test_falha_em_migration_faz_rollback_e_preserva_versao_anterior():
    def aplicar_1(conexao: sqlite3.Connection) -> None:
        conexao.execute("CREATE TABLE primeiro (id INTEGER PRIMARY KEY)")

    def aplicar_2(conexao: sqlite3.Connection) -> None:
        conexao.execute("CREATE TABLE segundo (id INTEGER PRIMARY KEY)")
        raise RuntimeError("falha proposital")

    migrations = [
        Migration(1, "primeira", aplicar_1),
        Migration(2, "segunda", aplicar_2),
    ]

    with criar_conexao() as conexao:
        assert executar_migrations(conexao, [migrations[0]]) == 1

        with pytest.raises(RuntimeError, match="falha proposital"):
            executar_migrations(conexao, migrations)

        assert obter_versao_schema(conexao) == 1
        assert conexao.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'segundo'"
        ).fetchone() is None


def test_migrations_posteriores_nao_sao_executadas_apos_falha():
    ordem = []

    def aplicar_2(conexao: sqlite3.Connection) -> None:
        ordem.append(2)
        raise RuntimeError("falha")

    def aplicar_3(conexao: sqlite3.Connection) -> None:
        ordem.append(3)

    migrations = [
        Migration(1, "primeira", lambda conexao: ordem.append(1)),
        Migration(2, "segunda", aplicar_2),
        Migration(3, "terceira", aplicar_3),
    ]

    with criar_conexao() as conexao:
        with pytest.raises(RuntimeError, match="falha"):
            executar_migrations(conexao, migrations)

        assert ordem == [1, 2]
        assert obter_versao_schema(conexao) == 1


def test_versoes_duplicadas_sao_rejeitadas_antes_da_execucao():
    executou = False

    def aplicar(conexao: sqlite3.Connection) -> None:
        nonlocal executou
        executou = True

    migrations = [
        Migration(1, "primeira", aplicar),
        Migration(1, "duplicada", aplicar),
    ]

    with criar_conexao() as conexao:
        with pytest.raises(ValueError, match="mesma versão"):
            executar_migrations(conexao, migrations)

        assert executou is False
        assert obter_versao_schema(conexao) == 0


def test_versionamento_negativo_ou_zero_e_rejeitado():
    migration = Migration(0, "invalida", lambda conexao: None)

    with criar_conexao() as conexao:
        with pytest.raises(ValueError, match="inteiro positivo"):
            executar_migrations(conexao, [migration])