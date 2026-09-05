"""Repositório de Exercícios."""

from app.models import Exercicio
from app.repositories.base import BaseRepository


class ExercicioRepository(BaseRepository[Exercicio]):
    """Persistência da entidade Exercicio.

    O exercício está na ponta da hierarquia do currículo e não possui
    filhos, portanto a exclusão herdada da base é segura.
    """

    _TABELA = "exercicios"
    _CAMPOS = ("nivel_id", "enunciado", "ordem", "ativo")
    _MODELO = Exercicio
    _ORDENACAO = "ordem, id"