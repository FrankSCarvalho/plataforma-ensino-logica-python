import sqlite3
from datetime import datetime, timezone

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


def ativar_habilidade(conexao: sqlite3.Connection, habilidade_id: int) -> Habilidade | None:
    """Ativa uma habilidade existente (ativa=True), preservando identidade e vínculo."""
    atual = obter_habilidade_por_id(conexao, habilidade_id)
    if atual is None:
        return None

    return atualizar_habilidade(
        conexao,
        Habilidade(
            id=atual.id,
            modulo_id=atual.modulo_id,
            nome=atual.nome,
            descricao=atual.descricao,
            ativa=True,
            ordem=atual.ordem,
            data_criacao=atual.data_criacao,
            data_atualizacao=atual.data_atualizacao,
        ),
    )


def desativar_habilidade(conexao: sqlite3.Connection, habilidade_id: int) -> Habilidade | None:
    """Desativa uma habilidade existente (ativa=False), sem excluir o registro."""
    atual = obter_habilidade_por_id(conexao, habilidade_id)
    if atual is None:
        return None

    return atualizar_habilidade(
        conexao,
        Habilidade(
            id=atual.id,
            modulo_id=atual.modulo_id,
            nome=atual.nome,
            descricao=atual.descricao,
            ativa=False,
            ordem=atual.ordem,
            data_criacao=atual.data_criacao,
            data_atualizacao=atual.data_atualizacao,
        ),
    )


def reativar_habilidade(conexao: sqlite3.Connection, habilidade_id: int) -> Habilidade | None:
    """Reativa uma habilidade existente (ativa=True)."""
    return ativar_habilidade(conexao, habilidade_id)


def atualizar_habilidade(
    conexao: sqlite3.Connection,
    habilidade: Habilidade,
) -> Habilidade | None:
    """Atualiza os dados de uma habilidade existente, preservando a identidade.

    A ``data_atualizacao`` é controlada exclusivamente pela persistência:
    - havendo alteração efetiva em ``nome``, ``descricao``, ``ativa`` ou ``ordem``,
      ela é avançada para o instante atual em UTC (timezone-aware);
    - sem alteração efetiva, o valor persistido é preservado, mesmo que a entidade
      recebida carregue outro ``data_atualizacao``.
    ``data_criacao`` e ``modulo_id`` são imutáveis por atualização.
    """
    # Uma habilidade só pode ser atualizada se já possuir id atribuído pelo banco.
    if habilidade.id is None:
        raise ValueError("Uma habilidade sem identificador não pode ser atualizada.")

    # O WHERE usa o id: a identidade é preservada e a operação nunca cria
    # um novo registro (UPDATE não insere). Um id inexistente devolve None,
    # seguindo o padrão de busca sem resultado adotado pelo projeto.
    # Lemos a linha persistida (e não usamos cursor.rowcount), pois um
    # UPDATE cujos valores são idênticos aos já persistidos pode resultar
    # em rowcount == 0 mesmo com a linha existindo.
    linha = conexao.execute(
        """
        SELECT modulo_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao
        FROM habilidade
        WHERE id = ?
        """,
        (habilidade.id,),
    ).fetchone()
    if linha is None:
        return None

    # 'data_criacao' é imutável: mesmo que o chamador envie outro valor,
    # o UPDATE nunca a altera (integridade do registro).
    # Há alteração efetiva quando pelo menos um dos campos editáveis
    # (nome, descricao, ativa ou ordem) difere do que está persistido.
    houve_alteracao = (
        habilidade.nome != linha["nome"]
        or habilidade.descricao != linha["descricao"]
        or int(habilidade.ativa) != linha["ativa"]
        or habilidade.ordem != linha["ordem"]
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

    # O vínculo estrutural com o módulo é preservado: o 'modulo_id' da
    # entidade recebida NUNCA é usado para alterar o registro. Mover uma
    # habilidade entre módulos está fora do escopo desta operação.
    modulo_id_persistido = linha["modulo_id"]

    conexao.execute(
        """
        UPDATE habilidade
        SET nome = ?, descricao = ?, ativa = ?, ordem = ?,
            data_atualizacao = ?
        WHERE id = ?
        """,
        (
            habilidade.nome,
            habilidade.descricao,
            int(habilidade.ativa),
            habilidade.ordem,
            data_atualizacao.isoformat(),
            habilidade.id,
        ),
    )

    # Devolvemos uma NOVA entidade (a original é frozen/imutável), com o
    # mesmo id, o mesmo modulo_id PERSISTIDO, a data_criacao PERSISTIDA e a
    # data_atualizacao resultante da regra acima.
    return Habilidade(
        id=habilidade.id,
        modulo_id=modulo_id_persistido,
        nome=habilidade.nome,
        descricao=habilidade.descricao,
        ativa=habilidade.ativa,
        ordem=habilidade.ordem,
        data_criacao=datetime.fromisoformat(linha["data_criacao"]),
        data_atualizacao=data_atualizacao,
    )
