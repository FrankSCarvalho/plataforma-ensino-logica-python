import sqlite3
from datetime import datetime, timezone

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
        """
        SELECT habilidade_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        FROM nivel
        WHERE id = ?
        """,
        (nivel.id,),
    ).fetchone()
    if linha is None:
        return None

    houve_alteracao = (
        nivel.nome != linha["nome"]
        or nivel.descricao != linha["descricao"]
        or int(nivel.ativa) != linha["ativa"]
        or nivel.ordem != linha["ordem"]
    )
    data_atualizacao_persistida = datetime.fromisoformat(linha["data_atualizacao"])
    data_atualizacao = (
        datetime.now(timezone.utc)
        if houve_alteracao
        else data_atualizacao_persistida
    )
    habilidade_id_persistido = linha["habilidade_id"]
    data_criacao_persistida = datetime.fromisoformat(linha["data_criacao"])
    conexao.execute(
        """
        UPDATE nivel
        SET nome = ?, descricao = ?, ativa = ?, ordem = ?,
            data_atualizacao = ?
        WHERE id = ?
        """,
        (
            nivel.nome,
            nivel.descricao,
            int(nivel.ativa),
            nivel.ordem,
            data_atualizacao.isoformat(),
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
        data_criacao=data_criacao_persistida,
        data_atualizacao=data_atualizacao,
    )


def ativar_nivel(conexao: sqlite3.Connection, nivel_id: int) -> Nivel | None:
    """Ativa um nível existente, preservando identidade e vínculo estrutural."""
    atual = obter_nivel_por_id(conexao, nivel_id)
    if atual is None:
        return None

    return atualizar_nivel(
        conexao,
        Nivel(
            id=atual.id,
            habilidade_id=atual.habilidade_id,
            nome=atual.nome,
            descricao=atual.descricao,
            ativa=True,
            ordem=atual.ordem,
            data_criacao=atual.data_criacao,
            data_atualizacao=atual.data_atualizacao,
        ),
    )


def desativar_nivel(conexao: sqlite3.Connection, nivel_id: int) -> Nivel | None:
    """Desativa um nível existente, sem excluir seu registro."""
    atual = obter_nivel_por_id(conexao, nivel_id)
    if atual is None:
        return None

    return atualizar_nivel(
        conexao,
        Nivel(
            id=atual.id,
            habilidade_id=atual.habilidade_id,
            nome=atual.nome,
            descricao=atual.descricao,
            ativa=False,
            ordem=atual.ordem,
            data_criacao=atual.data_criacao,
            data_atualizacao=atual.data_atualizacao,
        ),
    )


def reativar_nivel(conexao: sqlite3.Connection, nivel_id: int) -> Nivel | None:
    """Reativa um nível existente."""
    return ativar_nivel(conexao, nivel_id)
