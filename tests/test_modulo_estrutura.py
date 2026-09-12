import sqlite3  # Driver SQLite: usado para inspecionar schema e detectar IntegrityError

import pytest  # Framework de teste: fornece pytest.raises

from app.persistencia.migrations import MIGRATIONS
from app.persistencia.migrations.executor import executar_migrations


def criar_banco_migrado() -> sqlite3.Connection:
    """Cria um banco em memória com todas as migrations já aplicadas."""
    # ":memory:" cria um banco 100% em memória e descartável — ideal para
    # testes, pois não altera o arquivo real data/plataforma.db.
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row  # acesso às colunas por nome
    # Aplicamos todas as migrations para que o schema exista antes de testar.
    executar_migrations(conexao, MIGRATIONS)
    return conexao


def criar_materia(conexao: sqlite3.Connection) -> int:
    """Insere uma matéria mínima válida e devolve seu id gerado."""
    # A tabela 'modulo' exige materia_id válido (FK para materia.id),
    # por isso os testes criam primeiro a matéria dona.
    cursor = conexao.execute(
        """
        INSERT INTO materia (nome, descricao, ativa, ordem, data_criacao, data_atualizacao)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "Lógica de Programação",
            "Fundamentos da lógica de programação.",
            1,
            1,
            "2024-01-01T10:00:00+00:00",
            "2024-01-01T10:00:00+00:00",
        ),
    )
    conexao.commit()
    return cursor.lastrowid # type: ignore


def inserir_modulo(
    conexao: sqlite3.Connection,
    *,
    materia_id: int,
    nome: str = "Variáveis",
    descricao: str | None = "Conceitos de variáveis.",
    ativa: int = 1,
    ordem: int = 0,
) -> int:
    """Insere um módulo mínimo válido e devolve seu id gerado."""
    cursor = conexao.execute(
        """
        INSERT INTO modulo (materia_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            materia_id,
            nome,
            descricao,
            ativa,
            ordem,
            "2024-01-02T10:00:00+00:00",
            "2024-01-02T10:00:00+00:00",
        ),
    )
    conexao.commit()
    return cursor.lastrowid # type: ignore


def test_modulo_existe_como_tabela() -> None:
    # A migration deve criar a tabela 'modulo' no schema final.
    conexao = criar_banco_migrado()
    try:
        linha = conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'modulo'"
        ).fetchone()

        assert linha is not None
    finally:
        conexao.close()


def test_modulo_possui_colunas_nas_configuracoes_esperadas() -> None:
    # PRAGMA table_info(modulo) devolve a definição das colunas da tabela.
    # Cada tupla tem (cid, name, type, notnull, dflt_value, pk).
    conexao = criar_banco_migrado()
    try:
        colunas = {
            coluna[1]: coluna for coluna in conexao.execute("PRAGMA table_info(modulo)")
        }

        assert set(colunas) == {
            "id",
            "materia_id",
            "nome",
            "descricao",
            "ativa",
            "ordem",
            "data_criacao",
            "data_atualizacao",
        }

        assert colunas["id"][2] == "INTEGER"
        assert colunas["id"][5] == 1  # flag 'pk' = 1 -> é chave primária

        assert colunas["materia_id"][2] == "INTEGER"
        assert colunas["materia_id"][3] == 1  # NOT NULL

        assert colunas["nome"][2] == "TEXT"
        assert colunas["nome"][3] == 1  # NOT NULL

        assert colunas["descricao"][2] == "TEXT"
        assert colunas["descricao"][3] == 0  # pode ser NULL

        assert colunas["ativa"][2] == "INTEGER"
        assert colunas["ativa"][3] == 1  # NOT NULL
        assert colunas["ativa"][4] == "1"  # DEFAULT 1

        assert colunas["ordem"][2] == "INTEGER"
        assert colunas["ordem"][3] == 1  # NOT NULL
        assert colunas["ordem"][4] == "0"  # DEFAULT 0

        assert colunas["data_criacao"][2] == "TEXT"
        assert colunas["data_criacao"][3] == 1  # NOT NULL

        assert colunas["data_atualizacao"][2] == "TEXT"
        assert colunas["data_atualizacao"][3] == 1  # NOT NULL
    finally:
        conexao.close()


def test_modulo_usa_chave_primaria_sem_autoincrement_explicito() -> None:
    # O 'id' deve ser INTEGER PRIMARY KEY sem a palavra AUTOINCREMENT no DDL.
    conexao = criar_banco_migrado()
    try:
        linha = conexao.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'modulo'"
        ).fetchone()

        assert linha is not None
        assert "AUTOINCREMENT" not in linha[0].upper()
    finally:
        conexao.close()


def test_modulo_rejeita_materia_id_nulo() -> None:
    # 'materia_id' é obrigatório: NULL viola o NOT NULL.
    conexao = criar_banco_migrado()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO modulo (materia_id, nome, data_criacao, data_atualizacao)
                VALUES (NULL, 'Variáveis', '2024-01-02T10:00:00+00:00', '2024-01-02T10:00:00+00:00')
                """
            )
    finally:
        conexao.close()


def test_modulo_aplica_defaults_de_ativa_e_ordem() -> None:
    # Omitindo 'ativa' e 'ordem', o SQLite aplica os padrões 1 e 0.
    conexao = criar_banco_migrado()
    try:
        materia_id = criar_materia(conexao)

        cursor = conexao.execute(
            """
            INSERT INTO modulo (materia_id, nome, data_criacao, data_atualizacao)
            VALUES (?, 'Variáveis', '2024-01-02T10:00:00+00:00', '2024-01-02T10:00:00+00:00')
            """,
            (materia_id,),
        )
        conexao.commit()

        linha = conexao.execute(
            "SELECT ativa, ordem FROM modulo WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        assert linha["ativa"] == 1
        assert linha["ordem"] == 0
    finally:
        conexao.close()


def test_modulo_rejeita_nome_nulo_vazio_ou_somente_espacos() -> None:
    # O CHECK de nome bloqueia vazio e so-espacos; o NOT NULL bloqueia NULL.
    conexao = criar_banco_migrado()
    try:
        materia_id = criar_materia(conexao)

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO modulo (materia_id, nome, data_criacao, data_atualizacao)
                VALUES (?, NULL, '2024-01-02T10:00:00+00:00', '2024-01-02T10:00:00+00:00')
                """,
                (materia_id,),
            )

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO modulo (materia_id, nome, data_criacao, data_atualizacao)
                VALUES (?, '', '2024-01-02T10:00:00+00:00', '2024-01-02T10:00:00+00:00')
                """,
                (materia_id,),
            )

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO modulo (materia_id, nome, data_criacao, data_atualizacao)
                VALUES (?, '   ', '2024-01-02T10:00:00+00:00', '2024-01-02T10:00:00+00:00')
                """,
                (materia_id,),
            )
    finally:
        conexao.close()


def test_modulo_rejeita_ativa_fora_de_zero_e_um() -> None:
    # O CHECK (ativa IN (0, 1)) permite so os dois estados validos.
    conexao = criar_banco_migrado()
    try:
        materia_id = criar_materia(conexao)

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO modulo (materia_id, nome, ativa, data_criacao, data_atualizacao)
                VALUES (?, 'Variaveis', 2, '2024-01-02T10:00:00+00:00', '2024-01-02T10:00:00+00:00')
                """,
                (materia_id,),
            )
    finally:
        conexao.close()

def test_modulo_rejeita_datas_obrigatorias_nulas() -> None:
    # 'data_criacao' e 'data_atualizacao' sao NOT NULL.
    conexao = criar_banco_migrado()
    try:
        materia_id = criar_materia(conexao)

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO modulo (materia_id, nome, data_criacao, data_atualizacao)
                VALUES (?, 'Variaveis', NULL, '2024-01-02T10:00:00+00:00')
                """,
                (materia_id,),
            )

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO modulo (materia_id, nome, data_criacao, data_atualizacao)
                VALUES (?, 'Variaveis', '2024-01-02T10:00:00+00:00', NULL)
                """,
                (materia_id,),
            )
    finally:
        conexao.close()


def test_modulo_aceita_descricao_nula() -> None:
    # 'descricao' e opcional: NULL deve ser aceito e preservado.
    conexao = criar_banco_migrado()
    try:
        materia_id = criar_materia(conexao)
        modulo_id = inserir_modulo(conexao, materia_id=materia_id, descricao=None)

        linha = conexao.execute(
            "SELECT descricao FROM modulo WHERE id = ?",
            (modulo_id,),
        ).fetchone()

        assert linha["descricao"] is None
    finally:
        conexao.close()

def test_modulo_referencia_materia_existente() -> None:
    # PRAGMA foreign_key_list(modulo) deve declarar a FK para materia(id).
    conexao = criar_banco_migrado()
    try:
        chaves = conexao.execute("PRAGMA foreign_key_list(modulo)").fetchall()

        assert len(chaves) == 1
        assert chaves[0][2] == "materia"
        assert chaves[0][3] == "materia_id"
        assert chaves[0][4] == "id"
        assert chaves[0][6].upper() == "NO ACTION"

        ddl = conexao.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'modulo'"
        ).fetchone()[0]

        assert "ON DELETE CASCADE" not in ddl.upper()
    finally:
        conexao.close()


def test_modulo_nao_permite_materia_inexistente() -> None:
    # Com FK ativa, apontar para materia inexistente viola a integridade.
    conexao = criar_banco_migrado()
    try:
        conexao.execute("PRAGMA foreign_keys = ON")

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO modulo (materia_id, nome, data_criacao, data_atualizacao)
                VALUES (999999, 'Variaveis', '2024-01-02T10:00:00+00:00', '2024-01-02T10:00:00+00:00')
                """
            )
    finally:
        conexao.close()


def test_modulo_permite_repetir_ordem() -> None:
    # Sem UNIQUE em 'ordem': dois modulos da mesma materia podem repeti-la.
    conexao = criar_banco_migrado()
    try:
        materia_id = criar_materia(conexao)
        primeiro = inserir_modulo(conexao, materia_id=materia_id, nome="A", ordem=1)
        segundo = inserir_modulo(conexao, materia_id=materia_id, nome="B", ordem=1)

        assert primeiro != segundo

        ordens = [
            linha[0]
            for linha in conexao.execute(
                "SELECT ordem FROM modulo WHERE materia_id = ? ORDER BY id",
                (materia_id,),
            ).fetchall()
        ]

        assert ordens == [1, 1]
    finally:
        conexao.close()


def test_modulo_nao_cria_indices_extras() -> None:
    # A migration nao deve criar indices, triggers ou views para 'modulo'.
    conexao = criar_banco_migrado()
    try:
        indices = conexao.execute("PRAGMA index_list(modulo)").fetchall()
        triggers = conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'modulo'"
        ).fetchall()
        views = conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view' AND tbl_name = 'modulo'"
        ).fetchall()

        assert indices == []
        assert triggers == []
        assert views == []
    finally:
        conexao.close()


