"""Tela 4 — exercícios do nível atual (resposta, resultado e resumo).

Responsabilidades desta tela (APENAS apresentação):

    * exibir o enunciado do exercício corrente (vindo do banco);
    * coletar a resposta do aluno (campo multilinha para código e
      previsões de saída);
    * enviar a resposta AO SERVIÇO ``fluxo_estudo.responder``, que aciona
      avaliador -> tentativa -> motor pedagógico (nenhuma regra aqui);
    * mostrar o resultado, a mensagem de progressão (quando houver) e o
      resumo informativo do nível ao final da lista.

A tela NUNCA executa código do aluno e nunca decide pedagogia.
"""

import flet as ft

from app.models import (
    RESULTADO_CORRETA,
    RESULTADO_INCORRETA,
    TIPO_ESCREVER_CODIGO,
    TIPO_PREVER_RESULTADO,
)
from app.services import fluxo_estudo

# Rótulos amigáveis por tipo de exercício (a dica orienta o formato da
# resposta; a correção continua sendo responsabilidade do avaliador).
_DICA_POR_TIPO = {
    TIPO_PREVER_RESULTADO: (
        "Escreva a saída que o programa produz. Use uma linha por saída "
        "quando houver mais de uma."
    ),
    TIPO_ESCREVER_CODIGO: (
        "Escreva o código solicitado. Ele não é executado pelo "
        "aplicativo; a correção automática será implantada no futuro."
    ),
}


def _rotulo_do_resultado(resultado: str) -> str:
    """Converte o valor interno do resultado em texto amigável."""
    return {
        RESULTADO_CORRETA: "Correta!",
        RESULTADO_INCORRETA: "Incorreta.",
        "parcialmente_correta": "Parcialmente correta.",
        "nao_avaliada": "Resposta registrada (ainda não avaliada).",
    }.get(resultado, resultado)


def build(app) -> ft.Control:
    """Monta a tela corrente: exercício ou resumo (fim da lista)."""
    estado = app.estado_estudo
    exercicio = fluxo_estudo.exercicio_atual(estado)
    if exercicio is None:
        return _build_resumo(app, estado)
    return _build_exercicio(app, estado, exercicio)


def _cabecalho(app, estado) -> ft.Column:
    """Cabeçalho comum: aluno, habilidade, nível e posição na lista."""
    posicao = ""
    if estado.exercicios:
        posicao = (
            f"Exercício {min(estado.indice_exercicio + 1, len(estado.exercicios))} "
            f"de {len(estado.exercicios)}"
        )
    return ft.Column(
        [
            ft.Text(f"Aluno: {app.aluno.nome}", size=14),
            ft.Text(estado.habilidade.nome, size=15, weight=ft.FontWeight.BOLD),
            ft.Text(
                f"Nível: {estado.nivel.nome}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_900,
            ),
            ft.Text(posicao, size=13, color=ft.Colors.GREY_700),
            ft.Divider(),
        ],
        spacing=6,
    )


def _build_exercicio(app, estado, exercicio) -> ft.Control:
    """Tela do exercício corrente com envio e resultado."""
    # ---- Enunciado ------------------------------------------------------
    enunciado = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("Enunciado", size=13, color=ft.Colors.GREY_700),
                    ft.Text(exercicio.enunciado, size=16, selectable=True),
                ],
                spacing=4,
            ),
            padding=14,
        )
    )
    dica = _DICA_POR_TIPO.get(exercicio.tipo)

    # ---- Campo de resposta (multilinha: serve para todos os tipos) -----
    campo_resposta = ft.TextField(
        label="Sua resposta",
        hint_text=dica or "Digite sua resposta",
        multiline=True,
        min_lines=3,
        max_lines=8,
        expand=True,
    )

    # ---- Área de resultado (preenchida após o envio) --------------------
    area_resultado = ft.Container(visible=False)

    # O envio trava o botão até o processamento terminar, impedindo o
    # envio repetido da mesma resposta pelo mesmo botão.
    botao_enviar = ft.FilledButton("Enviar resposta", icon=ft.Icons.SEND)
    botao_continuar = ft.FilledButton(
        "Continuar", icon=ft.Icons.ARROW_FORWARD, disabled=True
    )

    def enviar(evento) -> None:
        resposta = campo_resposta.value or ""
        if not resposta.strip():
            app.mostrar_aviso("Escreva uma resposta antes de enviar.")
            return
        botao_enviar.disabled = True
        botao_continuar.disabled = True
        app.page.update()
        try:
            # Fluxo completo: avaliador -> tentativa -> motor -> progresso.
            fluxo_estudo.responder(estado, resposta)
        except Exception:
            app.mostrar_erro("Não foi possível registrar sua resposta.")
            botao_enviar.disabled = False
            app.page.update()
            return

        avaliacao = estado.ultima_avaliacao
        cor = {
            RESULTADO_CORRETA: ft.Colors.GREEN_700,
            RESULTADO_INCORRETA: ft.Colors.RED_700,
        }.get(avaliacao.resultado, ft.Colors.GREY_800)
        elementos_resultado = [
            ft.Text(
                _rotulo_do_resultado(avaliacao.resultado),
                size=16,
                weight=ft.FontWeight.BOLD,
                color=cor,
            )
        ]
        if avaliacao.feedback:
            elementos_resultado.append(ft.Text(avaliacao.feedback, size=14))
        if estado.houve_progressao:
            elementos_resultado.append(
                ft.Text(
                    "Nível concluído. Próximo nível liberado!",
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                )
            )
        area_resultado.content = ft.Column(elementos_resultado, spacing=4)
        area_resultado.visible = True
        # A resposta já foi processada: liberar "Continuar" e manter o
        # envio travado (a tentativa já registrada não pode se duplicar).
        botao_continuar.disabled = False
        app.page.update()

    botao_enviar.on_click = enviar

    def continuar(evento) -> None:
        # Recria a tela mostrando o exercício corrente (ou o resumo).
        app.mostrar_exercicios()

    botao_continuar.on_click = continuar

    def encerrar(evento) -> None:
        """Sai do fluxo encerrando a sessão de estudo normalmente."""
        try:
            fluxo_estudo.encerrar_sessao(estado)
        except Exception:
            app.mostrar_erro("Não foi possível encerrar a sessão.")
            return
        app.estado_estudo = None
        app.mostrar_aviso("Sessão de estudo encerrada.")
        app.mostrar_habilidades()

    acoes = ft.Row(
        [
            botao_enviar,
            botao_continuar,
            ft.OutlinedButton(
                "Encerrar sessão", icon=ft.Icons.LOGOUT, on_click=encerrar
            ),
        ],
        spacing=12,
        wrap=True,
    )

    return ft.Column(
        [
            _cabecalho(app, estado),
            enunciado,
            campo_resposta,
            area_resultado,
            acoes,
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=12,
        expand=True,
    )


def _build_resumo(app, estado) -> ft.Control:
    """Resumo INFORMATIVO do nível (fim da lista de exercícios).

    Os números são apenas para orientar o aluno: NENHUMA decisão
    pedagógica é tomada aqui — o domínio e a progressão continuam sendo
    responsabilidade exclusiva do motor pedagógico (que já atualizou o
    progresso durante as respostas).
    """
    situacao = (
        "concluído"
        if estado.progresso.status == "concluido"
        else "em andamento"
    )
    resumo = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"Nível {estado.nivel.nome} — ciclo concluído",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(f"Respostas corretas: {estado.corretas}"),
                    ft.Text(f"Respostas incorretas: {estado.incorretas}"),
                    ft.Text(
                        f"Respostas não avaliadas: {estado.nao_avaliadas}"
                    ),
                    ft.Text(f"Situação do nível: {situacao}"),
                    ft.Text(
                        "Você pode praticar novamente este nível: as "
                        "tentativas anteriores continuam valendo para a "
                        "sua evolução.",
                        size=13,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                spacing=6,
            ),
            padding=16,
        )
    )

    def praticar_novamente(evento) -> None:
        """Recomeça a lista do nível (o histórico nunca é reiniciado)."""
        fluxo_estudo.reiniciar_lista_de_exercicios(estado)
        app.mostrar_exercicios()

    def encerrar(evento) -> None:
        """Saída normal do fluxo: encerra a sessão de estudo."""
        try:
            fluxo_estudo.encerrar_sessao(estado)
        except Exception:
            app.mostrar_erro("Não foi possível encerrar a sessão.")
            return
        app.estado_estudo = None
        app.mostrar_aviso("Sessão de estudo encerrada.")
        app.mostrar_habilidades()

    acoes = ft.Row(
        [
            ft.FilledButton(
                "Praticar novamente",
                icon=ft.Icons.REFRESH,
                on_click=praticar_novamente,
            ),
            ft.OutlinedButton(
                "Encerrar sessão",
                icon=ft.Icons.LOGOUT,
                on_click=encerrar,
            ),
        ],
        spacing=12,
        wrap=True,
    )

    return ft.Column(
        [
            _cabecalho(app, estado),
            resumo,
            acoes,
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=12,
        expand=True,
    )