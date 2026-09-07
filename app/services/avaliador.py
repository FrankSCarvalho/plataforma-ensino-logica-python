"""Serviço de avaliação de respostas.

Responsabilidade única: determinar se a resposta do aluno está correta,
incorreta ou não avaliada.

Este serviço não decide domínio, progressão, repetição ou pontuação.
Essas decisões pertencem ao motor pedagógico.

A avaliação de código nesta etapa é exclusivamente textual.
O código enviado pelo aluno nunca é executado.
"""

from app.models import (
    TIPO_COMPLETAR_CODIGO,    
    Exercicio,
)
from app.models.avaliacao import (
    RESULTADO_CORRETA,
    RESULTADO_INCORRETA,
    RESULTADO_NAO_AVALIADA,
    Avaliacao,
)


def normalizar_resposta(texto: str) -> str:
    """Normaliza uma resposta para comparação determinística.

    São normalizados apenas finais de linha e espaços à direita das linhas.
    Espaços internos e diferença entre maiúsculas e minúsculas são
    preservados.
    """

    if texto is None:
        return ""

    texto = texto.replace("\r\n", "\n").replace("\r", "\n")

    linhas = [linha.rstrip() for linha in texto.split("\n")]
    texto = "\n".join(linhas)

    return texto.strip()


def _comparar_resposta_esperada(
    exercicio: Exercicio,
    resposta: str,
) -> Avaliacao:
    """Compara a resposta do aluno com a resposta esperada.

    A comparação é textual, determinística e normalizada.
    Nenhum código é executado.
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
        feedback="Resposta incorreta. Revise o código e tente novamente.",
        detalhes={"tipo_comparacao": "igualdade_exata_normalizada"},
    )


def avaliar_resposta(exercicio: Exercicio, resposta: str) -> Avaliacao:
    """Avalia a resposta do aluno para um exercício.

    A função é pura e determinística. O resultado depende somente do
    exercício e da resposta fornecida.

    O código enviado pelo aluno nunca é executado.
    """

    if exercicio.tipo == TIPO_COMPLETAR_CODIGO:
        return _comparar_resposta_esperada(exercicio, resposta)

    
    return Avaliacao(
        resultado=RESULTADO_NAO_AVALIADA,
        feedback="Tipo de exercício sem avaliação automática definida.",
        detalhes={
            "motivo": "tipo_desconhecido",
            "tipo": exercicio.tipo,
        },
    )