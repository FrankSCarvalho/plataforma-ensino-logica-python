"""Tela 3 — conteúdo conceitual do nível atual.

Apresenta o material de estudo armazenado no banco (título, explicação,
exemplos e observações do nível) de forma organizada:

    Título  ->  Explicação  ->  Exemplos  ->  Observações  ->  Iniciar

É apenas leitura: NÃO existe editor de conteúdo nem CMS — o texto vem
integralmente da tabela ``niveis``. Seções vazias não são exibidas.
"""

import flet as ft

from app.services import fluxo_estudo
from app.services.motor_pedagogico import STATUS_CONCLUIDO
from app.ui.components import theme
from app.ui.components.widgets import cabecalho_estudo, cartao_conteudo


def build(app) -> ft.Control:
    """Monta a tela do nível a partir do estado de estudo corrente."""
    estado = app.estado_estudo
    nivel = estado.nivel
    posicao, total = fluxo_estudo.posicao_do_nivel(estado)

    rotulo_posicao = (
        f"Nível {posicao} de {total}" if total else nivel.nome
    )

    # Cabeçalho claro: o que estamos estudando e em que ponto estamos.
    cabecalho = cabecalho_estudo(app, estado, rotulo_posicao)

    # ---- Conteúdo conceitual (4 seções simples, texto puro) ------------
    # O título do conteúdo é exibido como subtítulo; as demais seções
    # viram cartões. Seções vazias no banco simplesmente não aparecem.
    secoes: list[ft.Control] = []
    if (nivel.conteudo_titulo or "").strip():
        secoes.append(
            ft.Text(
                nivel.conteudo_titulo,
                size=theme.TAMANHO_SUBTITULO,
                weight=ft.FontWeight.BOLD,
                color=theme.COR_PRIMARIA,
            )
        )
    secoes.extend(
        [
            cartao_conteudo("Explicação", nivel.conteudo_explicacao),
            cartao_conteudo("Exemplos", nivel.conteudo_exemplos),
            cartao_conteudo(
                "Observações importantes", nivel.conteudo_observacoes
            ),
        ]
    )
    # Garante espaçamento mesmo quando todas as seções estiverem vazias.
    secoes = [s for s in secoes if s is not None] or [
        ft.Text(
            "Este nível ainda não possui conteúdo conceitual.",
            color=theme.COR_TEXTO_SECUNDARIO,
        )
    ]
    conteudo = ft.Column(secoes, spacing=theme.ESPACO_SECAO)

    situacao = (
        "concluído"
        if estado.progresso.status == STATUS_CONCLUIDO
        else "em andamento"
    )

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
        spacing=theme.ESPACO_SECAO,
    )

    return ft.Column(
        [
            cabecalho,
            ft.Text(
                f"Você está no nível: {nivel.nome} — situação: {situacao}.",
                size=theme.TAMANHO_TEXTO,
                color=theme.COR_TEXTO_SECUNDARIO,
            ),
            conteudo,
            ft.Container(height=8),
            acoes,
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=theme.ESPACO_PADRAO,
        expand=True,
    )