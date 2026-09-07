"""Repositório de Exercícios."""

from contextlib import closing

from app.database.connection import get_connection
from app.models import Exercicio
from app.repositories.base import BaseRepository


class ExercicioRepository(BaseRepository[Exercicio]):
    """Persistência da entidade Exercicio.

    O exercício está na ponta da hierarquia do currículo e não possui
    filhos, portanto a exclusão herdada da base é segura.
    """

    _TABELA = "exercicios"
    _CAMPOS = (
        "nivel_id",
        "enunciado",
        "ordem",
        "ativo",
        # Rótulo do tipo de exercício (migração v4).
        "tipo",
        # Resposta esperada usada pela correção automática do tipo
        # ``completar_codigo`` (migração v5, Tarefa 06). Armazenada aqui
        # apenas como DADO; a lógica de comparação fica no serviço de
        # avaliação, nunca neste repositório.
        "resposta_esperada",
        # Código apresentado ao aluno (migração v6). O repositório apenas
        # persiste e recupera o texto; NÃO interpreta o código nem a lacuna.
        "codigo",
    )
    _MODELO = Exercicio
    _ORDENACAO = "ordem, id"

    def listar_por_nivel(self, nivel_id: int) -> list[Exercicio]:
        """Lista os exercícios de um nível, na ordem pedagógica.

        A ordenação segue a mesma regra da listagem padrão (``ordem, id``),
        permitindo a progressão gradual de dificuldade planejada para o
        nível. Consulta parametrizada (valor via ``?``).
        """
        with closing(get_connection()) as connection:
            linhas = connection.execute(
                f"SELECT * FROM {self._TABELA} "
                "WHERE nivel_id = ? ORDER BY ordem, id",
                (nivel_id,),
            ).fetchall()

        return [self._MODELO.from_row(linha) for linha in linhas]