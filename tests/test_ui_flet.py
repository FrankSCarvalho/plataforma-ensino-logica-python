"""Testes de compatibilidade da UI com a API do Flet instalado (Tarefa 10A).

A Tarefa 10A corrigiu usos de ``Page.open`` que NÃO existem no Flet
0.86.5. Estes testes são COMPORTAMENTAIS: usam um substituto mínimo da
página (``PageFalsa``) que registra o que a ``AplicacaoUI`` faz, sem
abrir janela real. Como o substituto NÃO implementa ``open``, qualquer
regressão que volte a chamar ``page.open`` falha imediatamente com
``AttributeError`` — exatamente o erro observado pelo usuário.

O que é garantido aqui:

    * ``mostrar_erro``/``mostrar_aviso`` exibem mensagem sem exceção;
    * o mecanismo de exibição usado existe de fato na API instalada;
    * o fluxo de encerramento de sessão não é interrompido pelo aviso;
    * a navegação para a lista de habilidades continua funcionando
      após o aviso (reconstrução da tela clicável).
"""

from types import SimpleNamespace

import flet as ft

from app.models import Aluno
from app.repositories import AlunoRepository, HabilidadeRepository
from app.services import carga_inicial, fluxo_estudo
from app.ui.main_view import AplicacaoUI


class PageFalsa:
    """Substituto mínimo de ``ft.Page`` para testes comportamentais.

    Deliberadamente NÃO implementa ``open``: se o código da UI voltar a
    usar a API incompatível, os testes quebram com ``AttributeError``.
    """

    def __init__(self) -> None:
        self.controls = []
        self.title = ""
        self.padding = 0
        self.window = SimpleNamespace(width=0, height=0)
        self.dialogos_exibidos = []
        self.quantidade_updates = 0

    def add(self, controle) -> None:
        self.controls.append(controle)

    def update(self) -> None:
        self.quantidade_updates += 1

    def show_dialog(self, dialogo) -> None:
        self.dialogos_exibidos.append(dialogo)


def _ambiente(banco_de_teste, nome="Aluna Flet"):
    """Cria o currículo e um aluno; devolve (aluno, habilidades)."""
    carga_inicial.carregar_curriculo_inicial()
    carga_inicial.carregar_curriculo_inicial()  # idempotente por natureza
    aluno = AlunoRepository().inserir(Aluno(nome=nome))
    habilidades = HabilidadeRepository().listar()
    return aluno, habilidades


def test_mecanismo_de_exibicao_existe_na_api_do_flet_instalado():
    """O mecanismo usado pela UI é o disponível no Flet 0.86.5.

    Confirma por introspecção que ``Page.show_dialog`` existe e que
    ``Page.open`` NÃO existe (a API que causava o BUG-01).
    """
    assert hasattr(ft.Page, "show_dialog") is True
    assert hasattr(ft.Page, "open") is False


def test_mostrar_erro_nao_lanca_excecao_e_nao_usa_page_open(banco_de_teste):
    _ambiente(banco_de_teste)
    page = PageFalsa()
    app = AplicacaoUI(page)

    # Se ``mostrar_erro`` usasse ``page.open``, o AttributeError ocorria
    # aqui (o substituto não implementa ``open``).
    app.mostrar_erro("Mensagem de erro de teste.")

    assert len(page.dialogos_exibidos) == 1
    dialogo = page.dialogos_exibidos[0]
    assert isinstance(dialogo, ft.AlertDialog)


def test_mostrar_aviso_nao_lanca_excecao_e_nao_usa_page_open(banco_de_teste):
    _ambiente(banco_de_teste)
    page = PageFalsa()
    app = AplicacaoUI(page)

    app.mostrar_aviso("Mensagem de aviso de teste.")

    assert len(page.dialogos_exibidos) == 1
    dialogo = page.dialogos_exibidos[0]
    assert isinstance(dialogo, ft.AlertDialog)


def test_fluxo_encerramento_nao_eh_interrompido_pelo_aviso(banco_de_teste):
    """O mesmo fluxo do botão 'Encerrar sessão' completo, sem exceções.

    Passos reproduzidos (como em ``exercicio_view._build_resumo``):
    encerrar a sessão -> exibir o aviso -> voltar à lista de habilidades.
    A exibição do aviso NÃO pode interromper a navegação.
    """
    aluno, habilidades = _ambiente(banco_de_teste)
    page = PageFalsa()
    app = AplicacaoUI(page)
    app.aluno = aluno

    # Abre a habilidade e inicia os exercícios (cria a sessão).
    app.mostrar_nivel(habilidades[0].id)
    estado = app.estado_estudo
    assert estado is not None
    fluxo_estudo.iniciar_sessao(estado)
    assert estado.sessao is not None

    # Fluxo do botão "Encerrar sessão":
    fluxo_estudo.encerrar_sessao(estado)
    app.estado_estudo = None
    app.mostrar_aviso("Sessão de estudo encerrada.")
    app.mostrar_habilidades()

    # A sessão foi encerrada, o aviso foi exibido e a navegação seguiu.
    assert estado.sessao is None
    assert len(page.dialogos_exibidos) == 1
    assert page.controls  # a tela de habilidades foi reconstruída


def test_navegacao_para_habilidades_reconstrui_tela_clicavel(
    banco_de_teste,
):
    """A lista de habilidades pode ser reconstruída sem erro de API.

    Protege a correção do clique do cartão: no Flet 0.86.5 o ``Card``
    não aceita ``on_click``; a tela deve construir sem ``TypeError``.
    """
    aluno, habilidades = _ambiente(banco_de_teste)
    page = PageFalsa()
    app = AplicacaoUI(page)
    app.aluno = aluno

    # Não deve lançar TypeError (Card.on_click) nem qualquer outra exceção.
    app.mostrar_habilidades()
    assert page.controls