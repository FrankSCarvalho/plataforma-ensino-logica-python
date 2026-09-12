import sqlite3

from datetime import datetime  # Usado para converter o texto ISO 8601 do SQLite de volta para datetime
from app.dominio.modulo import Modulo


def inserir_modulo(conexao: sqlite3.Connection, modulo: Modulo) -> Modulo:
    """Persiste um módulo e devolve a entidade com o identificador gerado."""
    # Invariante: o id é responsabilidade EXCLUSIVA do banco (autoincrement).
    # Se o chamador envia um id, o módulo já existe (estado inconsistente).
    if modulo.id is not None:
        raise ValueError("Um novo módulo não deve possuir identificador definido.")

    # Usamos o marcador '?' e passamos os valores como tupla: isso evita
    # injeção SQL, pois o SQLite faz o escape do conteúdo automaticamente.
    # A conversão domínio -> SQLite acontece aqui:
    #   - ativa (bool)            -> 0 ou 1
    #   - datas (datetime)        -> texto ISO 8601 (UTC)
    cursor = conexao.execute(
        """
        INSERT INTO modulo (
            materia_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            modulo.materia_id,
            modulo.nome,
            modulo.descricao,
            int(modulo.ativa),
            modulo.ordem,
            modulo.data_criacao.isoformat(),
            modulo.data_atualizacao.isoformat(),
        ),
    )

    # cursor.lastrowid contém o id autogerado pela PRIMARY KEY (autoincrement).
    # Devolvemos uma NOVA entidade com id (a original é frozen/imutável).
    return Modulo(
        id=cursor.lastrowid,
        materia_id=modulo.materia_id,
        nome=modulo.nome,
        descricao=modulo.descricao,
        ativa=modulo.ativa,
        ordem=modulo.ordem,
        data_criacao=modulo.data_criacao,
        data_atualizacao=modulo.data_atualizacao,
    )


def obter_modulo_por_id(
    conexao: sqlite3.Connection,
    modulo_id: int,
) -> Modulo | None:
    """Recupera um módulo pelo identificador interno."""
    # fetchone() devolve apenas a primeira linha do resultado
    # (ou None se não houver nenhuma).
    linha = conexao.execute(
        """
        SELECT id, materia_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        FROM modulo
        WHERE id = ?
        """,
        (modulo_id,),
    ).fetchone()

    # Devolvemos None (em vez de lançar exceção) para o chamador
    # decidir como tratar a ausência do registro (padrão de busca).
    if linha is None:
        return None

    # Conversão SQLite -> domínio: 'ativa' volta a ser bool e
    # as datas voltam a ser datetime a partir do texto ISO 8601.
    return Modulo(
        id=linha["id"],
        materia_id=linha["materia_id"],
        nome=linha["nome"],
        descricao=linha["descricao"],
        ativa=bool(linha["ativa"]),
        ordem=linha["ordem"],
        data_criacao=datetime.fromisoformat(linha["data_criacao"]),
        data_atualizacao=datetime.fromisoformat(linha["data_atualizacao"]),
    )


def atualizar_modulo(conexao: sqlite3.Connection, modulo: Modulo) -> Modulo | None:
    """Atualiza os dados de um módulo existente, preservando a identidade."""
    # Um módulo só pode ser atualizado se já possuir id atribuído pelo banco.
    if modulo.id is None:
        raise ValueError("Um módulo sem identificador não pode ser atualizado.")

    # O WHERE usa o id: a identidade é preservada e a operação nunca cria
    # um novo registro (UPDATE não insere). Um id inexistente devolve None,
    # seguindo o padrão de busca sem resultado adotado pelo projeto.
    # A existência é verificada com SELECT (e não com cursor.rowcount),
    # pois um UPDATE cujos valores são idênticos aos já persistidos pode
    # resultar em rowcount == 0 mesmo com a linha existindo.
    existente = conexao.execute(
        "SELECT 1 FROM modulo WHERE id = ?",
        (modulo.id,),
    ).fetchone()
    if existente is None:
        return None

    # Nesta subetapa (F2-002.2) a atualização persiste os atributos recebidos
    # da entidade, sem regra automática de data_atualizacao por alteração
    # efetiva (essa regra pertence à F2-002.3).
    conexao.execute(
        """
        UPDATE modulo
        SET materia_id = ?, nome = ?, descricao = ?, ativa = ?, ordem = ?,
            data_criacao = ?, data_atualizacao = ?
        WHERE id = ?
        """,
        (
            modulo.materia_id,
            modulo.nome,
            modulo.descricao,
            int(modulo.ativa),
            modulo.ordem,
            modulo.data_criacao.isoformat(),
            modulo.data_atualizacao.isoformat(),
            modulo.id,
        ),
    )

    # Devolvemos a entidade atualizada (com o mesmo id).
    return modulo
