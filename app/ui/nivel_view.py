"""Tela 3 — conteúdo conceitual do nível atual.

Apresenta o material de estudo armazenado no banco (título, explicação,
exemplos e observações do nível). É apenas leitura: NÃO existe editor
de conteúdo nem CMS — o texto vem integralmente da tabela ``niveis``.
"""

import flet as ft

from app.services import fluxo_estudo
from app.services.motor_pedagogico import STATUS_CONCLUIDO


def _bloco(titulo: str, conteudo: str, icone) -> ft.Control | None:
    """Cria um cartão de conteúdo, ocultando seções vazias no banco."""
    texto = (conteudo or "").strip()
    if not texto:
        return None  # seção não preenchida: simplesmente não é exibida
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(titulo, weight=ft.FontWeight.BOLD, size=15),
                    ft.Text(texto, size=14, selectable=True),
                ],
                spacing=6,
            ),
            padding=14,
        )
    )


def build(app) -> ft.Control:
    """Monta a tela do nível a partir do estado de estudo corrente."""
    estado = app.estado_estudo
    nivel = estado.nivel

    cabecalho = ft.Column(
        [
            ft.Text(f"Aluno: {app.aluno.nome}", size=14),
            ft.Text(
                f"Habilidade: {estado.habilidade.nome}",
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                f"Nível atual: {nivel.nome}",
                size=22,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_900,
            ),
            ft.Text(
                "Situação: "
                + (
                    "concluído"
                    if estado.progresso.status == STATUS_CONCLUIDO
                    else "em andamento"
                ),
                size=13,
                color=ft.Colors.GREY_700,
            ),
            ft.Divider(),
        ],
        spacing=8,
    )

    # ---- Conteúdo conceitual (4 seções simples, texto puro) ------------
    # O título do conteúdo é exibido como subtítulo; os demais blocos
    # viram cartões. Seções vazias no banco simplesmente não aparecem.
    secoes = []
    if (nivel.conteudo_titulo or "").strip():
        secoes.append(
            ft.Text(nivel.conteudo_titulo, size=18, weight=ft.FontWeight.BOLD)
        )
    secoes.extend(
        [
            _bloco("Explicação", nivel.conteudo_explicacao, None),
            _bloco("Exemplos", nivel.conteudo_exemplos, None),
            _bloco("Observações importantes", nivel.conteudo_observacoes, None),
            ft.Container(height=8),
        ]
    )
    conteudo = ft.Column(secoes, spacing=12)

    def iniciar_exercicios(evento) -> None:
        """Cria a sessão de estudo e segue para a tela de exercícios."""
        try:
            fluxo_estudo.iniciar_sessao(estado)
        except Exception:
            app.mostrar_erro("Não foi possível iniciar a sessão de estudo.")
            return
        app.mostrar_exercicios()

    acoes = ft.Row(
        [
            ft.OutlinedButton(
                "Voltar às habilidades",
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda evento: app.mostrar_habilidades(),
            ),
            ft.FilledButton(
                "Iniciar exercícios",
                icon=ft.Icons.PLAY_ARROW,
                on_click=iniciar_exercicios,
            ),
        ],
        spacing=12,
    )

    return ft.Column(
        [cabecalho, conteudo, acoes],
        scroll=ft.ScrollMode.AUTO,
        spacing=10,
    )