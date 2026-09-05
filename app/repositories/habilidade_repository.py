"""Repositório de Habilidades."""

from contextlib import closing

from app.database.connection import get_connection
from app.models import Habilidade
from app.repositories.base import BaseRepository


class HabilidadeRepository(BaseRepository[Habilidade]):
    """Persistência da entidade Habilidade.

    A exclusão de uma habilidade é recusada quando existem níveis
    vinculados, preservando a integridade do currículo.
    """

    _TABELA = "habilidades"
    _CAMPOS = ("modulo_id", "nome", "descricao", "ordem", "ativo")
    _MODELO = Habilidade
    _ORDENACAO = "ordem, id"

    def excluir(self, id_registro: int) -> bool:
        """Exclui uma habilidade, desde que ela não possua níveis."""
        with closing(get_connection()) as connection:
            vinculos = connection.execute(
                "SELECT COUNT(*) FROM niveis WHERE habilidade_id = ?",
                (id_registro,),
            ).fetchone()[0]

            if vinculos > 0:
                raise ValueError(
                    "Não é possível excluir uma habilidade que possui níveis "
                    "vinculados."
                )

            cursor = connection.execute(
                "DELETE FROM habilidades WHERE id = ?",
                (id_registro,),
            )
            connection.commit()

        return cursor.rowcount > 0