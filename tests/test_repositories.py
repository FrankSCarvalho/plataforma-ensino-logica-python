"""Testes de persistência e integridade referencial dos repositórios."""

import sqlite3

import pytest

from app.models import Aluno, Exercicio, Habilidade, Modulo, Nivel
from app.repositories import (
    AlunoRepository,
    ExercicioRepository,
    HabilidadeRepository,
    ModuloRepository,
    NivelRepository,
)

ALUNOS = AlunoRepository()
MODULOS = ModuloRepository()
HABILIDADES = HabilidadeRepository()
NIVEIS = NivelRepository()
EXERCICIOS = ExercicioRepository()


def _criar_curriculo():
    """Cria um currículo completo (módulo, habilidade, nível, exercício)."""
    modulo = MODULOS.inserir(Modulo(nome="Fundamentos de Lógica", ordem=1))
    habilidade = HABILIDADES.inserir(
        Habilidade(modulo_id=modulo.id, nome="Variáveis", ordem=1)
    )
    nivel = NIVEIS.inserir(
        Nivel(habilidade_id=habilidade.id, nome="Nível 1", ordem=1)
    )
    exercicio = EXERCICIOS.inserir(
        Exercicio(nivel_id=nivel.id, enunciado="Crie uma variável", ordem=1)
    )
    return modulo, habilidade, nivel, exercicio


# ---------------------------------------------------------------------------
# Aluno (entidade independente)
# ---------------------------------------------------------------------------


def test_criar_aluno(banco_de_teste):
    aluno = ALUNOS.inserir(Aluno(nome="Maria"))

    assert aluno.id is not None

    registrado = ALUNOS.buscar_por_id(aluno.id)
    assert registrado.nome == "Maria"
    assert registrado.status == "ativo"
    assert registrado.criado_em is not None


def test_buscar_id_inexistente_retorna_none(banco_de_teste):
    assert ALUNOS.buscar_por_id(999) is None


def test_listar_alunos(banco_de_teste):
    ALUNOS.inserir(Aluno(nome="Primeiro"))
    ALUNOS.inserir(Aluno(nome="Segundo"))

    cadastrados = ALUNOS.listar()

    assert len(cadastrados) == 2
    assert [aluno.nome for aluno in cadastrados] == ["Primeiro", "Segundo"]


def test_atualizar_aluno(banco_de_teste):
    aluno = ALUNOS.inserir(Aluno(nome="João"))
    aluno.nome = "João Silva"
    aluno.status = "inativo"

    alterado = ALUNOS.atualizar(aluno)

    assert alterado is True
    registrado = ALUNOS.buscar_por_id(aluno.id)
    assert registrado.nome == "João Silva"
    assert registrado.status == "inativo"
    assert registrado.atualizado_em is not None


def test_excluir_aluno(banco_de_teste):
    aluno = ALUNOS.inserir(Aluno(nome="Temporário"))

    assert ALUNOS.excluir(aluno.id) is True
    assert ALUNOS.buscar_por_id(aluno.id) is None
# ---------------------------------------------------------------------------
# Módulo
# ---------------------------------------------------------------------------


def test_criar_modulo(banco_de_teste):
    modulo = MODULOS.inserir(Modulo(nome="Lógica", descricao="Base", ordem=1))

    assert modulo.id is not None
    assert MODULOS.buscar_por_id(modulo.id).nome == "Lógica"


def test_atualizar_modulo(banco_de_teste):
    modulo = MODULOS.inserir(Modulo(nome="Antigo", ordem=1))
    modulo.nome = "Novo"

    assert MODULOS.atualizar(modulo) is True
    assert MODULOS.buscar_por_id(modulo.id).nome == "Novo"


def test_listar_modulos_em_ordem(banco_de_teste):
    MODULOS.inserir(Modulo(nome="Segundo", ordem=2))
    MODULOS.inserir(Modulo(nome="Primeiro", ordem=1))

    modulos = MODULOS.listar()

    assert [m.nome for m in modulos] == ["Primeiro", "Segundo"]


# ---------------------------------------------------------------------------
# Criação da hierarquia do currículo
# ---------------------------------------------------------------------------


def test_criar_habilidade_vinculada_ao_modulo(banco_de_teste):
    modulo = MODULOS.inserir(Modulo(nome="Fundamentos", ordem=1))

    habilidade = HABILIDADES.inserir(
        Habilidade(modulo_id=modulo.id, nome="Estruturas", ordem=1)
    )

    assert habilidade.id is not None
    assert habilidade.modulo_id == modulo.id


def test_criar_nivel_vinculado_a_habilidade(banco_de_teste):
    modulo = MODULOS.inserir(Modulo(nome="Fundamentos", ordem=1))
    habilidade = HABILIDADES.inserir(
        Habilidade(modulo_id=modulo.id, nome="Estruturas", ordem=1)
    )

    nivel = NIVEIS.inserir(
        Nivel(habilidade_id=habilidade.id, nome="Nível 1", ordem=1)
    )

    assert nivel.id is not None
    assert nivel.habilidade_id == habilidade.id


def test_criar_exercicio_vinculado_ao_nivel(banco_de_teste):
    _, _, nivel, _ = _criar_curriculo()

    exercicio = EXERCICIOS.inserir(
        Exercicio(nivel_id=nivel.id, enunciado="Enunciado novo", ordem=2)
    )

    assert exercicio.id is not None
    assert exercicio.nivel_id == nivel.id


def test_buscar_por_id_de_cada_entidade(banco_de_teste):
    modulo, habilidade, nivel, exercicio = _criar_curriculo()

    assert MODULOS.buscar_por_id(modulo.id).nome == "Fundamentos de Lógica"
    assert HABILIDADES.buscar_por_id(habilidade.id).nome == "Variáveis"
    assert NIVEIS.buscar_por_id(nivel.id).nome == "Nível 1"
    assert EXERCICIOS.buscar_por_id(exercicio.id).enunciado == "Crie uma variável"


def test_atualizar_habilidade_preserva_vinculo(banco_de_teste):
    modulo, habilidade, _, _ = _criar_curriculo()
    habilidade.nome = "Variáveis e Tipos"

    assert HABILIDADES.atualizar(habilidade) is True

    atualizada = HABILIDADES.buscar_por_id(habilidade.id)
    assert atualizada.nome == "Variáveis e Tipos"
    assert atualizada.modulo_id == modulo.id
# ---------------------------------------------------------------------------
# Restrições de relacionamento (chaves estrangeiras)
# ---------------------------------------------------------------------------


def test_habilidade_nao_aceita_modulo_inexistente(banco_de_teste):
    with pytest.raises(sqlite3.IntegrityError):
        HABILIDADES.inserir(Habilidade(modulo_id=999, nome="Órfã", ordem=1))


def test_nivel_nao_aceita_habilidade_inexistente(banco_de_teste):
    with pytest.raises(sqlite3.IntegrityError):
        NIVEIS.inserir(Nivel(habilidade_id=999, nome="Órfão", ordem=1))


def test_exercicio_nao_aceita_nivel_inexistente(banco_de_teste):
    with pytest.raises(sqlite3.IntegrityError):
        EXERCICIOS.inserir(Exercicio(nivel_id=999, enunciado="Órfão", ordem=1))


# ---------------------------------------------------------------------------
# Comportamento coerente das exclusões
# ---------------------------------------------------------------------------


def test_excluir_modulo_com_habilidade_falha(banco_de_teste):
    modulo, _, _, _ = _criar_curriculo()

    with pytest.raises(ValueError):
        MODULOS.excluir(modulo.id)


def test_excluir_habilidade_com_nivel_falha(banco_de_teste):
    _, habilidade, _, _ = _criar_curriculo()

    with pytest.raises(ValueError):
        HABILIDADES.excluir(habilidade.id)


def test_excluir_nivel_com_exercicio_falha(banco_de_teste):
    _, _, nivel, _ = _criar_curriculo()

    with pytest.raises(ValueError):
        NIVEIS.excluir(nivel.id)


def test_excluir_exercicio_sem_filhos(banco_de_teste):
    _, _, _, exercicio = _criar_curriculo()

    assert EXERCICIOS.excluir(exercicio.id) is True


def test_excluir_modulo_sem_habilidades(banco_de_teste):
    modulo = MODULOS.inserir(Modulo(nome="Vazio", ordem=1))

    assert MODULOS.excluir(modulo.id) is True