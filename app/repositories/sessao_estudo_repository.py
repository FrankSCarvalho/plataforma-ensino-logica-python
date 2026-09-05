"""Repositório de SessaoEstudo (sessões de estudo do aluno)."""

from contextlib import closing

from app.database.connection import get_connection
from app.models import SessaoEstudo
from app.repositories.base import BaseRepository


class SessaoEstudoRepository(BaseRepository[SessaoEstudo]):
    """Persistência da entidade SessaoEstudo.

    O ``inicio`` é gerado pelo banco no INSERT. O encerramento de uma
    sessão ocorre pelo método específico ``encerrar``, que preenche o
    ``termino`` e atualiza o status — sem apagar o histórico.
    """

    _TABELA = "sessoes_estudo"
    _CAMPOS = ("aluno_id", "status")
    _MODELO = SessaoEstudo
    _ORDENACAO = "id"

    def encerrar(self, sessao: SessaoEstudo, status: str = "encerrada") -> bool:
        """Encerra uma sessão preenchendo ``termino`` e alterando o status."""
        if sessao.id is None:
            raise ValueError("Não é possível encerrar uma sessão sem id.")

        with closing(get_connection()) as connection:
            cursor = connection.execute(
                "UPDATE sessoes_estudo "
                "SET termino = datetime('now'), status = ? "
                "WHERE id = ?",
                (status, sessao.id),
            )
            connection.commit()

        return cursor.rowcount > 0

    def excluir(self, id_registro: int) -> bool:
        """Bloqueia a exclusão para preservar o histórico de aprendizagem."""
        raise NotImplementedError(
            "A exclusão de sessões de estudo não é permitida nesta versão: "
            "o histórico de aprendizagem deve ser preservado."
        )