"""Serviço de registro de tentativas (Tarefa 06).

Orquestra o fluxo completo de UMA resposta do aluno:

    aluno responde -> avaliador -> resultado -> nova tentativa registrada

Garantias desta camada:

    * valida que aluno, sessão e exercício existem (além das foreign keys
      do banco, a validação explícita devolve erros claros ao chamador);
    * valida que a sessão pertence ao aluno informado;
    * a tentativa é criada já com o resultado da avaliação e NUNCA é
      modificada depois (o repositório bloqueia atualização/exclusão);
    * o progresso do aluno NÃO é tocado: avaliar uma resposta não
      significa avançar de nível — isso é decisão do motor pedagógico
      futuro.
"""

from dataclasses import dataclass

from app.models import Tentativa
from app.models.avaliacao import Avaliacao
from app.repositories import (
    AlunoRepository,
    ExercicioRepository,
    SessaoEstudoRepository,
    TentativaRepository,
)
from app.services.avaliador import avaliar_resposta


@dataclass
class RegistroDeTentativa:
    """Resultado do registro de uma tentativa.

    Reúne a tentativa gravada (histórico imutável) e a avaliação
    estruturada produzida para a resposta (resultado + feedback).
    """

    tentativa: Tentativa
    avaliacao: Avaliacao


def registrar_tentativa(
    sessao_id: int,
    aluno_id: int,
    exercicio_id: int,
    resposta: str,
    tempo_resolucao_segundos: int = 0,
) -> RegistroDeTentativa:
    """Avalia a resposta do aluno e registra uma NOVA tentativa.

    Levanta ``ValueError`` (com mensagem clara) quando o aluno, a sessão
    ou o exercício não existem, ou quando a sessão não pertence ao aluno.
    """
    repositorio_alunos = AlunoRepository()
    repositorio_sessoes = SessaoEstudoRepository()
    repositorio_exercicios = ExercicioRepository()
    repositorio_tentativas = TentativaRepository()

    # ---- Validações de existência (antes de qualquer escrita) ---------
    if repositorio_alunos.buscar_por_id(aluno_id) is None:
        raise ValueError(f"Aluno {aluno_id} não existe.")

    sessao = repositorio_sessoes.buscar_por_id(sessao_id)
    if sessao is None:
        raise ValueError(f"Sessão de estudo {sessao_id} não existe.")
    if sessao.aluno_id != aluno_id:
        raise ValueError(
            f"A sessão {sessao_id} não pertence ao aluno {aluno_id}."
        )

    exercicio = repositorio_exercicios.buscar_por_id(exercicio_id)
    if exercicio is None:
        raise ValueError(f"Exercício {exercicio_id} não existe.")

    # ---- Avaliação (serviço puro; não altera nada no banco) -----------
    avaliacao = avaliar_resposta(exercicio, resposta)

    # ---- Registro da tentativa (histórico imutável) --------------------
    # A tentativa nasce já com o resultado da avaliação. Tentativas
    # anteriores permanecem intactas — este serviço só INSERE.
    tentativa = repositorio_tentativas.inserir(
        Tentativa(
            sessao_id=sessao_id,
            aluno_id=aluno_id,
            exercicio_id=exercicio_id,
            resposta=resposta,
            resultado=avaliacao.resultado,
            tempo_resolucao_segundos=tempo_resolucao_segundos,
        )
    )

    return RegistroDeTentativa(tentativa=tentativa, avaliacao=avaliacao)