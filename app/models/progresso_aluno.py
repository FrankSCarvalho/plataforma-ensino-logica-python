"""Modelo de domínio ProgressoAluno (estado atual da trajetória do aluno).

Representa o ESTADO ATUAL do aluno em uma determinada habilidade: qual
nível está sendo trabalhado e o status. É um "ponteiro" de progresso e
NÃO substitui o histórico de sessões e tentativas.
"""

import sqlite3
from dataclasses import dataclass


@dataclass
class ProgressoAluno:
    """Entidade ProgressoAluno, persistida na tabela ``progresso_aluno``.

    Um mesmo aluno pode possuir várias linhas de progresso, uma para
    cada habilidade que está trabalhando.
    """

    aluno_id: int
    habilidade_id: int
    nivel_id: int
    status: str = "em_andamento"
    id: int | None = None
    criado_em: str | None = None
    atualizado_em: str | None = None

    @classmethod
    def from_row(cls, linha: sqlite3.Row) -> "ProgressoAluno":
        """Converte uma linha retornada pelo banco em um modelo."""
        return cls(
            id=linha["id"],
            aluno_id=linha["aluno_id"],
            habilidade_id=linha["habilidade_id"],
            nivel_id=linha["nivel_id"],
            status=linha["status"],
            criado_em=linha["criado_em"],
            atualizado_em=linha["atualizado_em"],
        )