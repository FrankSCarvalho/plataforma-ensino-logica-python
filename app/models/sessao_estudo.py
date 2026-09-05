"""Modelo de domínio SessaoEstudo (unidade de estudo do aluno).

Representa uma sessão de estudo pertencente a um aluno. Uma sessão em
andamento possui ``termino`` vazio; ao encerrar, ``termino`` é preenchido
e o status muda. Não há regras de duração mínima ou máxima nesta etapa.
"""

import sqlite3
from dataclasses import dataclass


@dataclass
class SessaoEstudo:
    """Entidade SessaoEstudo, persistida na tabela ``sessoes_estudo``."""

    aluno_id: int
    status: str = "ativa"
    id: int | None = None
    inicio: str | None = None
    termino: str | None = None

    @classmethod
    def from_row(cls, linha: sqlite3.Row) -> "SessaoEstudo":
        """Converte uma linha retornada pelo banco em um modelo."""
        return cls(
            id=linha["id"],
            aluno_id=linha["aluno_id"],
            inicio=linha["inicio"],
            termino=linha["termino"],
            status=linha["status"],
        )