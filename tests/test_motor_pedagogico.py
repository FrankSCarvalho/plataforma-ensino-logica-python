"""Testes do motor pedagógico (Tarefa 07).

Cobrem o critério de domínio (janela de tentativas avaliadas), a
progressão entre níveis da mesma habilidade, a criação do progresso
inicial, o tratamento de ``nao_avaliada``/``parcialmente_correta`` e o
fluxo completo resposta -> avaliação -> tentativa -> motor -> progresso.

Todos os testes usam o banco TEMPORÁRIO da fixture ``banco_de_teste``.
"""

import pytest

from app.models import (
    RESULTADO_CORRETA,
    RESULTADO_INCORRETA,
    RESULTADO_NAO_AVALIADA,
    RESULTADO_PARCIALMENTE_CORRETA,
    Aluno,
    SessaoEstudo,
    Tentativa,
)
from app.repositories import (
    AlunoRepository,
    ExercicioRepository,
    NivelRepository,
    ProgressoAlunoRepository,
    SessaoEstudoRepository,
    TentativaRepository,
)
from app.services import carga_inicial
from app.services.motor_pedagogico import (
    ACERTOS_PARA_DOMINIO,
    JANELA_DOMINIO,
    STATUS_CONCLUIDO,
    STATUS_EM_ANDAMENTO,
    avaliar_progressao,
    garantir_progresso_inicial,
    processar_resposta,
)

NIVEIS = NivelRepository()
EXERCICIOS = ExercicioRepository()
ALUNOS = AlunoRepository()
SESSOES = SessaoEstudoRepository()
TENTATIVAS = TentativaRepository()
PROGRESSOS = ProgressoAlunoRepository()


# ---------------------------------------------------------------------------
# Cenário compartilhado
# ---------------------------------------------------------------------------

def _cenario(banco_de_teste):
    """Carrega o currículo inicial e cria alunos/sessões de teste."""
    seed = carga_inicial.carregar_curriculo_inicial()
    habilidade = seed["habilidade"]
    aluno = ALUNOS.inserir(Aluno(nome="Aluno Motor"))
    outro_aluno = ALUNOS.inserir(Aluno(nome="Outro Aluno"))
    sessao = SESSOES.inserir(SessaoEstudo(aluno_id=aluno.id))
    sessao_outro = SESSOES.inserir(SessaoEstudo(aluno_id=outro_aluno.id))
    niveis = NIVEIS.listar_por_habilidade(habilidade.id)
    exercicios = {
        nivel.id: EXERCICIOS.listar_por_nivel(nivel.id) for nivel in niveis
    }
    return {
        "habilidade": habilidade,
        "aluno": aluno,
        "outro_aluno": outro_aluno,
        "sessao": sessao,
        "sessao_outro": sessao_outro,
        "niveis": niveis,          # ordenados por ``ordem``
        "exercicios": exercicios,  # nivel_id -> lista de exercícios
    }


def _registrar(
    cenario,
    resultado: str,
    nivel_index: int = 0,
    aluno_id: int | None = None,
    sessao_id: int | None = None,
    exercicio_index: int = 0,
) -> Tentativa:
    """Insere uma tentativa com resultado fixo (histórico determinístico).

    Usada para montar históricos de teste sem depender do avaliador: o
    foco aqui é a interpretação dos resultados pelo motor.
    """
    nivel = cenario["niveis"][nivel_index]
    exercicio = cenario["exercicios"][nivel.id][exercicio_index]
    return TENTATIVAS.inserir(
        Tentativa(
            sessao_id=sessao_id or cenario["sessao"].id,
            aluno_id=aluno_id or cenario["aluno"].id,
            exercicio_id=exercicio.id,
            resposta="resposta de teste",
            resultado=resultado,
        )
    )


def _preencher(cenario, resultados: list[str], nivel_index: int = 0) -> None:
    """Insere uma sequência de tentativas (a última é a mais recente)."""
    for resultado in resultados:
        _registrar(cenario, resultado, nivel_index=nivel_index)


# ---------------------------------------------------------------------------
# Regra explícita e progresso inicial
# ---------------------------------------------------------------------------

def test_regra_de_dominio_esta_centralizada():
    # A regra é explícita e configurável em um único lugar.
    assert JANELA_DOMINIO == 5
    assert ACERTOS_PARA_DOMINIO == 4


def test_aluno_sem_progresso_recebe_o_primeiro_nivel(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    primeiro = cenario["niveis"][0]
    progresso = garantir_progresso_inicial(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert progresso.nivel_id == primeiro.id
    assert progresso.status == STATUS_EM_ANDAMENTO
    assert PROGRESSOS.listar() != []  # registro gravado no banco


def test_progresso_inicial_nao_eh_duplicado(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    primeiro = garantir_progresso_inicial(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    segundo = garantir_progresso_inicial(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert primeiro.id == segundo.id
    assert len(PROGRESSOS.listar()) == 1  # UNIQUE(aluno_id, habilidade_id)


# ---------------------------------------------------------------------------
# Critério de domínio — janela de tentativas
# ---------------------------------------------------------------------------

def test_menos_de_cinco_tentativas_permite_em_andamento(banco_de_teste):
    # 4 corretas < janela: permanece em_andamento mesmo com 100% de acerto.
    cenario = _cenario(banco_de_teste)
    _preencher(cenario, [RESULTADO_CORRETA] * 4)
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is False
    assert resultado.progresso.status == STATUS_EM_ANDAMENTO
    assert resultado.progresso.nivel_id == cenario["niveis"][0].id


def test_quatro_corretas_em_cinco_promove_nivel(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    _preencher(
        cenario,
        [
            RESULTADO_INCORRETA,
            RESULTADO_CORRETA,
            RESULTADO_CORRETA,
            RESULTADO_CORRETA,
            RESULTADO_CORRETA,
        ],
    )
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is True
    assert resultado.nivel_concluido_id == cenario["niveis"][0].id
    assert resultado.proximo_nivel_id == cenario["niveis"][1].id
    assert resultado.progresso.nivel_id == cenario["niveis"][1].id
    assert resultado.progresso.status == STATUS_EM_ANDAMENTO


def test_tres_corretas_em_cinco_nao_promove(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    _preencher(
        cenario,
        [
            RESULTADO_INCORRETA,
            RESULTADO_INCORRETA,
            RESULTADO_CORRETA,
            RESULTADO_CORRETA,
            RESULTADO_CORRETA,
        ],
    )
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is False
    assert resultado.progresso.nivel_id == cenario["niveis"][0].id


def test_cinco_corretas_promove(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    _preencher(cenario, [RESULTADO_CORRETA] * 5)
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is True
    assert resultado.proximo_nivel_id == cenario["niveis"][1].id


def test_cinco_parcialmente_corretas_nao_promove(banco_de_teste):
    # parcialmente_correta ocupa a janela mas NÃO conta como acerto.
    cenario = _cenario(banco_de_teste)
    _preencher(cenario, [RESULTADO_PARCIALMENTE_CORRETA] * 5)
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is False


def test_quatro_corretas_mais_parcial_nao_promove(banco_de_teste):
    # Janela completa (5 avaliadas) com 3 corretas + 2 parciais: como
    # parcialmente_correta NÃO conta como acerto, há apenas 3 acertos
    # (< ACERTOS_PARA_DOMINIO) -> não promove.
    cenario = _cenario(banco_de_teste)
    _preencher(
        cenario,
        [
            RESULTADO_PARCIALMENTE_CORRETA,
            RESULTADO_PARCIALMENTE_CORRETA,
            RESULTADO_CORRETA,
            RESULTADO_CORRETA,
            RESULTADO_CORRETA,
        ],
    )
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is False


def test_nao_avaliadas_ficam_fora_da_janela(banco_de_teste):
    # 4 corretas + 3 nao_avaliada: a janela só contém 4 AVALIADAS ->
    # permanece em_andamento (nao_avaliada não participa da contagem).
    cenario = _cenario(banco_de_teste)
    _preencher(cenario, [RESULTADO_NAO_AVALIADA] * 3)
    _preencher(cenario, [RESULTADO_CORRETA] * 4)
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is False

    # Com mais uma INCORRETA avaliada, a janela fecha com 4 corretas ->
    # domínio (prova que as nao_avaliadas ficaram fora da janela).
    _registrar(cenario, RESULTADO_INCORRETA)
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is True


# ---------------------------------------------------------------------------
# Janela deslizante e isolamento do histórico
# ---------------------------------------------------------------------------

def test_tentativas_antigas_fora_da_janela_nao_interferem(banco_de_teste):
    # 5 antigas INCORRETAS + 5 recentes com 4 corretas -> a janela pega
    # só as recentes -> domínio.
    cenario = _cenario(banco_de_teste)
    _preencher(cenario, [RESULTADO_INCORRETA] * 5)
    _preencher(
        cenario,
        [
            RESULTADO_CORRETA,
            RESULTADO_CORRETA,
            RESULTADO_CORRETA,
            RESULTADO_CORRETA,
            RESULTADO_INCORRETA,
        ],
    )
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is True


def test_acertos_antigos_fora_da_janela_nao_garantem_dominio(banco_de_teste):
    # Caso inverso: 5 antigas CORRETAS + 5 recentes INCORRETAS -> a janela
    # pega só as recentes -> NÃO há domínio (desempenho recente manda).
    cenario = _cenario(banco_de_teste)
    _preencher(cenario, [RESULTADO_CORRETA] * 5)
    _preencher(cenario, [RESULTADO_INCORRETA] * 5)
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is False


def test_tentativas_de_outro_aluno_nao_interferem(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    # O outro aluno tem 5 corretas no nível 1...
    for _ in range(5):
        _registrar(
            cenario,
            RESULTADO_CORRETA,
            aluno_id=cenario["outro_aluno"].id,
            sessao_id=cenario["sessao_outro"].id,
        )
    # ...mas o aluno em análise não tem nenhuma tentativa.
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is False


def test_tentativas_de_outro_nivel_nao_interferem(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    # 5 corretas registradas no NÍVEL 2...
    _preencher(cenario, [RESULTADO_CORRETA] * 5, nivel_index=1)
    # ...mas o aluno está no nível 1: não há domínio do nível 1.
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is False
    assert resultado.progresso.nivel_id == cenario["niveis"][0].id


# ---------------------------------------------------------------------------
# Último nível, repetição e preservação do histórico
# ---------------------------------------------------------------------------

def test_dominio_do_ultimo_nivel_conclui_sem_proximo(banco_de_teste):
    # O aluno "pula" para o último nível e o domina: status concluido,
    # sem próximo nível e sem mudar de nível.
    cenario = _cenario(banco_de_teste)
    niveis = cenario["niveis"]
    ultimo = niveis[-1]
    garantir_progresso_inicial(cenario["aluno"].id, cenario["habilidade"].id)
    # Atalho de teste: move o progresso diretamente para o último nível.
    progresso = PROGRESSOS.listar()[0]
    progresso.nivel_id = ultimo.id
    PROGRESSOS.atualizar(progresso)

    _preencher(cenario, [RESULTADO_CORRETA] * 5, nivel_index=len(niveis) - 1)
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is True
    assert resultado.nivel_concluido_id == ultimo.id
    assert resultado.proximo_nivel_id is None          # não há próximo nível
    assert resultado.progresso.nivel_id == ultimo.id   # permanece no último
    assert resultado.progresso.status == STATUS_CONCLUIDO


def test_sem_dominio_permite_repeticao_sem_reiniciar_historico(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    _preencher(
        cenario,
        [
            RESULTADO_CORRETA,
            RESULTADO_INCORRETA,
            RESULTADO_CORRETA,
            RESULTADO_INCORRETA,
            RESULTADO_CORRETA,
        ],
    )
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    # Permanece no nível, sem apagar tentativas e sem reduzir o nível.
    assert resultado.dominio_atingido is False
    assert resultado.progresso.nivel_id == cenario["niveis"][0].id
    assert resultado.progresso.status == STATUS_EM_ANDAMENTO
    assert len(TENTATIVAS.listar()) == 5  # histórico intacto


def test_progressao_nao_duplica_progresso(banco_de_teste):
    # Após a progressão, continua existindo UM único registro por
    # aluno + habilidade (o mesmo registro é atualizado).
    cenario = _cenario(banco_de_teste)
    _preencher(cenario, [RESULTADO_CORRETA] * 5)
    avaliar_progressao(cenario["aluno"].id, cenario["habilidade"].id)
    todos = PROGRESSOS.listar()
    assert len(todos) == 1
    assert todos[0].nivel_id == cenario["niveis"][1].id


def test_tentativas_anteriores_permanecem_apos_progressao(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    _preencher(cenario, [RESULTADO_CORRETA] * 5)
    resultado = avaliar_progressao(
        cenario["aluno"].id, cenario["habilidade"].id
    )
    assert resultado.dominio_atingido is True
    # As 5 tentativas que geraram o domínio continuam no banco, intactas.
    assert len(TENTATIVAS.listar()) == 5
    for tentativa in TENTATIVAS.listar():
        assert tentativa.resultado == RESULTADO_CORRETA


# ---------------------------------------------------------------------------
# Fluxo completo: resposta -> avaliação -> tentativa -> motor -> progresso
# ---------------------------------------------------------------------------

def test_fluxo_completo_registra_e_promove(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    exercicio = cenario["exercicios"][cenario["niveis"][0].id][0]
    # O primeiro exercício do nível 1 é prever_resultado ("Bola").
    for _ in range(4):
        processar_resposta(
            sessao_id=cenario["sessao"].id,
            aluno_id=cenario["aluno"].id,
            exercicio_id=exercicio.id,
            resposta="Bola",           # correta (avaliador real)
        )
    # Apenas 4 tentativas: ainda em_andamento (janela incompleta).
    progresso = PROGRESSOS.listar()[0]
    assert progresso.nivel_id == cenario["niveis"][0].id
    assert progresso.status == STATUS_EM_ANDAMENTO

    # 5ª tentativa correta fecha a janela -> domínio -> próximo nível.
    final = processar_resposta(
        sessao_id=cenario["sessao"].id,
        aluno_id=cenario["aluno"].id,
        exercicio_id=exercicio.id,
        resposta="Bola",
    )
    assert final.progressao.dominio_atingido is True
    assert final.progressao.progresso.nivel_id == cenario["niveis"][1].id
    assert final.registro.tentativa.resultado == RESULTADO_CORRETA
    # Histórico completo preservado: 5 tentativas no banco.
    assert len(TENTATIVAS.listar()) == 5


def test_fluxo_completo_resposta_incorreta_mantem_nivel(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    exercicio = cenario["exercicios"][cenario["niveis"][0].id][0]
    for _ in range(5):
        final = processar_resposta(
            sessao_id=cenario["sessao"].id,
            aluno_id=cenario["aluno"].id,
            exercicio_id=exercicio.id,
            resposta="errado",         # incorreta (avaliador real)
        )
    assert final.progressao.dominio_atingido is False
    assert final.progressao.progresso.nivel_id == cenario["niveis"][0].id
    assert final.progressao.progresso.status == STATUS_EM_ANDAMENTO