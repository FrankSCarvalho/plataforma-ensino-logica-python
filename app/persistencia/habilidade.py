import sqlite3

from datetime import datetime  # Usado para converter o texto ISO 8601 do SQLite de volta para datetime
from app.dominio.habilidade import Habilidade


def inserir_habilidade(conexao: sqlite3.Connection, habilidade: Habilidade) -> Habilidade:
    """Persiste uma habilidade e devolve a entidade com o identificador gerado."""
    # Invariante: o id é responsabilidade EXCLUSIVA do banco (autoincrement).
    # Se o chamador envia um id, a habilidade já existe (estado inconsistente).
    if habilidade.id is not None:
        raise ValueError("Uma nova habilidade não deve possuir identificador definido.")

    # Usamos o marcador '?' e passamos os valores como tupla: isso evita
    # injeção SQL, pois o SQLite faz o escape do conteúdo automaticamente.
    # A conversão domínio -> SQLite acontece aqui:
    #   - ativa (bool)            -> 0 ou 1
    #   - datas (datetime)        -> texto ISO 8601 (UTC)
    cursor = conexao.execute(
        """
        INSERT INTO habilidade (
            modulo_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            habilidade.modulo_id,
            habilidade.nome,
            habilidade.descricao,
            int(habilidade.ativa),
            habilidade.ordem,
            habilidade.data_criacao.isoformat(),
            habilidade.data_atualizacao.isoformat(),
        ),
    )

    # cursor.lastrowid contém o id autogerado pela PRIMARY KEY (autoincrement).
    # Devolvemos uma NOVA entidade com id (a original é frozen/imutável).
    return Habilidade(
        id=cursor.lastrowid,
        modulo_id=habilidade.modulo_id,
        nome=habilidade.nome,
        descricao=habilidade.descricao,
        ativa=habilidade.ativa,
        ordem=habilidade.ordem,
        data_criacao=habilidade.data_criacao,
        data_atualizacao=habilidade.data_atualizacao,
    )


def obter_habilidade_por_id(
    conexao: sqlite3.Connection,
    habilidade_id: int,
) -> Habilidade | None:
    """Recupera uma habilidade pelo identificador interno."""
    # fetchone() devolve apenas a primeira linha do resultado
    # (ou None se não houver nenhuma).
    linha = conexao.execute(
        """
        SELECT id, modulo_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        FROM habilidade
        WHERE id = ?
        """,
        (habilidade_id,),
    ).fetchone()

    # Devolvemos None (em vez de lançar exceção) para o chamador
    # decidir como tratar a ausência do registro (padrão de busca).
    if linha is None:
        return None

    # Conversão SQLite -> domínio: 'ativa' volta a ser bool e
    # as datas voltam a ser datetime a partir do texto ISO 8601.
    return Habilidade(
        id=linha["id"],
        modulo_id=linha["modulo_id"],
        nome=linha["nome"],
        descricao=linha["descricao"],
        ativa=bool(linha["ativa"]),
        ordem=linha["ordem"],
        data_criacao=datetime.fromisoformat(linha["data_criacao"]),
        data_atualizacao=datetime.fromisoformat(linha["data_atualizacao"]),
    )


def atualizar_habilidade(
    conexao: sqlite3.Connection,
    habilidade: Habilidade,
) -> Habilidade | None:
    """Atualiza os dados de uma habilidade existente, preservando a identidade."""
    # Uma habilidade só pode ser atualizada se já possuir id atribuído pelo banco.
    if habilidade.id is None:
        raise ValueError("Uma habilidade sem identificador não pode ser atualizada.")

    # O WHERE usa o id: a identidade é preservada e a operação nunca cria
    # um novo registro (UPDATE não insere). Um id inexistente devolve None,
    # seguindo o padrão de busca sem resultado adotado pelo projeto.
    # Lemos o 'modulo_id' persistido (e não usamos cursor.rowcount), pois um
    # UPDATE cujos valores são idênticos aos já persistidos pode resultar
    # em rowcount == 0 mesmo com a linha existindo.
    existente = conexao.execute(
        "SELECT modulo_id FROM habilidade WHERE id = ?",
        (habilidade.id,),
    ).fetchone()
    if existente is None:
        return None

    # O vínculo estrutural com o módulo é preservado: o 'modulo_id' da
    # entidade recebida NUNCA é usado para alterar o registro. Mover uma
    # habilidade entre módulos está fora do escopo desta operação.
    modulo_id_persistido = existente["modulo_id"]

    # Nesta subetapa (F2-003.2) a atualização persiste os atributos recebidos
    # da entidade, incluindo as datas definidas por ela; a regra automática
    # de data_atualizacao por alteração efetiva pertence à F2-003.3.
    # O 'modulo_id' fica fora do SET: o UPDATE não pode alterá-lo.
    conexao.execute(
        """
        UPDATE habilidade
        SET nome = ?, descricao = ?, ativa = ?, ordem = ?,
            data_criacao = ?, data_atualizacao = ?
        WHERE id = ?
        """,
        (
            habilidade.nome,
            habilidade.descricao,
            int(habilidade.ativa),
            habilidade.ordem,
            habilidade.data_criacao.isoformat(),
            habilidade.data_atualizacao.isoformat(),
            habilidade.id,
        ),
    )

    # Devolvemos uma NOVA entidade (a original é frozen/imutável), com o
    # mesmo id e o modulo_id PERSISTIDO (não o recebido do chamador).
    return Habilidade(
        id=habilidade.id,
        modulo_id=modulo_id_persistido,
        nome=habilidade.nome,
        descricao=habilidade.descricao,
        ativa=habilidade.ativa,
        ordem=habilidade.ordem,
        data_criacao=habilidade.data_criacao,
        data_atualizacao=habilidade.data_atualizacao,
    )
