import unittest

from src.plataforma.dominio.habilidade import Habilidade


class TestHabilidade(unittest.TestCase):
    def test_cria_habilidade_com_id_e_nome(self):
        habilidade = Habilidade(1, "Variáveis", 1)

        self.assertEqual(habilidade.id, 1)
        self.assertEqual(habilidade.nome, "Variáveis")
        self.assertEqual(habilidade.modulo_id, 1)

    def test_nao_cria_habilidade_sem_id(self):
        with self.assertRaises(ValueError):
            Habilidade(None, "Variáveis", 1)

    def test_nao_cria_habilidade_sem_nome(self):
        with self.assertRaises(ValueError):
            Habilidade(1, "", 1)

    def test_nao_cria_habilidade_com_nome_apenas_espacos(self):
        with self.assertRaises(ValueError):
            Habilidade(1, "   ", 1)

    def test_nao_cria_habilidade_sem_modulo(self):
        with self.assertRaises(ValueError):
            Habilidade(1, "Variáveis", None)


if __name__ == "__main__":
    unittest.main()