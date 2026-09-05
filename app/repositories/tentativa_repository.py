"""Repositório de Tentativa (registro imutável de histórico)."""

from contextlib import closing

from app.database.connection import get_connection
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

    def listar_avaliadas_do_aluno_por_nivel(
        self,
        aluno_id: int,
        nivel_id: int,
        limite: int | None = None,
    ) -> list[Tentativa]:
        """Lista as tentativas AVALIADAS de um aluno em um nível.

        Utilizada pelo motor pedagógico (Tarefa 07) para interpretar o
        histórico. Características:

            * o nível da tentativa é resolvido pelo relacionamento já
              existente (``tentativas.exercicio_id -> exercicios.nivel_id``);
              nenhuma informação de nível é duplicada em ``tentativas``;
            * tentativas com resultado ``nao_avaliada`` são EXCLUÍDAS,
              pois não participam da contagem de acertos/erros;
            * a ordenação é da MAIS RECENTE para a mais antiga
              (``realizada_em DESC, id DESC``), de modo que as primeiras
              linhas representam a janela de tentativas recentes;
            * ``limite`` (opcional) restringe a quantidade retornada —
              a janela de domínio é aplicada pelo serviço, não aqui;
            * consulta parametrizada (valores via ``?``).
        """
        sql = (
            "SELECT t.* FROM tentativas t "
            "JOIN exercicios e ON e.id = t.exercicio_id "
            "WHERE t.aluno_id = ? AND e.nivel_id = ? AND t.resultado <> ? "
            "ORDER BY t.realizada_em DESC, t.id DESC"
        )
        parametros: list[int | str] = [aluno_id, nivel_id, "nao_avaliada"]
        if limite is not None:
            sql += " LIMIT ?"
            parametros.append(limite)

        with closing(get_connection()) as connection:
            linhas = connection.execute(sql, parametros).fetchall()

        return [self._MODELO.from_row(linha) for linha in linhas]

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