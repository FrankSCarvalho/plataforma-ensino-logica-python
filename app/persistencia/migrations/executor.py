from dataclasses import dataclass
from typing import Callable, Iterable
import sqlite3


AplicarMigration = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True)
class Migration:
    """Representa uma alteração versionada do schema."""

    versao: int
    nome: str
    aplicar: AplicarMigration


def obter_versao_schema(conexao: sqlite3.Connection) -> int:
    """Retorna a versão atual do schema registrada pelo SQLite."""
    linha = conexao.execute("PRAGMA user_version").fetchone()
    return int(linha[0])


def definir_versao_schema(conexao: sqlite3.Connection, versao: int) -> None:
    """Registra a versão do schema no SQLite."""
    if versao < 0:
        raise ValueError("A versão do schema não pode ser negativa.")

    conexao.execute(f"PRAGMA user_version = {versao}")


def _validar_migrations(migrations: Iterable[Migration]) -> list[Migration]:
    """Valida e ordena as migrations antes de alterar o banco."""
    lista = list(migrations)

    if any(migration.versao <= 0 for migration in lista):
        raise ValueError("A versão de uma migration deve ser um inteiro positivo.")

    versoes = [migration.versao for migration in lista]
    if len(versoes) != len(set(versoes)):
        raise ValueError("Não pode haver duas migrations com a mesma versão.")

    return sorted(lista, key=lambda migration: migration.versao)


def executar_migrations(
    conexao: sqlite3.Connection,
    migrations: Iterable[Migration],
) -> int:
    """Aplica as migrations pendentes e retorna a versão final do schema."""
    migrations_ordenadas = _validar_migrations(migrations)
    versao_atual = obter_versao_schema(conexao)

    for migration in migrations_ordenadas:
        if migration.versao <= versao_atual:
            continue

        try:
            conexao.execute("BEGIN")
            migration.aplicar(conexao)
            definir_versao_schema(conexao, migration.versao)
            conexao.execute("COMMIT")
        except Exception:
            conexao.execute("ROLLBACK")
            raise

        versao_atual = migration.versao

    return versao_atual