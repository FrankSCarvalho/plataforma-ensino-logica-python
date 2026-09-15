import unittest

from src.plataforma.dominio.exercicio import Exercicio

class TestExercicio(unittest.TestCase):
    def test_cria_exercicio_com_dados_validos(self):
        exercicio = Exercicio(1, "Crie uma variavel chamada nome.", 1)

        self.assertEqual(exercicio.id, 1)
        self.assertEqual(exercicio.enunciado, "Crie uma variavel chamada nome.")
        self.assertEqual(exercicio.nivel_id,1)

    def test_nao_cria_exercicio_sem_id(self):
        with self.assertRaises(ValueError):
            Exercicio(None, "Crie uma variável chamada nome.", 1)

    def test_nao_cria_exercicio_sem_enunciado(self):
        with self.assertRaises(ValueError):
            Exercicio(1, "", 1)

    def test_nao_cria_exercicio_com_enunciado_apenas_espacos(self):
        with self.assertRaises(ValueError):
            Exercicio(1, "   ", 1)

    def test_nao_cria_exercicio_sem_nivel(self):
        with self.assertRaises(ValueError):
            Exercicio(1, "Crie uma variável chamada nome.", None)


if __name__ == "__main__":
    unittest.main()