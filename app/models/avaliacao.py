"""Modelo de domínio Avaliação (resultado estruturado da correção).

Centraliza os valores possíveis para o resultado de uma avaliação, evitando
strings espalhadas pelo projeto, e define a estrutura de dados devolvida
pelo serviço de avaliação (Tarefa 06).

Esta camada NÃO contém regras de avaliação: os valores apenas nomeiam os
estados que a camada de serviço produz. Regras pedagógicas (domínio,
progressão etc.) pertencem a tarefas futuras e não usam estas constantes
diretamente como decisão.
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Resultados possíveis de uma avaliação — ÚNICA fonte de verdade.
# ---------------------------------------------------------------------------
RESULTADO_CORRETA = "correta"
RESULTADO_INCORRETA = "incorreta"
RESULTADO_PARCIALMENTE_CORRETA = "parcialmente_correta"
RESULTADO_NAO_AVALIADA = "nao_avaliada"

# Conjunto completo, útil para validações e documentação.
RESULTADOS_AVALIACAO = (
    RESULTADO_CORRETA,
    RESULTADO_INCORRETA,
    RESULTADO_PARCIALMENTE_CORRETA,
    RESULTADO_NAO_AVALIADA,
)


@dataclass
class Avaliacao:
    """Resultado estruturado da avaliação de UMA resposta.

    Atributos:
        resultado: um dos valores em ``RESULTADOS_AVALIACAO``.
        feedback: texto curto e simples exibido ao aluno (nesta versão é
            apenas descritivo; geração rica de feedback é tarefa futura).
        detalhes: informações adicionais da correção (por exemplo, trechos
            comparados). Mantido como dicionário livre para permitir
            extensão futura sem alterar a estrutura.
    """

    resultado: str = RESULTADO_NAO_AVALIADA
    feedback: str = ""
    detalhes: dict = field(default_factory=dict)