"""Repositório de Níveis."""

from contextlib import closing

from app.database.connection import get_connection
from app.models import Nivel
from app.repositories.base import BaseRepository


class NivelRepository(BaseRepository[Nivel]):
    """Persistência da entidade Nivel.

    A exclusão de um nível é recusada quando existem exercícios
    vinculados, preservando a integridade do currículo.
    """

    _TABELA = "niveis"
    _CAMPOS = (
        "habilidade_id",
        "nome",
        "descricao",
        "ordem",
        "ativo",
        # Campos de conteúdo conceitual (migração v4). Estão em _CAMPOS
        # para que a inserção e a atualização os persistam normalmente.
        "conteudo_titulo",
        "conteudo_explicacao",
        "conteudo_exemplos",
        "conteudo_observacoes",
    )
    _MODELO = Nivel
    _ORDENACAO = "ordem, id"

    def listar_por_habilidade(self, habilidade_id: int) -> list[Nivel]:
        """Lista os níveis de uma habilidade, na ordem pedagógica.

        A ordenação segue a mesma regra da listagem padrão (``ordem, id``),
        garantindo que os passos progressivos apareçam na sequência em que
        foram planejados. Consulta parametrizada (valor via ``?``).
        """
        with closing(get_connection()) as connection:
            linhas = connection.execute(
                f"SELECT * FROM {self._TABELA} "
                "WHERE habilidade_id = ? ORDER BY ordem, id",
                (habilidade_id,),
            ).fetchall()

        return [self._MODELO.from_row(linha) for linha in linhas]

    def excluir(self, id_registro: int) -> bool:
        """Exclui um nível, desde que ele não possua exercícios."""
        with closing(get_connection()) as connection:
            vinculos = connection.execute(
                "SELECT COUNT(*) FROM exercicios WHERE nivel_id = ?",
                (id_registro,),
            ).fetchone()[0]

            if vinculos > 0:
                raise ValueError(
                    "Não é possível excluir um nível que possui exercícios "
                    "vinculados."
                )

            cursor = connection.execute(
                "DELETE FROM niveis WHERE id = ?",
                (id_registro,),
            )
            connection.commit()

        return cursor.rowcount > 0