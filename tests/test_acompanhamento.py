"""Testes da infraestrutura de acompanhamento da aprendizagem.

Cobre progresso do aluno, sessões de estudo, tentativas, vínculos,
busca, listagem, atualização e a preservação do histórico.
"""

import sqlite3

import pytest

from app.models import (
    Aluno,
    Exercicio,
    Habilidade,
    Modulo,
    Nivel,
    ProgressoAluno,
    SessaoEstudo,
    Tentativa,
)
from app.repositories import (
    AlunoRepository,
    ExercicioRepository,
    HabilidadeRepository,
    ModuloRepository,
    NivelRepository,
    ProgressoAlunoRepository,
    SessaoEstudoRepository,
    TentativaRepository,
)

ALUNOS = AlunoRepository()
MODULOS = ModuloRepository()
HABILIDADES = HabilidadeRepository()
NIVEIS = NivelRepository()
EXERCICIOS = ExercicioRepository()
PROGRESSOS = ProgressoAlunoRepository()
SESSOES = SessaoEstudoRepository()
TENTATIVAS = TentativaRepository()


def _criar_cenario():
    """Cria aluno + currículo completo e retorna as entidades envolvidas.

    O currículo é composto por:
      * 1 módulo
      * 2 habilidades (para testar progresso em várias habilidades)
      * 1 nível na habilidade 1 e 1 nível na habilidade 2
      * 1 exercício no nível da habilidade 1
    """
    aluno = ALUNOS.inserir(Aluno(nome="Ana"))
    modulo = MODULOS.inserir(Modulo(nome="Fundamentos", ordem=1))

    habilidade_1 = HABILIDADES.inserir(
        Habilidade(modulo_id=modulo.id, nome="Variáveis", ordem=1)
    )
    habilidade_2 = HABILIDADES.inserir(
        Habilidade(modulo_id=modulo.id, nome="Estruturas", ordem=2)
    )

    nivel_1 = NIVEIS.inserir(
        Nivel(habilidade_id=habilidade_1.id, nome="Nível 1", ordem=1)
    )
    nivel_2 = NIVEIS.inserir(
        Nivel(habilidade_id=habilidade_1.id, nome="Nível 2", ordem=2)
    )
    nivel_h2 = NIVEIS.inserir(
        Nivel(habilidade_id=habilidade_2.id, nome="Nível 1", ordem=1)
    )

    exercicio = EXERCICIOS.inserir(
        Exercicio(nivel_id=nivel_1.id, enunciado="Crie uma variável", ordem=1)
    )

    return {
        "aluno": aluno,
        "modulo": modulo,
        "habilidade_1": habilidade_1,
        "habilidade_2": habilidade_2,
        "nivel_1": nivel_1,
        "nivel_2": nivel_2,
        "nivel_h2": nivel_h2,
        "exercicio": exercicio,
    }


def _criar_sessao_e_tentativa(cenario):
    """Cria uma sessão de estudo e uma tentativa no cenário base."""
    sessao = SESSOES.inserir(
        SessaoEstudo(aluno_id=cenario["aluno"].id, status="ativa")
    )
    tentativa = TENTATIVAS.inserir(
        Tentativa(
            sessao_id=sessao.id,
            aluno_id=cenario["aluno"].id,
            exercicio_id=cenario["exercicio"].id,
            resposta="x = 10",
            resultado="correta",
            tempo_resolucao_segundos=45,
        )
    )
    return sessao, tentativa


# ---------------------------------------------------------------------------
# Criação e vínculos
# ---------------------------------------------------------------------------


def test_criar_progresso_do_aluno(banco_de_teste):
    cenario = _criar_cenario()

    progresso = PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["habilidade_1"].id,
            nivel_id=cenario["nivel_1"].id,
        )
    )

    assert progresso.id is not None
    assert progresso.status == "em_andamento"

    registrado = PROGRESSOS.buscar_por_id(progresso.id)
    assert registrado.criado_em is not None


def test_criar_sessao_de_estudo(banco_de_teste):
    cenario = _criar_cenario()

    sessao = SESSOES.inserir(
        SessaoEstudo(aluno_id=cenario["aluno"].id)
    )

    assert sessao.id is not None
    assert sessao.status == "ativa"

    registrada = SESSOES.buscar_por_id(sessao.id)
    assert registrada.inicio is not None
    assert registrada.termino is None


def test_criar_tentativa(banco_de_teste):
    cenario = _criar_cenario()
    _, tentativa = _criar_sessao_e_tentativa(cenario)

    assert tentativa.id is not None
    assert tentativa.resultado == "correta"
    assert tentativa.tempo_resolucao_segundos == 45

    registrada = TENTATIVAS.buscar_por_id(tentativa.id)
    assert registrada.realizada_em is not None


def test_tentativa_aceita_resposta_extensa(banco_de_teste):
    """Respostas de programação podem ser longas; TEXT não tem limite prático."""
    cenario = _criar_cenario()
    sessao = SESSOES.inserir(SessaoEstudo(aluno_id=cenario["aluno"].id))

    codigo_longo = "# codigo do aluno\n" + "\n".join(
        f"linha_{i} = {i}" for i in range(500)
    )
    assert len(codigo_longo) > 1000

    tentativa = TENTATIVAS.inserir(
        Tentativa(
            sessao_id=sessao.id,
            aluno_id=cenario["aluno"].id,
            exercicio_id=cenario["exercicio"].id,
            resposta=codigo_longo,
        )
    )

    registrada = TENTATIVAS.buscar_por_id(tentativa.id)
    assert registrada.resposta == codigo_longo


def test_vinculos_corretos_do_progresso(banco_de_teste):
    cenario = _criar_cenario()

    progresso = PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["habilidade_1"].id,
            nivel_id=cenario["nivel_2"].id,
            status="em_andamento",
        )
    )

    registrado = PROGRESSOS.buscar_por_id(progresso.id)
    assert registrado.aluno_id == cenario["aluno"].id
    assert registrado.habilidade_id == cenario["habilidade_1"].id
    assert registrado.nivel_id == cenario["nivel_2"].id


def test_vinculos_corretos_da_tentativa(banco_de_teste):
    cenario = _criar_cenario()
    sessao, tentativa = _criar_sessao_e_tentativa(cenario)

    registrada = TENTATIVAS.buscar_por_id(tentativa.id)
    assert registrada.sessao_id == sessao.id
    assert registrada.aluno_id == cenario["aluno"].id
    assert registrada.exercicio_id == cenario["exercicio"].id


# ---------------------------------------------------------------------------
# Busca e listagem
# ---------------------------------------------------------------------------


def test_buscar_por_id_das_novas_entidades(banco_de_teste):
    cenario = _criar_cenario()
    sessao, tentativa = _criar_sessao_e_tentativa(cenario)
    progresso = PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["habilidade_1"].id,
            nivel_id=cenario["nivel_1"].id,
        )
    )

    assert PROGRESSOS.buscar_por_id(progresso.id).aluno_id == cenario["aluno"].id
    assert SESSOES.buscar_por_id(sessao.id).aluno_id == cenario["aluno"].id
    assert TENTATIVAS.buscar_por_id(tentativa.id).exercicio_id == (
        cenario["exercicio"].id
    )


def test_buscar_id_inexistente_retorna_none(banco_de_teste):
    assert PROGRESSOS.buscar_por_id(999) is None
    assert SESSOES.buscar_por_id(999) is None
    assert TENTATIVAS.buscar_por_id(999) is None


def test_listagem_de_progresso_e_tentativas(banco_de_teste):
    cenario = _criar_cenario()

    PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["habilidade_1"].id,
            nivel_id=cenario["nivel_1"].id,
        )
    )
    PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["habilidade_2"].id,
            nivel_id=cenario["nivel_h2"].id,
        )
    )
    sessao = SESSOES.inserir(SessaoEstudo(aluno_id=cenario["aluno"].id))
    TENTATIVAS.inserir(
        Tentativa(
            sessao_id=sessao.id,
            aluno_id=cenario["aluno"].id,
            exercicio_id=cenario["exercicio"].id,
            resposta="a",
        )
    )
    TENTATIVAS.inserir(
        Tentativa(
            sessao_id=sessao.id,
            aluno_id=cenario["aluno"].id,
            exercicio_id=cenario["exercicio"].id,
            resposta="b",
        )
    )

    assert len(PROGRESSOS.listar()) == 2
    assert len(SESSOES.listar()) == 1
    assert len(TENTATIVAS.listar()) == 2


# ---------------------------------------------------------------------------
# Atualização e encerramento
# ---------------------------------------------------------------------------


def test_atualizar_progresso(banco_de_teste):
    cenario = _criar_cenario()

    progresso = PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["habilidade_1"].id,
            nivel_id=cenario["nivel_1"].id,
        )
    )

    # O aluno avança do nível 1 para o nível 2.
    progresso.nivel_id = cenario["nivel_2"].id
    progresso.status = "em_andamento"

    assert PROGRESSOS.atualizar(progresso) is True

    atualizado = PROGRESSOS.buscar_por_id(progresso.id)
    assert atualizado.nivel_id == cenario["nivel_2"].id
    assert atualizado.habilidade_id == cenario["habilidade_1"].id
    assert atualizado.atualizado_em is not None


def test_encerrar_sessao_preenche_termino(banco_de_teste):
    cenario = _criar_cenario()
    sessao = SESSOES.inserir(SessaoEstudo(aluno_id=cenario["aluno"].id))

    assert SESSOES.encerrar(sessao, status="encerrada") is True

    encerrada = SESSOES.buscar_por_id(sessao.id)
    assert encerrada.status == "encerrada"
    assert encerrada.termino is not None


def test_aluno_com_progresso_em_varias_habilidades(banco_de_teste):
    cenario = _criar_cenario()

    PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["habilidade_1"].id,
            nivel_id=cenario["nivel_1"].id,
        )
    )
    PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["habilidade_2"].id,
            nivel_id=cenario["nivel_h2"].id,
        )
    )

    progressos = PROGRESSOS.listar()

    assert len(progressos) == 2
    assert {p.habilidade_id for p in progressos} == {
        cenario["habilidade_1"].id,
        cenario["habilidade_2"].id,
    }


# ---------------------------------------------------------------------------
# Rejeição de referências inexistentes
# ---------------------------------------------------------------------------


def test_progresso_rejeita_aluno_inexistente(banco_de_teste):
    cenario = _criar_cenario()

    with pytest.raises(sqlite3.IntegrityError):
        PROGRESSOS.inserir(
            ProgressoAluno(
                aluno_id=999,
                habilidade_id=cenario["habilidade_1"].id,
                nivel_id=cenario["nivel_1"].id,
            )
        )


def test_progresso_rejeita_habilidade_inexistente(banco_de_teste):
    cenario = _criar_cenario()

    with pytest.raises(sqlite3.IntegrityError):
        PROGRESSOS.inserir(
            ProgressoAluno(
                aluno_id=cenario["aluno"].id,
                habilidade_id=999,
                nivel_id=cenario["nivel_1"].id,
            )
        )


def test_progresso_rejeita_nivel_inexistente(banco_de_teste):
    cenario = _criar_cenario()

    with pytest.raises(sqlite3.IntegrityError):
        PROGRESSOS.inserir(
            ProgressoAluno(
                aluno_id=cenario["aluno"].id,
                habilidade_id=cenario["habilidade_1"].id,
                nivel_id=999,
            )
        )


def test_sessao_rejeita_aluno_inexistente(banco_de_teste):
    with pytest.raises(sqlite3.IntegrityError):
        SESSOES.inserir(SessaoEstudo(aluno_id=999))


def test_tentativa_rejeita_referencias_inexistentes(banco_de_teste):
    cenario = _criar_cenario()
    sessao = SESSOES.inserir(SessaoEstudo(aluno_id=cenario["aluno"].id))

    casos = [
        # sessão inexistente
        {"sessao_id": 999, "aluno_id": cenario["aluno"].id,
         "exercicio_id": cenario["exercicio"].id},
        # aluno inexistente
        {"sessao_id": sessao.id, "aluno_id": 999,
         "exercicio_id": cenario["exercicio"].id},
        # exercício inexistente
        {"sessao_id": sessao.id, "aluno_id": cenario["aluno"].id,
         "exercicio_id": 999},
    ]

    for caso in casos:
        with pytest.raises(sqlite3.IntegrityError):
            TENTATIVAS.inserir(Tentativa(resposta="x", **caso))


# ---------------------------------------------------------------------------
# Preservação do histórico (ponto fundamental)
# ---------------------------------------------------------------------------


def test_atualizar_progresso_nao_remove_tentativas_anteriores(banco_de_teste):
    """Atualizar o progresso NÃO deve apagar o histórico de tentativas.

    Cenário: o aluno faz tentativas nos níveis 1 e 2. Depois o progresso
    é atualizado para o nível 3. As tentativas antigas devem continuar
    existindo no banco, pois estado atual e histórico são coisas
    diferentes.
    """
    cenario = _criar_cenario()

    # Sessão onde o aluno praticou nos níveis 1 e 2.
    sessao = SESSOES.inserir(SessaoEstudo(aluno_id=cenario["aluno"].id))
    exercicio_nivel_1 = cenario["exercicio"]

    # Exercício do nível 2 para simular tentativas em níveis anteriores.
    exercicio_nivel_2 = EXERCICIOS.inserir(
        Exercicio(nivel_id=cenario["nivel_2"].id, enunciado="Nível 2", ordem=1)
    )

    # Tentativa no nível 1.
    t1 = TENTATIVAS.inserir(
        Tentativa(
            sessao_id=sessao.id,
            aluno_id=cenario["aluno"].id,
            exercicio_id=exercicio_nivel_1.id,
            resposta="x = 1",
            resultado="correta",
        )
    )
    # Tentativa no nível 2.
    t2 = TENTATIVAS.inserir(
        Tentativa(
            sessao_id=sessao.id,
            aluno_id=cenario["aluno"].id,
            exercicio_id=exercicio_nivel_2.id,
            resposta="x = 2",
            resultado="incorreta",
        )
    )

    # O progresso aponta para o nível 3 (estado atual atualizado).
    progresso = PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["habilidade_1"].id,
            nivel_id=cenario["nivel_1"].id,
        )
    )
    progresso.nivel_id = cenario["nivel_2"].id
    PROGRESSOS.atualizar(progresso)

    # O histórico de tentativas precisa continuar completo.
    tentativas_restantes = TENTATIVAS.listar()
    assert len(tentativas_restantes) == 2
    ids_restantes = {t.id for t in tentativas_restantes}
    assert t1.id in ids_restantes
    assert t2.id in ids_restantes

    # O progresso continua refletindo o novo estado.
    registrado = PROGRESSOS.buscar_por_id(progresso.id)
    assert registrado.nivel_id == cenario["nivel_2"].id


def test_bloqueio_de_exclusao_de_historico(banco_de_teste):
    """Sessões, tentativas e progresso não devem poder ser excluídos."""
    cenario = _criar_cenario()
    sessao, tentativa = _criar_sessao_e_tentativa(cenario)
    progresso = PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["habilidade_1"].id,
            nivel_id=cenario["nivel_1"].id,
        )
    )

    with pytest.raises(NotImplementedError):
        SESSOES.excluir(sessao.id)

    with pytest.raises(NotImplementedError):
        TENTATIVAS.excluir(tentativa.id)

    with pytest.raises(NotImplementedError):
        PROGRESSOS.excluir(progresso.id)


def test_bloqueio_de_alteracao_de_tentativa(banco_de_teste):
    cenario = _criar_cenario()
    _, tentativa = _criar_sessao_e_tentativa(cenario)

    with pytest.raises(NotImplementedError):
        TENTATIVAS.atualizar(tentativa)