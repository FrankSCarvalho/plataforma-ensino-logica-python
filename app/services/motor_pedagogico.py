"""Motor pedagógico da plataforma (Tarefa 07).

Primeira versão do componente que interpreta o histórico de tentativas
e decide a progressão do aluno ENTRE NÍVEIS DA MESMA HABILIDADE.

Responsabilidades (e não-responsabilidades):

    * interpreta resultados de tentativas JÁ AVALIADAS e armazenadas no
      banco — o avaliador (Tarefa 06) continua independente: este módulo
      não corrige respostas;
    * decide quando um nível está concluído (critério de domínio);
    * cria o progresso inicial quando o aluno ainda não o possui;
    * promove o aluno ao próximo nível da MESMA habilidade (nunca avança
      para outra habilidade);
    * NÃO decide qual exercício apresentar, NÃO pontua, NÃO usa IA,
      NÃO implementa diagnóstico, dificuldade adaptativa ou repetição
      espaçada — decisões de tarefas futuras.

Regra de domínio (centralizada nas constantes abaixo, determinística e
fácil de alterar):

    * considera apenas as tentativas AVALIADAS mais recentes do nível;
    * ``nao_avaliada`` não participa da contagem (fica fora da janela);
    * ``parcialmente_correta`` participa da janela mas NÃO conta como
      acerto (não satisfaz o domínio nesta versão);
    * com menos de ``JANELA_DOMINIO`` tentativas avaliadas, o nível
      permanece ``em_andamento``;
    * o nível é concluído com pelo menos ``ACERTOS_PARA_DOMINIO``
      respostas ``correta`` dentro da janela.

Consistência tentativa + progresso: as operações são executadas NESSA
ORDEM (tentativa primeiro, progresso depois) e qualquer falha PROPAGA —
não há captura silenciosa de exceções. Como a decisão do motor é
determinística a partir do histórico, reexecutar ``avaliar_progressao``
reconstrói o estado correto do progresso sem duplicar tentativas (a
tentativa é imutável e a atualização do progresso é idempotente).
"""

from dataclasses import dataclass

from app.models import (
    RESULTADO_CORRETA,
    Nivel,
    ProgressoAluno,
)
from app.repositories import (
    NivelRepository,
    ProgressoAlunoRepository,
    TentativaRepository,
)
from app.services.registro_tentativas import (
    RegistroDeTentativa,
    registrar_tentativa,
)

# ---------------------------------------------------------------------------
# Configuração do critério de domínio (sem números mágicos espalhados).
# Alterar estes valores ajusta a regra em todo o sistema.
# ---------------------------------------------------------------------------
JANELA_DOMINIO = 5          # últimas N tentativas avaliadas consideradas
ACERTOS_PARA_DOMINIO = 4    # acertos mínimos dentro da janela

# Status possíveis do progresso (mesmos valores usados desde a Tarefa 04).
STATUS_EM_ANDAMENTO = "em_andamento"
STATUS_CONCLUIDO = "concluido"


@dataclass
class ResultadoProgressao:
    """Resultado da análise do motor pedagógico para uma habilidade.

    ``nivel_concluido_id`` indica o nível que atingiu domínio (``None``
    quando ainda não atingiu); ``proximo_nivel_id`` indica o nível de
    destino da progressão (``None`` quando o nível concluído era o último
    da habilidade ou quando não houve domínio).
    """

    dominio_atingido: bool
    nivel_concluido_id: int | None
    proximo_nivel_id: int | None
    progresso: ProgressoAluno


@dataclass
class RegistroComProgressao:
    """Resultado do fluxo completo: tentativa registrada + progressão."""

    registro: RegistroDeTentativa
    progressao: ResultadoProgressao


def contar_acertos(tentativas: list) -> int:
    """Conta quantas tentativas da lista têm resultado ``correta``."""
    return sum(1 for t in tentativas if t.resultado == RESULTADO_CORRETA)


def atingiu_dominio(tentativas_avaliadas_recentes: list) -> bool:
    """Aplica o critério de domínio sobre a janela de tentativas.

    ``tentativas_avaliadas_recentes`` deve estar ordenada da MAIS RECENTE
    para a mais antiga (ordem devolvida por
    ``TentativaRepository.listar_avaliadas_do_aluno_por_nivel``).

    Regras: a janela só é considerada completa quando existem pelo menos
    ``JANELA_DOMINIO`` tentativas avaliadas; ``parcialmente_correta``
    ocupa lugar na janela mas não conta como acerto.
    """
    janela = tentativas_avaliadas_recentes[:JANELA_DOMINIO]
    if len(janela) < JANELA_DOMINIO:
        # Histórico insuficiente: o nível permanece em_andamento.
        return False
    return contar_acertos(janela) >= ACERTOS_PARA_DOMINIO


def _niveis_ordenados(habilidade_id: int) -> list[Nivel]:
    """Devolve os níveis da habilidade em ordem pedagógica (``ordem``)."""
    niveis = NivelRepository().listar_por_habilidade(habilidade_id)
    if not niveis:
        raise ValueError(
            f"A habilidade {habilidade_id} não possui níveis cadastrados."
        )
    return niveis


def garantir_progresso_inicial(
    aluno_id: int, habilidade_id: int
) -> ProgressoAluno:
    """Garante que o aluno possui progresso na habilidade informada.

    Se ainda não existe registro em ``progresso_aluno`` para a combinação
    (aluno, habilidade), cria um apontando para o PRIMEIRO nível da
    habilidade com status ``em_andamento``. Se já existe, apenas o
    devolve — nunca cria um segundo registro (a restrição
    ``UNIQUE(aluno_id, habilidade_id)`` é respeitada).
    """
    repositorio_progresso = ProgressoAlunoRepository()

    existente = repositorio_progresso.buscar_por_aluno_e_habilidade(
        aluno_id, habilidade_id
    )
    if existente is not None:
        return existente

    primeiro_nivel = _niveis_ordenados(habilidade_id)[0]
    return repositorio_progresso.inserir(
        ProgressoAluno(
            aluno_id=aluno_id,
            habilidade_id=habilidade_id,
            nivel_id=primeiro_nivel.id,
            status=STATUS_EM_ANDAMENTO,
        )
    )


def avaliar_progressao(aluno_id: int, habilidade_id: int) -> ResultadoProgressao:
    """Analisa o histórico e promove o aluno quando o domínio é atingido.

    Fluxo:

        1. garante a existência do progresso (primeiro nível, se novo);
        2. consulta no banco as tentativas avaliadas do nível atual;
        3. aplica o critério de domínio (janela configurável);
        4. sem domínio: nada é alterado (o aluno continua praticando);
        5. com domínio: marca o nível atual como ``concluido`` e, se
           existir próximo nível NA MESMA habilidade, move o progresso
           para ele com status ``em_andamento``. No último nível, o
           progresso permanece ``concluido`` (não há avanço para outra
           habilidade nesta versão).

    As tentativas nunca são apagadas nem alteradas — o histórico é a
    fonte da decisão e permanece intacto.
    """
    repositorio_progresso = ProgressoAlunoRepository()
    repositorio_tentativas = TentativaRepository()

    progresso = garantir_progresso_inicial(aluno_id, habilidade_id)

    # Tentativas avaliadas do nível atual, da mais recente para a mais antiga.
    avaliadas = repositorio_tentativas.listar_avaliadas_do_aluno_por_nivel(
        aluno_id, progresso.nivel_id
    )
    if not atingiu_dominio(avaliadas):
        # Sem domínio: permanece no nível atual, sem reiniciar histórico
        # e sem reduzir o nível.
        return ResultadoProgressao(
            dominio_atingido=False,
            nivel_concluido_id=None,
            proximo_nivel_id=None,
            progresso=progresso,
        )

    # ---- Domínio atingido ---------------------------------------------
    nivel_concluido_id = progresso.nivel_id
    progresso.status = STATUS_CONCLUIDO
    repositorio_progresso.atualizar(progresso)

    niveis = _niveis_ordenados(habilidade_id)
    indice_atual = next(
        i for i, n in enumerate(niveis) if n.id == nivel_concluido_id
    )

    # Progressão restrita aos níveis da MESMA habilidade.
    if indice_atual + 1 < len(niveis):
        proximo_nivel = niveis[indice_atual + 1]
        # O MESMO registro é atualizado (não se cria um novo por nível).
        progresso.nivel_id = proximo_nivel.id
        progresso.status = STATUS_EM_ANDAMENTO
        repositorio_progresso.atualizar(progresso)
        return ResultadoProgressao(
            dominio_atingido=True,
            nivel_concluido_id=nivel_concluido_id,
            proximo_nivel_id=proximo_nivel.id,
            progresso=progresso,
        )

    # Último nível da habilidade: permanece concluído, sem próximo nível.
    return ResultadoProgressao(
        dominio_atingido=True,
        nivel_concluido_id=nivel_concluido_id,
        proximo_nivel_id=None,
        progresso=progresso,
    )


def processar_resposta(
    sessao_id: int,
    aluno_id: int,
    exercicio_id: int,
    resposta: str,
    tempo_resolucao_segundos: int = 0,
) -> RegistroComProgressao:
    """Operação de alto nível: resposta -> tentativa -> progressão.

    Fluxo (as etapas de avaliação e registro são reutilizadas do serviço
    da Tarefa 06 — a avaliação permanece independente deste módulo):

        aluno responde -> avaliador -> tentativa registrada
        -> motor consulta o histórico -> verifica domínio -> atualiza progresso

    A tentativa é gravada PRIMEIRO e a progressão DEPOIS; exceções
    propagam sem captura silenciosa (ver nota de consistência no
    docstring do módulo). Se ``processar_resposta`` falhar após gravar a
    tentativa, reexecutar ``avaliar_progressao`` reconstrói o estado do
    progresso — a operação é segura para repetição.
    """
    registro = registrar_tentativa(
        sessao_id=sessao_id,
        aluno_id=aluno_id,
        exercicio_id=exercicio_id,
        resposta=resposta,
        tempo_resolucao_segundos=tempo_resolucao_segundos,
    )

    # O nível/habilidade da tentativa são resolvidos pelos relacionamentos
    # já existentes: tentativa -> exercício -> nível -> habilidade.
    exercicio = _exercicio_do_registro(registro)
    nivel = NivelRepository().buscar_por_id(exercicio.nivel_id)

    progressao = avaliar_progressao(aluno_id, nivel.habilidade_id)
    return RegistroComProgressao(registro=registro, progressao=progressao)


def _exercicio_do_registro(registro: RegistroDeTentativa):
    """Recupera o exercício da tentativa recém-registrada."""
    from app.repositories import ExercicioRepository

    exercicio = ExercicioRepository().buscar_por_id(
        registro.tentativa.exercicio_id
    )
    if exercicio is None:
        # Situação teoricamente impossível (a tentativa tem FK para o
        # exercício), mas protegida para falhar de forma explícita.
        raise ValueError(
            f"Exercício {registro.tentativa.exercicio_id} não existe."
        )
    return exercicio