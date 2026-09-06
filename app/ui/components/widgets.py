"""Componentes Flet reutilizáveis (Tarefa 09).

Reúne apenas os elementos que realmente se repetem em mais de uma tela:

    * ``cabecalho_estudo`` — cabeçalho comum das telas de estudo
      (aluno + habilidade + título + divisor);
    * ``cartao_conteudo``  — bloco "título + texto" que se oculta quando
      o conteúdo está vazio.

Componentes usados em uma única tela continuam na própria view — sem
abstrações desnecessárias.
"""

from __future__ import annotations

import flet as ft

from app.ui.components import theme


def cabecalho_estudo(app, estado, titulo: str) -> ft.Column:
    """Cabeçalho das telas de estudo (nível e exercícios).

    Deixa claro onde o aluno está (habilidade em estudo e título da
    tela), mantendo a navegação previsível nas transições.
    """
    return ft.Column(
        [
            ft.Text(f"Aluno: {app.aluno.nome}", size=theme.TAMANHO_LEGENDA),
            ft.Text(
                estado.habilidade.nome,
                size=theme.TAMANHO_SUBTITULO,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                titulo,
                size=theme.TAMANHO_TITULO,
                weight=ft.FontWeight.BOLD,
                color=theme.COR_PRIMARIA,
            ),
            ft.Divider(),
        ],
        spacing=6,
    )


def cartao_conteudo(titulo: str, conteudo: str) -> ft.Control | None:
    """Cartão com um título e um bloco de texto.

    Devolve ``None`` quando o texto está vazio, para que a tela não exiba
    seções sem conteúdo (ex.: um nível sem "exemplos" preenchidos).
    """
    texto = (conteudo or "").strip()
    if not texto:
        return None
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(titulo, weight=ft.FontWeight.BOLD, size=15),
                    ft.Text(texto, size=theme.TAMANHO_TEXTO, selectable=True),
                ],
                spacing=6,
            ),
            padding=theme.ESPACO_INTERNO,
        )
    )