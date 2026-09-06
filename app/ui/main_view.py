"""Aplicação principal (Tarefa 08): navegação e estado da interface.

Primeira versão do fluxo real de estudo. Este módulo contém APENAS a
camada de apresentação/navegação:

    * mantém o estado da interface em uma única instância de
      ``AplicacaoUI`` (sem variáveis globais);
    * navega entre as telas (aluno -> habilidades -> nível -> exercícios)
      reconstruindo o controle da página a cada transição;
    * delega TODA regra ao serviço ``app.services.fluxo_estudo``, que por
      sua vez usa os repositórios, o avaliador e o motor pedagógico.

Estrutura das telas (cada arquivo com responsabilidade clara):

    app/ui/aluno_view.py       -- seleção do aluno (sem autenticação)
    app/ui/habilidade_view.py  -- lista de habilidades + progresso atual
    app/ui/nivel_view.py       -- conteúdo conceitual do nível atual
    app/ui/exercicio_view.py   -- exercícios, resposta, resultado, resumo
"""

import traceback

import flet as ft

from app.services import fluxo_estudo
from app.ui import aluno_view, exercicio_view, habilidade_view, nivel_view


class AplicacaoUI:
    """Estado e navegação da aplicação (um objeto por janela aberta)."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page

        # ---- Estado explícito da interface (nada de globais) -----------
        self.aluno = None            # aluno selecionado (tela de aluno)
        self.estado_estudo = None    # EstadoEstudo do serviço de fluxo

        # Configuração da janela (desktop).
        page.title = "Plataforma de Ensino de Lógica"
        page.window.width = 960
        page.window.height = 680
        page.padding = 24

        self.mostrar_selecao_aluno()

    # ------------------------------------------------------------------
    # Navegação
    # ------------------------------------------------------------------
    def navegar(self, controle: ft.Control) -> None:
        """Substitui o conteúdo da página pelo controle informado."""
        self.page.controls.clear()
        self.page.add(controle)
        self.page.update()

    # Telas (cada método delega a composição ao módulo da tela) ---------
    def mostrar_selecao_aluno(self) -> None:
        """Tela 1: seleção/cadastro simples do aluno."""
        self.navegar(aluno_view.build(self))

    def mostrar_habilidades(self) -> None:
        """Tela 2: lista de habilidades com o progresso do aluno."""
        if self.aluno is None:
            # Defesa: voltar para a seleção quando não há aluno definido.
            self.mostrar_selecao_aluno()
            return
        self.navegar(habilidade_view.build(self))

    def mostrar_nivel(self, habilidade_id: int) -> None:
        """Tela 3: abre a habilidade e exibe o conteúdo do nível atual.

        A abertura garante o progresso inicial (motor pedagógico) e
        carrega o nível apontado por ele. Erros são tratados de forma
        amigável (sem traceback para o aluno).
        """
        try:
            self.estado_estudo = fluxo_estudo.abrir_habilidade(
                self.aluno.id, habilidade_id
            )
        except Exception:
            traceback.print_exc()  # detalhe técnico apenas no console
            self.mostrar_erro(
                "Não foi possível abrir esta habilidade. Verifique se ela "
                "possui níveis cadastrados."
            )
            return
        self.navegar(nivel_view.build(self))

    def mostrar_exercicios(self) -> None:
        """Tela 4: sequência de exercícios com resposta e resultado."""
        self.navegar(exercicio_view.build(self))

    # ------------------------------------------------------------------
    # Tratamento de erros amigável
    # ------------------------------------------------------------------
    def mostrar_erro(self, mensagem: str) -> None:
        """Exibe uma mensagem amigável; o detalhe técnico vai ao console.

        Usada pelas telas para envolver chamadas ao serviço: o aluno
        nunca vê um traceback, mas o desenvolvedor mantém o diagnóstico
        completo na saída padrão.
        """
        self.page.open(
            ft.SnackBar(
                content=ft.Text(mensagem, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
                duration=4000,
            )
        )

    def mostrar_aviso(self, mensagem: str) -> None:
        """Exibe uma mensagem informativa (ex.: sessão encerrada)."""
        self.page.open(
            ft.SnackBar(
                content=ft.Text(mensagem, color=ft.Colors.WHITE),
                duration=3000,
            )
        )


def build_main_view(page: ft.Page) -> None:
    """Ponto de montagem da interface (chamado por ``main.py``)."""
    AplicacaoUI(page)