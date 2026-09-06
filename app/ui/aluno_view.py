"""Tela 1 — seleção/cadastro simples do aluno (sem autenticação).

A escolha do aluno é feita por lista (mecanismo deliberadamente simples
da Tarefa 08: ainda NÃO existe login). Quando não há nenhum aluno
cadastrado, a própria tela oferece a criação de um aluno inicial.

Toda persistência é delegada ao serviço ``fluxo_estudo`` — esta tela
não conhece repositories nem SQL.
"""

import flet as ft

from app.services import fluxo_estudo


def build(app) -> ft.Control:
    """Monta a tela de seleção de aluno para a aplicação informada."""
    alunos = fluxo_estudo.listar_alunos()

    elementos: list[ft.Control] = [
        ft.Text("Plataforma de Ensino de Lógica", size=28, weight=ft.FontWeight.BOLD),
        ft.Text("Quem vai estudar agora?", size=16),
        ft.Divider(),
    ]

    if alunos:
        # Lista de alunos existentes: um botão por aluno.
        elementos.append(
            ft.Text("Selecione um aluno cadastrado:", size=14, weight=ft.FontWeight.BOLD)
        )
        for aluno in alunos:
            elementos.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PERSON),
                    title=ft.Text(aluno.nome, size=16),
                    subtitle=ft.Text(f"Estudante #{aluno.id}"),
                    on_click=lambda evento, a=aluno: _selecionar(app, a),
                    hover_color=ft.Colors.BLUE_50,
                )
            )
    else:
        elementos.append(
            ft.Container(
                content=ft.Text(
                    "Nenhum aluno cadastrado ainda. "
                    "Crie o primeiro aluno para começar.",
                    color=ft.Colors.ORANGE_800,
                ),
                padding=10,
                bgcolor=ft.Colors.ORANGE_50,
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
            ft.FilledButton("Cadastrar e estudar com este aluno", on_click=cadastrar),
        ]
    )

    return ft.Column(elementos, scroll=ft.ScrollMode.AUTO, spacing=10)


def _selecionar(app, aluno) -> None:
    """Guarda o aluno escolhido no estado e avança para as habilidades."""
    app.aluno = aluno
    app.mostrar_habilidades()