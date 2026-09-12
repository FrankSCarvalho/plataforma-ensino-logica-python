import sqlite3  # Driver SQLite: usado para criar conexões e detectar IntegrityError
from datetime import datetime, timezone  # Datas usadas nos testes

import pytest  # Framework de teste: fornece pytest.raises, fixtures, etc.

# Importamos usando a MESMA via que o código de produção (pacote 'app'),
# para que os testes exercitem exatamente o que a aplicação usará.
from app.dominio.materia import Materia
from app.persistencia.materia import (
    atualizar_materia,
    inserir_materia,
    obter_materia_por_id,
)
from app.persistencia.migrations import MIGRATIONS
from app.persistencia.migrations.executor import executar_migrations


def criar_banco_com_materia() -> sqlite3.Connection:
    """Cria um banco em memória já migrado, com a tabela 'materia' pronta."""
    # ":memory:" cria um banco 100% em memória e descartável — ideal para
    # testes, pois não altera o arquivo real data/plataforma.db.
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row  # acesso às colunas por nome
    # Aplicamos todas as migrations para que o schema exista antes de testar.
    executar_migrations(conexao, MIGRATIONS)
    return conexao


def criar_materia_exemplo(
    *,
    id: int | None = None,
    nome: str = "Lógica de Programação",
) -> Materia:
    """Cria uma matéria de exemplo com valores padrão para facilitar os testes."""
    return Materia(
        id=id,
        nome=nome,
        descricao="Fundamentos da lógica de programação.",
        ativa=True,
        ordem=1,
        data_criacao=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        data_atualizacao=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )


def test_materia_exige_nome_valido() -> None:
    # A entidade do DOMÍNIO deve rejeitar nomes inválidos antes de qualquer
    # contato com o banco (proteção na camada mais baixa do modelo).
    with pytest.raises(ValueError):
        criar_materia_exemplo(nome="")  # nome vazio

    with pytest.raises(ValueError):
        criar_materia_exemplo(nome="   ")  # nome composto só por espaços


def test_materia_aceita_descricao_ausente() -> None:
    # A descrição é opcional: a entidade deve representar a ausência com None.
    materia = criar_materia_exemplo()
    materia_sem_descricao = Materia(
        id=None,
        nome=materia.nome,
        descricao=None,
        ativa=materia.ativa,
        ordem=materia.ordem,
        data_criacao=materia.data_criacao,
        data_atualizacao=materia.data_atualizacao,
    )

    assert materia_sem_descricao.descricao is None


def test_materia_representa_entidade_nao_persistida() -> None:
    # Antes de persistir, a matéria não possui id atribuído pelo banco (None).
    materia = criar_materia_exemplo(id=None)

    assert materia.id is None


def test_materia_representa_atributos_corretamente() -> None:
    # Verifica a representação de todos os atributos no domínio.
    materia = criar_materia_exemplo()

    assert materia.nome == "Lógica de Programação"
    assert materia.ativa is True
    assert materia.ordem == 1
    assert materia.data_criacao == datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert materia.data_atualizacao == datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
def test_insercao_gera_id_e_recuperacao_preserva_dados() -> None:
    # Fluxo "redondo": inserir -> obter id -> recuperar por id.
    conexao = criar_banco_com_materia()

    criada = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore

    assert recuperada == criada  # a dataclass compara todos os campos
    assert recuperada is not None
    assert recuperada.id == criada.id
    assert recuperada.nome == "Lógica de Programação"
    assert recuperada.descricao == "Fundamentos da lógica de programação."
    assert recuperada.ativa is True
    assert recuperada.ordem == 1
    assert recuperada.data_criacao == datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert recuperada.data_atualizacao == datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)


def test_recuperacao_de_materia_inexistente_retorna_none() -> None:
    # Buscar algo que não existe deve devolver None (e não lançar exceção).
    conexao = criar_banco_com_materia()

    assert obter_materia_por_id(conexao, 999999) is None


def test_entidade_existente_nao_e_inserida_novamente() -> None:
    # Invariante de persistência: uma matéria que já possui id (persistida)
    # não pode ser inserida de novo como se fosse nova.
    conexao = criar_banco_com_materia()
    materia = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    with pytest.raises(ValueError):
        inserir_materia(conexao, materia)


def test_persistencia_de_ativa_false() -> None:
    # O valor 'ativa' deve ser persistido e recuperado corretamente
    # (conversão bool -> INTEGER 0/1 no SQLite -> bool no domínio).
    conexao = criar_banco_com_materia()
    materia = criar_materia_exemplo()
    materia_inativa = Materia(
        id=None,
        nome=materia.nome,
        descricao=materia.descricao,
        ativa=False,
        ordem=materia.ordem,
        data_criacao=materia.data_criacao,
        data_atualizacao=materia.data_atualizacao,
    )

    criada = inserir_materia(conexao, materia_inativa)
    conexao.commit()

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None
    assert recuperada.ativa is False


def test_banco_rejeita_nome_nulo() -> None:
    # A CONSTRAINT NOT NULL da migration é a última barreira de defesa:
    # mesmo quem contorne a entidade não conseguirá guardar NULL.
    conexao = criar_banco_com_materia()

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute("INSERT INTO materia (nome) VALUES (NULL)")


def test_banco_rejeita_nome_vazio() -> None:
    # A CHECK (length(trim(nome)) > 0) impede strings vazias ou só espaços
    # de serem persistidas, mesmo via SQL direto.
    conexao = criar_banco_com_materia()

    with pytest.raises(sqlite3.IntegrityError):
        conexao.execute("INSERT INTO materia (nome) VALUES ('   ')")


def test_persistencia_de_descricao_nula() -> None:
    # A descrição é opcional: None no domínio deve virar NULL no SQLite
    # e voltar a ser None ao recuperar.
    conexao = criar_banco_com_materia()
    materia = criar_materia_exemplo()
    materia_sem_descricao = Materia(
        id=None,
        nome=materia.nome,
        descricao=None,
        ativa=materia.ativa,
        ordem=materia.ordem,
        data_criacao=materia.data_criacao,
        data_atualizacao=materia.data_atualizacao,
    )

    criada = inserir_materia(conexao, materia_sem_descricao)
    conexao.commit()

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None
    assert recuperada.descricao is None


def test_persistencia_de_ordem_e_datas() -> None:
    # 'ordem' e as datas devem atravessar o mapeamento domínio <-> SQLite
    # sem perda (ordem como inteiro, datas como texto ISO 8601).
    conexao = criar_banco_com_materia()
    materia = Materia(
        id=None,
        nome="Matemática Básica",
        descricao="Operações e raciocínio.",
        ativa=True,
        ordem=5,
        data_criacao=datetime(2024, 5, 10, 8, 30, 0, tzinfo=timezone.utc),
        data_atualizacao=datetime(2024, 6, 11, 9, 45, 0, tzinfo=timezone.utc),
    )

    criada = inserir_materia(conexao, materia)
    conexao.commit()

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None
    assert recuperada.ordem == 5
    assert recuperada.data_criacao == datetime(2024, 5, 10, 8, 30, 0, tzinfo=timezone.utc)
    assert recuperada.data_atualizacao == datetime(2024, 6, 11, 9, 45, 0, tzinfo=timezone.utc)


def test_atualizacao_altera_dados_e_preserva_id() -> None:
    # UPDATE deve alterar os dados, manter o mesmo id e chegar ao banco
    # (confirmado com uma releitura após o commit).
    conexao = criar_banco_com_materia()
    criada = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    alterada = Materia(
        id=criada.id,
        nome="Lógica Avançada",
        descricao="Nova descrição.",
        ativa=False,
        ordem=2,
        data_criacao=criada.data_criacao,
        data_atualizacao=datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    resultado = atualizar_materia(conexao, alterada)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criada.id  # identidade preservada

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None
    assert recuperada == alterada  # a alteração chegou ao banco
    assert recuperada.nome == "Lógica Avançada"
    assert recuperada.descricao == "Nova descrição."
    assert recuperada.ativa is False
    assert recuperada.ordem == 2


def test_atualizacao_de_materia_inexistente_retorna_none() -> None:
    # Atualizar um id que não existe não deve criar nada: devolve None,
    # seguindo a convenção de busca sem resultado do projeto.
    conexao = criar_banco_com_materia()
    materia = criar_materia_exemplo()
    inexistente = Materia(
        id=999999,
        nome=materia.nome,
        descricao=materia.descricao,
        ativa=materia.ativa,
        ordem=materia.ordem,
        data_criacao=materia.data_criacao,
        data_atualizacao=materia.data_atualizacao,
    )

    assert atualizar_materia(conexao, inexistente) is None


def test_atualizacao_exige_identificador() -> None:
    # Uma matéria sem id (ainda não persistida) não pode ser atualizada:
    # sem identidade, o UPDATE não saberia qual linha alterar.
    conexao = criar_banco_com_materia()

    with pytest.raises(ValueError):
        atualizar_materia(conexao, criar_materia_exemplo(id=None))


def test_atualizacao_de_materia_existente_sem_alteracao_nao_e_confundida_com_inexistente() -> None:
    # UPDATE com valores idênticos aos já persistidos não deve ser
    # confundido com matéria inexistente: a operação reconhece a
    # matéria como existente e preserva sua identidade.
    conexao = criar_banco_com_materia()
    criada = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    persistida = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert persistida is not None

    resultado = atualizar_materia(conexao, persistida)
    conexao.commit()

    assert resultado is not None  # existente, mesmo sem alteração efetiva
    assert resultado.id == criada.id  # identidade preservada

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None  # continua recuperável do banco
    assert recuperada == persistida


def test_materia_rejeita_datas_sem_fuso_horario() -> None:
    # As datas do domínio devem ser cientes de fuso (UTC), para que um
    # datetime ingênuo nunca seja gravado como se fosse UTC.
    with pytest.raises(ValueError):
        criar_materia_exemplo_sem_fuso_data_criacao()

    with pytest.raises(ValueError):
        criar_materia_exemplo_sem_fuso_data_atualizacao()


def criar_materia_exemplo_sem_fuso_data_criacao() -> Materia:
    """Matéria de exemplo com data de criação ingênua (sem tzinfo)."""
    materia = criar_materia_exemplo()
    return Materia(
        id=None,
        nome=materia.nome,
        descricao=materia.descricao,
        ativa=materia.ativa,
        ordem=materia.ordem,
        data_criacao=datetime(2024, 1, 1, 10, 0, 0),
        data_atualizacao=materia.data_atualizacao,
    )


def criar_materia_exemplo_sem_fuso_data_atualizacao() -> Materia:
    """Matéria de exemplo com data de atualização ingênua (sem tzinfo)."""
    materia = criar_materia_exemplo()
    return Materia(
        id=None,
        nome=materia.nome,
        descricao=materia.descricao,
        ativa=materia.ativa,
        ordem=materia.ordem,
        data_criacao=materia.data_criacao,
        data_atualizacao=datetime(2024, 1, 1, 10, 0, 0),
    )