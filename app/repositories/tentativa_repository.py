"""Repositório de Tentativa (registro imutável de histórico)."""

from app.models import Tentativa
from app.repositories.base import BaseRepository


class TentativaRepository(BaseRepository[Tentativa]):
    """Persistência da entidade Tentativa.

    Tentativas são registros de histórico: a alteração e a exclusão são
    bloqueadas. O objetivo é garantir que o histórico de tentativas
    nunca seja modificado — inclusive quando o progresso do aluno é
    atualizado (a atualização do progresso NÃO toca esta tabela).
    """

    _TABELA = "tentativas"
    _CAMPOS = (
        "sessao_id",
        "aluno_id",
        "exercicio_id",
        "resposta",
        "resultado",
        "tempo_resolucao_segundos",
    )
    _MODELO = Tentativa
    _ORDENACAO = "realizada_em, id"

    def atualizar(self, entidade: Tentativa) -> bool:
        """Bloqueia a alteração de tentativas já registradas."""
        raise NotImplementedError(
            "A alteração de tentativas não é permitida: o histórico deve "
            "permanecer imutável."
        )

    def excluir(self, id_registro: int) -> bool:
        """Bloqueia a exclusão para preservar o histórico de aprendizagem."""
        raise NotImplementedError(
            "A exclusão de tentativas não é permitida: o histórico deve "
            "permanecer imutável."
        )