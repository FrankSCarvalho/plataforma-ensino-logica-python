"""Base comum para os repositórios de persistência.

Concentra as operações CRUD genéricas compartilhadas por todos os
repositórios. Cada repositório concreto informa a tabela, as colunas
editáveis e o modelo correspondente — evitando duplicação de código
sem esconder o SQL, que permanece explícito e parametrizado.
"""

from contextlib import closing
from typing import Generic, TypeVar

from app.database.connection import get_connection

# TypeVar usado para que os métodos genéricos preservem o tipo do modelo.
T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Operações genéricas de persistência."""

    # Atributos que cada repositório concreto deve definir:
    _TABELA: str = ""
    _CAMPOS: tuple[str, ...] = ()        # colunas editáveis (sem o id)
    _MODELO: type | None = None          # classe de modelo
    _ORDENACAO: str = "id"               # ORDER BY padrão das listagens
    _CAMPO_TIMESTAMP: str | None = None  # coluna atualizada pelo banco

    def inserir(self, entidade: T) -> T:
        """Insere uma entidade e preenche o ``id`` gerado pelo banco."""
        colunas = ", ".join(self._CAMPOS)
        placeholders = ", ".join("?" for _ in self._CAMPOS)
        valores = tuple(getattr(entidade, campo) for campo in self._CAMPOS)

        with closing(get_connection()) as connection:
            cursor = connection.execute(
                f"INSERT INTO {self._TABELA} ({colunas}) VALUES ({placeholders})",
                valores,
            )
            connection.commit()
            entidade.id = cursor.lastrowid
        return entidade

    def buscar_por_id(self, id_registro: int) -> T | None:
        """Retorna a entidade pelo id, ou ``None`` se não existir."""
        with closing(get_connection()) as connection:
            linha = connection.execute(
                f"SELECT * FROM {self._TABELA} WHERE id = ?",
                (id_registro,),
            ).fetchone()

        return self._MODELO.from_row(linha) if linha else None

    def listar(self) -> list[T]:
        """Lista todas as entidades na ordenação padrão da tabela."""
        with closing(get_connection()) as connection:
            linhas = connection.execute(
                f"SELECT * FROM {self._TABELA} ORDER BY {self._ORDENACAO}"
            ).fetchall()

        return [self._MODELO.from_row(linha) for linha in linhas]

    def atualizar(self, entidade: T) -> bool:
        """Atualiza uma entidade existente; retorna ``True`` se alterou."""
        if entidade.id is None:
            raise ValueError("Não é possível atualizar uma entidade sem id.")

        # Todo o SQL de atualização é parametrizado (valores via "?").
        campos_editaveis = list(self._CAMPOS)
        if self._CAMPO_TIMESTAMP:
            campos_editaveis = [
                campo for campo in campos_editaveis if campo != self._CAMPO_TIMESTAMP
            ]

        atribuicoes = [f"{campo} = ?" for campo in campos_editaveis]
        valores = [getattr(entidade, campo) for campo in campos_editaveis]

        # Timestamps de atualização são gerados pelo próprio SQLite.
        if self._CAMPO_TIMESTAMP:
            atribuicoes.append(f"{self._CAMPO_TIMESTAMP} = datetime('now')")

        valores.append(entidade.id)
        with closing(get_connection()) as connection:
            cursor = connection.execute(
                f"UPDATE {self._TABELA} SET {', '.join(atribuicoes)} WHERE id = ?",
                valores,
            )
            connection.commit()

        return cursor.rowcount > 0

    def excluir(self, id_registro: int) -> bool:
        """Exclui a entidade pelo id; retorna ``True`` se excluiu."""
        with closing(get_connection()) as connection:
            cursor = connection.execute(
                f"DELETE FROM {self._TABELA} WHERE id = ?",
                (id_registro,),
            )
            connection.commit()

        return cursor.rowcount > 0