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
from app.ui.components import theme


def _situacao_do_progresso(app, habilidade_id: int) -> tuple[str, ft.Icon]:
    """Devolve (texto curto, ícone) da situação do aluno na habilidade.

    Estados exibidos pela tela:

        * sem progresso                -> "Não iniciada (começa no nível 1)";
        * em andamento                 -> "Em andamento";
        * concluída                    -> "Concluída".

    A frase completa (com o nível atual) é produzida pelo serviço
    (``resumo_do_progresso``) e exibida como subtítulo do cartão.
    """
    progresso = fluxo_estudo.progresso_do_aluno(app.aluno.id, habilidade_id)
    if progresso is None:
        return "Não iniciada", ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED)
    if progresso.status == STATUS_CONCLUIDO:
        return "Concluída", ft.Icon(
            ft.Icons.CHECK_CIRCLE, color=theme.COR_SUCESSO
        )
    return "Em andamento", ft.Icon(
        ft.Icons.PLAY_CIRCLE_OUTLINE, color=theme.COR_PRIMARIA
    )


def build(app) -> ft.Control:
    """Monta a tela de habilidades para o aluno selecionado."""
    habilidades = fluxo_estudo.listar_habilidades()

    elementos: list[ft.Control] = [
        ft.Row(
            [
                ft.Icon(ft.Icons.SCHOOL, size=30, color=theme.COR_PRIMARIA),
                ft.Text(
                    "Habilidades do currículo",
                    size=theme.TAMANHO_TITULO_PAGINA,
                    weight=ft.FontWeight.BOLD,
                    color=theme.COR_PRIMARIA,
                ),
            ],
            spacing=8,
        ),
        ft.Text(
            f"Aluno: {app.aluno.nome}",
            size=theme.TAMANHO_TEXTO,
            color=theme.COR_TEXTO_SECUNDARIO,
        ),
        ft.Text(
            "Escolha uma habilidade para começar ou continuar estudando.",
            size=theme.TAMANHO_TEXTO,
        ),
        ft.Divider(),
    ]

    if not habilidades:
        # Currículo vazio (seed ainda não executado): orientar o usuário.
        elementos.append(
            ft.Container(
                content=ft.Text(
                    "Nenhuma habilidade disponível. Execute a carga inicial "
                    "do currículo (python -m app.services.carga_inicial).",
                    color=theme.COR_AVISO,
                ),
                padding=10,
                bgcolor=theme.COR_AVISO_FUNDO,
                border_radius=8,
            )
        )
    else:
        for habilidade in habilidades:
            situacao, icone_situacao = _situacao_do_progresso(
                app, habilidade.id
            )
            # Cartão clicável: nome + descrição + nível atual/situação.
            elementos.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        icone_situacao,
                                        ft.Text(
                                            habilidade.nome,
                                            size=17,
                                            weight=ft.FontWeight.BOLD,
                                            expand=True,
                                        ),
                                        ft.Text(
                                            situacao,
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                            color=(
                                                theme.COR_SUCESSO
                                                if situacao == "Concluída"
                                                else theme.COR_PRIMARIA
                                            ),
                                        ),
                                        ft.Icon(
                                            ft.Icons.CHEVRON_RIGHT,
                                            color=theme.COR_TEXTO_SECUNDARIO,
                                        ),
                                    ],
                                    spacing=10,
                                ),
                                ft.Text(
                                    habilidade.descricao or "",
                                    size=14,
                                    color=ft.Colors.GREY_800,
                                ),
                                ft.Text(
                                    f"Progresso: "
                                    f"{fluxo_estudo.resumo_do_progresso(app.aluno.id, habilidade.id)}",
                                    size=13,
                                    color=theme.COR_TEXTO_SECUNDARIO,
                                ),
                            ],
                            spacing=8,
                        ),
                        padding=theme.ESPACO_INTERNO,
                        # O clique fica no Container interno porque o Card
                        # do Flet 0.86.5 não aceita ``on_click`` diretamente.
                        on_click=lambda evento, h=habilidade: app.mostrar_nivel(
                            h.id
                        ),
                    ),
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