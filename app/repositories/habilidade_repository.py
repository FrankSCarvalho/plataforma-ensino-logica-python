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

    def listar_por_modulo(self, modulo_id: int) -> list[Habilidade]:
        """Lista as habilidades de um módulo, na ordem pedagógica.

        A ordenação segue a mesma regra da listagem padrão (``ordem, id``).
        Consulta parametrizada (valor via ``?``).
        """
        with closing(get_connection()) as connection:
            linhas = connection.execute(
                f"SELECT * FROM {self._TABELA} "
                "WHERE modulo_id = ? ORDER BY ordem, id",
                (modulo_id,),
            ).fetchall()

        return [self._MODELO.from_row(linha) for linha in linhas]

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