"""Repositório de Módulos (grandes áreas do currículo)."""

from contextlib import closing

from app.database.connection import get_connection
from app.models import Modulo
from app.repositories.base import BaseRepository


class ModuloRepository(BaseRepository[Modulo]):
    """Persistência da entidade Modulo.

    A exclusão de um módulo é recusada quando existem habilidades
    vinculadas, preservando a integridade do currículo.
    """

    _TABELA = "modulos"
    _CAMPOS = ("nome", "descricao", "ordem", "ativo")
    _MODELO = Modulo
    _ORDENACAO = "ordem, id"

    def excluir(self, id_registro: int) -> bool:
        """Exclui um módulo, desde que ele não possua habilidades."""
        with closing(get_connection()) as connection:
            vinculos = connection.execute(
                "SELECT COUNT(*) FROM habilidades WHERE modulo_id = ?",
                (id_registro,),
            ).fetchone()[0]

            if vinculos > 0:
                raise ValueError(
                    "Não é possível excluir um módulo que possui habilidades "
                    "vinculadas."
                )

            cursor = connection.execute(
                "DELETE FROM modulos WHERE id = ?",
                (id_registro,),
            )
            connection.commit()

        return cursor.rowcount > 0