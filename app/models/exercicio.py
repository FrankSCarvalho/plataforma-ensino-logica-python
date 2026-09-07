"""Modelo de domínio Exercício (unidade de prática dentro de um nível)."""

import sqlite3
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Tipos de exercício suportados pela plataforma.
#
# A coluna ``tipo`` da tabela ``exercicios`` armazena um destes rótulos,
# tornando a entidade extensível: novos tipos podem ser acrescentados
# futuramente sem alterar o schema.
# ---------------------------------------------------------------------------


TIPO_COMPLETAR_CODIGO = "completar_codigo"   # aluno completa uma lacuna no código

# Rótulos conhecidos (usados para validação futura e documentação).
TIPOS_DE_EXERCICIO = (    
    TIPO_COMPLETAR_CODIGO,
)

# Tipo padrão atribuído a novos exercícios.
TIPO_PADRAO = TIPO_COMPLETAR_CODIGO


@dataclass
class Exercicio:
    """Entidade Exercício, persistida na tabela ``exercicios``.

    Representa uma unidade de prática vinculada a um nível. Contém o
    enunciado, a ordenação dentro do nível e o ``tipo``, que permite
    diferentes formatos de exercício.
    """

    nivel_id: int
    enunciado: str
    ordem: int = 0
    ativo: int = 1
    # Rótulo do tipo de exercício (extensível; ver TIPOS_DE_EXERCICIO).
    tipo: str = TIPO_PADRAO
    # Resposta esperada usada pela correção automática quando o tipo
    # possuir uma resposta cadastrada. O campo é preenchido pelo
    # currículo/seed; o aluno nunca o vê.
    resposta_esperada: str = ""
    # Código apresentado ao aluno (migração v6). Contém o código com a
    # lacuna ``______`` que o aluno deve completar; é a fonte principal do
    # código exibido pela UI. Permanece vazio em bancos anteriores à
    # retrocompatibilidade da carga inicial até que esta o preencha.
    codigo: str = ""
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
            tipo=linha["tipo"],
            resposta_esperada=linha["resposta_esperada"],
            codigo=linha["codigo"],
        )