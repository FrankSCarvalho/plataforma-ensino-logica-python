"""Modelo de domínio Módulo (grande área do currículo)."""

import sqlite3
from dataclasses import dataclass


@dataclass
class Modulo:
    """Entidade Módulo, persistida na tabela ``modulos``.

    Representa uma grande área do currículo, que agrupa habilidades.
    """

    nome: str
    descricao: str = ""
    ordem: int = 0
    ativo: int = 1
    id: int | None = None

    @classmethod
    def from_row(cls, linha: sqlite3.Row) -> "Modulo":
        """Converte uma linha retornada pelo banco em um modelo Modulo."""
        return cls(
            id=linha["id"],
            nome=linha["nome"],
            descricao=linha["descricao"],
            ordem=linha["ordem"],
            ativo=linha["ativo"],
        )