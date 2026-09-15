import unittest

from src.plataforma.dominio.modulo import Modulo


class TestModulo(unittest.TestCase):
    def test_cria_modulo_com_id_e_nome(self):
        modulo = Modulo(1, "Fundamentos", 1)

        self.assertEqual(modulo.id, 1)
        self.assertEqual(modulo.nome, "Fundamentos")
        self.assertEqual(modulo.materia_id,1)

    def test_nao_cria_modulo_sem_id(self):
        with self.assertRaises(ValueError):
            Modulo(None, "Fundamentos", 1)

    def test_nao_cria_modulo_sem_nome(self):
        with self.assertRaises(ValueError):
            Modulo(1, "", 1)

    def test_nao_cria_modulo_sem_materia(self):
        with self.assertRaises(ValueError):
            Modulo(1, "Fundamentos", None)


if __name__ == "__main__":
    unittest.main()