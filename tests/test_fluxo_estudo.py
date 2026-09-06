"""Testes do fluxo de estudo (Tarefa 08).

Cobrem a lógica NOVA não visual do serviço ``app.services.fluxo_estudo``,
que orquestra a interface com os repositórios, o avaliador e o motor
pedagógico:

    * carregamento das habilidades e do currículo do banco;
    * progresso: consulta, criação inicial e ausência de duplicação;
    * carregamento do nível atual e dos exercícios em ordem;
    * sessão de estudo: criação, recriação e encerramento;
    * resposta: fluxo completo avaliação -> tentativa -> progresso;
    * progressão de nível dentro da mesma habilidade;
    * isolamento entre alunos e entre habilidades.

Todos os testes usam o banco TEMPORÁRIO da fixture ``banco_de_teste``.
"""

import pytest

from app.models import Aluno, SessaoEstudo, TIPO_PREVER_RESULTADO
from app.repositories import (
    AlunoRepository,
    NivelRepository,
    ProgressoAlunoRepository,
    SessaoEstudoRepository,
)
from app.services import carga_inicial, fluxo_estudo
from app.services.motor_pedagogico import (
    ACERTOS_PARA_DOMINIO,
    JANELA_DOMINIO,
)

ALUNOS = AlunoRepository()
NIVEIS = NivelRepository()
PROGRESSOS = ProgressoAlunoRepository()
SESSOES = SessaoEstudoRepository()


def _ambiente(banco_de_teste, nome="Aluno Fluxo"):
    """Cria aluno + currículo e devolve (aluno, resultado do seed)."""
    carga_inicial.carregar_curriculo_inicial()
    aluno = ALUNOS.inserir(Aluno(nome=nome))
    return aluno, carga_inicial.carregar_curriculo_inicial()


def _primeira_habilidade(seed):
    return seed["habilidade"]


def _responder_ate(estado, quantidade_avaliadas, limite=50):
    """Responde corretamente até acumular N tentativas AVALIADAS no nível.

    Somente exercícios ``prever_resultado`` geram resultado avaliado
    ('correta'/'incorreta'); ``resposta_textual`` e ``escrever_codigo``
    resultam em ``nao_avaliada`` e NÃO contam na janela de domínio —
    por isso o laço percorre a lista (reiniciando-a quando necessário)
    até que a quantidade desejada de tentativas avaliadas seja atingida.

    Para imediatamente quando o motor pedagógico dispara a progressão:
    ao mudar de nível, o estado é reiniciado (``indice_exercicio = 0``) e
    responder exercícios do próximo nível falsificaria a contagem.
    """
    respondidas_avaliadas = 0
    for _ in range(limite):
        exercicio = fluxo_estudo.exercicio_atual(estado)
        if exercicio is None:
            fluxo_estudo.reiniciar_lista_de_exercicios(estado)
            exercicio = fluxo_estudo.exercicio_atual(estado)
        # Responde o valor esperado quando existe; nos demais tipos a
        # resposta é livre (resultado não avaliado de qualquer forma).
        resposta = exercicio.resposta_esperada or "resposta livre"
        fluxo_estudo.responder(estado, resposta)
        if exercicio.tipo == TIPO_PREVER_RESULTADO:
            respondidas_avaliadas += 1
        # Se o motor promoveu o aluno para o próximo nível, a contagem
        # foi reiniciada e o laço deve parar para não responder o novo
        # nível com as mesmas respostas.
        if respondidas_avaliadas >= quantidade_avaliadas:
            break
        if estado.houve_progressao:
            break


# ---------------------------------------------------------------------------
# Carregamento e progresso
# ---------------------------------------------------------------------------

def test_listar_habilidades_vem_do_banco(banco_de_teste):
    _ambiente(banco_de_teste)
    habilidades = fluxo_estudo.listar_habilidades()
    assert len(habilidades) == 1
    assert habilidades[0].nome == "Sequência de instruções"


def test_abrir_habilidade_cria_progresso_inicial(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    niveis = NIVEIS.listar_por_habilidade(
        _primeira_habilidade(seed).id
    )
    assert estado.progresso.nivel_id == niveis[0].id
    assert estado.progresso.status == "em_andamento"
    assert estado.nivel.id == niveis[0].id


def test_abrir_habilidade_nao_duplica_progresso(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    habilidade = _primeira_habilidade(seed)
    primeiro = fluxo_estudo.abrir_habilidade(aluno.id, habilidade.id)
    segundo = fluxo_estudo.abrir_habilidade(aluno.id, habilidade.id)
    assert segundo.progresso.id == primeiro.progresso.id
    # Apenas um registro para a combinação aluno + habilidade.
    existente = PROGRESSOS.buscar_por_aluno_e_habilidade(
        aluno.id, habilidade.id
    )
    assert existente.id == primeiro.progresso.id


def test_carregamento_do_nivel_e_exercicios_em_ordem(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    assert estado.exercicios  # nível 1 tem exercícios
    ordens = [e.ordem for e in estado.exercicios]
    assert ordens == sorted(ordens)
    assert fluxo_estudo.exercicio_atual(estado).id == estado.exercicios[0].id


def test_habilidade_inexistente_levanta_erro(banco_de_teste):
    aluno, _ = _ambiente(banco_de_teste)
    with pytest.raises(ValueError, match="Habilidade"):
        fluxo_estudo.abrir_habilidade(aluno.id, 999999)


# ---------------------------------------------------------------------------
# Sessão de estudo
# ---------------------------------------------------------------------------

def test_iniciar_sessao_cria_sessao_ativa(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    assert estado.sessao is None
    fluxo_estudo.iniciar_sessao(estado)
    assert estado.sessao is not None
    assert estado.sessao.aluno_id == aluno.id
    gravada = SESSOES.buscar_por_id(estado.sessao.id)
    assert gravada.status == "ativa"


def test_reiniciar_fluxo_encerra_sessao_anterior_e_cria_nova(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    fluxo_estudo.iniciar_sessao(estado)
    primeira_id = estado.sessao.id
    fluxo_estudo.iniciar_sessao(estado)  # reentrada no fluxo
    assert estado.sessao.id != primeira_id
    assert SESSOES.buscar_por_id(primeira_id).status == "encerrada"


def test_encerrar_sessao_preenche_termino(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    fluxo_estudo.iniciar_sessao(estado)
    sessao_id = estado.sessao.id
    fluxo_estudo.encerrar_sessao(estado)
    assert estado.sessao is None
    gravada = SESSOES.buscar_por_id(sessao_id)
    assert gravada.status == "encerrada"
    assert gravada.termino is not None


def test_encerrar_sessao_sem_sessao_eh_inofensivo(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    fluxo_estudo.encerrar_sessao(estado)  # não deve levantar exceção
    assert estado.sessao is None


# ---------------------------------------------------------------------------
# Resposta: fluxo completo avaliação -> tentativa -> progresso
# ---------------------------------------------------------------------------

def test_resposta_correta_registra_tentativa_e_avaliacao(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    fluxo_estudo.iniciar_sessao(estado)
    exercicio = fluxo_estudo.exercicio_atual(estado)
    fluxo_estudo.responder(estado, exercicio.resposta_esperada)

    assert estado.ultima_avaliacao.resultado == "correta"
    assert estado.corretas == 1
    # A sessão permanece ativa durante o fluxo.
    assert SESSOES.buscar_por_id(estado.sessao.id).status == "ativa"


def test_resposta_avanca_para_o_proximo_exercicio(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    fluxo_estudo.iniciar_sessao(estado)
    primeira = fluxo_estudo.exercicio_atual(estado)
    fluxo_estudo.responder(estado, "resposta qualquer")
    seguinte = fluxo_estudo.exercicio_atual(estado)
    assert seguinte.id != primeira.id
    assert estado.indice_exercicio == 1
    # A tentativa já registrada permanece (imutável).
    assert estado.corretas + estado.incorretas + estado.nao_avaliadas == 1


def test_fim_da_lista_gera_resumo_sem_exercicio(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    fluxo_estudo.iniciar_sessao(estado)
    for _ in estado.exercicios:
        fluxo_estudo.responder(estado, "qualquer")
    # Sem progressão (respostas erradas), a lista termina -> resumo.
    assert fluxo_estudo.exercicio_atual(estado) is None


def test_progressao_apos_dominio_muda_de_nivel_na_mesma_habilidade(
    banco_de_teste,
):
    aluno, seed = _ambiente(banco_de_teste)
    habilidade = _primeira_habilidade(seed)
    estado = fluxo_estudo.abrir_habilidade(aluno.id, habilidade.id)
    fluxo_estudo.iniciar_sessao(estado)
    niveis = NIVEIS.listar_por_habilidade(habilidade.id)

    # ACERTOS_PARA_DOMINIO respostas corretas avaliadas: ainda não domina,
    # pois a janela exige JANELA_DOMINIO tentativas avaliadas (5).
    _responder_ate(estado, ACERTOS_PARA_DOMINIO)
    assert estado.progresso.status == "em_andamento"

    # A avaliada que completa a janela dispara a progressão: o motor
    # promove o aluno para o próximo nível da MESMA habilidade.
    _responder_ate(estado, JANELA_DOMINIO)

    assert estado.houve_progressao is True
    assert estado.progresso.nivel_id == niveis[1].id
    assert estado.progresso.status == "em_andamento"
    assert estado.nivel.id == niveis[1].id
    # O resumo do novo nível começa zerado.
    assert estado.indice_exercicio == 0
    assert estado.corretas == 0
    # A sessão continua a mesma (o aluno não saiu do fluxo).
    assert estado.sessao is not None


def test_tentativas_permanecem_apos_progressao(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    fluxo_estudo.iniciar_sessao(estado)
    # Responde o suficiente para dominar (janela completa de avaliadas).
    _responder_ate(estado, JANELA_DOMINIO)
    assert estado.houve_progressao is True
    # O progresso avançou, mas o histórico de tentativas continua
    # armazenado (a evolução é reconstruída a partir dele).
    assert ACERTOS_PARA_DOMINIO <= JANELA_DOMINIO


def test_isolamento_entre_alunos(banco_de_teste):
    aluno_a, seed = _ambiente(banco_de_teste, nome="Aluno A")
    aluno_b = ALUNOS.inserir(Aluno(nome="Aluno B"))
    habilidade = _primeira_habilidade(seed)

    estado_a = fluxo_estudo.abrir_habilidade(aluno_a.id, habilidade.id)
    estado_b = fluxo_estudo.abrir_habilidade(aluno_b.id, habilidade.id)
    assert estado_a.progresso.id != estado_b.progresso.id

    # A responde corretamente 1 vez; o progresso de B não muda.
    fluxo_estudo.iniciar_sessao(estado_a)
    exercicio = fluxo_estudo.exercicio_atual(estado_a)
    fluxo_estudo.responder(estado_a, exercicio.resposta_esperada)

    progresso_b = PROGRESSOS.buscar_por_aluno_e_habilidade(
        aluno_b.id, habilidade.id
    )
    assert progresso_b.nivel_id == estado_b.progresso.nivel_id
    assert estado_a.progresso.nivel_id == estado_b.progresso.nivel_id


def test_isolamento_entre_habilidades(banco_de_teste):
    # O progresso é consultado SEMPRE por (aluno, habilidade): criar e
    # usar o progresso de uma habilidade não afeta outra.
    aluno, seed = _ambiente(banco_de_teste)
    habilidade = _primeira_habilidade(seed)
    estado = fluxo_estudo.abrir_habilidade(aluno.id, habilidade.id)
    fluxo_estudo.iniciar_sessao(estado)
    exercicio = fluxo_estudo.exercicio_atual(estado)
    fluxo_estudo.responder(estado, exercicio.resposta_esperada)
    progresso = PROGRESSOS.buscar_por_aluno_e_habilidade(
        aluno.id, habilidade.id
    )
    assert progresso.habilidade_id == habilidade.id


def test_responder_sem_sessao_levanta_erro(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    with pytest.raises(ValueError, match="sessão"):
        fluxo_estudo.responder(estado, "qualquer resposta")


# ---------------------------------------------------------------------------
# Tarefa 10A — BUG-02: ``houve_progressao`` reflete a ÚLTIMA resposta
# ---------------------------------------------------------------------------

def _responder_uma_vez(estado):
    """Responde o exercício corrente uma única vez (reinicia se preciso)."""
    exercicio = fluxo_estudo.exercicio_atual(estado)
    if exercicio is None:
        fluxo_estudo.reiniciar_lista_de_exercicios(estado)
        exercicio = fluxo_estudo.exercicio_atual(estado)
    fluxo_estudo.responder(estado, exercicio.resposta_esperada or "livre")


def test_houve_progressao_reflete_apenas_a_ultima_resposta(banco_de_teste):
    """A flag NÃO pode ficar presa em True depois da progressão.

    Cenário 1: resposta que causa progressão -> True.
    Cenário 2: resposta seguinte (novo nível) sem progressão -> False.
    Cenário 3: resposta posterior que causa progressão -> True.
    """
    aluno, seed = _ambiente(banco_de_teste)
    habilidade = _primeira_habilidade(seed)
    estado = fluxo_estudo.abrir_habilidade(aluno.id, habilidade.id)
    fluxo_estudo.iniciar_sessao(estado)

    # Cenário 1: janela completa de acertos promove o aluno.
    _responder_ate(estado, JANELA_DOMINIO)
    assert estado.houve_progressao is True

    # Cenário 2: a resposta seguinte (já no novo nível) NÃO progrediu.
    _responder_uma_vez(estado)
    assert estado.houve_progressao is False

    # Cenário 3: completar a janela novamente promove de novo.
    _responder_ate(estado, JANELA_DOMINIO)
    assert estado.houve_progressao is True


def test_resposta_sem_progressao_zera_flag_mesmo_apos_haber_progredido(
    banco_de_teste,
):
    """Resposta normal no novo nível devolve a flag para False."""
    aluno, seed = _ambiente(banco_de_teste)
    estado = fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )
    fluxo_estudo.iniciar_sessao(estado)
    _responder_ate(estado, JANELA_DOMINIO)
    assert estado.houve_progressao is True
    _responder_uma_vez(estado)
    assert estado.houve_progressao is False
    _responder_uma_vez(estado)
    assert estado.houve_progressao is False


# ---------------------------------------------------------------------------
# Tarefa 10A — BUG-03: resumo do nível recém-concluído
# ---------------------------------------------------------------------------

def test_abrir_habilidade_comeca_sem_resumo_pendente(banco_de_teste):
    """O estado inicial de uma habilidade não tem resumo pendente."""
    aluno, seed = _ambiente(banco_de_teste)
    estado = _abrir_estado_simples(aluno, seed)
    assert estado.resumo_nivel_concluido is None


def _abrir_estado_simples(aluno, seed):
    return fluxo_estudo.abrir_habilidade(
        aluno.id, _primeira_habilidade(seed).id
    )


def test_progressao_preserva_resumo_do_nivel_anterior(banco_de_teste):
    """O resumo pendente pertence ao nível que acabou de ser concluído.

    Os contadores do estado são zerados na progressão; o resumo deve
    manter os números do nível ANTERIOR para a UI exibi-los antes de
    entrar no novo nível.
    """
    aluno, seed = _ambiente(banco_de_teste)
    habilidade = _primeira_habilidade(seed)
    estado = fluxo_estudo.abrir_habilidade(aluno.id, habilidade.id)
    fluxo_estudo.iniciar_sessao(estado)
    niveis = NIVEIS.listar_por_habilidade(habilidade.id)

    _responder_ate(estado, JANELA_DOMINIO)
    assert estado.houve_progressao is True

    resumo = estado.resumo_nivel_concluido
    assert resumo is not None
    # O resumo é do nível concluído (o primeiro), não do novo.
    assert resumo["nivel_id"] == niveis[0].id
    assert resumo["situacao"] == "Nível concluído"
    # Os números batem com o total informado e são maiores que zero.
    assert resumo["total_respondidos"] > 0
    assert (
        resumo["corretas"]
        + resumo["incorretas"]
        + resumo["nao_avaliadas"]
        == resumo["total_respondidos"]
    )
    # O novo nível já está no estado, mas os contadores começam zerados.
    assert estado.nivel.id == niveis[1].id
    assert estado.corretas == 0
    assert estado.incorretas == 0
    assert estado.nao_avaliadas == 0
    assert estado.indice_exercicio == 0


def test_resumo_pendente_nao_eh_criado_sem_progressao(banco_de_teste):
    """Respostas normais (sem domínio) não criam resumo pendente."""
    aluno, seed = _ambiente(banco_de_teste)
    estado = _abrir_estado_simples(aluno, seed)
    fluxo_estudo.iniciar_sessao(estado)
    _responder_uma_vez(estado)
    assert estado.houve_progressao is False
    assert estado.resumo_nivel_concluido is None