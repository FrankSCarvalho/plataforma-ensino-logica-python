"""Repositório de Alunos."""

from app.models import Aluno
from app.repositories.base import BaseRepository


class AlunoRepository(BaseRepository[Aluno]):
    """Persistência da entidade Aluno.

    O aluno é uma entidade independente nesta versão, portanto a
    exclusão é segura (não possui vínculos com o currículo).
    """

    _TABELA = "alunos"
    _CAMPOS = ("nome", "status")
    _MODELO = Aluno
    _ORDENACAO = "id"
    # A coluna ``atualizado_em`` é regenerada pelo banco a cada UPDATE.
    _CAMPO_TIMESTAMP = "atualizado_em"