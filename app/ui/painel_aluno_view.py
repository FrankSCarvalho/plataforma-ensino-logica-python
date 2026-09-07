"""Tela do Painel do Aluno (Tarefa 11).

Tela principal do aluno depois que ele é selecionado.

Apresenta de forma simples e clara:

    * identificação do aluno;
    * resumo geral do progresso (total / não iniciadas / em andamento / concluídas);
    * lista de habilidades com situação e nível atual;
    * orientação de próximo passo;
    * acesso rápido para continuar os estudos.

A tela NUNCA consulta o banco diretamente: delega ao serviço
``painel_aluno``, que usa os repositories existentes.
"""

import flet as ft

from app.services import painel_aluno
from app.ui.components import theme


def build(app) -> ft.Control:
    """Monta a tela do painel do aluno selecionado."""
    painel = painel_aluno.obter_painel_do_aluno(app.aluno.id, app.aluno.nome)

    cabecalho = ft.Column(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.PERSON, size=30, color=theme.COR_PRIMARIA),
                    ft.Text(
                        f"Olá, {painel.aluno_nome}!",
                        size=theme.TAMANHO_TITULO_PAGINA,
                        weight=ft.FontWeight.BOLD,
                        color=theme.COR_PRIMARIA,
                    ),
                ],
                spacing=8,
            ),
            ft.Text(
                painel.proximo_passo,
                size=theme.TAMANHO_TEXTO,
                color=theme.COR_TEXTO_SECUNDARIO,
            ),
        ],
        spacing=4,
    )

    resumo = _construir_cartoes_de_resumo(painel)
    habilidades = _construir_lista_de_habilidades(app, painel)

    acoes = ft.Row(
        [
            ft.OutlinedButton(
                "Trocar aluno",
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda evento: app.mostrar_selecao_aluno(),
            ),
        ],
        spacing=theme.ESPACO_PADRAO,
    )

    return ft.Column(
        [
            cabecalho,
            ft.Divider(),
            resumo,
            ft.Divider(),
            ft.Text(
                "Habilidades",
                size=theme.TAMANHO_SUBTITULO,
                weight=ft.FontWeight.BOLD,
            ),
            *habilidades,
            ft.Container(height=8),
            ft.Text(
                f"Próximo passo: {painel.proximo_passo}",
                size=theme.TAMANHO_TEXTO,
                color=theme.COR_TEXTO_SECUNDARIO,
            ),
            ft.Divider(),
            acoes,
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=theme.ESPACO_PADRAO,
        expand=True,
    )


def _construir_cartoes_de_resumo(
    painel: painel_aluno.PainelDoAluno,
) -> ft.Control:
    """Cartões com os números do resumo do progresso."""
    resumo = painel.resumo
    cartoes = [
        (ft.Icons.LIST, str(resumo.total_habilidades), "Total", theme.COR_PRIMARIA),
        (
            ft.Icons.RADIO_BUTTON_UNCHECKED,
            str(resumo.nao_iniciadas),
            "Não iniciadas",
            theme.COR_TEXTO_SECUNDARIO,
        ),
        (
            ft.Icons.PLAY_CIRCLE_OUTLINE,
            str(resumo.em_andamento),
            "Em andamento",
            theme.COR_PRIMARIA,
        ),
        (ft.Icons.CHECK_CIRCLE, str(resumo.concluidas), "Concluídas", theme.COR_SUCESSO),
    ]

    linha: list[ft.Control] = []
    for icone, numero, descricao, cor in cartoes:
        linha.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(icone, color=cor, size=24),
                            ft.Text(
                                numero,
                                size=theme.TAMANHO_TITULO,
                                weight=ft.FontWeight.BOLD,
                                color=cor,
                            ),
                            ft.Text(
                                descricao,
                                size=theme.TAMANHO_LEGENDA,
                                color=theme.COR_TEXTO_SECUNDARIO,
                            ),
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=theme.ESPACO_INTERNO,
                    width=120,
                )
            )
        )

    return ft.Row(linha, spacing=theme.ESPACO_PADRAO, wrap=True)


def _construir_lista_de_habilidades(
    app, painel: painel_aluno.PainelDoAluno
) -> list[ft.Control]:
    """Cartões clicáveis de cada habilidade."""
    elementos: list[ft.Control] = []

    for situacao in painel.habilidades:
        icone, cor = _icone_e_cor(situacao.situacao)
        texto_nivel = (
            situacao.nivel_atual
            if situacao.nivel_atual is not None
            else _texto_sem_nivel(situacao.situacao)
        )

        elementos.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    icone,
                                    ft.Text(
                                        situacao.nome,
                                        size=17,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                    ),
                                    ft.Text(
                                        situacao.situacao,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=cor,
                                    ),
                                    ft.Icon(
                                        ft.Icons.CHEVRON_RIGHT,
                                        color=theme.COR_TEXTO_SECUNDARIO,
                                    ),
                                ],
                                spacing=10,
                            ),
                            ft.Text(
                                situacao.descricao,
                                size=14,
                                color=ft.Colors.GREY_800,
                            ),
                            ft.Text(
                                texto_nivel,
                                size=13,
                                color=theme.COR_TEXTO_SECUNDARIO,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=theme.ESPACO_INTERNO,
                    # O clique fica no Container interno porque o Card
                    # do Flet 0.86.5 não aceita ``on_click`` diretamente.
                    on_click=lambda evento, h=situacao: app.mostrar_nivel(
                        h.habilidade_id
                    ),
                )
            )
        )

    return elementos


def _icone_e_cor(situacao: str) -> tuple[ft.Icon, str]:
    """Devolve (ícone, cor) conforme a situação da habilidade."""
    if situacao == "Concluída":
        return (
            ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme.COR_SUCESSO),
            theme.COR_SUCESSO,
        )
    if situacao == "Em andamento":
        return (
            ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, color=theme.COR_PRIMARIA),
            theme.COR_PRIMARIA,
        )
    return (
        ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=theme.COR_TEXTO_SECUNDARIO),
        theme.COR_TEXTO_SECUNDARIO,
    )


def _texto_sem_nivel(situacao: str) -> str:
    """Texto exibido quando não há nível atual para mostrar."""
    if situacao == "Não iniciada":
        return "Nível 1 será iniciado quando você começar."
    if situacao == "Concluída":
        return "Habilidade concluída."
    return ""