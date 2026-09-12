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

    # A data enviada pelo chamador e ignorada: havendo alteracao efetiva,
    # a persistencia gera a nova data_atualizacao (UTC, timezone-aware).
    antes = datetime.now(timezone.utc)

    resultado = atualizar_materia(conexao, alterada)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criada.id  # identidade preservada
    assert resultado.data_criacao == criada.data_criacao
    assert resultado.data_atualizacao != alterada.data_atualizacao
    assert resultado.data_atualizacao >= antes
    assert resultado.data_atualizacao.tzinfo is not None

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore

    assert recuperada is not None
    assert recuperada == resultado  # a alteração chegou ao banco
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


def test_desativar_materia_preserva_identidade_e_registro() -> None:
    # Desativar não exclui nem altera a identidade: o registro continua
    # recuperável, com o mesmo id, apenas com ativa=False.
    conexao = criar_banco_com_materia()
    criada = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    persistida = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert persistida is not None
    assert persistida.ativa is True

    desativada = Materia(
        id=persistida.id,
        nome=persistida.nome,
        descricao=persistida.descricao,
        ativa=False,
        ordem=persistida.ordem,
        data_criacao=persistida.data_criacao,
        data_atualizacao=persistida.data_atualizacao,
    )

    resultado = atualizar_materia(conexao, desativada)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criada.id  # identidade inalterada
    assert resultado.ativa is False  # domínio usa bool

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert recuperada is not None  # não foi excluída
    assert recuperada.id == criada.id
    assert recuperada.ativa is False

    # SQLite continua usando 0/1 para o booleano.
    linha = conexao.execute(
        "SELECT ativa FROM materia WHERE id = ?",
        (criada.id,),
    ).fetchone()
    assert linha["ativa"] == 0


def test_reativar_materia_desativada() -> None:
    # Uma matéria desativada pode ser reativada sem perder a identidade.
    conexao = criar_banco_com_materia()
    materia = criar_materia_exemplo()
    inativa = Materia(
        id=None,
        nome=materia.nome,
        descricao=materia.descricao,
        ativa=False,
        ordem=materia.ordem,
        data_criacao=materia.data_criacao,
        data_atualizacao=materia.data_atualizacao,
    )
    criada = inserir_materia(conexao, inativa)
    conexao.commit()

    persistida = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert persistida is not None
    assert persistida.ativa is False

    reativada = Materia(
        id=persistida.id,
        nome=persistida.nome,
        descricao=persistida.descricao,
        ativa=True,
        ordem=persistida.ordem,
        data_criacao=persistida.data_criacao,
        data_atualizacao=persistida.data_atualizacao,
    )

    resultado = atualizar_materia(conexao, reativada)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criada.id
    assert resultado.ativa is True

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert recuperada is not None
    assert recuperada.ativa is True
    linha = conexao.execute(
        "SELECT ativa FROM materia WHERE id = ?",
        (criada.id,),
    ).fetchone()
    assert linha["ativa"] == 1


def test_ordem_pode_ser_alterada_sem_alterar_id() -> None:
    # 'ordem' é independente de 'id': pode mudar sem afetar a identidade.
    conexao = criar_banco_com_materia()
    criada = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    persistida = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert persistida is not None

    reordenada = Materia(
        id=persistida.id,
        nome=persistida.nome,
        descricao=persistida.descricao,
        ativa=persistida.ativa,
        ordem=99,
        data_criacao=persistida.data_criacao,
        data_atualizacao=persistida.data_atualizacao,
    )

    resultado = atualizar_materia(conexao, reordenada)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criada.id  # id preservado
    assert resultado.ordem == 99  # ordem alterada

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert recuperada is not None
    assert recuperada.id == criada.id
    assert recuperada.ordem == 99


def test_ordem_permite_valores_repetidos() -> None:
    # Sem unicidade para 'ordem': duas matérias podem partilhar a posição.
    conexao = criar_banco_com_materia()

    primeira = inserir_materia(conexao, criar_materia_exemplo())
    base_segunda = criar_materia_exemplo(nome="Matematica Basica")
    segunda = Materia(
        id=None,
        nome=base_segunda.nome,
        descricao=base_segunda.descricao,
        ativa=base_segunda.ativa,
        ordem=1,  # mesma ordem da primeira
        data_criacao=base_segunda.data_criacao,
        data_atualizacao=base_segunda.data_atualizacao,
    )
    segunda_criada = inserir_materia(conexao, segunda)
    conexao.commit()

    assert primeira.id != segunda_criada.id
    assert primeira.ordem == segunda_criada.ordem == 1


def test_atualizacao_preserva_data_criacao() -> None:
    # Mesmo que o chamador envie outra data_criacao, o UPDATE nunca a altera.
    conexao = criar_banco_com_materia()
    criada = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    persistida = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert persistida is not None

    adulterada = Materia(
        id=persistida.id,
        nome="Logica Avancada",  # alteracao efetiva para forcar o UPDATE
        descricao=persistida.descricao,
        ativa=persistida.ativa,
        ordem=persistida.ordem,
        data_criacao=datetime(2030, 5, 5, 5, 5, 5, tzinfo=timezone.utc),
        data_atualizacao=persistida.data_atualizacao,
    )

    resultado = atualizar_materia(conexao, adulterada)
    conexao.commit()

    assert resultado is not None
    assert resultado.data_criacao == persistida.data_criacao

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert recuperada is not None
    assert recuperada.data_criacao == persistida.data_criacao
    assert recuperada.data_criacao == criada.data_criacao


def test_atualizacao_nao_cria_outra_materia() -> None:
    # Atualizar nunca insere: a quantidade de registros permanece a mesma.
    conexao = criar_banco_com_materia()
    criada = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    persistida = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert persistida is not None

    alterada = Materia(
        id=persistida.id,
        nome="Logica Avancada",
        descricao=persistida.descricao,
        ativa=persistida.ativa,
        ordem=persistida.ordem,
        data_criacao=persistida.data_criacao,
        data_atualizacao=persistida.data_atualizacao,
    )

    resultado = atualizar_materia(conexao, alterada)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criada.id

    total = conexao.execute("SELECT COUNT(*) AS total FROM materia").fetchone()
    assert total["total"] == 1

    ids = [linha["id"] for linha in conexao.execute("SELECT id FROM materia")]
    assert ids == [criada.id]


def test_atualizacao_inexistente_nao_cria_registro() -> None:
    # Id inexistente nao e atualizacao bem-sucedida nem cria registro.
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
    conexao.commit()

    total = conexao.execute("SELECT COUNT(*) AS total FROM materia").fetchone()
    assert total["total"] == 0
    assert obter_materia_por_id(conexao, 999999) is None


def test_data_atualizacao_avanca_quando_ha_alteracao_efetiva() -> None:
    # Mesmo reutilizando o instante anterior, a alteracao efetiva em 'nome'
    # faz data_atualizacao avancar (UTC, timezone-aware).
    conexao = criar_banco_com_materia()
    criada = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    persistida = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert persistida is not None

    mesma_data = Materia(
        id=persistida.id,
        nome="Logica Avancada",  # unica alteracao efetiva
        descricao=persistida.descricao,
        ativa=persistida.ativa,
        ordem=persistida.ordem,
        data_criacao=persistida.data_criacao,
        data_atualizacao=persistida.data_atualizacao,
    )

    resultado = atualizar_materia(conexao, mesma_data)
    conexao.commit()

    assert resultado is not None
    assert resultado.data_atualizacao > persistida.data_atualizacao
    assert resultado.data_atualizacao.tzinfo is not None

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert recuperada is not None
    assert recuperada.data_atualizacao == resultado.data_atualizacao
    assert recuperada.data_atualizacao > persistida.data_atualizacao


def test_data_atualizacao_avanca_ao_alternar_ativa_e_ordem() -> None:
    # 'ativa' e 'ordem' tambem contam como alteracao efetiva: cada uma,
    # isoladamente, deve avancar data_atualizacao.
    conexao = criar_banco_com_materia()
    criada = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    persistida = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert persistida is not None

    # 1) Alterna apenas 'ativa'.
    so_ativa = Materia(
        id=persistida.id,
        nome=persistida.nome,
        descricao=persistida.descricao,
        ativa=not persistida.ativa,
        ordem=persistida.ordem,
        data_criacao=persistida.data_criacao,
        data_atualizacao=persistida.data_atualizacao,
    )
    resultado_ativa = atualizar_materia(conexao, so_ativa)
    conexao.commit()

    assert resultado_ativa is not None
    assert resultado_ativa.data_atualizacao > persistida.data_atualizacao

    intermediaria = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert intermediaria is not None

    # 2) Altera apenas 'ordem'.
    so_ordem = Materia(
        id=intermediaria.id,
        nome=intermediaria.nome,
        descricao=intermediaria.descricao,
        ativa=intermediaria.ativa,
        ordem=intermediaria.ordem + 10,
        data_criacao=intermediaria.data_criacao,
        data_atualizacao=intermediaria.data_atualizacao,
    )
    resultado_ordem = atualizar_materia(conexao, so_ordem)
    conexao.commit()

    assert resultado_ordem is not None
    assert resultado_ordem.data_atualizacao > intermediaria.data_atualizacao
    assert resultado_ordem.id == criada.id  # identidade preservada


def test_data_atualizacao_nao_muda_sem_alteracao_efetiva() -> None:
    # Valores exatamente iguais preservam data_atualizacao, inclusive se o
    # chamador enviar outro instante na entidade.
    conexao = criar_banco_com_materia()
    criada = inserir_materia(conexao, criar_materia_exemplo())
    conexao.commit()

    persistida = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert persistida is not None

    # Caso 1: entidade identica a persistida.
    resultado = atualizar_materia(conexao, persistida)
    conexao.commit()

    assert resultado is not None
    assert resultado.data_atualizacao == persistida.data_atualizacao

    # Caso 2: mesmos nome/descricao/ativa/ordem, mas data_atualizacao
    # diferente na entidade enviada — o banco mantem o instante anterior.
    com_outra_data = Materia(
        id=persistida.id,
        nome=persistida.nome,
        descricao=persistida.descricao,
        ativa=persistida.ativa,
        ordem=persistida.ordem,
        data_criacao=persistida.data_criacao,
        data_atualizacao=datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    )
    resultado_2 = atualizar_materia(conexao, com_outra_data)
    conexao.commit()

    assert resultado_2 is not None
    assert resultado_2.data_atualizacao == persistida.data_atualizacao

    recuperada = obter_materia_por_id(conexao, criada.id)  # type: ignore
    assert recuperada is not None
    assert recuperada.data_atualizacao == persistida.data_atualizacao


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