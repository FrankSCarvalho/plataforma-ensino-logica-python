import sqlite3

from app.persistencia.banco import CAMINHO_BANCO, obter_conexao


def test_obter_conexao_cria_banco():
    with obter_conexao() as conexao:
        assert isinstance(conexao, sqlite3.Connection)
        assert conexao.execute("SELECT 1").fetchone()[0] == 1

    assert CAMINHO_BANCO.exists()


def test_conexao_usa_row_factory():
    with obter_conexao() as conexao:
        linha = conexao.execute("SELECT 1 AS valor").fetchone()

    assert linha["valor"] == 1