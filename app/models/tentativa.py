"""Modelo de domínio Tentativa (registro de uma tentativa de exercício).

Representa UMA tentativa do aluno em um exercício dentro de uma sessão
de estudo. É um registro imutável de histórico: tentativas antigas nunca
são apagadas nem alteradas.
"""

import sqlite3
from dataclasses import dataclass

from app.models.avaliacao import RESULTADO_NAO_AVALIADA


@dataclass
class Tentativa:
    """Entidade Tentativa, persistida na tabela ``tentativas``.

    O resultado utiliza a representação centralizada em
    ``app.models.avaliacao`` ('correta', 'incorreta',
    'parcialmente_correta', 'nao_avaliada') e é preenchido pelo serviço
    de avaliação no momento do registro — tentativas nunca são alteradas
    depois de gravadas.
    """

    sessao_id: int
    aluno_id: int
    exercicio_id: int
    resposta: str
    resultado: str = RESULTADO_NAO_AVALIADA
    tempo_resolucao_segundos: int = 0
    id: int | None = None
    realizada_em: str | None = None

    @classmethod
    def from_row(cls, linha: sqlite3.Row) -> "Tentativa":
        """Converte uma linha retornada pelo banco em um modelo."""
        return cls(
            id=linha["id"],
            sessao_id=linha["sessao_id"],
            aluno_id=linha["aluno_id"],
            exercicio_id=linha["exercicio_id"],
            resposta=linha["resposta"],
            resultado=linha["resultado"],
            tempo_resolucao_segundos=linha["tempo_resolucao_segundos"],
            realizada_em=linha["realizada_em"],
        )