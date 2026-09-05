"""Modelo de domínio Nível (pequeno passo progressivo de uma habilidade)."""

import sqlite3
from dataclasses import dataclass


@dataclass
class Nivel:
    """Entidade Nível, persistida na tabela ``niveis``.

    Representa um pequeno passo progressivo dentro de uma habilidade,
    agrupando os exercícios de prática.

    Além da identificação e da ordenação, o nível carrega o conteúdo
    conceitual apresentado ao aluno antes dos exercícios (Tarefa 05):
    título, explicação, exemplos e observações — gravados como texto
    simples, sem formatação avançada. Os campos iniciam vazios, pois o
    conteúdo é preenchido pela carga inicial do currículo.
    """

    habilidade_id: int
    nome: str
    descricao: str = ""
    ordem: int = 0
    ativo: int = 1
    # Campos de conteúdo conceitual (adicionados na migração v4).
    conteudo_titulo: str = ""
    conteudo_explicacao: str = ""
    conteudo_exemplos: str = ""
    conteudo_observacoes: str = ""
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
            conteudo_titulo=linha["conteudo_titulo"],
            conteudo_explicacao=linha["conteudo_explicacao"],
            conteudo_exemplos=linha["conteudo_exemplos"],
            conteudo_observacoes=linha["conteudo_observacoes"],
        )