import unittest

from src.plataforma.persistencia.conexao import criar_conexao

class TestConexao(unittest.TestCase):
    def test_criar_conexao_com_sqlite(self):
        conexao = criar_conexao()

        self.assertIsNotNone(conexao)

        conexao.close()


if __name__ == "__main__":
    unittest.main()