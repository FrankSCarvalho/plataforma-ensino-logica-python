import sqlite3  # Driver SQLite: usado para criar conexões em memória

from datetime import datetime, timezone  # Datas usadas nos testes

import pytest  # Framework de teste: fornece pytest.raises

# Importamos usando a MESMA via que o código de produção (pacote 'app'),
# para que os testes exercitem exatamente o que a aplicação usará.
from app.dominio.modulo import Modulo
from app.persistencia.modulo import (
    ativar_modulo,
    atualizar_modulo,
    desativar_modulo,
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
    # outro registro. A data enviada pelo chamador é ignorada: havendo
    # alteração efetiva, a persistência gera a nova data_atualizacao
    # (UTC, timezone-aware); data_criacao permanece a persistida.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    criado = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    alterado = Modulo(
        id=criado.id,
        materia_id=materia_id,
        nome="Condicionais",
        descricao="Estruturas de decisão.",
        ativa=False,
        ordem=2,
        data_criacao=criado.data_criacao,
        data_atualizacao=datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    # O instante enviado acima é ignorado: como há alteração efetiva,
    # a persistência gera um novo instante em UTC.
    antes = datetime.now(timezone.utc)

    resultado = atualizar_modulo(conexao, alterado)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criado.id  # identidade preservada
    assert resultado.data_criacao == criado.data_criacao
    assert resultado.data_atualizacao != alterado.data_atualizacao
    assert resultado.data_atualizacao >= antes
    assert resultado.data_atualizacao.tzinfo is not None

    total = conexao.execute("SELECT COUNT(*) AS total FROM modulo").fetchone()
    assert total["total"] == 1  # nenhum registro novo foi criado

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore

    assert recuperado is not None
    assert recuperado == resultado
    assert recuperado.id == criado.id
    assert recuperado.materia_id == materia_id
    assert recuperado.nome == "Condicionais"
    assert recuperado.descricao == "Estruturas de decisão."
    assert recuperado.ativa is False
    assert recuperado.ordem == 2
    assert recuperado.data_criacao == criado.data_criacao
    assert recuperado.data_atualizacao == resultado.data_atualizacao


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


def test_desativar_modulo_preserva_identidade_e_registro() -> None:
    # Desativar não exclui nem altera a identidade: o registro continua
    # recuperável, com o mesmo id, apenas com ativa=False.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    criado = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    resultado = desativar_modulo(conexao, criado.id)  # type: ignore
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criado.id  # identidade inalterada
    assert resultado.ativa is False  # domínio usa bool
    assert resultado.data_criacao == criado.data_criacao

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert recuperado is not None  # não foi excluído
    assert recuperado.id == criado.id
    assert recuperado.ativa is False

    # SQLite continua usando 0/1 para o booleano.
    linha = conexao.execute(
        "SELECT ativa FROM modulo WHERE id = ?",
        (criado.id,),
    ).fetchone()
    assert linha["ativa"] == 0


def test_ativar_modulo_preserva_identidade_e_registro() -> None:
    # Ativar um módulo inativo resulta em ativa=True, sem novo registro.
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

    resultado = ativar_modulo(conexao, criado.id)  # type: ignore
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criado.id
    assert resultado.ativa is True
    assert resultado.data_criacao == criado.data_criacao

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert recuperado is not None
    assert recuperado.ativa is True

    linha = conexao.execute(
        "SELECT ativa FROM modulo WHERE id = ?",
        (criado.id,),
    ).fetchone()
    assert linha["ativa"] == 1


def test_ativacao_e_desativacao_sao_reversiveis() -> None:
    # O ciclo ativo -> inativo -> ativo preserva o mesmo registro e id.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    criado = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    desativado = desativar_modulo(conexao, criado.id)  # type: ignore
    conexao.commit()
    assert desativado is not None
    assert desativado.ativa is False

    reativado = ativar_modulo(conexao, criado.id)  # type: ignore
    conexao.commit()
    assert reativado is not None
    assert reativado.id == criado.id
    assert reativado.ativa is True

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert recuperado is not None
    assert recuperado.id == criado.id
    assert recuperado.ativa is True
    assert recuperado.data_criacao == criado.data_criacao

    total = conexao.execute("SELECT COUNT(*) AS total FROM modulo").fetchone()
    assert total["total"] == 1  # nenhuma exclusão ou criação no ciclo


def test_ativar_ou_desativar_modulo_inexistente_retorna_none() -> None:
    # Ids inexistentes seguem o padrão de busca: devolvem None, sem criar.
    conexao = criar_banco_com_modulo()

    assert ativar_modulo(conexao, 999999) is None
    assert desativar_modulo(conexao, 999999) is None

    total = conexao.execute("SELECT COUNT(*) AS total FROM modulo").fetchone()
    assert total["total"] == 0


def test_desativacao_nao_avanca_data_sem_alteracao_efetiva() -> None:
    # Desativar um módulo que já está inativo não altera nada: o registro
    # permanece com o mesmo data_atualizacao (sem mudança artificial).
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

    persistido = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert persistido is not None
    assert persistido.ativa is False

    resultado = desativar_modulo(conexao, criado.id)  # type: ignore
    conexao.commit()

    assert resultado is not None
    assert resultado.ativa is False  # desejado
    assert resultado.data_atualizacao == persistido.data_atualizacao
    assert resultado.data_criacao == criado.data_criacao


def test_ativacao_nao_avanca_data_sem_alteracao_efetiva() -> None:
    # Ativar um módulo que já está ativo não altera nada: o registro
    # permanece com o mesmo data_atualizacao (sem mudança artificial).
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    criado = inserir_modulo(
        conexao, criar_modulo_exemplo(materia_id=materia_id)  # ativa=True
    )
    conexao.commit()

    persistido = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert persistido is not None
    assert persistido.ativa is True

    resultado = ativar_modulo(conexao, criado.id)  # type: ignore
    conexao.commit()

    assert resultado is not None
    assert resultado.ativa is True  # desejado
    assert resultado.data_atualizacao == persistido.data_atualizacao
    assert resultado.data_criacao == criado.data_criacao


def test_ordem_pode_ser_alterada_sem_alterar_id() -> None:
    # 'ordem' é independente de 'id': pode mudar sem afetar a identidade.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    criado = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    persistido = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert persistido is not None

    reordenado = Modulo(
        id=persistido.id,
        materia_id=persistido.materia_id,
        nome=persistido.nome,
        descricao=persistido.descricao,
        ativa=persistido.ativa,
        ordem=99,
        data_criacao=persistido.data_criacao,
        data_atualizacao=persistido.data_atualizacao,
    )

    resultado = atualizar_modulo(conexao, reordenado)
    conexao.commit()

    assert resultado is not None
    assert resultado.id == criado.id  # id preservado
    assert resultado.ordem == 99  # ordem alterada
    assert resultado.data_criacao == criado.data_criacao

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert recuperado is not None
    assert recuperado.id == criado.id
    assert recuperado.ordem == 99


def test_ordem_permite_valores_repetidos() -> None:
    # Sem unicidade para 'ordem': dois módulos podem partilhar a posição.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    primeiro = inserir_modulo(
        conexao, criar_modulo_exemplo(materia_id=materia_id, nome="A")
    )
    segundo = inserir_modulo(
        conexao, criar_modulo_exemplo(materia_id=materia_id, nome="B")
    )
    conexao.commit()

    assert primeiro.id != segundo.id
    assert primeiro.ordem == segundo.ordem == 1

    # Alterar ambos para a mesma nova ordem também é permitido.
    for modulo in (primeiro, segundo):
        atual = obter_modulo_por_id(conexao, modulo.id)  # type: ignore
        assert atual is not None
        resultado = atualizar_modulo(
            conexao,
            Modulo(
                id=atual.id,
                materia_id=atual.materia_id,
                nome=atual.nome,
                descricao=atual.descricao,
                ativa=atual.ativa,
                ordem=5,
                data_criacao=atual.data_criacao,
                data_atualizacao=atual.data_atualizacao,
            ),
        )
        assert resultado is not None
        assert resultado.ordem == 5
    conexao.commit()

    ordens = [
        linha[0]
        for linha in conexao.execute(
            "SELECT ordem FROM modulo WHERE materia_id = ? ORDER BY id",
            (materia_id,),
        ).fetchall()
    ]
    assert ordens == [5, 5]


def test_data_atualizacao_avanca_quando_ha_alteracao_efetiva() -> None:
    # Mesmo reutilizando o instante anterior, a alteração efetiva em 'nome'
    # faz data_atualizacao avançar (UTC, timezone-aware).
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    criado = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    persistido = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert persistido is not None

    mesma_data = Modulo(
        id=persistido.id,
        materia_id=persistido.materia_id,
        nome="Condicionais",  # única alteração efetiva
        descricao=persistido.descricao,
        ativa=persistido.ativa,
        ordem=persistido.ordem,
        data_criacao=persistido.data_criacao,
        data_atualizacao=persistido.data_atualizacao,
    )

    resultado = atualizar_modulo(conexao, mesma_data)
    conexao.commit()

    assert resultado is not None
    assert resultado.data_atualizacao > persistido.data_atualizacao
    assert resultado.data_atualizacao.tzinfo is not None
    assert resultado.data_criacao == persistido.data_criacao

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert recuperado is not None
    assert recuperado.data_atualizacao == resultado.data_atualizacao
    assert recuperado.data_atualizacao > persistido.data_atualizacao


def test_data_atualizacao_avanca_ao_alternar_ativa_ordem_e_descricao() -> None:
    # 'ativa', 'ordem' e 'descricao' também contam como alteração efetiva:
    # cada uma, isoladamente, deve avançar data_atualizacao.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    criado = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    persistido = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert persistido is not None

    # 1) Alterna apenas 'ativa'.
    so_ativa = Modulo(
        id=persistido.id,
        materia_id=persistido.materia_id,
        nome=persistido.nome,
        descricao=persistido.descricao,
        ativa=not persistido.ativa,
        ordem=persistido.ordem,
        data_criacao=persistido.data_criacao,
        data_atualizacao=persistido.data_atualizacao,
    )
    resultado_ativa = atualizar_modulo(conexao, so_ativa)
    conexao.commit()

    assert resultado_ativa is not None
    assert resultado_ativa.data_atualizacao > persistido.data_atualizacao

    intermediario = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert intermediario is not None

    # 2) Altera apenas 'ordem'.
    so_ordem = Modulo(
        id=intermediario.id,
        materia_id=intermediario.materia_id,
        nome=intermediario.nome,
        descricao=intermediario.descricao,
        ativa=intermediario.ativa,
        ordem=intermediario.ordem + 10,
        data_criacao=intermediario.data_criacao,
        data_atualizacao=intermediario.data_atualizacao,
    )
    resultado_ordem = atualizar_modulo(conexao, so_ordem)
    conexao.commit()

    assert resultado_ordem is not None
    assert resultado_ordem.data_atualizacao > intermediario.data_atualizacao
    assert resultado_ordem.id == criado.id  # identidade preservada

    atual = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert atual is not None

    # 3) Altera apenas 'descricao'.
    so_descricao = Modulo(
        id=atual.id,
        materia_id=atual.materia_id,
        nome=atual.nome,
        descricao="Nova descrição.",
        ativa=atual.ativa,
        ordem=atual.ordem,
        data_criacao=atual.data_criacao,
        data_atualizacao=atual.data_atualizacao,
    )
    resultado_descricao = atualizar_modulo(conexao, so_descricao)
    conexao.commit()

    assert resultado_descricao is not None
    assert resultado_descricao.data_atualizacao > atual.data_atualizacao
    assert resultado_descricao.descricao == "Nova descrição."


def test_data_atualizacao_nao_muda_sem_alteracao_efetiva() -> None:
    # Valores exatamente iguais preservam data_atualizacao, inclusive se o
    # chamador enviar outro instante na entidade.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    criado = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    persistido = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert persistido is not None

    # Caso 1: entidade idêntica à persistida.
    resultado = atualizar_modulo(conexao, persistido)
    conexao.commit()

    assert resultado is not None
    assert resultado.data_atualizacao == persistido.data_atualizacao

    # Caso 2: mesmos nome/descricao/ativa/ordem, mas data_atualizacao
    # diferente na entidade enviada — o banco mantém o instante anterior.
    com_outra_data = Modulo(
        id=persistido.id,
        materia_id=persistido.materia_id,
        nome=persistido.nome,
        descricao=persistido.descricao,
        ativa=persistido.ativa,
        ordem=persistido.ordem,
        data_criacao=persistido.data_criacao,
        data_atualizacao=datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    )
    resultado_2 = atualizar_modulo(conexao, com_outra_data)
    conexao.commit()

    assert resultado_2 is not None
    assert resultado_2.data_atualizacao == persistido.data_atualizacao

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert recuperado is not None
    assert recuperado.data_atualizacao == persistido.data_atualizacao


def test_atualizacao_preserva_data_criacao() -> None:
    # Mesmo que o chamador envie outra data_criacao, o UPDATE nunca a altera.
    conexao = criar_banco_com_modulo()
    materia_id = criar_materia_id(conexao)
    criado = inserir_modulo(conexao, criar_modulo_exemplo(materia_id=materia_id))
    conexao.commit()

    persistido = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert persistido is not None

    adulterado = Modulo(
        id=persistido.id,
        materia_id=persistido.materia_id,
        nome="Condicionais",  # alteração efetiva para forçar o UPDATE
        descricao=persistido.descricao,
        ativa=persistido.ativa,
        ordem=persistido.ordem,
        data_criacao=datetime(2030, 5, 5, 5, 5, 5, tzinfo=timezone.utc),
        data_atualizacao=persistido.data_atualizacao,
    )

    resultado = atualizar_modulo(conexao, adulterado)
    conexao.commit()

    assert resultado is not None
    assert resultado.data_criacao == persistido.data_criacao

    recuperado = obter_modulo_por_id(conexao, criado.id)  # type: ignore
    assert recuperado is not None
    assert recuperado.data_criacao == persistido.data_criacao
    assert recuperado.data_criacao == criado.data_criacao


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
