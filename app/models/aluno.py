"""Modelo de domínio Aluno.

Representa um aluno da plataforma. Nesta primeira versão é uma entidade
independente — não possui vínculo direto com o currículo; as relações
com habilidades e desempenho serão modeladas em etapas futuras.
"""

import sqlite3
from dataclasses import dataclass


@dataclass
class Aluno:
    """Entidade Aluno, persistida na tabela ``alunos``."""

    nome: str
    status: str = "ativo"
    id: int | None = None
    criado_em: str | None = None
    atualizado_em: str | None = None

    @classmethod
    def from_row(cls, linha: sqlite3.Row) -> "Aluno":
        """Converte uma linha retornada pelo banco em um modelo Aluno."""
        return cls(
            id=linha["id"],
            nome=linha["nome"],
            status=linha["status"],
            criado_em=linha["criado_em"],
            atualizado_em=linha["atualizado_em"],
        )