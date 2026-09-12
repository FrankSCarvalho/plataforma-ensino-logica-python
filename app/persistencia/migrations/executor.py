from dataclasses import dataclass
from typing import Callable, Iterable
import sqlite3


# Alias de tipo: uma migração é qualquer função que recebe a conexão
# com o banco e devolve None, aplicando alterações no schema.
AplicarMigration = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True)
class Migration:
    """Representa uma alteração versionada do schema."""

    versao: int  # Número da versão: define a ordem de aplicação
    nome: str  # Nome descritivo (ex.: "criar_tabela_aluno")
    aplicar: AplicarMigration  # Função que executa a alteração no banco


def obter_versao_schema(conexao: sqlite3.Connection) -> int:
    """Retorna a versão atual do schema registrada pelo SQLite."""
    # PRAGMA user_version é um metadato que o próprio SQLite guarda no banco
    # (inicia em 0). Usamos isso como "contador" de migrations aplicadas.
    linha = conexao.execute("PRAGMA user_version").fetchone()
    return int(linha[0])


def definir_versao_schema(conexao: sqlite3.Connection, versao: int) -> None:
    """Registra a versão do schema no SQLite."""
    if versao < 0:
        raise ValueError("A versão do schema não pode ser negativa.")

    # PRAGMA user_version não aceita parâmetro '?', por isso usamos f-string;
    # o valor é um inteiro controlado pelo nosso código (não é entrada do
    # usuário), portanto interpolá-lo é seguro.
    conexao.execute(f"PRAGMA user_version = {versao}")


def _validar_migrations(migrations: Iterable[Migration]) -> list[Migration]:
    """Valida e ordena as migrations antes de alterar o banco."""
    lista = list(migrations)  # Converte o iterable em lista para percorrer várias vezes

    # Todas as versões devem ser positivas (> 0); a versão 0 representa um
    # banco novo, e não uma migração real.
    if any(migration.versao <= 0 for migration in lista):
        raise ValueError("A versão de uma migration deve ser um inteiro positivo.")

    versoes = [migration.versao for migration in lista]
    # Duas migrations com a mesma versão seriam ambíguas (qual aplicar primeiro?).
    if len(versoes) != len(set(versoes)):
        raise ValueError("Não pode haver duas migrations com a mesma versão.")

    # Ordena por versão crescente para garantir uma ordem determinística.
    return sorted(lista, key=lambda migration: migration.versao)


def executar_migrations(
    conexao: sqlite3.Connection,
    migrations: Iterable[Migration],
) -> int:
    """Aplica as migrations pendentes e retorna a versão final do schema."""
    migrations_ordenadas = _validar_migrations(migrations)
    versao_atual = obter_versao_schema(conexao)

    for migration in migrations_ordenadas:
        # Só aplicamos migrations MAIS NOVAS que a versão atual:
        # assim, um banco já atualizado não re-executa nada (idempotência).
        if migration.versao <= versao_atual:
            continue

        try:
            # Cada migration roda dentro de uma TRANSAÇÃO: se falhar, faremos
            # ROLLBACK e o schema permanecerá na versão anterior (atômico).
            conexao.execute("BEGIN")
            migration.aplicar(conexao)
            definir_versao_schema(conexao, migration.versao)
            conexao.execute("COMMIT")
        except Exception:
            conexao.execute("ROLLBACK")
            raise  # Re-lança a exceção para a camada superior tratar

        versao_atual = migration.versao  # Avançamos a versão conhecida do schema

    return versao_atual