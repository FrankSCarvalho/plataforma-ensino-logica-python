"""Modelo de domínio Habilidade (competência dentro de um módulo)."""

import sqlite3
from dataclasses import dataclass


@dataclass
class Habilidade:
    """Entidade Habilidade, persistida na tabela ``habilidades``.

    Representa uma competência específica que o aluno deve dominar.
    Pertence a um módulo e agrupa níveis progressivos.
    """

    modulo_id: int
    nome: str
    descricao: str = ""
    ordem: int = 0
    ativo: int = 1
    id: int | None = None

    @classmethod
    def from_row(cls, linha: sqlite3.Row) -> "Habilidade":
        """Converte uma linha retornada pelo banco em um modelo Habilidade."""
        return cls(
            id=linha["id"],
            modulo_id=linha["modulo_id"],
            nome=linha["nome"],
            descricao=linha["descricao"],
            ordem=linha["ordem"],
            ativo=linha["ativo"],
        )