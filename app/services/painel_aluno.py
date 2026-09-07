"""Serviço do Painel do Aluno (Tarefa 11).

Reúne e transforma dados existentes do banco em informações adequadas
para a tela do painel, SEM conter SQL direto e SEM componentes Flet:

    UI (painel_aluno_view.py)
        ↓
    PainelAlunoService  (este módulo)
        ↓
    Repositories existentes (ProgressoAlunoRepository,
                            HabilidadeRepository,
                            NivelRepository)
        ↓
    SQLite

As estruturas de dados são simples ``dataclass`` (testáveis sem Flet).
"""

from dataclasses import dataclass

from app.repositories import (
    HabilidadeRepository,
    NivelRepository,
    ProgressoAlunoRepository,
)
from app.services.motor_pedagogico import STATUS_CONCLUIDO


@dataclass
class ResumoDoAluno:
    """Resumo quantitativo do progresso do aluno nas habilidades."""
    total_habilidades: int
    nao_iniciadas: int
    em_andamento: int
    concluidas: int


@dataclass
class SituacaoDaHabilidade:
    """Situação de uma habilidade para o aluno."""
    habilidade_id: int
    nome: str
    descricao: str
    situacao: str                # "Não iniciada", "Em andamento", "Concluída"
    nivel_atual: str | None      # ex.: "Nível 2 de 3" ou None


@dataclass
class PainelDoAluno:
    """Dados completos do painel do aluno."""
    aluno_id: int
    aluno_nome: str
    resumo: ResumoDoAluno
    habilidades: list[SituacaoDaHabilidade]
    proximo_passo: str


def obter_painel_do_aluno(aluno_id: int, aluno_nome: str) -> PainelDoAluno:
    """Reúne os dados do painel do aluno a partir dos repositories.

    Percorre todas as habilidades do currículo e, para cada uma, consulta
    o progresso do aluno. Monta o resumo quantitativo, a lista de situações
    e a orientação de próximo passo.
    """
    repositorio_habilidades = HabilidadeRepository()
    repositorio_progresso = ProgressoAlunoRepository()
    repositorio_niveis = NivelRepository()

    habilidades = repositorio_habilidades.listar()

    situacoes: list[SituacaoDaHabilidade] = []
    nao_iniciadas = 0
    em_andamento = 0
    concluidas = 0

    for habilidade in habilidades:
        progresso = repositorio_progresso.buscar_por_aluno_e_habilidade(
            aluno_id, habilidade.id
        )

        if progresso is None:
            situacao = "Não iniciada"
            nivel_atual = None
            nao_iniciadas += 1
        elif progresso.status == STATUS_CONCLUIDO:
            situacao = "Concluída"
            nivel_atual = None
            concluidas += 1
        else:
            situacao = "Em andamento"
            nivel_atual = _nivel_atual_texto(
                repositorio_niveis, habilidade.id, progresso.nivel_id
            )
            em_andamento += 1

        situacoes.append(
            SituacaoDaHabilidade(
                habilidade_id=habilidade.id,
                nome=habilidade.nome,
                descricao=habilidade.descricao or "",
                situacao=situacao,
                nivel_atual=nivel_atual,
            )
        )

    resumo = ResumoDoAluno(
        total_habilidades=len(habilidades),
        nao_iniciadas=nao_iniciadas,
        em_andamento=em_andamento,
        concluidas=concluidas,
    )

    return PainelDoAluno(
        aluno_id=aluno_id,
        aluno_nome=aluno_nome,
        resumo=resumo,
        habilidades=situacoes,
        proximo_passo=_proximo_passo(nao_iniciadas, em_andamento, concluidas),
    )


def _nivel_atual_texto(
    repositorio_niveis: NivelRepository,
    habilidade_id: int,
    nivel_atual_id: int,
) -> str | None:
    """Calcula o texto 'Nível X de Y' a partir do progresso do aluno."""
    niveis = repositorio_niveis.listar_por_habilidade(habilidade_id)
    if not niveis:
        return None
    posicao = next(
        (i + 1 for i, n in enumerate(niveis) if n.id == nivel_atual_id),
        None,
    )
    if posicao is None:
        return None
    return f"Nível {posicao} de {len(niveis)}"


def _proximo_passo(
    nao_iniciadas: int, em_andamento: int, concluidas: int
) -> str:
    """Orientação simples de navegação baseada nos estados existentes."""
    if em_andamento > 0:
        return "Continue seus estudos."
    if nao_iniciadas > 0:
        return "Escolha uma habilidade para começar."
    if concluidas > 0:
        return "Você concluiu todas as habilidades disponíveis."
    return "Nenhuma habilidade disponível no momento."
