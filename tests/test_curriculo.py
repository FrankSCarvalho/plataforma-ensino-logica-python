"""Testes do conteúdo pedagógico e da carga inicial do currículo (Tarefa 05).

Cobrem: migração v4 (colunas de conteúdo e tipo), armazenamento do
conteúdo conceitual, hierarquia do currículo com consultas ordenadas,
idempotência e preservação de dados na carga inicial.

Todos os testes usam o banco temporário da fixture ``banco_de_teste`` e
não tocam no banco de desenvolvimento localizado em ``data/``.
"""

from app.database import SCHEMA_VERSION, get_connection
from app.models import Aluno, Exercicio, Habilidade, Modulo, Nivel
from app.repositories import (
    ExercicioRepository,
    HabilidadeRepository,
    ModuloRepository,
    NivelRepository,
)
from app.services.carga_inicial import carregar_curriculo_inicial

# Quantidades esperadas do currículo inicial desta tarefa.
QTD_NIVEIS = 3
QTD_EXERCICIOS_POR_NIVEL = 3
QTD_EXERCICIOS = QTD_NIVEIS * QTD_EXERCICIOS_POR_NIVEL


# ---------------------------------------------------------------------------
# Migração v4 — estrutura de conteúdo
# ---------------------------------------------------------------------------

def _colunas_da_tabela(tabela: str) -> set[str]:
    """Retorna os nomes das colunas de uma tabela no banco ativo."""
    with get_connection() as connection:
        linhas = connection.execute(
            f"PRAGMA table_info({tabela})"
        ).fetchall()
    return {linha["name"] for linha in linhas}


def test_migracao_cria_colunas_de_conteudo_em_niveis(banco_de_teste):
    colunas = _colunas_da_tabela("niveis")
    for coluna in (
        "conteudo_titulo",
        "conteudo_explicacao",
        "conteudo_exemplos",
        "conteudo_observacoes",
    ):
        assert coluna in colunas, f"Coluna {coluna} deveria existir em niveis"


def test_migracao_cria_coluna_tipo_em_exercicios(banco_de_teste):
    assert "tipo" in _colunas_da_tabela("exercicios")


def test_versao_do_schema_eh_4(banco_de_teste):
    with get_connection() as connection:
        versao = connection.execute("PRAGMA user_version").fetchone()[0]
    assert versao == SCHEMA_VERSION == 4


# ---------------------------------------------------------------------------
# Armazenamento do conteúdo conceitual e do tipo
# ---------------------------------------------------------------------------

def test_nivel_armazena_conteudo_conceitual(banco_de_teste):
    habilidade = _habilidade_auxiliar()
    repositorio = NivelRepository()
    nivel = repositorio.inserir(
        Nivel(
            habilidade_id=habilidade.id,
            nome="Nível teste",
            ordem=1,
            conteudo_titulo="Título do conteúdo",
            conteudo_explicacao="Explicação do conceito.",
            conteudo_exemplos="Exemplo simples de sequência.",
            conteudo_observacoes="Observação importante.",
        )
    )

    # Recupera do banco e confere cada campo de conteúdo.
    recuperado = repositorio.buscar_por_id(nivel.id)
    assert recuperado.conteudo_titulo == "Título do conteúdo"
    assert recuperado.conteudo_explicacao == "Explicação do conceito."
    assert recuperado.conteudo_exemplos == "Exemplo simples de sequência."
    assert recuperado.conteudo_observacoes == "Observação importante."


def _habilidade_auxiliar():
    """Cria módulo + habilidade simples para apoiar os testes."""
    modulo = ModuloRepository().inserir(Modulo(nome="Módulo auxiliar"))
    return HabilidadeRepository().inserir(
        Habilidade(modulo_id=modulo.id, nome="Habilidade auxiliar")
    )


def test_exercicio_armazena_tipo(banco_de_teste):
    habilidade = _habilidade_auxiliar()
    nivel = NivelRepository().inserir(
        Nivel(habilidade_id=habilidade.id, nome="Nível", ordem=1)
    )
    repositorio = ExercicioRepository()
    exercicio = repositorio.inserir(
        Exercicio(
            nivel_id=nivel.id,
            enunciado="Preveja a saída do programa.",
            ordem=1,
            tipo="prever_resultado",
        )
    )

    recuperado = repositorio.buscar_por_id(exercicio.id)
    assert recuperado.tipo == "prever_resultado"


def test_exercicio_sem_tipo_recebe_padrao(banco_de_teste):
    habilidade = _habilidade_auxiliar()
    nivel = NivelRepository().inserir(
        Nivel(habilidade_id=habilidade.id, nome="Nível", ordem=1)
    )
    exercicio = ExercicioRepository().inserir(
        Exercicio(nivel_id=nivel.id, enunciado="Sem tipo informado.", ordem=1)
    )

    recuperado = ExercicioRepository().buscar_por_id(exercicio.id)
    # O DEFAULT da coluna preenche o tipo quando nada é informado.
    assert recuperado.tipo == "resposta_textual"


# ---------------------------------------------------------------------------
# Carga inicial do currículo
# ---------------------------------------------------------------------------

def test_carga_inicial_cria_curriculo_completo(banco_de_teste):
    resumo = carregar_curriculo_inicial()

    # Tudo é novo na primeira execução.
    assert resumo["modulo_criado"] is True
    assert resumo["habilidade_criada"] is True
    assert resumo["niveis_criados"] == QTD_NIVEIS
    assert resumo["exercicios_criados"] == QTD_EXERCICIOS

    # A hierarquia criada corresponde ao planejado.
    modulos = ModuloRepository().listar()
    assert len(modulos) == 1
    assert modulos[0].nome == "Lógica de Programação"

    habilidades = HabilidadeRepository().listar_por_modulo(modulos[0].id)
    assert len(habilidades) == 1
    assert habilidades[0].nome == "Sequência de instruções"

    niveis = NivelRepository().listar_por_habilidade(habilidades[0].id)
    assert len(niveis) == QTD_NIVEIS
    # Conteúdo conceitual gravado nos níveis da carga.
    assert all(nivel.conteudo_explicacao for nivel in niveis)


def test_relacao_habilidade_para_nivel_em_ordem(banco_de_teste):
    carregar_curriculo_inicial()

    habilidade = HabilidadeRepository().listar()[0]
    niveis = NivelRepository().listar_por_habilidade(habilidade.id)

    # As ordens devem vir em sequência progressiva (1, 2, 3).
    assert [nivel.ordem for nivel in niveis] == [1, 2, 3]
    # Cada nível pertence à habilidade correta (vínculo consistente).
    assert all(nivel.habilidade_id == habilidade.id for nivel in niveis)


def test_relacao_nivel_para_exercicio_em_ordem(banco_de_teste):
    carregar_curriculo_inicial()

    habilidade = HabilidadeRepository().listar()[0]
    niveis = NivelRepository().listar_por_habilidade(habilidade.id)

    for nivel in niveis:
        exercicios = ExercicioRepository().listar_por_nivel(nivel.id)
        assert len(exercicios) == QTD_EXERCICIOS_POR_NIVEL
        # Ordens em sequência dentro do nível (1, 2, 3).
        assert [exercicio.ordem for exercicio in exercicios] == [1, 2, 3]
        # Vínculo consistente com o nível.
        assert all(ex.nivel_id == nivel.id for ex in exercicios)


def test_busca_de_exercicio_especifico(banco_de_teste):
    carregar_curriculo_inicial()

    nivel = NivelRepository().listar_por_habilidade(
        HabilidadeRepository().listar()[0].id
    )[0]
    primeiro = ExercicioRepository().listar_por_nivel(nivel.id)[0]

    recuperado = ExercicioRepository().buscar_por_id(primeiro.id)
    assert recuperado is not None
    assert recuperado.id == primeiro.id
    assert recuperado.enunciado == primeiro.enunciado
    assert recuperado.tipo in ("prever_resultado", "resposta_textual",
                               "escrever_codigo")


def test_carga_inicial_e_idempotente(banco_de_teste):
    carregar_curriculo_inicial()
    primeiro_resumo = carregar_curriculo_inicial()

    # Na segunda execução nada novo é criado.
    assert primeiro_resumo["modulo_criado"] is False
    assert primeiro_resumo["habilidade_criada"] is False
    assert primeiro_resumo["niveis_criados"] == 0
    assert primeiro_resumo["exercicios_criados"] == 0

    # E as quantidades no banco permanecem inalteradas.
    assert len(ModuloRepository().listar()) == 1
    assert len(NivelRepository().listar()) == QTD_NIVEIS
    assert len(ExercicioRepository().listar()) == QTD_EXERCICIOS


def test_carga_inicial_preserva_dados_existentes(banco_de_teste):
    # Dados criados ANTES da carga: um aluno e um módulo próprio.
    from app.repositories import AlunoRepository

    aluno = AlunoRepository().inserir(Aluno(nome="Aluno Pré-existente"))
    modulo_proprio = ModuloRepository().inserir(
        Modulo(nome="Meu módulo personalizado")
    )

    carregar_curriculo_inicial()
    carregar_curriculo_inicial()  # segunda passada também não altera nada

    # O aluno continua intacto (a carga não apaga nada).
    aluno_recuperado = AlunoRepository().buscar_por_id(aluno.id)
    assert aluno_recuperado is not None
    assert aluno_recuperado.nome == "Aluno Pré-existente"

    # O módulo próprio continua lá e não houve duplicação do módulo da carga.
    modulos = ModuloRepository().listar()
    nomes = [modulo.nome for modulo in modulos]
    assert nomes.count("Lógica de Programação") == 1
    assert "Meu módulo personalizado" in nomes