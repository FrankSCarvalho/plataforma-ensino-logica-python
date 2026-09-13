import sqlite3  # Driver SQLite: usado para criar conexões em memória

from datetime import datetime, timezone  # Datas usadas nos testes

import pytest  # Framework de teste: fornece pytest.raises

# Importamos usando a MESMA via que o código de produção (pacote 'app'),
# para que os testes exercitem exatamente o que a aplicação usará.
from app.dominio.habilidade import Habilidade
from app.persistencia.habilidade import (
    atualizar_habilidade,
    inserir_habilidade,
    obter_habilidade_por_id,
)
from app.persistencia.migrations import MIGRATIONS
from app.persistencia.migrations.executor import executar_migrations


def criar_banco_com_habilidade() -> sqlite3.Connection:
    """Cria um banco em memória já migrado, com as tabelas prontas."""
    # ":memory:" cria um banco 100% em memória e descartável — ideal para
    # testes, pois não altera o arquivo real data/plataforma.db.
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row  # acesso às colunas por nome
    # Aplicamos todas as migrations para que o schema exista antes de testar.
    executar_migrations(conexao, MIGRATIONS)
    return conexao


def criar_modulo_id(conexao: sqlite3.Connection, nome: str = "Variáveis") -> int:
    """Insere matéria e módulo mínimos válidos e devolve o id do módulo."""
    # A habilidade referencia o módulo apenas pelo id (FK habilidade.modulo_id),
    # e o módulo por sua vez exige uma matéria válida (FK modulo.materia_id).
    # O parâmetro 'nome' permite criar mais de um módulo (ex.: módulos A e B).
    materia = conexao.execute(
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
    modulo = conexao.execute(
        """
        INSERT INTO modulo (materia_id, nome, descricao, ativa, ordem, data_criacao, data_atualizacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            materia.lastrowid,
            nome,
            "Conceitos de variáveis.",
            1,
            1,
            "2024-01-02T10:00:00+00:00",
            "2024-01-02T10:00:00+00:00",
        ),
    )
    conexao.commit()
    return modulo.lastrowid  # type: ignore


def criar_habilidade_exemplo(
    *,
    id: int | None = None,
    modulo_id: int = 1,
    nome: str = "Identificar variáveis",
) -> Habilidade:
    """Cria uma habilidade de exemplo com valores padrão para facilitar os testes."""
    return Habilidade(
        id=id,
        modulo_id=modulo_id,
        nome=nome,
        descricao="Capacidade de identificar variáveis.",
        ativa=True,
        ordem=1,
        data_criacao=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
        data_atualizacao=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
    )


def test_habilidade_representa_entidade_nao_persistida() -> None:
    # Antes de persistir, a habilidade não possui id atribuído pelo banco (None).
    habilidade = criar_habilidade_exemplo(id=None)

    assert habilidade.id is None


def test_habilidade_exige_nome_valido() -> None:
    # A entidade do DOMÍNIO deve rejeitar nomes inválidos antes de qualquer
    # contato com o banco (proteção na camada mais baixa do modelo).
    with pytest.raises(ValueError):
        criar_habilidade_exemplo(nome="")  # nome vazio

    with pytest.raises(ValueError):
        criar_habilidade_exemplo(nome="   ")  # nome composto só por espaços


def test_habilidade_rejeita_nome_nulo() -> None:
    # Nome nulo (None) também é inválido no domínio.
    with pytest.raises(ValueError):
        Habilidade(
            id=None,
            modulo_id=1,
            nome=None,  # type: ignore
            descricao="Capacidade de identificar variáveis.",
            ativa=True,
            ordem=1,
            data_criacao=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
            data_atualizacao=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
        )


def test_habilidade_aceita_nome_valido() -> None:
    # Um nome com conteúdo deve ser aceito e preservado na entidade.
    habilidade = criar_habilidade_exemplo(nome="Construir condicionais")

    assert habilidade.nome == "Construir condicionais"


def test_habilidade_representa_atributos_corretamente() -> None:
    # Verifica a representação de todos os atributos no domínio:
    # modulo_id e ordem inteiros, ativa booleana, datas como datetime.
    habilidade = criar_habilidade_exemplo(modulo_id=7)

    assert habilidade.modulo_id == 7
    assert isinstance(habilidade.modulo_id, int)
    assert habilidade.nome == "Identificar variáveis"
    assert habilidade.descricao == "Capacidade de identificar variáveis."
    assert habilidade.ativa is True
    assert isinstance(habilidade.ativa, bool)
    assert habilidade.ordem == 1
    assert isinstance(habilidade.ordem, int)
    assert isinstance(habilidade.data_criacao, datetime)
    assert isinstance(habilidade.data_atualizacao, datetime)
    assert habilidade.data_criacao == datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)
    assert habilidade.data_atualizacao == datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)


def test_habilidade_aceita_descricao_ausente() -> None:
    # A descrição é opcional: a entidade deve representar a ausência com None.
    habilidade = criar_habilidade_exemplo()
    habilidade_sem_descricao = Habilidade(
        id=None,
        modulo_id=habilidade.modulo_id,
        nome=habilidade.nome,
        descricao=None,
        ativa=habilidade.ativa,
        ordem=habilidade.ordem,
        data_criacao=habilidade.data_criacao,
        data_atualizacao=habilidade.data_atualizacao,
    )

    assert habilidade_sem_descricao.descricao is None


def test_habilidade_exige_modulo_id() -> None:
    # 'modulo_id' representa o módulo dono: None ou não-inteiro é inválido.
    with pytest.raises(ValueError):
        Habilidade(
            id=None,
            modulo_id=None,  # type: ignore
            nome="Identificar variáveis",
            descricao="Capacidade de identificar variáveis.",
            ativa=True,
            ordem=1,
            data_criacao=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
            data_atualizacao=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
        )

    with pytest.raises(ValueError):
        Habilidade(
            id=None,
            modulo_id="1",  # type: ignore
            nome="Identificar variáveis",
            descricao="Capacidade de identificar variáveis.",
            ativa=True,
            ordem=1,
            data_criacao=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
            data_atualizacao=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
        )


def test_habilidade_rejeita_datas_sem_fuso_horario() -> None:
    # As datas do domínio devem ser cientes de fuso (UTC), para que um
    # datetime ingênuo nunca seja gravado como se fosse UTC.
    with pytest.raises(ValueError):
        criar_habilidade_sem_fuso_data_criacao()

    with pytest.raises(ValueError):
        criar_habilidade_sem_fuso_data_atualizacao()


def test_insercao_gera_id_e_recuperacao_preserva_dados() -> None:
    # Fluxo "redondo": inserir -> obter id -> recuperar por id.
    conexao = criar_banco_com_habilidade()
    modulo_id = criar_modulo_id(conexao)

    criada = inserir_habilidade(
        conexao, criar_habilidade_exemplo(modulo_id=modulo_id)
    )
    conexao.commit()

    assert criada.id is not None  # id gerado pelo SQLite

    recuperada = obter_habilidade_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None
    assert recuperada == criada  # a dataclass compara os 8 atributos
    assert recuperada.modulo_id == modulo_id
    assert recuperada.nome == "Identificar variáveis"
    assert recuperada.descricao == "Capacidade de identificar variáveis."
    assert recuperada.ativa is True
    assert recuperada.ordem == 1
    assert recuperada.data_criacao == datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)
    assert recuperada.data_atualizacao == datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)


def test_recuperacao_de_habilidade_inexistente_retorna_none() -> None:
    # Buscar algo que não existe deve devolver None (e não lançar exceção).
    conexao = criar_banco_com_habilidade()

    assert obter_habilidade_por_id(conexao, 999999) is None


def test_entidade_existente_nao_e_inserida_novamente() -> None:
    # Invariante de persistência: uma habilidade que já possui id (persistida)
    # não pode ser inserida de novo como se fosse nova.
    conexao = criar_banco_com_habilidade()
    modulo_id = criar_modulo_id(conexao)
    habilidade = inserir_habilidade(
        conexao, criar_habilidade_exemplo(modulo_id=modulo_id)
    )
    conexao.commit()

    with pytest.raises(ValueError):
        inserir_habilidade(conexao, habilidade)


def test_recuperacao_preserva_descricao_nula() -> None:
    # 'descricao=None' deve atravessar o banco (NULL) e voltar como None.
    conexao = criar_banco_com_habilidade()
    modulo_id = criar_modulo_id(conexao)
    base = criar_habilidade_exemplo(modulo_id=modulo_id)
    sem_descricao = Habilidade(
        id=None,
        modulo_id=base.modulo_id,
        nome=base.nome,
        descricao=None,
        ativa=base.ativa,
        ordem=base.ordem,
        data_criacao=base.data_criacao,
        data_atualizacao=base.data_atualizacao,
    )

    criada = inserir_habilidade(conexao, sem_descricao)
    conexao.commit()

    recuperada = obter_habilidade_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None
    assert recuperada.descricao is None


def test_recuperacao_converte_ativa_para_booleano() -> None:
    # O SQLite guarda 0/1; o domínio deve devolver False/True (bool).
    conexao = criar_banco_com_habilidade()
    modulo_id = criar_modulo_id(conexao)
    base = criar_habilidade_exemplo(modulo_id=modulo_id)
    inativa = Habilidade(
        id=None,
        modulo_id=base.modulo_id,
        nome=base.nome,
        descricao=base.descricao,
        ativa=False,
        ordem=base.ordem,
        data_criacao=base.data_criacao,
        data_atualizacao=base.data_atualizacao,
    )

    criada = inserir_habilidade(conexao, inativa)
    conexao.commit()

    recuperada = obter_habilidade_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None
    assert recuperada.ativa is False
    assert isinstance(recuperada.ativa, bool)

    linha = conexao.execute(
        "SELECT ativa FROM habilidade WHERE id = ?",
        (criada.id,),
    ).fetchone()
    assert linha["ativa"] == 0


def test_atualizacao_altera_dados_e_preserva_id_e_modulo() -> None:
    # Atualizar altera os dados enviados, mantém o mesmo id e preserva
    # modulo_id, sem criar outro registro. Nesta subetapa (F2-003.2) as
    # datas persistidas são exatamente as recebidas da entidade.
    conexao = criar_banco_com_habilidade()
    modulo_id = criar_modulo_id(conexao)
    criada = inserir_habilidade(
        conexao, criar_habilidade_exemplo(modulo_id=modulo_id)
    )
    conexao.commit()

    alterada = Habilidade(
        id=criada.id,
        modulo_id=modulo_id,
        nome="Construir condicionais",
        descricao="Capacidade de construir estruturas de decisão.",
        ativa=False,
        ordem=2,
        data_criacao=criada.data_criacao,
        data_atualizacao=datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    resultado = atualizar_habilidade(conexao, alterada)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criada.id  # identidade preservada
    assert resultado.modulo_id == modulo_id  # vínculo preservado

    total = conexao.execute("SELECT COUNT(*) AS total FROM habilidade").fetchone()
    assert total["total"] == 1  # nenhum registro novo foi criado

    recuperada = obter_habilidade_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None
    assert recuperada == alterada
    assert recuperada.id == criada.id
    assert recuperada.modulo_id == modulo_id
    assert recuperada.nome == "Construir condicionais"
    assert recuperada.descricao == "Capacidade de construir estruturas de decisão."
    assert recuperada.ativa is False
    assert recuperada.ordem == 2
    assert recuperada.data_criacao == criada.data_criacao
    assert recuperada.data_atualizacao == datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_atualizacao_nao_altera_o_vinculo_ao_modulo() -> None:
    # Garantia estrutural: 'modulo_id' é o vínculo estrutural da habilidade
    # com seu módulo e NÃO pode ser alterado por atualizar_habilidade, mesmo
    # que a entidade enviada traga um modulo_id diferente.
    conexao = criar_banco_com_habilidade()
    modulo_a = criar_modulo_id(conexao, nome="Modulo A")
    modulo_b = criar_modulo_id(conexao, nome="Modulo B")

    criada = inserir_habilidade(
        conexao, criar_habilidade_exemplo(modulo_id=modulo_a)
    )
    conexao.commit()

    persistida = obter_habilidade_por_id(conexao, criada.id)  # type: ignore
    assert persistida is not None
    assert persistida.modulo_id == modulo_a

    # Entidade de atualização: mesmo id, mas modulo_id DIFERENTE (módulo B)
    # e demais atributos alterados — o vínculo deve permanecer no módulo A.
    atualizacao = Habilidade(
        id=persistida.id,
        modulo_id=modulo_b,
        nome="Construir condicionais",
        descricao="Capacidade de construir estruturas de decisão.",
        ativa=False,
        ordem=2,
        data_criacao=persistida.data_criacao,
        data_atualizacao=datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    resultado = atualizar_habilidade(conexao, atualizacao)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criada.id  # id permanece inalterado
    assert resultado.modulo_id == modulo_a  # vínculo preservado (não B)

    recuperada = obter_habilidade_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None
    assert recuperada.id == criada.id
    assert recuperada.modulo_id == modulo_a  # registro continua no módulo A

    # Demais atributos previstos para atualização foram efetivamente alterados.
    assert recuperada.nome == "Construir condicionais"
    assert recuperada.descricao == "Capacidade de construir estruturas de decisão."
    assert recuperada.ativa is False
    assert recuperada.ordem == 2
    assert recuperada.data_criacao == criada.data_criacao
    assert recuperada.data_atualizacao == datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Confirmação direta no banco: o modulo_id persistido segue sendo A.
    linha = conexao.execute(
        "SELECT modulo_id FROM habilidade WHERE id = ?",
        (criada.id,),
    ).fetchone()
    assert linha["modulo_id"] == modulo_a


def test_atualizacao_de_habilidade_inexistente_retorna_none() -> None:
    # Atualizar um id que não existe não deve criar nada: devolve None,
    # seguindo a convenção de busca sem resultado do projeto.
    conexao = criar_banco_com_habilidade()
    modulo_id = criar_modulo_id(conexao)
    base = criar_habilidade_exemplo(modulo_id=modulo_id)
    inexistente = Habilidade(
        id=999999,
        modulo_id=base.modulo_id,
        nome=base.nome,
        descricao=base.descricao,
        ativa=base.ativa,
        ordem=base.ordem,
        data_criacao=base.data_criacao,
        data_atualizacao=base.data_atualizacao,
    )

    assert atualizar_habilidade(conexao, inexistente) is None

    total = conexao.execute("SELECT COUNT(*) AS total FROM habilidade").fetchone()
    assert total["total"] == 0  # nada foi criado


def test_atualizacao_exige_identificador() -> None:
    # Uma habilidade sem id (ainda não persistida) não pode ser atualizada:
    # sem identidade, o UPDATE não saberia qual linha alterar.
    conexao = criar_banco_com_habilidade()
    modulo_id = criar_modulo_id(conexao)

    with pytest.raises(ValueError):
        atualizar_habilidade(
            conexao, criar_habilidade_exemplo(modulo_id=modulo_id, id=None)
        )


def criar_habilidade_sem_fuso_data_criacao() -> Habilidade:
    """Habilidade de exemplo com data de criação ingênua (sem tzinfo)."""
    habilidade = criar_habilidade_exemplo()
    return Habilidade(
        id=None,
        modulo_id=habilidade.modulo_id,
        nome=habilidade.nome,
        descricao=habilidade.descricao,
        ativa=habilidade.ativa,
        ordem=habilidade.ordem,
        data_criacao=datetime(2024, 1, 3, 10, 0, 0),
        data_atualizacao=habilidade.data_atualizacao,
    )


def criar_habilidade_sem_fuso_data_atualizacao() -> Habilidade:
    """Habilidade de exemplo com data de atualização ingênua (sem tzinfo)."""
    habilidade = criar_habilidade_exemplo()
    return Habilidade(
        id=None,
        modulo_id=habilidade.modulo_id,
        nome=habilidade.nome,
        descricao=habilidade.descricao,
        ativa=habilidade.ativa,
        ordem=habilidade.ordem,
        data_criacao=habilidade.data_criacao,
        data_atualizacao=datetime(2024, 1, 3, 10, 0, 0),
    )
