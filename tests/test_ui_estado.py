"""Testes da lógica nova da Tarefa 09 (refinamento da experiência).

Cobrem apenas a lógica NÃO visual introducida nesta tarefa — não são
testados detalhes de apariencia (cores, tamanhos), mas o comportamento
que as telas utilizam:

    * ``posicao_do_nivel``  — "Nível X de Y" da tela do nível e do resumo;
    * ``resumo_do_progresso`` — texto de estado de cada habilidade na
      lista (não iniciada / em andamento / concluída);
    * limpeza de estado ao reabrir uma habilidade (sem sessão nem
      referências da habilidade anterior);
    * encerramento de sessão seguro quando não há sessão ativa.

Todos os testes usam o banco TEMPORÁRIO da fixture ``banco_de_teste``.
"""

from app.models import Aluno, Habilidade, Modulo, Nivel
from app.repositories import (
    AlunoRepository,
    HabilidadeRepository,
    ModuloRepository,
    NivelRepository,
)
from app.services import carga_inicial, fluxo_estudo
from app.services.motor_pedagogico import STATUS_CONCLUIDO

ALUNOS = AlunoRepository()
MODULOS = ModuloRepository()
HABILIDADES = HabilidadeRepository()
NIVEIS = NivelRepository()


def _ambiente(banco_de_teste, nome="Aluna UI"):
    """Cria aluno + currículo e devuelve (alumno, seed)."""
    carga_inicial.carregar_curriculo_inicial()
    aluno = ALUNOS.inserir(Aluno(nome=nome))
    return aluno, carga_inicial.carregar_curriculo_inicial()


def _abrir_estado(aluno, seed):
    habilidade = seed["habilidade"]
    return fluxo_estudo.abrir_habilidade(aluno.id, habilidade.id)


# ---------------------------------------------------------------------------
# Posição do nível "X de Y"
# ---------------------------------------------------------------------------

def test_posicao_do_nivel_inicial_eh_1_de_3(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    estado = _abrir_estado(aluno, seed)
    posicao, total = fluxo_estudo.posicao_do_nivel(estado)
    assert posicao == 1
    assert total == 3


def test_posicao_do_nivel_avanca_depois_da_progressao(banco_de_teste):
    # Verifica o dato informativo que a tela mostra após a progressão
    # ("Nível 2 de 3"): o motor segue sendo o único responsável de mover
    # o progresso; aqui apenas se confirma que a posição é derivada do
    # nível atual apuntado pelo progresso.
    aluno, seed = _ambiente(banco_de_teste)
    estado = _abrir_estado(aluno, seed)
    # Simula o que o motor faría após dominar o nível 1: avançar o
    # progresso ao nível 2 (mesmo registro, respeitando UNIQUE).
    niveis = NIVEIS.listar_por_habilidade(seed["habilidade"].id)
    estado.progresso.nivel_id = niveis[1].id
    estado.progresso.status = "em_andamento"
    estado.nivel = NIVEIS.buscar_por_id(niveis[1].id)
    posicao, total = fluxo_estudo.posicao_do_nivel(estado)
    assert posicao == 2
    assert total == 3


# ---------------------------------------------------------------------------
# Texto de estado del progresso (lista de habilidades)
# ---------------------------------------------------------------------------

def test_resumo_do_progresso_sem_progresso_indica_inicio(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    texto = fluxo_estudo.resumo_do_progresso(
        aluno.id, seed["habilidade"].id
    )
    # Ainda não foi aberta a habilidade -> ainda não existe progresso.
    assert "primeiro nível" in texto


def test_resumo_do_progresso_em_andamento(banco_de_teste):
    aluno, seed = _ambiente(banco_de_teste)
    fluxo_estudo.abrir_habilidade(aluno.id, seed["habilidade"].id)
    texto = fluxo_estudo.resumo_do_progresso(
        aluno.id, seed["habilidade"].id
    )
    assert "Em andamento" in texto
    assert "nível atual" in texto


def test_resumo_do_progresso_concluida(banco_de_teste):
    from app.repositories import ProgressoAlunoRepository

    aluno, seed = _ambiente(banco_de_teste)
    estado = _abrir_estado(aluno, seed)
    # Persiste a marcação de concluído (o que o motor faria no último
    # nível) para verificar o texto da lista de habilidades.
    estado.progresso.status = STATUS_CONCLUIDO
    ProgressoAlunoRepository().atualizar(estado.progresso)
    texto = fluxo_estudo.resumo_do_progresso(
        aluno.id, seed["habilidade"].id
    )
    assert "Concluída" in texto


# ---------------------------------------------------------------------------
# Limpeza de estado ao abrir outra habilidade / sair do fluxo
# ---------------------------------------------------------------------------

def test_abrir_habilidade_devolve_estado_sem_sessao(banco_de_teste):
    """O estado inicial de uma habilidade não deve ter sessão ativa."""
    aluno, seed = _ambiente(banco_de_teste)
    estado = _abrir_estado(aluno, seed)
    assert estado.sessao is None
    assert estado.houve_progressao is False
    assert estado.corretas == 0


def test_abrir_nova_habilidade_nao_arrasta_a_anterior(banco_de_teste):
    """Ao abrir outra habilidade, o novo estado não mantém referências
    do estado anterior (nível, exercícios, sessão)."""
    aluno, seed = _ambiente(banco_de_teste)
    # Cria uma segunda habilidade (com seu módulo e um nível).
    modulo = MODULOS.inserir(
        Modulo(nome="Módulo extra", descricao="", ordem=9)
    )
    habilidade_extra = HABILIDADES.inserir(
        Habilidade(
            modulo_id=modulo.id,
            nome="Habilidade extra",
            descricao="Para testes",
            ordem=9,
        )
    )
    NIVEIS.inserir(
        Nivel(habilidade_id=habilidade_extra.id, nome="N1", ordem=1)
    )

    estado_primera = _abrir_estado(aluno, seed)
    # Abre a habilidade extra e confirma que tudo pertence a ELA.
    estado_segunda = fluxo_estudo.abrir_habilidade(
        aluno.id, habilidade_extra.id
    )
    assert estado_segunda.habilidade.id == habilidade_extra.id
    assert estado_segunda.habilidade.id != estado_primera.habilidade.id
    # Não deve conservar a sessão nem referências do estado anterior.
    assert estado_segunda.sessao is None
    assert estado_segunda.historico == []
    assert estado_segunda.nivel.habilidade_id == habilidade_extra.id


def test_encerrar_sessao_sem_sessao_ativa_eh_seguro(banco_de_teste):
    """Encerrar sem sessão ativa não deve lançar exceção."""
    aluno, seed = _ambiente(banco_de_teste)
    estado = _abrir_estado(aluno, seed)
    assert estado.sessao is None
    fluxo_estudo.encerrar_sessao(estado)  # não deve falhar
    assert estado.sessao is None