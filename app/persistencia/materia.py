import sqlite3

from datetime import datetime, timezone  # timezone garante o "agora" em UTC ao versionar a atualização
from app.dominio.materia import Materia


def inserir_materia(conexao: sqlite3.Connection, materia: Materia) -> Materia:
    """Persiste uma matéria e devolve a entidade com o identificador gerado."""
    # Invariante: o id é responsabilidade EXCLUSIVA do banco (autoincrement).
    # Se o chamador envia um id, a matéria já existe (estado inconsistente).
    if materia.id is not None:
        raise ValueError("Uma nova matéria não deve possuir identificador definido.")

    # Usamos o marcador '?' e passamos os valores como tupla: isso evita
    # injeção SQL, pois o SQLite faz o escape do conteúdo automaticamente.
    # A conversão domínio -> SQLite acontece aqui:
    #   - ativa (bool)            -> 0 ou 1
    #   - datas (datetime)        -> texto ISO 8601 (UTC)
    cursor = conexao.execute(
        """
        INSERT INTO materia (
            nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            materia.nome,
            materia.descricao,
            int(materia.ativa),
            materia.ordem,
            materia.data_criacao.isoformat(),
            materia.data_atualizacao.isoformat(),
        ),
    )

    # cursor.lastrowid contém o id autogerado pela PRIMARY KEY (autoincrement).
    # Devolvemos uma NOVA entidade com id (a original é frozen/imutável).
    return Materia(
        id=cursor.lastrowid,
        nome=materia.nome,
        descricao=materia.descricao,
        ativa=materia.ativa,
        ordem=materia.ordem,
        data_criacao=materia.data_criacao,
        data_atualizacao=materia.data_atualizacao,
    )


def obter_materia_por_id(
    conexao: sqlite3.Connection,
    materia_id: int,
) -> Materia | None:
    """Recupera uma matéria pelo identificador interno."""
    # fetchone() devolve apenas a primeira linha do resultado
    # (ou None se não houver nenhuma).
    linha = conexao.execute(
        """
        SELECT id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        FROM materia
        WHERE id = ?
        """,
        (materia_id,),
    ).fetchone()

    # Devolvemos None (em vez de lançar exceção) para o chamador
    # decidir como tratar a ausência do registro (padrão de busca).
    if linha is None:
        return None

    # Conversão SQLite -> domínio: 'ativa' volta a ser bool e
    # as datas voltam a ser datetime a partir do texto ISO 8601.
    return Materia(
        id=linha["id"],
        nome=linha["nome"],
        descricao=linha["descricao"],
        ativa=bool(linha["ativa"]),
        ordem=linha["ordem"],
        data_criacao=datetime.fromisoformat(linha["data_criacao"]),
        data_atualizacao=datetime.fromisoformat(linha["data_atualizacao"]),
    )


def atualizar_materia(conexao: sqlite3.Connection, materia: Materia) -> Materia | None:
    """Atualiza os dados de uma matéria existente, preservando a identidade."""
    # Uma matéria só pode ser atualizada se já possuir id atribuído pelo banco.
    if materia.id is None:
        raise ValueError("Uma matéria sem identificador não pode ser atualizada.")

    # O WHERE usa o id: a identidade é preservada e a operação nunca cria
    # um novo registro (UPDATE não insere). Um id inexistente devolve None,
    # seguindo o padrão de busca sem resultado adotado pelo projeto.
    # Lemos a linha persistida (e não usamos cursor.rowcount), pois um
    # UPDATE cujos valores são idênticos aos já persistidos pode resultar
    # em rowcount == 0 mesmo com a linha existindo.
    linha = conexao.execute(
        """
        SELECT nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        FROM materia
        WHERE id = ?
        """,
        (materia.id,),
    ).fetchone()
    if linha is None:
        return None

    # 'data_criacao' é imutável: mesmo que o chamador envie outro valor,
    # o UPDATE nunca a altera (integridade do registro).
    # Há alteração efetiva quando pelo menos um dos campos editáveis
    # (nome, descricao, ativa ou ordem) difere do que está persistido.
    houve_alteracao = (
        materia.nome != linha["nome"]
        or materia.descricao != linha["descricao"]
        or int(materia.ativa) != linha["ativa"]
        or materia.ordem != linha["ordem"]
    )

    # 'data_atualizacao' e controlada exclusivamente pela persistencia:
    # havendo alteracao efetiva, gera o instante atual em UTC
    # (timezone-aware); sem alteracao efetiva, preserva exatamente
    # a 'data_atualizacao' persistida. O valor enviado pelo chamador
    # nunca e honrado.
    persistida_atualizacao = datetime.fromisoformat(linha["data_atualizacao"])
    if houve_alteracao:
        data_atualizacao = datetime.now(timezone.utc)
    else:
        data_atualizacao = persistida_atualizacao

    conexao.execute(
        """
        UPDATE materia
        SET nome = ?, descricao = ?, ativa = ?, ordem = ?,
            data_atualizacao = ?
        WHERE id = ?
        """,
        (
            materia.nome,
            materia.descricao,
            int(materia.ativa),
            materia.ordem,
            data_atualizacao.isoformat(),
            materia.id,
        ),
    )

    # Devolvemos uma NOVA entidade (a original é frozen/imutável), com o
    # mesmo id, a data_criacao persistida e a data_atualizacao resultante
    # da regra acima.
    return Materia(
        id=materia.id,
        nome=materia.nome,
        descricao=materia.descricao,
        ativa=materia.ativa,
        ordem=materia.ordem,
        data_criacao=datetime.fromisoformat(linha["data_criacao"]),
        data_atualizacao=data_atualizacao,
    )