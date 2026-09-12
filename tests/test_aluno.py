import sqlite3  # Driver SQLite: usado para criar conexões e detectar IntegrityError

import pytest  # Framework de test: fornece pytest.raises, fixtures, etc.

# Importamos usando a MESMA via que o código de produção (pacote 'app'),
# para que os testes exercitem exatamente o que a aplicação usará.
from app.dominio.aluno import Aluno
from app.persistencia.aluno import inserir_aluno, obter_aluno_por_id
from app.persistencia.migrations import MIGRATIONS
from app.persistencia.migrations.executor import executar_migrations


def criar_banco_com_aluno() -> sqlite3.Connection:
    """Cria um banco em memória já migrado, com a tabela 'aluno' pronta."""
    # ":memory:" cria um banco 100% em memória e descartável — ideal para
    # testes, pois não altera o arquivo real data/plataforma.db.
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row  # acesso às colunas por nome
    # Aplicamos todas as migrations para que o schema exista antes de testar.
    executar_migrations(conexao, MIGRATIONS)
    return conexao


def test_aluno_exige_nome_valido() -> None:
    # A entidade do DOMÍNIO deve rejeitar nomes inválidos antes de qualquer
    # contato com o banco (proteção na camada mais baixa do modelo).
    with pytest.raises(ValueError):
        Aluno(id=None, nome="")  # nome vazio

    with pytest.raises(ValueError):
        Aluno(id=None, nome="   ")  # nome composto só por espaços


def test_dois_alunos_podem_ter_o_mesmo_nome() -> None:
    # O schema NÃO define UNIQUE sobre 'nome'; portanto, permitir duplicados
    # é um comportamento esperado (cada registro recebe um id distinto).
    conexao = criar_banco_com_aluno()

    primeiro = inserir_aluno(conexao, Aluno(id=None, nome="João"))
    segundo = inserir_aluno(conexao, Aluno(id=None, nome="João"))
    conexao.commit()  # Confirmamos a transação no banco

    assert primeiro.id is not None
    assert segundo.id is not None
    assert primeiro.id != segundo.id  # ids únicos, mesmo com nomes iguais


def test_insercao_gera_id_e_recuperacao_preserva_dados() -> None:
    # Fluxo "redondo" do CRUD: inserir -> obter id -> recuperar por id.
    conexao = criar_banco_com_aluno()

    criado = inserir_aluno(conexao, Aluno(id=None, nome="Maria"))
    conexao.commit()

    recuperado = obter_aluno_por_id(conexao, criado.id)  # type: ignore

    assert recuperado == criado  # a dataclass compara campos (id e nome)
    assert recuperado is not None
    assert recuperado.id == criado.id
    assert recuperado.nome == "Maria"


def test_recuperacao_de_aluno_inexistente_retorna_none() -> None:
    # Buscar algo que não existe deve devolver None (e não lançar exceção).
    conexao = criar_banco_com_aluno()

    assert obter_aluno_por_id(conexao, 999999) is None


def test_entidade_existente_nao_e_inserida_novamente() -> None:
    # Invariante de persistência: um aluno que já possui id (persistido)
    # não pode ser inserido de novo como se fosse novo.
    conexao = criar_banco_com_aluno()
    aluno = inserir_aluno(conexao, Aluno(id=None, nome="Carlos"))
    conexao.commit()

    with pytest.raises(ValueError):
        inserir_aluno(conexao, aluno)


def test_banco_rejeita_nome_nulo() -> None:
    # A CONSTRAINT NOT NULL da migration é a última barreira de defesa:
    # mesmo quem contorne a entidade não conseguirá guardar NULL.
    conexao = criar_banco_com_aluno()

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute("INSERT INTO aluno (nome) VALUES (NULL)")


def test_banco_rejeita_nome_vazio() -> None:
    # A CHECK (length(trim(nome)) > 0) impede strings vazias ou só espaços
    # de ser persistidas, mesmo via SQL direto.
    conexao = criar_banco_com_aluno()

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute("INSERT INTO aluno (nome) VALUES ('   ')")