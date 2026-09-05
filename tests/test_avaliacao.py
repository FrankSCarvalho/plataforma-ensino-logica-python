"""Testes da camada de avaliação de respostas (Tarefa 06).

Cobrem o avaliador (função pura), o serviço de registro de tentativas e
as garantias de segurança/imutabilidade:

    * correção automática determinística do tipo ``prever_resultado``
      (sem IA, sem comparação aproximada, sem bibliotecas externas);
    * normalização conservadora de respostas (espaços triviais sim,
      conteúdo interno preservado);
    * ``resposta_textual`` e ``escrever_codigo`` -> ``nao_avaliada``;
    * registro da tentativa com vínculos corretos e histórico intacto;
    * nenhuma avaliação altera o progresso do aluno.

Todos os testes usam o banco TEMPORÁRIO da fixture ``banco_de_teste`` —
o banco de desenvolvimento em ``data/`` não é tocado.
"""

import inspect

import pytest

from app.models import (
    RESULTADO_CORRETA,
    RESULTADO_INCORRETA,
    RESULTADO_NAO_AVALIADA,
    TIPO_ESCREVER_CODIGO,
    TIPO_PREVER_RESULTADO,
    TIPO_RESPOSTA_TEXTUAL,
    Aluno,
    Exercicio,
    ProgressoAluno,
    SessaoEstudo,
)
from app.repositories import (
    AlunoRepository,
    ExercicioRepository,
    NivelRepository,
    ProgressoAlunoRepository,
    SessaoEstudoRepository,
    TentativaRepository,
)
from app.services import carga_inicial
from app.services.avaliador import avaliar_resposta, normalizar_resposta
from app.services.registro_tentativas import registrar_tentativa

# Repositórios reutilizados (a conexão é aberta por operação; não há
# estado no repositório).
NIVEIS = NivelRepository()
EXERCICIOS = ExercicioRepository()
ALUNOS = AlunoRepository()
SESSOES = SessaoEstudoRepository()
TENTATIVAS = TentativaRepository()
PROGRESSOS = ProgressoAlunoRepository()


# ---------------------------------------------------------------------------
# Normalização da resposta — regra explícita e testada
# ---------------------------------------------------------------------------

def test_normalizacao_remove_espacos_nas_bordas():
    assert normalizar_resposta("  Bola  \n") == "Bola"


def test_normalizacao_unifica_quebras_de_linha():
    # \r\n e \r são triviais (Windows x outros sistemas) e viram \n.
    assert normalizar_resposta("cafe\r\npao\rleite") == "cafe\npao\nleite"


def test_normalizacao_remove_espacos_a_direita_de_cada_linha():
    assert normalizar_resposta("cafe  \npao\t\nleite") == "cafe\npao\nleite"


def test_normalizacao_preserva_maiusculas_e_minusculas():
    # A saída de um programa distingue caixa: Bola != bola.
    assert normalizar_resposta("Bola") != normalizar_resposta("bola")


def test_normalizacao_preserva_espacos_internos():
    # Normalização conservadora: não transforma respostas diferentes em iguais.
    assert normalizar_resposta("dois um") != normalizar_resposta("dois  um")


def test_normalizacao_trata_none_como_vazio():
    assert normalizar_resposta(None) == ""


# ---------------------------------------------------------------------------
# Avaliador — função pura, por tipo de exercício
# ---------------------------------------------------------------------------

def _exercicio_prever_resposta_esperada(resposta: str) -> Exercicio:
    """Cria um exercício ``prever_resultado`` em memória (sem banco)."""
    return Exercicio(
        nivel_id=1,
        enunciado="Preveja a saída.",
        ordem=1,
        tipo=TIPO_PREVER_RESULTADO,
        resposta_esperada=resposta,
    )


def test_prever_resultado_resposta_correta():
    exercicio = _exercicio_prever_resposta_esperada("Bola")
    avaliacao = avaliar_resposta(exercicio, "Bola")
    assert avaliacao.resultado == RESULTADO_CORRETA


def test_prever_resultado_diferenca_de_formatacao_trivial_eh_correta():
    exercicio = _exercicio_prever_resposta_esperada("Bola")
    # Espaços nas bordas e quebra de linha final são diferenças triviais.
    avaliacao = avaliar_resposta(exercicio, "   Bola  \r\n")
    assert avaliacao.resultado == RESULTADO_CORRETA


def test_prever_resultado_resposta_multilinha_com_formatacao_trivial():
    exercicio = _exercicio_prever_resposta_esperada("cafe\npao\nleite")
    avaliacao = avaliar_resposta(exercicio, "cafe \r\npao\r\nleite\n")
    assert avaliacao.resultado == RESULTADO_CORRETA


def test_prever_resultado_resposta_incorreta():
    exercicio = _exercicio_prever_resposta_esperada("Bola")
    avaliacao = avaliar_resposta(exercicio, "Chuteira")
    assert avaliacao.resultado == RESULTADO_INCORRETA


def test_prever_resultado_diferenca_de_caixa_eh_incorreta():
    # Bola != bola: a comparação é sensível a maiúsculas/minúsculas.
    exercicio = _exercicio_prever_resposta_esperada("Bola")
    avaliacao = avaliar_resposta(exercicio, "bola")
    assert avaliacao.resultado == RESULTADO_INCORRETA


def test_prever_resultado_resposta_vazia_eh_incorreta():
    # Resposta vazia existe e não é igual à esperada -> incorreta.
    exercicio = _exercicio_prever_resposta_esperada("Bola")
    avaliacao = avaliar_resposta(exercicio, "")
    assert avaliacao.resultado == RESULTADO_INCORRETA


def test_prever_resultado_sem_resposta_esperada_fica_nao_avaliada():
    # Exercício sem resposta esperada cadastrada (coluna vazia da v5).
    exercicio = _exercicio_prever_resposta_esperada("")
    avaliacao = avaliar_resposta(exercicio, "qualquer coisa")
    assert avaliacao.resultado == RESULTADO_NAO_AVALIADA


def test_resposta_textual_fica_nao_avaliada():
    exercicio = Exercicio(
        nivel_id=1,
        enunciado="Reescreva as instruções.",
        tipo=TIPO_RESPOSTA_TEXTUAL,
    )
    avaliacao = avaliar_resposta(
        exercicio, 'escreva("Fim")\nescreva("Inicio")'
    )
    assert avaliacao.resultado == RESULTADO_NAO_AVALIADA


def test_escrever_codigo_fica_nao_avaliada_e_nao_executa_codigo():
    exercicio = Exercicio(
        nivel_id=1,
        enunciado="Escreva as instruções.",
        tipo=TIPO_ESCREVER_CODIGO,
    )
    # Resposta hostil: se o código fosse executado, o teste falharia.
    resposta_maliciosa = "__import__('os').system('echo PWNED')"
    avaliacao = avaliar_resposta(exercicio, resposta_maliciosa)
    assert avaliacao.resultado == RESULTADO_NAO_AVALIADA


def test_tipo_desconhecido_fica_nao_avaliada():
    exercicio = Exercicio(nivel_id=1, enunciado="?", tipo="multipla_escolha")
    avaliacao = avaliar_resposta(exercicio, "A")
    assert avaliacao.resultado == RESULTADO_NAO_AVALIADA


def test_avaliador_eh_deterministico():
    # Mesma entrada -> mesmo resultado (função pura, sem IA).
    exercicio = _exercicio_prever_resposta_esperada("Bola")
    primeira = avaliar_resposta(exercicio, "Bola")
    segunda = avaliar_resposta(exercicio, "Bola")
    assert primeira.resultado == segunda.resultado
    assert primeira.feedback == segunda.feedback


def test_avaliador_nao_utiliza_ia_nem_execucao_de_codigo():
    # Verificação estática: o módulo do avaliador não usa eval/exec/
    # subprocess e não depende de serviços de IA ou bibliotecas externas.
    from app.services import avaliador as modulo_avaliador

    fonte = inspect.getsource(modulo_avaliador)
    # Verifica USO real (import/chamada), não apenas menção em comentários.
    assert "eval(" not in fonte
    assert "exec(" not in fonte
    assert "import subprocess" not in fonte
    assert "subprocess." not in fonte
    assert "os.system" not in fonte
    assert "openai" not in fonte.lower()
    assert "requests" not in fonte.lower()
    assert "anthropic" not in fonte.lower()


# ---------------------------------------------------------------------------
# Registro de tentativas — fluxo completo com banco de teste
# ---------------------------------------------------------------------------

def _cenario(banco_de_teste):
    """Cria aluno + currículo + sessão e devolve os objetos necessários."""
    aluno = ALUNOS.inserir(Aluno(nome="Aluna Teste"))
    resultado_seed = carga_inicial.carregar_curriculo_inicial()
    habilidade = resultado_seed["habilidade"]
    niveis = NIVEIS.listar_por_habilidade(habilidade.id)
    exercicios = EXERCICIOS.listar_por_nivel(niveis[0].id)
    exercicio_prever = next(
        e for e in exercicios if e.tipo == TIPO_PREVER_RESULTADO
    )
    sessao = SESSOES.inserir(SessaoEstudo(aluno_id=aluno.id))
    return {
        "aluno": aluno,
        "sessao": sessao,
        "exercicio": exercicio_prever,
        "seed": resultado_seed,
    }


def test_registro_de_tentativa_com_resposta_correta(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    registro = registrar_tentativa(
        sessao_id=cenario["sessao"].id,
        aluno_id=cenario["aluno"].id,
        exercicio_id=cenario["exercicio"].id,
        resposta="  Bola  \n",
    )
    assert registro.avaliacao.resultado == RESULTADO_CORRETA
    assert registro.tentativa.id is not None
    assert registro.tentativa.resultado == RESULTADO_CORRETA


def test_registro_de_tentativa_com_resposta_incorreta(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    registro = registrar_tentativa(
        sessao_id=cenario["sessao"].id,
        aluno_id=cenario["aluno"].id,
        exercicio_id=cenario["exercicio"].id,
        resposta="Chuteira",
    )
    assert registro.avaliacao.resultado == RESULTADO_INCORRETA
    assert registro.tentativa.resultado == RESULTADO_INCORRETA


def test_tentativa_fica_vinculada_ao_aluno_e_a_sessao_corretos(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    registro = registrar_tentativa(
        sessao_id=cenario["sessao"].id,
        aluno_id=cenario["aluno"].id,
        exercicio_id=cenario["exercicio"].id,
        resposta="Bola",
    )
    gravada = TENTATIVAS.buscar_por_id(registro.tentativa.id)
    assert gravada.aluno_id == cenario["aluno"].id
    assert gravada.sessao_id == cenario["sessao"].id
    assert gravada.exercicio_id == cenario["exercicio"].id


def test_tentativas_anteriores_sao_preservadas(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    primeiro = registrar_tentativa(
        sessao_id=cenario["sessao"].id,
        aluno_id=cenario["aluno"].id,
        exercicio_id=cenario["exercicio"].id,
        resposta="errado",
    )
    segundo = registrar_tentativa(
        sessao_id=cenario["sessao"].id,
        aluno_id=cenario["aluno"].id,
        exercicio_id=cenario["exercicio"].id,
        resposta="Bola",
    )
    # Duas tentativas distintas coexistem; a primeira permanece intacta.
    assert len(TENTATIVAS.listar()) == 2
    original = TENTATIVAS.buscar_por_id(primeiro.tentativa.id)
    assert original.resposta == "errado"
    assert original.resultado == RESULTADO_INCORRETA
    assert segundo.tentativa.id != primeiro.tentativa.id


def test_exercicio_inexistente_eh_rejeitado(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    with pytest.raises(ValueError, match="Exercício"):
        registrar_tentativa(
            sessao_id=cenario["sessao"].id,
            aluno_id=cenario["aluno"].id,
            exercicio_id=999999,
            resposta="Bola",
        )


def test_sessao_inexistente_eh_rejeitada(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    with pytest.raises(ValueError, match="Sessão"):
        registrar_tentativa(
            sessao_id=999999,
            aluno_id=cenario["aluno"].id,
            exercicio_id=cenario["exercicio"].id,
            resposta="Bola",
        )


def test_aluno_inexistente_eh_rejeitado(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    with pytest.raises(ValueError, match="Aluno"):
        registrar_tentativa(
            sessao_id=cenario["sessao"].id,
            aluno_id=999999,
            exercicio_id=cenario["exercicio"].id,
            resposta="Bola",
        )


def test_sessao_de_outro_aluno_eh_rejeitada(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    outro_aluno = ALUNOS.inserir(Aluno(nome="Outro Aluno"))
    with pytest.raises(ValueError, match="não pertence"):
        registrar_tentativa(
            sessao_id=cenario["sessao"].id,
            aluno_id=outro_aluno.id,
            exercicio_id=cenario["exercicio"].id,
            resposta="Bola",
        )


def test_avaliacao_nao_altera_progresso_do_aluno(banco_de_teste):
    cenario = _cenario(banco_de_teste)
    niveis = NIVEIS.listar_por_habilidade(cenario["seed"]["habilidade"].id)
    progresso = PROGRESSOS.inserir(
        ProgressoAluno(
            aluno_id=cenario["aluno"].id,
            habilidade_id=cenario["seed"]["habilidade"].id,
            nivel_id=niveis[0].id,
            status="em_andamento",
        )
    )
    # Campos gerados pelo banco (timestamps) só aparecem ao reler.
    progresso_gravado = PROGRESSOS.buscar_por_id(progresso.id)
    registrar_tentativa(
        sessao_id=cenario["sessao"].id,
        aluno_id=cenario["aluno"].id,
        exercicio_id=cenario["exercicio"].id,
        resposta="Bola",
    )
    recuperado = PROGRESSOS.buscar_por_id(progresso.id)
    assert recuperado.nivel_id == niveis[0].id
    assert recuperado.status == "em_andamento"
    # Nenhum campo do progresso mudou após a avaliação/registro.
    assert recuperado.atualizado_em == progresso_gravado.atualizado_em
    assert recuperado.criado_em == progresso_gravado.criado_em


# ---------------------------------------------------------------------------
# Seed — respostas esperadas e idempotência
# ---------------------------------------------------------------------------

def test_seed_preenche_resposta_esperada_dos_prever_resultado(banco_de_teste):
    carga_inicial.carregar_curriculo_inicial()
    prever = [
        e for e in EXERCICIOS.listar() if e.tipo == TIPO_PREVER_RESULTADO
    ]
    assert len(prever) == 5
    assert all(e.resposta_esperada for e in prever)


def test_seed_eh_idempotente_com_respostas_esperadas(banco_de_teste):
    carga_inicial.carregar_curriculo_inicial()
    segunda = carga_inicial.carregar_curriculo_inicial()
    assert segunda["exercicios_criados"] == 0
    assert segunda["niveis_criados"] == 0
    # Nada restou para preencher: as respostas já foram gravadas.
    assert segunda["respostas_esperadas_preenchidas"] == 0


def test_seed_backfill_de_exercicios_sem_resposta_esperada(banco_de_teste):
    # Simula um banco criado na Tarefa 05: currículo existente SEM resposta
    # esperada. A carga desta versão deve preencher o campo uma única vez,
    # sem duplicar exercícios e preservando os enunciados.
    carga_inicial.carregar_curriculo_inicial()
    for exercicio in EXERCICIOS.listar():
        exercicio.resposta_esperada = ""
        EXERCICIOS.atualizar(exercicio)

    resumo = carga_inicial.carregar_curriculo_inicial()
    assert resumo["exercicios_criados"] == 0  # nada duplicado
    assert resumo["respostas_esperadas_preenchidas"] == 5

    # Segunda execução: idempotente (nada mais a preencher).
    novamente = carga_inicial.carregar_curriculo_inicial()
    assert novamente["respostas_esperadas_preenchidas"] == 0