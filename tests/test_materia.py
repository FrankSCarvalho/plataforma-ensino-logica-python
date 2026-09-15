import unittest

from src.plataforma.dominio.materia import Materia


class TestMateria(unittest.TestCase):
    def test_cria_materia_com_id_e_nome(self):
        materia = Materia(1, "Python")

        self.assertEqual(materia.id, 1)
        self.assertEqual(materia.nome, "Python")

    def test_nao_cria_materia_sem_id(self):
        with self.assertRaises(ValueError):
            Materia(None, "Python")

    def test_nao_cria_materia_sem_nome(self):
        with self.assertRaises(ValueError):
            Materia(1, "")


if __name__ == "__main__":
    unittest.main()