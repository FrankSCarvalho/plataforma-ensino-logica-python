"""Tela 2 — lista de habilidades disponíveis com o progresso do aluno.

Os dados vêm do banco (via serviço ``fluxo_estudo``): a UI nunca
carrega currículo fixo em código. Para cada habilidade são exibidos
nome, descrição e a situação atual do progresso do aluno selecionado.

A abertura de uma habilidade (clique) delega ao ``main_view``, que
aciona o motor pedagógico para garantir o progresso inicial.
"""

import flet as ft

from app.services import fluxo_estudo
from app.services.motor_pedagogico import STATUS_CONCLUIDO


def _descricao_do_progresso(app, habilidade_id: int) -> str:
    """Monta o texto informativo do progresso do aluno na habilidade."""
    progresso = fluxo_estudo.progresso_do_aluno(app.aluno.id, habilidade_id)
    if progresso is None:
        return "Ainda não iniciada"
    situacao = "Concluída" if progresso.status == STATUS_CONCLUIDO else "Em andamento"
    return f"{situacao} — nível atual: {fluxo_estudo.nome_do_nivel(progresso.nivel_id)}"


def build(app) -> ft.Control:
    """Monta a tela de habilidades para o aluno selecionado."""
    habilidades = fluxo_estudo.listar_habilidades()

    elementos: list[ft.Control] = [
        ft.Text(f"Aluno: {app.aluno.nome}", size=16, weight=ft.FontWeight.BOLD),
        ft.Text("Habilidades do currículo", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(),
    ]

    if not habilidades:
        # Currículo vazio (seed ainda não executado): orientar o usuário.
        elementos.append(
            ft.Container(
                content=ft.Text(
                    "Nenhuma habilidade disponível. Execute a carga inicial "
                    "do currículo (python -m app.services.carga_inicial).",
                    color=ft.Colors.ORANGE_800,
                ),
                padding=10,
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=8,
            )
        )
    else:
        for habilidade in habilidades:
            elementos.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.SCHOOL),
                    title=ft.Text(habilidade.nome, size=17, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(
                        f"{habilidade.descricao}\n"
                        f"Progresso: {_descricao_do_progresso(app, habilidade.id)}"
                    ),
                    is_three_line=True,
                    on_click=lambda evento, h=habilidade: app.mostrar_nivel(h.id),
                    hover_color=ft.Colors.BLUE_50,
                )
            )

    elementos.append(ft.Divider())
    elementos.append(
        ft.OutlinedButton(
            "Trocar aluno",
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda evento: app.mostrar_selecao_aluno(),
        )
    )

    return ft.Column(elementos, scroll=ft.ScrollMode.AUTO, spacing=10)