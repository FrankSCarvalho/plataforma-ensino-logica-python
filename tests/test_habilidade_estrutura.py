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


def criar_modulo(conexao: sqlite3.Connection) -> int:
    """Insere um módulo mínimo válido e devolve seu id gerado."""
    # A tabela 'habilidade' exige modulo_id válido (FK para modulo.id),
    # por isso os testes criam primeiro a matéria e o módulo donos.
    materia = conexao.execute(
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
    modulo = conexao.execute(
        """
        INSERT INTO modulo (materia_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            materia.lastrowid,
            "Variáveis",
            "Conceitos de variáveis.",
            1,
            1,
            "2024-01-02T10:00:00+00:00",
            "2024-01-02T10:00:00+00:00",
        ),
    )
    conexao.commit()
    return modulo.lastrowid  # type: ignore


def inserir_habilidade(
    conexao: sqlite3.Connection,
    *,
    modulo_id: int,
    nome: str = "Identificar variáveis",
    descricao: str | None = "Capacidade de identificar variáveis.",
    ativa: int = 1,
    ordem: int = 0,
) -> int:
    """Insere uma habilidade mínima válida e devolve seu id gerado."""
    cursor = conexao.execute(
        """
        INSERT INTO habilidade (modulo_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            modulo_id,
            nome,
            descricao,
            ativa,
            ordem,
            "2024-01-03T10:00:00+00:00",
            "2024-01-03T10:00:00+00:00",
        ),
    )
    conexao.commit()
    return cursor.lastrowid  # type: ignore


def test_habilidade_existe_como_tabela() -> None:
    # A migration deve criar a tabela 'habilidade' no schema final.
    conexao = criar_banco_migrado()
    try:
        linha = conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'habilidade'"
        ).fetchone()

        assert linha is not None
    finally:
        conexao.close()


def test_habilidade_possui_colunas_nas_configuracoes_esperadas() -> None:
    # PRAGMA table_info(habilidade) devolve a definição das colunas da tabela.
    # Cada tupla tem (cid, name, type, notnull, dflt_value, pk).
    conexao = criar_banco_migrado()
    try:
        colunas = {
            coluna[1]: coluna for coluna in conexao.execute("PRAGMA table_info(habilidade)")
        }

        assert set(colunas) == {
            "id",
            "modulo_id",
            "nome",
            "descricao",
            "ativa",
            "ordem",
            "data_criacao",
            "data_atualizacao",
        }

        assert colunas["id"][2] == "INTEGER"
        assert colunas["id"][5] == 1  # flag 'pk' = 1 -> é chave primária

        assert colunas["modulo_id"][2] == "INTEGER"
        assert colunas["modulo_id"][3] == 1  # NOT NULL

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


def test_habilidade_usa_chave_primaria_sem_autoincrement_explicito() -> None:
    # O 'id' deve ser INTEGER PRIMARY KEY sem a palavra AUTOINCREMENT no DDL.
    conexao = criar_banco_migrado()
    try:
        linha = conexao.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'habilidade'"
        ).fetchone()

        assert linha is not None
        assert "AUTOINCREMENT" not in linha[0].upper()
    finally:
        conexao.close()


def test_habilidade_rejeita_modulo_id_nulo() -> None:
    # 'modulo_id' é obrigatório: NULL viola o NOT NULL.
    conexao = criar_banco_migrado()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO habilidade (modulo_id, nome, data_criacao, data_atualizacao)
                VALUES (NULL, 'Identificar variáveis', '2024-01-03T10:00:00+00:00', '2024-01-03T10:00:00+00:00')
                """
            )
    finally:
        conexao.close()


def test_habilidade_aplica_defaults_de_ativa_e_ordem() -> None:
    # Omitindo 'ativa' e 'ordem', o SQLite aplica os padrões 1 e 0.
    conexao = criar_banco_migrado()
    try:
        modulo_id = criar_modulo(conexao)

        cursor = conexao.execute(
            """
            INSERT INTO habilidade (modulo_id, nome, data_criacao, data_atualizacao)
            VALUES (?, 'Identificar variáveis', '2024-01-03T10:00:00+00:00', '2024-01-03T10:00:00+00:00')
            """,
            (modulo_id,),
        )
        conexao.commit()

        linha = conexao.execute(
            "SELECT ativa, ordem FROM habilidade WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        assert linha["ativa"] == 1
        assert linha["ordem"] == 0
    finally:
        conexao.close()


def test_habilidade_rejeita_nome_nulo_vazio_ou_somente_espacos() -> None:
    # O CHECK de nome bloqueia vazio e só-espaços; o NOT NULL bloqueia NULL.
    conexao = criar_banco_migrado()
    try:
        modulo_id = criar_modulo(conexao)

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO habilidade (modulo_id, nome, data_criacao, data_atualizacao)
                VALUES (?, NULL, '2024-01-03T10:00:00+00:00', '2024-01-03T10:00:00+00:00')
                """,
                (modulo_id,),
            )

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO habilidade (modulo_id, nome, data_criacao, data_atualizacao)
                VALUES (?, '', '2024-01-03T10:00:00+00:00', '2024-01-03T10:00:00+00:00')
                """,
                (modulo_id,),
            )

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO habilidade (modulo_id, nome, data_criacao, data_atualizacao)
                VALUES (?, '   ', '2024-01-03T10:00:00+00:00', '2024-01-03T10:00:00+00:00')
                """,
                (modulo_id,),
            )
    finally:
        conexao.close()


def test_habilidade_rejeita_ativa_fora_de_zero_e_um() -> None:
    # O CHECK (ativa IN (0, 1)) permite só os dois estados válidos.
    conexao = criar_banco_migrado()
    try:
        modulo_id = criar_modulo(conexao)

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO habilidade (modulo_id, nome, ativa, data_criacao, data_atualizacao)
                VALUES (?, 'Identificar variáveis', 2, '2024-01-03T10:00:00+00:00', '2024-01-03T10:00:00+00:00')
                """,
                (modulo_id,),
            )
    finally:
        conexao.close()


def test_habilidade_rejeita_datas_obrigatorias_nulas() -> None:
    # 'data_criacao' e 'data_atualizacao' são NOT NULL.
    conexao = criar_banco_migrado()
    try:
        modulo_id = criar_modulo(conexao)

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO habilidade (modulo_id, nome, data_criacao, data_atualizacao)
                VALUES (?, 'Identificar variáveis', NULL, '2024-01-03T10:00:00+00:00')
                """,
                (modulo_id,),
            )

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO habilidade (modulo_id, nome, data_criacao, data_atualizacao)
                VALUES (?, 'Identificar variáveis', '2024-01-03T10:00:00+00:00', NULL)
                """,
                (modulo_id,),
            )
    finally:
        conexao.close()


def test_habilidade_aceita_descricao_nula() -> None:
    # 'descricao' é opcional: NULL deve ser aceito e preservado.
    conexao = criar_banco_migrado()
    try:
        modulo_id = criar_modulo(conexao)
        habilidade_id = inserir_habilidade(conexao, modulo_id=modulo_id, descricao=None)

        linha = conexao.execute(
            "SELECT descricao FROM habilidade WHERE id = ?",
            (habilidade_id,),
        ).fetchone()

        assert linha["descricao"] is None
    finally:
        conexao.close()


def test_habilidade_referencia_modulo_existente() -> None:
    # PRAGMA foreign_key_list(habilidade) deve declarar a FK para modulo(id).
    conexao = criar_banco_migrado()
    try:
        chaves = conexao.execute("PRAGMA foreign_key_list(habilidade)").fetchall()

        assert len(chaves) == 1
        # Colunas do PRAGMA: (id, seq, table, from, to, on_update, on_delete, match).
        assert chaves[0][2] == "modulo"
        assert chaves[0][3] == "modulo_id"
        assert chaves[0][4] == "id"
        assert chaves[0][6].upper() == "NO ACTION"

        ddl = conexao.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'habilidade'"
        ).fetchone()[0]

        assert "ON DELETE CASCADE" not in ddl.upper()
    finally:
        conexao.close()


def test_habilidade_nao_permite_modulo_inexistente() -> None:
    # Com FK ativa, apontar para módulo inexistente viola a integridade.
    conexao = criar_banco_migrado()
    try:
        conexao.execute("PRAGMA foreign_keys = ON")

        with pytest.raises(sqlite3.IntegrityError):
            conexao.execute(
                """
                INSERT INTO habilidade (modulo_id, nome, data_criacao, data_atualizacao)
                VALUES (999999, 'Identificar variáveis', '2024-01-03T10:00:00+00:00', '2024-01-03T10:00:00+00:00')
                """
            )
    finally:
        conexao.close()


def test_habilidade_permite_repetir_ordem() -> None:
    # Sem UNIQUE em 'ordem': duas habilidades do mesmo módulo podem repeti-la.
    conexao = criar_banco_migrado()
    try:
        modulo_id = criar_modulo(conexao)
        primeira = inserir_habilidade(conexao, modulo_id=modulo_id, nome="A", ordem=1)
        segunda = inserir_habilidade(conexao, modulo_id=modulo_id, nome="B", ordem=1)

        assert primeira != segunda

        ordens = [
            linha[0]
            for linha in conexao.execute(
                "SELECT ordem FROM habilidade WHERE modulo_id = ? ORDER BY id",
                (modulo_id,),
            ).fetchall()
        ]

        assert ordens == [1, 1]
    finally:
        conexao.close()


def test_habilidade_nao_cria_indices_extras() -> None:
    # A migration não deve criar índices, triggers ou views para 'habilidade'.
    conexao = criar_banco_migrado()
    try:
        indices = conexao.execute("PRAGMA index_list(habilidade)").fetchall()
        triggers = conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'habilidade'"
        ).fetchall()
        views = conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view' AND tbl_name = 'habilidade'"
        ).fetchall()

        assert indices == []
        assert triggers == []
        assert views == []
    finally:
        conexao.close()


def test_habilidade_nao_antecipa_exercicio_ou_pre_requisito() -> None:
    # A migration v4 cria somente a estrutura da habilidade; tabelas de
    # exercício e pré-requisitos não podem ser antecipadas.
    conexao = criar_banco_migrado()
    try:
        nomes_tabelas = [
            linha[0]
            for linha in conexao.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        ]

        for nome in ("exercicio", "pre_requisito", "pre_requisitos"):
            assert nome not in nomes_tabelas
    finally:
        conexao.close()
