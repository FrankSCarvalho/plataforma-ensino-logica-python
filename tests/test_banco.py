import sqlite3
import unittest

from src.plataforma.persistencia.banco import criar_tabelas
from src.plataforma.persistencia.conexao import criar_conexao


class TestBanco(unittest.TestCase):
    def test_cria_tabelas(self):
        conexao = criar_conexao(":memory:")

        criar_tabelas(conexao)

        tabelas = conexao.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        nomes_tabelas = {tabela[0] for tabela in tabelas}

        self.assertIn("materia", nomes_tabelas)
        self.assertIn("modulo", nomes_tabelas)
        self.assertIn("habilidade", nomes_tabelas)
        self.assertIn("nivel", nomes_tabelas)
        self.assertIn("exercicio", nomes_tabelas)

        conexao.close()

    def test_nao_permite_modulo_sem_materia_existente(self):
        conexao = criar_conexao(":memory:")

        criar_tabelas(conexao)

        with self.assertRaises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO modulo (id, nome, materia_id)
                VALUES (1, 'Fundamentos', 999)
                """
            )

        conexao.close()

    def test_nao_permite_nivel_com_numero_invalido(self):
        conexao = criar_conexao(":memory:")

        criar_tabelas(conexao)

        conexao.execute(
            """
            INSERT INTO materia (id, nome)
            VALUES (1, 'Python')
            """
        )

        conexao.execute(
            """
            INSERT INTO modulo (id, nome, materia_id)
            VALUES (1, 'Fundamentos', 1)
            """
        )

        conexao.execute(
            """
            INSERT INTO habilidade (id, nome, modulo_id)
            VALUES (1, 'Variáveis', 1)
            """
        )

        with self.assertRaises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO nivel (id, numero, habilidade_id)
                VALUES (1, 0, 1)
                """
            )

        conexao.close()


if __name__ == "__main__":
    unittest.main()