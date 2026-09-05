"""Modelo de domínio Exercício (unidade de prática dentro de um nível)."""

import sqlite3
from dataclasses import dataclass


@dataclass
class Exercicio:
    """Entidade Exercício, persistida na tabela ``exercicios``.

    Representa uma unidade de prática vinculada a um nível. Nesta etapa
    contém apenas o enunciado e a ordenação; o modelo de respostas e a
    correção serão adicionados em tarefas futuras.
    """

    nivel_id: int
    enunciado: str
    ordem: int = 0
    ativo: int = 1
    id: int | None = None

    @classmethod
    def from_row(cls, linha: sqlite3.Row) -> "Exercicio":
        """Converte uma linha retornada pelo banco em um modelo Exercicio."""
        return cls(
            id=linha["id"],
            nivel_id=linha["nivel_id"],
            enunciado=linha["enunciado"],
            ordem=linha["ordem"],
            ativo=linha["ativo"],
        )