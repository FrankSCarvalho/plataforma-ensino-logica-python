import sqlite3

import pytest

from app.dominio.aluno import Aluno
from app.persistencia.aluno import inserir_aluno, obter_aluno_por_id
from app.persistencia.migrations import MIGRATIONS
from app.persistencia.migrations.executor import executar_migrations


def criar_banco_com_aluno() -> sqlite3.Connection:
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row
    executar_migrations(conexao, MIGRATIONS)
    return conexao


def test_aluno_exige_nome_valido() -> None:
    with pytest.raises(ValueError):
        Aluno(id=None, nome="")

    with pytest.raises(ValueError):
        Aluno(id=None, nome="   ")


def test_dois_alunos_podem_ter_o_mesmo_nome() -> None:
    conexao = criar_banco_com_aluno()

    primeiro = inserir_aluno(conexao, Aluno(id=None, nome="João"))
    segundo = inserir_aluno(conexao, Aluno(id=None, nome="João"))
    conexao.commit()

    assert primeiro.id is not None
    assert segundo.id is not None
    assert primeiro.id != segundo.id


def test_insercao_gera_id_e_recuperacao_preserva_dados() -> None:
    conexao = criar_banco_com_aluno()

    criado = inserir_aluno(conexao, Aluno(id=None, nome="Maria"))
    conexao.commit()

    recuperado = obter_aluno_por_id(conexao, criado.id) # type: ignore

    assert recuperado == criado
    assert recuperado is not None
    assert recuperado.id == criado.id
    assert recuperado.nome == "Maria"


def test_recuperacao_de_aluno_inexistente_retorna_none() -> None:
    conexao = criar_banco_com_aluno()

    assert obter_aluno_por_id(conexao, 999999) is None


def test_entidade_existente_nao_e_inserida_novamente() -> None:
    conexao = criar_banco_com_aluno()
    aluno = inserir_aluno(conexao, Aluno(id=None, nome="Carlos"))
    conexao.commit()

    with pytest.raises(ValueError):
        inserir_aluno(conexao, aluno)


def test_banco_rejeita_nome_nulo() -> None:
    conexao = criar_banco_com_aluno()

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute("INSERT INTO aluno (nome) VALUES (NULL)")


def test_banco_rejeita_nome_vazio() -> None:
    conexao = criar_banco_com_aluno()

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute("INSERT INTO aluno (nome) VALUES ('   ')")