"""Serviço de avaliação de respostas (Tarefa 06).

Responsabilidade ÚNICA: responder à pergunta

    "A resposta do aluno está correta, incorreta, parcialmente correta
     ou não avaliada?"

Este serviço NÃO decide domínio, progressão, repetição, pontuação ou
qualquer coisa pedagógica — essas decisões pertencem ao motor pedagógico,
que será implementado em tarefa futura.

Regras por tipo de exercício:

    * ``prever_resultado``  -> correção automática DETERMINÍSTICA: compara
      a resposta normalizada do aluno com a resposta esperada normalizada
      (comparação de igualdade exata de texto). Não usa IA, não usa
      bibliotecas externas, não faz comparação aproximada.
    * ``resposta_textual``  -> sempre ``nao_avaliada`` (avaliação manual
      ficará para uma etapa futura).
    * ``escrever_codigo``   -> sempre ``nao_avaliada``. O código do aluno
      NÃO é executado nesta versão (sem ``exec``, ``eval`` ou
      ``subprocess``); execução segura é uma decisão arquitetural
      independente, planejada para depois.
    * tipo desconhecido     -> ``nao_avaliada`` (comportamento seguro).
"""

from app.models import (
    TIPO_ESCREVER_CODIGO,
    TIPO_PREVER_RESULTADO,
    TIPO_RESPOSTA_TEXTUAL,
    Exercicio,
)
from app.models.avaliacao import (
    RESULTADO_CORRETA,
    RESULTADO_INCORRETA,
    RESULTADO_NAO_AVALIADA,
    Avaliacao,
)


def normalizar_resposta(texto: str) -> str:
    """Normaliza uma resposta para comparação, de forma conservadora.

    Regras adotadas (definidas explicitamente, conforme a Tarefa 06):

    1. Fim de linha: ``\\r\\n`` e ``\\r`` são convertidos para ``\\n`` —
       apenas elimina a diferença trivial entre Windows e outros sistemas.
    2. Espaços no início/fim do texto inteiro: removidos (``strip``).
    3. Espaços à direita de cada linha: removidos — são artefatos de
       digitação que não alteram o conteúdo da resposta.
    4. Maiúsculas/minúsculas: PRESERVADAS. A saída de um programa distingue
       ``Bola`` de ``bola``, portanto a comparação é sensível a caixa.
    5. Espaços internos e quebras de linha internas: PRESERVADOS. Duas
       respostas com conteúdo interno diferente continuam diferentes — a
       normalização não pode transformar respostas diferentes em iguais.
    6. Entrada ``None`` é tratada como string vazia (conveniência para
       chamadores; não muda a semântica da comparação).
    """
    if texto is None:
        return ""

    # Regra 1: unificação de finais de linha.
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")

    # Regra 3: espaços à direita de cada linha (sem tocar os internos).
    linhas = [linha.rstrip() for linha in texto.split("\n")]
    texto = "\n".join(linhas)

    # Regra 2: espaços no início/fim do texto completo.
    return texto.strip()


def _avaliar_prever_resultado(exercicio: Exercicio, resposta: str) -> Avaliacao:
    """Correção automática determinística do tipo ``prever_resultado``.

    Compara a resposta normalizada do aluno com a resposta esperada
    normalizada. Igualdade exata -> correta; qualquer diferença ->
    incorreta. Se o exercício não tiver resposta esperada cadastrada
    (coluna vazia), retorna ``nao_avaliada`` — não há como corrigir.
    """
    esperada = (exercicio.resposta_esperada or "").strip()
    if not esperada:
        return Avaliacao(
            resultado=RESULTADO_NAO_AVALIADA,
            feedback="Exercício sem resposta esperada cadastrada.",
            detalhes={"motivo": "sem_resposta_esperada"},
        )

    resposta_normalizada = normalizar_resposta(resposta)
    esperada_normalizada = normalizar_resposta(esperada)

    if resposta_normalizada == esperada_normalizada:
        return Avaliacao(
            resultado=RESULTADO_CORRETA,
            feedback="Resposta correta!",
            detalhes={"tipo_comparacao": "igualdade_exata_normalizada"},
        )

    return Avaliacao(
        resultado=RESULTADO_INCORRETA,
        feedback="Resposta incorreta. Revise a ordem de execução.",
        detalhes={"tipo_comparacao": "igualdade_exata_normalizada"},
    )


def avaliar_resposta(exercicio: Exercicio, resposta: str) -> Avaliacao:
    """Avalia a resposta do aluno para um exercício.

    Função PURA e determinística: o resultado depende somente do exercício
    (tipo e resposta esperada) e da resposta fornecida. Nunca altera o
    banco, o progresso do aluno ou a própria tentativa.
    """
    if exercicio.tipo == TIPO_PREVER_RESULTADO:
        return _avaliar_prever_resultado(exercicio, resposta)

    if exercicio.tipo == TIPO_RESPOSTA_TEXTUAL:
        # Sem inferência automática: aguardará avaliação manual/etapa futura.
        return Avaliacao(
            resultado=RESULTADO_NAO_AVALIADA,
            feedback="Resposta registrada. Será avaliada em breve.",
            detalhes={"motivo": "tipo_resposta_textual"},
        )

    if exercicio.tipo == TIPO_ESCREVER_CODIGO:
        # O código do aluno NÃO é executado nesta versão (sem exec, eval
        # ou subprocess). A correção automática de código será analisada
        # em uma tarefa arquitetural independente.
        return Avaliacao(
            resultado=RESULTADO_NAO_AVALIADA,
            feedback="Resposta registrada. O código será analisado em breve.",
            detalhes={"motivo": "tipo_escrever_codigo"},
        )

    # Tipo desconhecido: comportamento seguro é não avaliar.
    return Avaliacao(
        resultado=RESULTADO_NAO_AVALIADA,
        feedback="Tipo de exercício sem avaliação automática definida.",
        detalhes={"motivo": "tipo_desconhecido", "tipo": exercicio.tipo},
    )