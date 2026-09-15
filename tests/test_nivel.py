import unittest

from src.plataforma.dominio.nivel import Nivel

class TestNivel(unittest.TestCase):
    def test_cria_nivel_com_dados_validos(self):
        nivel = Nivel(1,1,1)

        self.assertEqual(nivel.id, 1)
        self.assertEqual(nivel.numero, 1)
        self.assertEqual(nivel.habilidade_id, 1)

    def test_nao_cria_nivel_sem_id(self):
        with self.assertRaises(ValueError):
            Nivel(None, 1, 1)

    def test_nao_cria_nivel_sem_numero(self):
        with self.assertRaises(ValueError):
            Nivel(1, None, 1)

    def test_nao_cria_nivel_com_numero_zero(self):
        with self.assertRaises(ValueError):
            Nivel(1,0,1)

    def test_nao_cria_nivel_com_numero_negativo(self):
        with self.assertRaises(ValueError):
            Nivel(1,-1,1)

    def test_nao_cria_nivel_sem_habilidade(self):
        with self.assertRaises(ValueError):
            Nivel(1,1,None)

if __name__ == "__main__":
    unittest.main()