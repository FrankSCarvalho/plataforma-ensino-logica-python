import inspect
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.dominio.habilidade import Habilidade
from app.dominio.nivel import Nivel
from app.persistencia.habilidade import inserir_habilidade
from app.persistencia.migrations import MIGRATIONS
from app.persistencia.migrations.executor import executar_migrations
from app.persistencia.nivel import (
    ativar_nivel,
    atualizar_nivel,
    desativar_nivel,
    inserir_nivel,
    obter_nivel_por_id,
    reativar_nivel,
)


def criar_banco_com_nivel() -> sqlite3.Connection:
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row
    executar_migrations(conexao, MIGRATIONS)
    return conexao


def criar_habilidade_id(conexao: sqlite3.Connection, nome: str = "Variáveis") -> int:
    materia = conexao.execute(
        """
        INSERT INTO materia (nome, data_criacao, data_atualizacao)
        VALUES ('Lógica de Programação', '2024-01-01T10:00:00+00:00', '2024-01-01T10:00:00+00:00')
        """
    )
    modulo = conexao.execute(
        """
        INSERT INTO modulo (materia_id, nome, data_criacao, data_atualizacao)
        VALUES (?, ?, '2024-01-02T10:00:00+00:00', '2024-01-02T10:00:00+00:00')
        """,
        (materia.lastrowid, nome),
    )
    habilidade = inserir_habilidade(
        conexao,
        Habilidade(
            id=None,
            modulo_id=modulo.lastrowid,  # type: ignore[arg-type]
            nome="Identificar variáveis",
            descricao="Capacidade de identificar variáveis.",
            ativa=True,
            ordem=1,
            data_criacao=datetime(2024, 1, 3, 10, 0, tzinfo=timezone.utc),
            data_atualizacao=datetime(2024, 1, 3, 10, 0, tzinfo=timezone.utc),
        ),
    )
    conexao.commit()
    return habilidade.id  # type: ignore[return-value]


def criar_nivel_exemplo(*, id: int | None = None, habilidade_id: int = 1) -> Nivel:
    return Nivel(
        id=id,
        habilidade_id=habilidade_id,
        nome="Básico",
        descricao="Introdução à habilidade.",
        ativa=True,
        ordem=1,
        data_criacao=datetime(2024, 1, 4, 10, 0, tzinfo=timezone.utc),
        data_atualizacao=datetime(2024, 1, 4, 10, 0, tzinfo=timezone.utc),
    )


def test_nivel_representa_atributos_validos_do_dominio() -> None:
    nivel = criar_nivel_exemplo(habilidade_id=7)

    assert nivel.id is None
    assert nivel.habilidade_id == 7
    assert isinstance(nivel.habilidade_id, int)
    assert nivel.nome == "Básico"
    assert nivel.descricao == "Introdução à habilidade."
    assert nivel.ativa is True
    assert isinstance(nivel.ativa, bool)
    assert nivel.ordem == 1
    assert isinstance(nivel.ordem, int)
    assert isinstance(nivel.data_criacao, datetime)
    assert isinstance(nivel.data_atualizacao, datetime)


@pytest.mark.parametrize("nome", [None, "", "   "])
def test_nivel_rejeita_nome_invalido(nome: str | None) -> None:
    with pytest.raises(ValueError):
        Nivel(
            id=None,
            habilidade_id=1,
            nome=nome,  # type: ignore[arg-type]
            descricao="Introdução à habilidade.",
            ativa=True,
            ordem=1,
            data_criacao=datetime(2024, 1, 4, 10, 0, tzinfo=timezone.utc),
            data_atualizacao=datetime(2024, 1, 4, 10, 0, tzinfo=timezone.utc),
        )


@pytest.mark.parametrize("descricao", [None, "", "   "])
def test_nivel_rejeita_descricao_invalida(descricao: str | None) -> None:
    with pytest.raises(ValueError):
        Nivel(
            id=None,
            habilidade_id=1,
            nome="Básico",
            descricao=descricao,  # type: ignore[arg-type]
            ativa=True,
            ordem=1,
            data_criacao=datetime(2024, 1, 4, 10, 0, tzinfo=timezone.utc),
            data_atualizacao=datetime(2024, 1, 4, 10, 0, tzinfo=timezone.utc),
        )


def test_nivel_dominio_nao_depende_de_sqlite() -> None:
    assert "sqlite3" not in inspect.getsource(inspect.getmodule(Nivel))


def test_insercao_gera_id_e_recuperacao_preserva_todos_os_atributos() -> None:
    conexao = criar_banco_com_nivel()
    habilidade_id = criar_habilidade_id(conexao)
    nivel = Nivel(
        id=None,
        habilidade_id=habilidade_id,
        nome="Básico",
        descricao="Introdução à habilidade.",
        ativa=False,
        ordem=3,
        data_criacao=datetime(2024, 1, 4, 10, 0, tzinfo=timezone.utc),
        data_atualizacao=datetime(2024, 1, 4, 11, 0, tzinfo=timezone.utc),
    )

    criado = inserir_nivel(conexao, nivel)
    conexao.commit()
    recuperado = obter_nivel_por_id(conexao, criado.id)  # type: ignore[arg-type]
    linha = conexao.execute(
        "SELECT ativa, data_criacao, data_atualizacao FROM nivel WHERE id = ?",
        (criado.id,),
    ).fetchone()

    assert criado.id is not None
    assert recuperado == criado
    assert recuperado.ativa is False  # type: ignore[union-attr]
    assert isinstance(recuperado.ativa, bool)  # type: ignore[union-attr]
    assert linha["ativa"] == 0
    assert linha["data_criacao"] == nivel.data_criacao.isoformat()
    assert linha["data_atualizacao"] == nivel.data_atualizacao.isoformat()


def test_insercao_de_nivel_com_id_definido_e_rejeitada() -> None:
    conexao = criar_banco_com_nivel()
    habilidade_id = criar_habilidade_id(conexao)

    with pytest.raises(ValueError):
        inserir_nivel(conexao, criar_nivel_exemplo(id=1, habilidade_id=habilidade_id))


def test_recuperacao_de_nivel_inexistente_retorna_none() -> None:
    assert obter_nivel_por_id(criar_banco_com_nivel(), 999999) is None


def test_atualizacao_altera_campos_permitidos_e_preserva_id_e_habilidade() -> None:
    conexao = criar_banco_com_nivel()
    habilidade_original = criar_habilidade_id(conexao, "Variáveis")
    habilidade_outra = criar_habilidade_id(conexao, "Condicionais")
    criado = inserir_nivel(
        conexao, criar_nivel_exemplo(habilidade_id=habilidade_original)
    )
    conexao.commit()
    atualizacao = Nivel(
        id=criado.id,
        habilidade_id=habilidade_outra,
        nome="Intermediário",
        descricao="Aplicação guiada da habilidade.",
        ativa=False,
        ordem=2,
        data_criacao=datetime(2024, 2, 1, 10, 0, tzinfo=timezone.utc),
        data_atualizacao=datetime(2024, 2, 1, 11, 0, tzinfo=timezone.utc),
    )

    resultado = atualizar_nivel(conexao, atualizacao)
    conexao.commit()
    recuperado = obter_nivel_por_id(conexao, criado.id)  # type: ignore[arg-type]

    assert resultado is not None
    assert resultado.id == criado.id
    assert resultado.habilidade_id == habilidade_original
    assert recuperado is not None
    assert recuperado.id == criado.id
    assert recuperado.habilidade_id == habilidade_original
    assert recuperado.nome == "Intermediário"
    assert recuperado.descricao == "Aplicação guiada da habilidade."
    assert recuperado.ativa is False
    assert recuperado.ordem == 2
    assert recuperado.data_criacao == criado.data_criacao
    assert recuperado.data_atualizacao > criado.data_atualizacao
    assert resultado.data_atualizacao == recuperado.data_atualizacao


def test_atualizacao_exige_id_e_retorna_none_quando_inexistente() -> None:
    conexao = criar_banco_com_nivel()
    habilidade_id = criar_habilidade_id(conexao)

    with pytest.raises(ValueError):
        atualizar_nivel(conexao, criar_nivel_exemplo(habilidade_id=habilidade_id))

    inexistente = criar_nivel_exemplo(id=999999, habilidade_id=habilidade_id)
    assert atualizar_nivel(conexao, inexistente) is None


def test_ativar_nivel_inativo_atualiza_data_e_preserva_vinculo() -> None:
    conexao = criar_banco_com_nivel()
    habilidade_id = criar_habilidade_id(conexao)
    criado = inserir_nivel(
        conexao,
        replace(criar_nivel_exemplo(habilidade_id=habilidade_id), ativa=False),
    )
    conexao.commit()

    ativado = ativar_nivel(conexao, criado.id)  # type: ignore[arg-type]

    assert ativado is not None
    assert ativado.ativa is True
    assert ativado.id == criado.id
    assert ativado.habilidade_id == habilidade_id
    assert ativado.data_criacao == criado.data_criacao
    assert ativado.data_atualizacao > criado.data_atualizacao


def test_desativar_nivel_ativo_atualiza_data_sem_excluir_registro() -> None:
    conexao = criar_banco_com_nivel()
    habilidade_id = criar_habilidade_id(conexao)
    criado = inserir_nivel(conexao, criar_nivel_exemplo(habilidade_id=habilidade_id))
    conexao.commit()

    desativado = desativar_nivel(conexao, criado.id)  # type: ignore[arg-type]
    recuperado = obter_nivel_por_id(conexao, criado.id)  # type: ignore[arg-type]

    assert desativado is not None
    assert desativado.ativa is False
    assert desativado.data_atualizacao > criado.data_atualizacao
    assert recuperado is not None
    assert recuperado.id == criado.id
    assert recuperado.nome == criado.nome


def test_reativar_nivel_preserva_identidade_e_vinculo() -> None:
    conexao = criar_banco_com_nivel()
    habilidade_id = criar_habilidade_id(conexao)
    criado = inserir_nivel(
        conexao,
        replace(criar_nivel_exemplo(habilidade_id=habilidade_id), ativa=False),
    )
    conexao.commit()

    reativado = reativar_nivel(conexao, criado.id)  # type: ignore[arg-type]

    assert reativado is not None
    assert reativado.ativa is True
    assert reativado.id == criado.id
    assert reativado.habilidade_id == habilidade_id


@pytest.mark.parametrize(
    ("operacao", "ativa"),
    [(ativar_nivel, True), (desativar_nivel, False)],
)
def test_ativacao_idempotente_nao_altera_data_atualizacao(
    operacao: object,
    ativa: bool,
) -> None:
    conexao = criar_banco_com_nivel()
    habilidade_id = criar_habilidade_id(conexao)
    criado = inserir_nivel(
        conexao,
        replace(criar_nivel_exemplo(habilidade_id=habilidade_id), ativa=ativa),
    )
    conexao.commit()

    resultado = operacao(conexao, criado.id)  # type: ignore[operator, arg-type]

    assert resultado is not None
    assert resultado.ativa is ativa
    assert resultado.data_atualizacao == criado.data_atualizacao
    assert resultado.data_criacao == criado.data_criacao


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("nome", "Avançado"),
        ("descricao", "Aprofundamento da habilidade."),
        ("ativa", False),
        ("ordem", 8),
    ],
)
def test_alteracao_efetiva_atualiza_data_atualizacao(
    campo: str,
    valor: str | bool | int,
) -> None:
    conexao = criar_banco_com_nivel()
    habilidade_id = criar_habilidade_id(conexao)
    criado = inserir_nivel(conexao, criar_nivel_exemplo(habilidade_id=habilidade_id))
    conexao.commit()
    atualizacao = replace(
        criado,
        **{campo: valor},
        data_criacao=datetime(2030, 1, 1, tzinfo=timezone.utc),
        data_atualizacao=datetime(2030, 1, 2, tzinfo=timezone.utc),
    )

    resultado = atualizar_nivel(conexao, atualizacao)

    assert resultado is not None
    assert resultado.data_atualizacao > criado.data_atualizacao
    assert resultado.data_atualizacao != atualizacao.data_atualizacao
    assert resultado.data_criacao == criado.data_criacao


def test_atualizacao_sem_mudanca_efetiva_preserva_datas_persistidas() -> None:
    conexao = criar_banco_com_nivel()
    habilidade_id = criar_habilidade_id(conexao)
    criado = inserir_nivel(conexao, criar_nivel_exemplo(habilidade_id=habilidade_id))
    conexao.commit()
    mesma_definicao = replace(
        criado,
        data_criacao=datetime(2030, 1, 1, tzinfo=timezone.utc),
        data_atualizacao=datetime(2030, 1, 2, tzinfo=timezone.utc),
    )

    resultado = atualizar_nivel(conexao, mesma_definicao)

    assert resultado is not None
    assert resultado.data_criacao == criado.data_criacao
    assert resultado.data_atualizacao == criado.data_atualizacao


def test_ordem_pode_repetir_e_ser_alterada_sem_mudar_id() -> None:
    conexao = criar_banco_com_nivel()
    habilidade_id = criar_habilidade_id(conexao)
    primeiro = inserir_nivel(conexao, criar_nivel_exemplo(habilidade_id=habilidade_id))
    segundo = inserir_nivel(
        conexao,
        replace(criar_nivel_exemplo(habilidade_id=habilidade_id), nome="Intermediário"),
    )
    conexao.commit()

    reordenado = atualizar_nivel(conexao, replace(primeiro, ordem=7))

    assert primeiro.ordem == segundo.ordem
    assert reordenado is not None
    assert reordenado.id == primeiro.id
    assert reordenado.ordem == 7
