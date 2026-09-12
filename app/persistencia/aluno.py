import sqlite3

from app.dominio.aluno import Aluno


def inserir_aluno(conexao: sqlite3.Connection, aluno: Aluno) -> Aluno:
    """Persiste um aluno e devolve a entidade com o identificador gerado."""
    if aluno.id is not None:
        raise ValueError("Um novo aluno não deve possuir identificador definido.")

    cursor = conexao.execute(
        "INSERT INTO aluno (nome) VALUES (?)",
        (aluno.nome,),
    )
    return Aluno(id=cursor.lastrowid, nome=aluno.nome)


def obter_aluno_por_id(
    conexao: sqlite3.Connection,
    aluno_id: int,
) -> Aluno | None:
    """Recupera um aluno pelo identificador interno."""
    linha = conexao.execute(
        "SELECT id, nome FROM aluno WHERE id = ?",
        (aluno_id,),
    ).fetchone()

    if linha is None:
        return None

    return Aluno(id=linha["id"], nome=linha["nome"])