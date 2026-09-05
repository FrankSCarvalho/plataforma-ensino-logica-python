"""Ponto de entrada da Plataforma de Ensino de Lógica.

Ao executar ``python main.py``, este módulo:
  1. Inicializa o banco de dados SQLite (infraestrutura);
  2. Abre a janela do aplicativo Flet com a tela principal.
"""

import flet as ft

from app.database.initialize import initialize_database
from app.ui.main_view import build_main_view


def main(page: ft.Page) -> None:
    """Função de callback chamada pelo Flet para montar a interface."""
    build_main_view(page)


if __name__ == "__main__":
    # Prepara o banco de dados antes de abrir a interface.
    initialize_database()

    # Inicia o aplicativo Flet exibindo uma janela nativa do Windows.
    # ``ft.run`` é a API atual do Flet (a partir da versão 0.80).
    ft.run(main=main)