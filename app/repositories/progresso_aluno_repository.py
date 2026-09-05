"""Repositório de ProgressoAluno (estado atual da trajetória do aluno)."""

from app.models import ProgressoAluno
from app.repositories.base import BaseRepository


class ProgressoAlunoRepository(BaseRepository[ProgressoAluno]):
    """Persistência da entidade ProgressoAluno.

    A exclusão é bloqueada: o progresso é um registro de acompanhamento
    e sua remoção será tratada apenas por decisão futura. A atualização
    é permitida (o estado atual muda com o avanço do aluno) e regenera a
    coluna ``atualizado_em`` via SQLite.
    """

    _TABELA = "progresso_aluno"
    _CAMPOS = ("aluno_id", "habilidade_id", "nivel_id", "status")
    _MODELO = ProgressoAluno
    _ORDENACAO = "aluno_id, habilidade_id"
    _CAMPO_TIMESTAMP = "atualizado_em"

    def excluir(self, id_registro: int) -> bool:
        """Bloqueia a exclusão para preservar o histórico de aprendizagem."""
        raise NotImplementedError(
            "A exclusão de progresso do aluno não é permitida nesta versão: "
            "o histórico de aprendizagem deve ser preservado."
        )