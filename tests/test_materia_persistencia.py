import unittest

from src.plataforma.dominio.materia import Materia
from src.plataforma.persistencia.banco import criar_tabelas
from src.plataforma.persistencia.conexao import criar_conexao
from src.plataforma.persistencia.materia import salvar_materia

class TestMateriaPersistencia(unittest.TestCase):
    def test_salvar_materia(self):
        conexao = criar_conexao(":memory:")

        criar_tabelas(conexao)

        materia = Materia(1,"Python")

        salvar_materia(conexao,materia)

        resultado = conexao.execute("SELECT id, nome FROM materia WHERE  id = ?", (1,),).fetchone()

        self.assertEqual(resultado, (1,"Python"))

        conexao.close()

if __name__ == "__main__":
    unittest.main()