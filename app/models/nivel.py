"""Modelo de domínio Nível (pequeno passo progressivo de uma habilidade)."""

import sqlite3
from dataclasses import dataclass


@dataclass
class Nivel:
    """Entidade Nível, persistida na tabela ``niveis``.

    Representa um pequeno passo progressivo dentro de uma habilidade,
    agrupando os exercícios de prática.
    """

    habilidade_id: int
    nome: str
    descricao: str = ""
    ordem: int = 0
    ativo: int = 1
    id: int | None = None

    @classmethod
    def from_row(cls, linha: sqlite3.Row) -> "Nivel":
        """Converte uma linha retornada pelo banco em um modelo Nivel."""
        return cls(
            id=linha["id"],
            habilidade_id=linha["habilidade_id"],
            nome=linha["nome"],
            descricao=linha["descricao"],
            ordem=linha["ordem"],
            ativo=linha["ativo"],
        )