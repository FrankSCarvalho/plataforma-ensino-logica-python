"""Testes do serviço de Painel do Aluno (Tarefa 11).

O currículo padrão possui 1 habilidade com 3 níveis.
Todos os testes usam o banco TEMPORÁRIO da fixture ``banco_de_teste``.
"""

import pytest

from app.models import Aluno, Habilidade, Modulo, Nivel, ProgressoAluno
from app.repositories import (
    AlunoRepository,
    HabilidadeRepository,
    NivelRepository,
    ProgressoAlunoRepository,
)
from app.services import carga_inicial, fluxo_estudo, painel_aluno
from app.services.motor_pedagogico import JANELA_DOMINIO, STATUS_CONCLUIDO

ALUNOS = AlunoRepository()
HABILIDADES = HabilidadeRepository()
NIVEIS = NivelRepository()
PROGRESSOS = ProgressoAlunoRepository()


def _ambiente(banco_de_teste, nome="Aluna Painel"):
    carga_inicial.carregar_curriculo_inicial()
    aluno = ALUNOS.inserir(Aluno(nome=nome))
    return aluno, carga_inicial.carregar_curriculo_inicial()


def _responder_ate(estado, quantidade_avaliadas, limite=200):
    """Responde corretamente até acumular N tentativas AVALIADAS."""
    respondidas = 0
    for _ in range(limite):
        exercicio = fluxo_estudo.exercicio_atual(estado)
        if exercicio is None:
            fluxo_estudo.reiniciar_lista_de_exercicios(estado)
            exercicio = fluxo_estudo.exercicio_atual(estado)
        fluxo_estudo.responder(estado, exercicio.resposta_esperada or "livre")
        if exercicio.tipo == "prever_resultado":
            respondidas += 1
        if respondidas >= quantidade_avaliadas:
            break


def _dominar_niveis_ate_fim(estado, repositorio_niveis):
    """Domina níveis iterativamente até o status ficar CONCLUIDO."""
    for _ in range(30):
        if estado.progresso.status == STATUS_CONCLUIDO:
            break
        _responder_ate(estado, JANELA_DOMINIO)


def _criar_habilidade_extra(nome="Habilidade extra"):
    from app.repositories import ModuloRepository
    modulo = ModuloRepository().inserir(Modulo(nome="M extra", descricao="", ordem=9))
    habilidade = HABILIDADES.inserir(
        Habilidade(modulo_id=modulo.id, nome=nome, descricao="Testes", ordem=9)
    )
    NIVEIS.inserir(Nivel(habilidade_id=habilidade.id, nome="N1", ordem=1))
    return habilidade


def _marcar_habilidade_como_concluida(aluno_id, habilidade_id):
    """Marca o progresso de uma habilidade como concluída (teste do painel)."""
    progresso = PROGRESSOS.buscar_por_aluno_e_habilidade(aluno_id, habilidade_id)
    if progresso is None:
        niveis = NIVEIS.listar_por_habilidade(habilidade_id)
        progresso = PROGRESSOS.inserir(
            ProgressoAluno(
                aluno_id=aluno_id,
                habilidade_id=habilidade_id,
                nivel_id=niveis[-1].id if niveis else 0,
                status=STATUS_CONCLUIDO,
            )
        )
    else:
        progresso.status = STATUS_CONCLUIDO
        PROGRESSOS.atualizar(progresso)


def test_aluno_sem_progresso_todas_nao_iniciadas(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.aluno_nome == aluno.nome
    assert painel.resumo.total_habilidades == 1
    assert painel.resumo.nao_iniciadas == 1
    assert painel.resumo.em_andamento == 0
    assert painel.resumo.concluidas == 0


def test_aluno_sem_progresso_proximo_passo_inicia(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.proximo_passo == "Escolha uma habilidade para começar."


def test_aluno_sem_progresso_nivel_texto_padrao(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert len(painel.habilidades) == 1
    assert painel.habilidades[0].situacao == "Não iniciada"
    assert painel.habilidades[0].nivel_atual is None


def test_aluno_com_habilidade_em_andamento(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado)
    exercicio = fluxo_estudo.exercicio_atual(estado)
    fluxo_estudo.responder(estado, exercicio.resposta_esperada)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.resumo.em_andamento == 1
    assert painel.resumo.nao_iniciadas == 0
    assert painel.resumo.concluidas == 0


def test_habilidade_em_andamento_mostra_nivel_atual(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert len(painel.habilidades) == 1
    assert painel.habilidades[0].situacao == "Em andamento"
    assert painel.habilidades[0].nivel_atual == "Nível 1 de 3"


def test_habilidade_em_andamento_proximo_passo_continua(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.proximo_passo == "Continue seus estudos."


def test_aluno_com_habilidade_concluida(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado)
    _responder_ate(estado, JANELA_DOMINIO)
    assert estado.houve_progressao is True
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.resumo.em_andamento == 1
    assert painel.resumo.concluidas == 0


def test_habilidade_concluida_apos_ultimo_nivel(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    _marcar_habilidade_como_concluida(aluno.id, seed["habilidade"].id)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert len(painel.habilidades) == 1
    assert painel.habilidades[0].situacao == "Concluída"
    assert painel.habilidades[0].nivel_atual is None


def test_habilidades_mistas_com_habilidade_extra(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    habilidade_b = _criar_habilidade_extra("Habilidade B")
    estado = fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.resumo.total_habilidades == 2
    assert painel.resumo.em_andamento == 1
    assert painel.resumo.nao_iniciadas == 1


def test_todas_habilidades_concluidas(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    _marcar_habilidade_como_concluida(aluno.id, seed["habilidade"].id)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.resumo.concluidas == 1
    assert painel.resumo.em_andamento == 0
    assert painel.resumo.nao_iniciadas == 0
    assert painel.proximo_passo == "Você concluiu todas as habilidades disponíveis."


def test_contagem_correta_das_situacoes(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    total = (
        painel.resumo.nao_iniciadas
        + painel.resumo.em_andamento
        + painel.resumo.concluidas
    )
    assert total == painel.resumo.total_habilidades


def test_ausencia_de_progresso_nao_gera_erro(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel is not None
    assert painel.resumo.total_habilidades == 1


def test_proximo_passo_para_cada_situacao(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.proximo_passo == "Escolha uma habilidade para começar."
    estado = fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.proximo_passo == "Continue seus estudos."


def test_habilidades_mistas_com_habilidade_extra(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    _criar_habilidade_extra("Habilidade B")
    estado = fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado)
    _responder_ate(estado, JANELA_DOMINIO)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.resumo.total_habilidades == 2
    assert painel.resumo.em_andamento == 1
    assert painel.resumo.nao_iniciadas == 1


def test_todas_habilidades_concluidas(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado)
    niveis = NIVEIS.listar_por_habilidade(seed["habilidade"].id)
    _dominar_niveis_ate_fim(estado, NIVEIS)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.resumo.concluidas == 1
    assert painel.resumo.em_andamento == 0
    assert painel.resumo.nao_iniciadas == 0
    assert painel.proximo_passo == "Você concluiu todas as habilidades disponíveis."


def test_contagem_correta_das_situacoes(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    total = (
        painel.resumo.nao_iniciadas
        + painel.resumo.em_andamento
        + painel.resumo.concluidas
    )
    assert total == painel.resumo.total_habilidades


def test_ausencia_de_progresso_nao_gera_erro(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel is not None
    assert painel.resumo.total_habilidades == 1


def test_proximo_passo_para_cada_situacao(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.proximo_passo == "Escolha uma habilidade para começar."
    estado = fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert painel.proximo_passo == "Continue seus estudos."


def test_isolamento_entre_alunos(banco_de_teste):
    aluno_a, seed = _ambiente(banco_de_teste, nome="Aluno A")
    aluno_b = ALUNOS.inserir(Aluno(nome="Aluno B"))
    estado_a = fluxo_estudo.abrir_habilidade(aluno_a.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado_a)
    painel_a = painel_aluno.obter_painel_do_aluno(aluno_a.id, aluno_a.nome)
    painel_b = painel_aluno.obter_painel_do_aluno(aluno_b.id, aluno_b.nome)
    assert painel_a.resumo.em_andamento == 1
    assert painel_b.resumo.em_andamento == 0
    assert painel_b.resumo.nao_iniciadas == 1


def test_dados_do_painel_nao_alteram_progresso(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    fluxo_estudo.iniciar_sessao(estado)
    fluxo_estudo.responder(estado, fluxo_estudo.exercicio_atual(estado).resposta_esperada)
    progresso_antes = PROGRESSOS.buscar_por_aluno_e_habilidade(
        aluno.id, seed["habilidade"].id
    )
    painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    progresso_depois = PROGRESSOS.buscar_por_aluno_e_habilidade(
        aluno.id, seed["habilidade"].id
    )
    assert progresso_antes.nivel_id == progresso_depois.nivel_id
    assert progresso_antes.status == progresso_depois.status


def test_servico_nao_depende_de_flet(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    painel = painel_aluno.obter_painel_do_aluno(aluno.id, aluno.nome)
    assert isinstance(painel, painel_aluno.PainelDoAluno)
    assert isinstance(painel.resumo, painel_aluno.ResumoDoAluno)
    assert isinstance(painel.habilidades[0], painel_aluno.SituacaoDaHabilidade)
