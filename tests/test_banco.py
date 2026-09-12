import sqlite3  # Driver SQLite: tipo de conexão esperado pela função testada

from app.persistencia.banco import CAMINHO_BANCO, obter_conexao


def test_obter_conexao_cria_banco():
    # Verifica que obter_conexao() devolve uma conexão funcional e que
    # conectar realmente cria o arquivo físico data/plataforma.db.
    with obter_conexao() as conexao:
        assert isinstance(conexao, sqlite3.Connection)
        assert conexao.execute("SELECT 1").fetchone()[0] == 1  # consulta trivial

    # Depois de fechar o gerenciador de contexto, o arquivo físico deve existir.
    assert CAMINHO_BANCO.exists()


def test_conexao_usa_row_factory():
    # Garantia de conforto: as linhas devolvidas permitem acesso POR NOME
    # da coluna (linha["valor"]), e não apenas por índice (linha[0]).
    with obter_conexao() as conexao:
        linha = conexao.execute("SELECT 1 AS valor").fetchone()

    assert linha["valor"] == 1
