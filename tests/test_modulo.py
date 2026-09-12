import sqlite3  # Driver SQLite: usado para criar conexões em memória

from datetime import datetime, timezone  # Datas usadas nos testes

import pytest  # Framework de teste: fornece pytest.raises

# Importamos usando a MESMA via que o código de produção (pacote 'app'),
# para que os testes exercitem exatamente o que a aplicação usará.
from app.dominio.modulo import Modulo
from app.persistencia.modulo import (
    atualizar_modulo,
    inserir_modulo,
    obter_modulo_por_id,
)
from app.persistencia.migrations import MIGRATIONS
from app.persistencia.migrations.executor import executar_migrations


def criar_banco_com_modulo() -> sqlite3.Connection:
    """Cria um banco em memória já migrado, com as tabelas prontas."""
    # ":memory:" cria um banco 100% em memória e descartável — ideal para
    # testes, pois não altera o arquivo real data/plataforma.db.
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row  # acesso às colunas por nome
    # Aplicamos todas as migrations para que o schema exista antes de testar.
    executar_migrations(conexao, MIGRATIONS)
    return conexao


def criar_materia_id(conexao: sqlite3.Connection) -> int:
    """Insere uma matéria mínima válida e devolve seu id gerado."""
    # O módulo referencia a matéria apenas pelo id (FK modulo.materia_id).
    cursor = conexao.execute(
        """
        INSERT INTO materia (nome, descricao, ativa, ordem, data_criacao, data_atualizacao)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "Lógica de Programação",
            "Fundamentos da lógica de programação.",
            1,
            1,
            "2024-01-01T10:00:00+00:00",
            "2024-01-01T10:00:00+00:00",
        ),
    )
    conexao.commit()
    return cursor.lastrowid


def criar_modulo_exemplo(
    *,
    id: int | None = None,
    materia_id: int = 1,
    nome: str = "Variáveis",
) -> Modulo:
    """Cria um módulo de exemplo com valores padrão para facilitar os testes."""
    return Modulo(
        id=id,
        materia_id=materia_id,
        nome=nome,
        descricao="Conceitos de variáveis.",
        ativa=True,
        ordem=1,
        data_criacao=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
        data_atualizacao=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
    )


def test_modulo_representa_entidade_nao_persistida() -> None:
    # Antes de persistir, o módulo não possui id atribuído pelo banco (None).
    modulo = criar_modulo_exemplo(id=None)

    assert modulo.id is None


def test_modulo_exige_nome_valido() -> None:
    # A entidade do DOMÍNIO deve rejeitar nomes inválidos antes de qualquer
    # contato com o banco (proteção na camada mais baixa do modelo).
    with pytest.raises(ValueError):
        criar_modulo_exemplo(nome="")  # nome vazio

    with pytest.raises(ValueError):
        criar_modulo_exemplo(nome="   ")  # nome composto só por espaços


def test_modulo_rejeita_nome_nulo() -> None:
    # Nome nulo (None) também é inválido no domínio.
    with pytest.raises(ValueError):
        Modulo(
            id=None,
            materia_id=1,
            nome=None,  # type: ignore
            descricao="Conceitos de variáveis.",
            ativa=True,
            ordem=1,
            data_criacao=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
            data_atualizacao=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
        )


def test_modulo_exige_materia_id() -> None:
    # 'materia_id' representa a matéria dona: None ou não-inteiro é inválido.
    with pytest.raises(ValueError):
        Modulo(
            id=None,
            materia_id=None,  # type: ignore
            nome="Variáveis",
            descricao="Conceitos de variáveis.",
            ativa=True,
            ordem=1,
            data_criacao=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
            data_atualizacao=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
        )

    with pytest.raises(ValueError):
        Modulo(
            id=None,
            materia_id="1",  # type: ignore
            nome="Variáveis",
            descricao="Conceitos de variáveis.",
            ativa=True,
            ordem=1,
            data_criacao=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
            data_atualizacao=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
        )


def test_modulo_rejeita_datas_sem_fuso_horario() -> None:
    # As datas do domínio devem ser cientes de fuso (UTC), para que um
    # datetime ingênuo nunca seja gravado como se fosse UTC.
    with pytest.raises(ValueError):
        criar_modulo_sem_fuso_data_criacao()

    with pytest.raises(ValueError):
        criar_modulo_sem_fuso_data_atualizacao()


def test_modulo_aceita_nome_valido() -> None:
    # Um nome com conteúdo deve ser aceito e preservado na entidade.
    modulo = criar_modulo_exemplo(nome="Condicionais")

    assert modulo.nome == "Condicionais"


def test_modulo_representa_atributos_corretamente() -> None:
    # Verifica a representação de todos os atributos no domínio.
    modulo = criar_modulo_exemplo(materia_id=7)

    assert modulo.materia_id == 7
    assert modulo.nome == "Variáveis"
    assert modulo.descricao == "Conceitos de variáveis."
    assert modulo.ativa is True
    assert modulo.ordem == 1
    assert modulo.data_criacao == datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
    assert modulo.data_atualizacao == datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)


def test_modulo_aceita_descricao_ausente() -> None:
    # A descrição é opcional: a entidade deve representar a ausência com None.
    modulo = criar_modulo_exemplo()
    modulo_sem_descricao = Modulo(
        id=None,
        materia_id=modulo.materia_id,
        nome=modulo.nome,
        descricao=None,
        ativa=modulo.ativa,
        ordem=modulo.ordem,
        data_criacao=modulo.data_criacao,
        data_atualizacao=modulo.data_atualizacao,
    )

    assert modulo_sem_descricao.descricao is None


def test_insercao_gera_id_e_recuperacao_preserva_dados() -> None:
    # Fluxo "redondo": inserir -> obter id -> recuperar por id.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)

    criado = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    assert criado.id is not None  # id gerado pelo SQLite

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore

    assert recuperado is not None
    assert recuperado == criado  # a dataclass compara os 8 atributos
    assert recuperado.materia_id == materia_id
    assert recuperado.nome == "Variáveis"
    assert recuperado.descricao == "Conceitos de variáveis."
    assert recuperado.ativa is True
    assert recuperado.ordem == 1
    assert recuperado.data_criacao == datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
    assert recuperado.data_atualizacao == datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)


def test_recuperacao_de_modulo_inexistente_retorna_none() -> None:
    # Buscar algo que não existe deve devolver None (e não lançar exceção).
    conexao = criar_banco_com_modulo()

    assert obter_modulo_por_id(conexao, 999999) is None


def test_entidade_existente_nao_e_inserida_novamente() -> None:
    # Invariante de persistência: um módulo que já possui id (persistido)
    # não pode ser inserido de novo como se fosse novo.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    modulo = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    with pytest.raises(ValueError):
        inserir_modulo(conexao, modulo)


def test_recuperacao_preserva_descricao_nula() -> None:
    # 'descricao=None' deve atravessar o banco (NULL) e voltar como None.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    base = criar_modulo_exemplo(materia_id=materia_id)
    sem_descricao = Modulo(
        id=None,
        materia_id=base.materia_id,
        nome=base.nome,
        descricao=None,
        ativa=base.ativa,
        ordem=base.ordem,
        data_criacao=base.data_criacao,
        data_atualizacao=base.data_atualizacao,
    )

    criado = inserir_modulo(conexao, sem_descricao)
    conexao.commit()

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore

    assert recuperado is not None
    assert recuperado.descricao is None


def test_recuperacao_converte_ativa_para_booleano() -> None:
    # O SQLite guarda 0/1; o domínio deve devolver False/True (bool).
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    base = criar_modulo_exemplo(materia_id=materia_id)
    inativo = Modulo(
        id=None,
        materia_id=base.materia_id,
        nome=base.nome,
        descricao=base.descricao,
        ativa=False,
        ordem=base.ordem,
        data_criacao=base.data_criacao,
        data_atualizacao=base.data_atualizacao,
    )

    criado = inserir_modulo(conexao, inativo)
    conexao.commit()

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore

    assert recuperado is not None
    assert recuperado.ativa is False
    assert isinstance(recuperado.ativa, bool)

    linha = conexao.execute(
        "SELECT ativa FROM modulo WHERE id = ?",
        (criado.id,),
    ).fetchone()
    assert linha["ativa"] == 0


def test_atualizacao_altera_dados_e_preserva_id() -> None:
    # Atualizar altera os dados enviados e mantém o mesmo id, sem criar
    # outro registro. Sem regra automática de data: as datas persistidas
    # são exatamente as recebidas da entidade (F2-002.3 fica para depois).
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    criada = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    alterado = Modulo(
        id=criada.id,
        materia_id=materia_id,
        nome="Condicionais",
        descricao="Estruturas de decisão.",
        ativa=False,
        ordem=2,
        data_criacao=criada.data_criacao,
        data_atualizacao=datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    resultado = atualizar_modulo(conexao, alterado)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criada.id  # identidade preservada
    assert resultado == alterado  # valores atualizados persistidos

    total = conexao.execute("SELECT COUNT(*) AS total FROM modulo").fetchone()
    assert total["total"] == 1  # nenhum registro novo foi criado

    recuperado = obter_modulo_por_id(conexao, criada.id)  # type: ignore

    assert recuperado is not None
    assert recuperado == alterado
    assert recuperado.id == criada.id
    assert recuperado.materia_id == materia_id
    assert recuperado.nome == "Condicionais"
    assert recuperado.descricao == "Estruturas de decisão."
    assert recuperado.ativa is False
    assert recuperado.ordem == 2
    assert recuperado.data_criacao == criada.data_criacao
    assert recuperado.data_atualizacao == datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_atualizacao_de_modulo_inexistente_retorna_none() -> None:
    # Atualizar um id que não existe não deve criar nada: devolve None,
    # seguindo a convenção de busca sem resultado do projeto.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    base = criar_modulo_exemplo(materia_id=materia_id)
    inexistente = Modulo(
        id=999999,
        materia_id=base.materia_id,
        nome=base.nome,
        descricao=base.descricao,
        ativa=base.ativa,
        ordem=base.ordem,
        data_criacao=base.data_criacao,
        data_atualizacao=base.data_atualizacao,
    )

    assert atualizar_modulo(conexao, inexistente) is None

    total = conexao.execute("SELECT COUNT(*) AS total FROM modulo").fetchone()
    assert total["total"] == 0  # nada foi criado


def test_atualizacao_exige_identificador() -> None:
    # Um módulo sem id (ainda não persistido) não pode ser atualizado:
    # sem identidade, o UPDATE não saberia qual linha alterar.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)

    with pytest.raises(ValueError):
        atualizar_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id, id=None))


def criar_modulo_sem_fuso_data_criacao() -> Modulo:
    """Módulo de exemplo com data de criação ingênua (sem tzinfo)."""
    modulo = criar_modulo_exemplo()
    return Modulo(
        id=None,
        materia_id=modulo.materia_id,
        nome=modulo.nome,
        descricao=modulo.descricao,
        ativa=modulo.ativa,
        ordem=modulo.ordem,
        data_criacao=datetime(2024, 1, 2, 10, 0, 0),
        data_atualizacao=modulo.data_atualizacao,
    )


def criar_modulo_sem_fuso_data_atualizacao() -> Modulo:
    """Módulo de exemplo com data de atualização ingênua (sem tzinfo)."""
    modulo = criar_modulo_exemplo()
    return Modulo(
        id=None,
        materia_id=modulo.materia_id,
        nome=modulo.nome,
        descricao=modulo.descricao,
        ativa=modulo.ativa,
        ordem=modulo.ordem,
        data_criacao=modulo.data_criacao,
        data_atualizacao=datetime(2024, 1, 2, 10, 0, 0),
    )
