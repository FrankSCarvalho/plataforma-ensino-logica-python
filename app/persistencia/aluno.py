import sqlite3

from app.dominio.aluno import Aluno


def inserir_aluno(conexao: sqlite3.Connection, aluno: Aluno) -> Aluno:
    """Persiste um aluno e devolve a entidade com o identificador gerado."""
    # Invariante: o id é responsabilidade EXCLUSIVA do banco (autoincrement).
    # Se o chamador envia um id, o aluno já existe (estado inconsistente).
    if aluno.id is not None:
        raise ValueError("Um novo aluno não deve possuir identificador definido.")

    # Usamos o marcador '?' e passamos os valores como tupla: isso evita
    # injeção SQL, pois o SQLite faz o escape do conteúdo automaticamente.
    cursor = conexao.execute(
        "INSERT INTO aluno (nome) VALUES (?)",
        (aluno.nome,),
    )

    # cursor.lastrowid contém o id autogerado pela PRIMARY KEY (autoincrement).
    # Devolvemos uma NOVA entidade com id (a original é frozen/imutável).
    return Aluno(id=cursor.lastrowid, nome=aluno.nome)


def obter_aluno_por_id(
    conexao: sqlite3.Connection,
    aluno_id: int,
) -> Aluno | None:
    """Recupera um aluno pelo identificador interno."""
    # fetchone() devolve apenas a primeira linha do resultado
    # (ou None se não houver nenhuma).
    linha = conexao.execute(
        "SELECT id, nome FROM aluno WHERE id = ?",
        (aluno_id,),
    ).fetchone()

    # Devolvemos None (em vez de lançar exceção) para o chamador
    # decidir como tratar a ausência do registro (padrão de busca).
    if linha is None:
        return None

    # Graças a row_factory=sqlite3.Row, acessamos cada coluna por nome.
    return Aluno(id=linha["id"], nome=linha["nome"])