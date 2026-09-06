"""Tela 1 — seleção/cadastro simples do aluno (sem autenticação).

A escolha do aluno é feita por lista (mecanismo deliberadamente simples
da Tarefa 08: ainda NÃO existe login). Quando não há nenhum aluno
cadastrado, a própria tela oferece a criação de um aluno inicial.

Toda persistência é delegada ao serviço ``fluxo_estudo`` — esta tela
não conhece repositories nem SQL.
"""

import flet as ft

from app.services import fluxo_estudo
from app.ui.components import theme


def build(app) -> ft.Control:
    """Monta a tela de seleção de aluno para a aplicação informada."""
    alunos = fluxo_estudo.listar_alunos()

    elementos: list[ft.Control] = [
        ft.Text(
            "Plataforma de Ensino de Lógica",
            size=theme.TAMANHO_TITULO_PAGINA,
            weight=ft.FontWeight.BOLD,
            color=theme.COR_PRIMARIA,
        ),
        ft.Text(
            "Quem vai estudar agora?",
            size=theme.TAMANHO_SUBTITULO,
            color=theme.COR_TEXTO_SECUNDARIO,
        ),
        ft.Divider(),
    ]

    if alunos:
        # Lista de alunos existentes: um botão/cartão por aluno.
        elementos.append(
            ft.Text(
                "Selecione um aluno cadastrado:",
                size=theme.TAMANHO_TEXTO,
                weight=ft.FontWeight.BOLD,
            )
        )
        for aluno in alunos:
            elementos.append(
                ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.PERSON, color=theme.COR_PRIMARIA
                    ),
                    title=ft.Text(aluno.nome, size=16),
                    subtitle=ft.Text(
                        "Toque para começar ou continuar os estudos"
                    ),
                    trailing=ft.Icon(
                        ft.Icons.CHEVRON_RIGHT, color=theme.COR_TEXTO_SECUNDARIO
                    ),
                    on_click=lambda evento, a=aluno: _selecionar(app, a),
                    hover_color=theme.COR_DESTAQUE_FUNDO,
                )
            )
    else:
        elementos.append(
            ft.Container(
                content=ft.Text(
                    "Nenhum aluno cadastrado ainda. "
                    "Crie o primeiro aluno para começar.",
                    color=theme.COR_AVISO,
                ),
                padding=10,
                bgcolor=theme.COR_AVISO_FUNDO,
                border_radius=8,
            )
        )

    # ---- Criação de novo aluno ----------------------------------------
    campo_nome = ft.TextField(
        label="Nome de um novo aluno",
        hint_text="Ex.: Maria",
        expand=False,
    )

    def cadastrar(evento) -> None:
        nome = (campo_nome.value or "").strip()
        if not nome:
            app.mostrar_aviso("Digite um nome para o novo aluno.")
            return
        try:
            aluno = fluxo_estudo.criar_aluno(nome)
        except Exception:
            app.mostrar_erro("Não foi possível cadastrar o aluno.")
            return
        _selecionar(app, aluno)

    elementos.extend(
        [
            ft.Divider(),
            campo_nome,
            ft.FilledButton(
                "Cadastrar e estudar com este aluno",
                icon=ft.Icons.ADD,
                on_click=cadastrar,
            ),
            ft.Container(height=8),
        ]
    )

    return ft.Column(elementos, scroll=ft.ScrollMode.AUTO, spacing=10)


def _selecionar(app, aluno) -> None:
    """Guarda o aluno escolhido no estado e avança para as habilidades.

    Ao trocar de aluno, o estado de estudo anterior (progresso, exercícios
    e sessão) é limpado para que nenhum dado de um aluno apareça na lista
    de outro. A limpeza é feita pela aplicação (``main_view``).
    """
    app.aluno = aluno
    app.mostrar_habilidades()