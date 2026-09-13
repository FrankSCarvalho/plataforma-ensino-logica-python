import sqlite3
from datetime import datetime

from app.dominio.nivel import Nivel


def inserir_nivel(conexao: sqlite3.Connection, nivel: Nivel) -> Nivel:
    """Persiste um nível e devolve a entidade com o identificador gerado."""
    if nivel.id is not None:
        raise ValueError("Um novo nível não deve possuir identificador definido.")

    cursor = conexao.execute(
        """
        INSERT INTO nivel (
            habilidade_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nivel.habilidade_id,
            nivel.nome,
            nivel.descricao,
            int(nivel.ativa),
            nivel.ordem,
            nivel.data_criacao.isoformat(),
            nivel.data_atualizacao.isoformat(),
        ),
    )

    return Nivel(
        id=cursor.lastrowid,
        habilidade_id=nivel.habilidade_id,
        nome=nivel.nome,
        descricao=nivel.descricao,
        ativa=nivel.ativa,
        ordem=nivel.ordem,
        data_criacao=nivel.data_criacao,
        data_atualizacao=nivel.data_atualizacao,
    )


def obter_nivel_por_id(conexao: sqlite3.Connection, nivel_id: int) -> Nivel | None:
    """Recupera um nível pelo identificador interno."""
    linha = conexao.execute(
        """
        SELECT id, habilidade_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        FROM nivel
        WHERE id = ?
        """,
        (nivel_id,),
    ).fetchone()

    if linha is None:
        return None

    return Nivel(
        id=linha["id"],
        habilidade_id=linha["habilidade_id"],
        nome=linha["nome"],
        descricao=linha["descricao"],
        ativa=bool(linha["ativa"]),
        ordem=linha["ordem"],
        data_criacao=datetime.fromisoformat(linha["data_criacao"]),
        data_atualizacao=datetime.fromisoformat(linha["data_atualizacao"]),
    )


def atualizar_nivel(conexao: sqlite3.Connection, nivel: Nivel) -> Nivel | None:
    """Atualiza um nível existente, preservando identidade e vínculo estrutural."""
    if nivel.id is None:
        raise ValueError("Um nível sem identificador não pode ser atualizado.")

    linha = conexao.execute(
        "SELECT habilidade_id FROM nivel WHERE id = ?",
        (nivel.id,),
    ).fetchone()
    if linha is None:
        return None

    habilidade_id_persistido = linha["habilidade_id"]
    conexao.execute(
        """
        UPDATE nivel
        SET nome = ?, descricao = ?, ativa = ?, ordem = ?,
            data_criacao = ?, data_atualizacao = ?
        WHERE id = ?
        """,
        (
            nivel.nome,
            nivel.descricao,
            int(nivel.ativa),
            nivel.ordem,
            nivel.data_criacao.isoformat(),
            nivel.data_atualizacao.isoformat(),
            nivel.id,
        ),
    )

    return Nivel(
        id=nivel.id,
        habilidade_id=habilidade_id_persistido,
        nome=nivel.nome,
        descricao=nivel.descricao,
        ativa=nivel.ativa,
        ordem=nivel.ordem,
        data_criacao=nivel.data_criacao,
        data_atualizacao=nivel.data_atualizacao,
    )
