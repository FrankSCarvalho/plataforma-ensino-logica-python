"""Tela principal (única) da aplicação.

Exibe apenas a identificação do sistema e uma mensagem indicando
que a aplicação foi iniciada corretamente.
"""

import flet as ft


def build_main_view(page: ft.Page) -> None:
    """Compõe os elementos visuais da tela principal."""
    # Título da janela do aplicativo.
    page.title = "Plataforma de Ensino de Lógica"

    # Dimensões iniciais da janela (comportamento de desktop).
    page.window.width = 900
    page.window.height = 600

    # Centraliza o conteúdo na janela.
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Conteúdo da tela principal.
    page.add(
        ft.Text(
            "Plataforma de Ensino de Lógica",
            size=32,
            weight=ft.FontWeight.BOLD,
        ),
        ft.Text(
            "Aplicação iniciada corretamente.",
            size=16,
        ),
    )