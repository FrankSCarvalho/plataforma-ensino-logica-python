import sqlite3

from datetime import datetime, timezone  # timezone garante o "agora" em UTC ao versionar a atualização
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
    # Lemos a linha persistida (e não usamos cursor.rowcount), pois um
    # UPDATE cujos valores são idênticos aos já persistidos pode resultar
    # em rowcount == 0 mesmo com a linha existindo.
    linha = conexao.execute(
        """
        SELECT materia_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        FROM modulo
        WHERE id = ?
        """,
        (modulo.id,),
    ).fetchone()
    if linha is None:
        return None

    # 'data_criacao' é imutável: mesmo que o chamador envie outro valor,
    # o UPDATE nunca a altera (integridade do registro).
    # Há alteração efetiva quando pelo menos um dos campos editáveis
    # (nome, descricao, ativa ou ordem) difere do que está persistido.
    houve_alteracao = (
        modulo.nome != linha["nome"]
        or modulo.descricao != linha["descricao"]
        or int(modulo.ativa) != linha["ativa"]
        or modulo.ordem != linha["ordem"]
    )

    # 'data_atualizacao' é controlada exclusivamente pela persistência:
    # havendo alteração efetiva, gera o instante atual em UTC
    # (timezone-aware); sem alteração efetiva, preserva exatamente
    # a 'data_atualizacao' persistida. O valor enviado pelo chamador
    # nunca é honrado.
    persistida_atualizacao = datetime.fromisoformat(linha["data_atualizacao"])
    if houve_alteracao:
        data_atualizacao = datetime.now(timezone.utc)
    else:
        data_atualizacao = persistida_atualizacao

    conexao.execute(
        """
        UPDATE modulo
        SET materia_id = ?, nome = ?, descricao = ?, ativa = ?, ordem = ?,
            data_atualizacao = ?
        WHERE id = ?
        """,
        (
            modulo.materia_id,
            modulo.nome,
            modulo.descricao,
            int(modulo.ativa),
            modulo.ordem,
            data_atualizacao.isoformat(),
            modulo.id,
        ),
    )

    # Devolvemos uma NOVA entidade (a original é frozen/imutável), com o
    # mesmo id, o mesmo materia_id, a data_criacao persistida e a
    # data_atualizacao resultante da regra acima.
    return Modulo(
        id=modulo.id,
        materia_id=linha["materia_id"],
        nome=modulo.nome,
        descricao=modulo.descricao,
        ativa=modulo.ativa,
        ordem=modulo.ordem,
        data_criacao=datetime.fromisoformat(linha["data_criacao"]),
        data_atualizacao=data_atualizacao,
    )


def ativar_modulo(conexao: sqlite3.Connection, modulo_id: int) -> Modulo | None:
    """Ativa um módulo existente (ativa=True), preservando a identidade."""
    # Buscamos o registro atual para reaproveitar seus dados: a ativação
    # altera apenas 'ativa', sem tocar em nome, descricao, ordem, materia_id
    # ou data_criacao. Um id inexistente devolve None (padrão de busca).
    atual = obter_modulo_por_id(conexao, modulo_id)
    if atual is None:
        return None

    # Reutilizamos atualizar_modulo para que a regra de data_atualizacao
    # (só avança diante de alteração efetiva) seja aplicada de forma única.
    return atualizar_modulo(
        conexao,
        Modulo(
            id=atual.id,
            materia_id=atual.materia_id,
            nome=atual.nome,
            descricao=atual.descricao,
            ativa=True,
            ordem=atual.ordem,
            data_criacao=atual.data_criacao,
            data_atualizacao=atual.data_atualizacao,
        ),
    )


def desativar_modulo(conexao: sqlite3.Connection, modulo_id: int) -> Modulo | None:
    """Desativa um módulo existente (ativa=False), sem excluir o registro."""
    # Desativar não exclui nem altera a identidade: o registro continua
    # recuperável, apenas indisponível para oferta de estudo. Reversível
    # via ativar_modulo. Um id inexistente devolve None (padrão de busca).
    atual = obter_modulo_por_id(conexao, modulo_id)
    if atual is None:
        return None

    # Reutilizamos atualizar_modulo para que a regra de data_atualizacao
    # (só avança diante de alteração efetiva) seja aplicada de forma única.
    return atualizar_modulo(
        conexao,
        Modulo(
            id=atual.id,
            materia_id=atual.materia_id,
            nome=atual.nome,
            descricao=atual.descricao,
            ativa=False,
            ordem=atual.ordem,
            data_criacao=atual.data_criacao,
            data_atualizacao=atual.data_atualizacao,
        ),
    )
