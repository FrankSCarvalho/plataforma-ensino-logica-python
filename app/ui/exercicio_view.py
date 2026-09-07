"""Tela 4 — exercícios do nível atual (resposta, resultado e resumo).

Responsabilidades desta tela (APENAS apresentação):

    * exibir o enunciado do exercício corrente (vindo do banco);
    * coletar a resposta do aluno (campo multilinha para código e
      previsões de saída);
    * enviar a resposta AO SERVIÇO ``fluxo_estudo.responder``, que aciona
      avaliador -> tentativa -> motor pedagógico (nenhuma regra aqui);
    * mostrar o resultado, a mensagem de progressão (quando houver) e o
      resumo informativo do nível ao final da lista;
    * quando a resposta anterior causou progressão, exibir PRIMEIRO o
      resumo do nível recém-concluído (preservado em
      ``estado.resumo_nivel_concluido``) e só carregar o novo nível após
      a ação de continuar do aluno.

A tela NUNCA executa código do aluno e nunca decide pedagogia.
"""

import flet as ft

from app.models import (
    TIPO_COMPLETAR_CODIGO,
    TIPO_ESCREVER_CODIGO,
    TIPO_PREVER_RESULTADO,
    TIPO_RESPOSTA_TEXTUAL,
    RESULTADO_CORRETA,
    RESULTADO_INCORRETA,
    RESULTADO_PARCIALMENTE_CORRETA,
    Exercicio,
)
from app.services import fluxo_estudo
from app.ui.components import theme

# Rótulos amigáveis por tipo de exercício (a dica orienta o formato da
# resposta; a correção continua sendo responsabilidade do avaliador).
_DICA_POR_TIPO = {
    TIPO_PREVER_RESULTADO: (
        "Escreva a saída que o programa produz. Use uma linha por saída "
        "quando houver mais de uma."
    ),
    TIPO_ESCREVER_CODIGO: (
        "Escreva o código solicitado."
    ),
    TIPO_COMPLETAR_CODIGO: (
        "Preencha a lacuna do código. Escreva somente o que deve ocupar "
        "o espaço indicado."
    ),
}

# Mensagens claras por resultado. Importante: um exercício não avaliado
# NUNCA é apresentado como correto — a mensagem apenas informa que a
# resposta foi registrada.
_MENSAGEM_POR_RESULTADO = {
    RESULTADO_CORRETA: "Resposta correta! Muito bem.",
    RESULTADO_INCORRETA: (
        "A resposta não correspondeu ao esperado. "
        "Você pode tentar novamente."
    ),
    RESULTADO_PARCIALMENTE_CORRETA: (
        "A resposta está parcialmente correta."
    ),
    "nao_avaliada": (
        "Sua resposta foi registrada, mas este formato de exercício "
        "ainda não possui correção automática."
    ),
}

_COR_POR_RESULTADO = {
    RESULTADO_CORRETA: theme.COR_SUCESSO,
    RESULTADO_INCORRETA: theme.COR_ERRO,
    RESULTADO_PARCIALMENTE_CORRETA: theme.COR_PARCIAL,
    "nao_avaliada": theme.COR_TEXTO_SECUNDARIO,
}

_ICONE_POR_RESULTADO = {
    RESULTADO_CORRETA: ft.Icons.CHECK_CIRCLE,
    RESULTADO_INCORRETA: ft.Icons.CANCEL,
    RESULTADO_PARCIALMENTE_CORRETA: ft.Icons.TIMELAPSE,
    "nao_avaliada": ft.Icons.INFO_OUTLINE,
}


def build(app) -> ft.Control:
    """Monta a tela corrente: resumo de nível anterior -> exercício ou resumo (fim da lista)."""
    estado = app.estado_estudo
    
    # PRIORIDADE: Se há resumo de nível concluído (apenas após progressão),
    # mostrar o resumo do nível anterior antes de carregar o novo nível.
    if estado.resumo_nivel_concluido is not None:
        return _build_resumo_nivel_concluido(app, estado)
    
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
            ft.Text(f"Aluno: {app.aluno.nome}", size=theme.TAMANHO_LEGENDA),
            ft.Text(
                estado.habilidade.nome,
                size=theme.TAMANHO_SUBTITULO,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Row(
                [
                    ft.Text(
                        f"Nível: {estado.nivel.nome}",
                        size=theme.TAMANHO_TITULO,
                        weight=ft.FontWeight.BOLD,
                        color=theme.COR_PRIMARIA,
                        expand=True,
                    ),
                    ft.Text(
                        posicao,
                        size=theme.TAMANHO_LEGENDA,
                        color=theme.COR_TEXTO_SECUNDARIO,
                    ),
                ],
                spacing=8,
            ),
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
        # Bloquea enquanto processa: impede o envio repetido da MESMA
        # resposta através do mesmo botão.
        botao_enviar.disabled = True
        botao_continuar.disabled = True
        campo_resposta.disabled = True
        app.page.update()
        try:
            # Fluxo completo: avaliador -> tentativa -> motor -> progresso.
            fluxo_estudo.responder(estado, resposta)
        except Exception:
            app.mostrar_erro("Não foi possível registrar sua resposta.")
            botao_enviar.disabled = False
            botao_continuar.disabled = False
            campo_resposta.disabled = False
            app.page.update()
            return

        avaliacao = estado.ultima_avaliacao
        cor = _COR_POR_RESULTADO.get(avaliacao.resultado)
        elementos_resultado = [
            ft.Row(
                [
                    ft.Icon(
                        _ICONE_POR_RESULTADO.get(
                            avaliacao.resultado, ft.Icons.INFO_OUTLINE
                        ),
                        color=cor,
                    ),
                    ft.Text(
                        _MENSAGEM_POR_RESULTADO.get(
                            avaliacao.resultado, "Resultado registrado."
                        ),
                        size=theme.TAMANHO_TEXTO,
                        weight=ft.FontWeight.BOLD,
                        color=cor,
                    ),
                ],
                spacing=8,
            )
        ]
        if avaliacao.feedback:
            elementos_resultado.append(
                ft.Text(avaliacao.feedback, size=theme.TAMANHO_LEGENDA)
            )
        # A progressão NUNCA é decidida aqui: apenas o motor pedagógico
        # decide. A UI apenas comunica o resultado de forma clara.
        if estado.houve_progressao:
            elementos_resultado.append(
                ft.Text(
                    "Nível concluído. Você avançou para o próximo nível.",
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=theme.COR_PRIMARIA,
                )
            )
        else:
            # Mensagem neutra (nunca "falhaste"): o aluno simplesmente
            # continua praticando o nível atual.
            elementos_resultado.append(
                ft.Text(
                    "Você continuará praticando o nível atual.",
                    size=theme.TAMANHO_LEGENDA,
                    color=theme.COR_TEXTO_SECUNDARIO,
                )
            )
        area_resultado.content = ft.Column(elementos_resultado, spacing=6)
        area_resultado.visible = True
        # A tentativa já foi registrada: o campo e o botão permanecem
        # bloqueados (impede reenvio); só "Continuar" fica habilitado.
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


def _build_resumo_nivel_concluido(app, estado) -> ft.Control:
    """Resumo do nível recém-concluído, exibido antes do próximo nível.
    
    Mostra os dados do nível que acabou de ser concluído, sem usar os
    contadores do ciclo atual (que já foram resetados pelo fluxo de
    progressão). O resumo é armazenado em ``estado.resumo_nivel_concluido``
    no momento exato em que a progressão ocorre, preservando os dados do
    nível anterior.
    """
    resumo = estado.resumo_nivel_concluido
    
    def continuar(evento) -> None:
        """Limpa o resumo pendente e recarrega a tela para o novo nível."""
        estado.resumo_nivel_concluido = None
        app.mostrar_exercicios()
    
    return ft.Column(
        [
            _cabecalho(app, estado),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.SUMMARIZE,
                                    color=theme.COR_PRIMARIA,
                                ),
                                ft.Text(
                                    f"Nível {resumo['nivel_nome']} — concluído",
                                    size=theme.TAMANHO_SUBTITULO,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Divider(),
                        ft.Text(
                            f"Exercícios respondidos: {resumo['total_respondidos']}",
                            size=theme.TAMANHO_TEXTO,
                        ),
                        ft.Text(
                            f"Corretas: {resumo['corretas']}  ·  "
                            f"Incorretas: {resumo['incorretas']}  ·  "
                            f"Não avaliadas: {resumo['nao_avaliadas']}",
                            size=theme.TAMANHO_TEXTO,
                        ),
                        ft.Divider(),
                        ft.Text(
                            f"Situação: {resumo['situacao']}",
                            size=theme.TAMANHO_TEXTO,
                            weight=ft.FontWeight.BOLD,
                            color=theme.COR_SUCESSO,
                        ),
                        ft.Divider(),
                        ft.Text(
                            f"Próximo passo: {resumo['proximo_passo']}",
                            size=theme.TAMANHO_TEXTO,
                        ),
                        ft.Text(
                            "Os dados mostrados são informativos: a decisão de "
                            "avançar de nível foi do motor pedagógico, com base "
                            "no seu histórico de respostas.",
                            size=theme.TAMANHO_LEGENDA,
                            color=theme.COR_TEXTO_SECUNDARIO,
                        ),
                    ],
                    spacing=6,
                ),
                padding=16,
            ),
            ft.FilledButton(
                "Continuar para o próximo nível",
                icon=ft.Icons.ARROW_FORWARD,
                on_click=continuar,
            ),
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
    respondidos = (
        estado.corretas + estado.incorretas + estado.nao_avaliadas
    )
    _, total_niveis = fluxo_estudo.posicao_do_nivel(estado)
    nivel_concluido = estado.progresso.status == "concluido"

    # Próximo passo: texto informativo (a UI NUNCA decide pedagogía —
    # apenas orienta com base no que o motor pedagógico já registrou).
    if nivel_concluido and total_niveis == 0:
        proximo_passo = "Habilidade concluida."
    elif nivel_concluido:
        proximo_passo = (
            "Nível concluído. Você pode avançar ao próximo nível a partir "
            "da lista de habilidades."
        )
    else:
        proximo_passo = (
            "Continue praticando: suas tentativas continuam contando para "
            "demonstrar domínio do nível."
        )

    resumo = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.SUMMARIZE,
                                color=theme.COR_PRIMARIA,
                            ),
                            ft.Text(
                                f"Nível {estado.nivel.nome} — ciclo concluído",
                                size=theme.TAMANHO_SUBTITULO,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        f"Ciclo encerrado: {respondidos} exercício(s) "
                        "respondidos.",
                        size=theme.TAMANHO_LEGENDA,
                        color=theme.COR_TEXTO_SECUNDARIO,
                    ),
                    ft.Divider(),
                    ft.Text(
                        f"Corretas: {estado.corretas}  ·  "
                        f"Incorretas: {estado.incorretas}  ·  "
                        f"Não avaliadas: {estado.nao_avaliadas}"
                    ),
                    ft.Text(
                        f"Situação do nível: {situacao}",
                        size=theme.TAMANHO_TEXTO,
                        weight=ft.FontWeight.BOLD,
                        color=(
                            theme.COR_SUCESSO
                            if nivel_concluido
                            else theme.COR_TEXTO_SECUNDARIO
                        ),
                    ),
                    ft.Divider(),
                    ft.Text(
                        f"Próximo passo: {proximo_passo}",
                        size=theme.TAMANHO_TEXTO,
                    ),
                    ft.Text(
                        "Os dados mostrados são informativos: a decisão de "
                        "avançar de nível é do motor pedagógico, com base "
                        "no seu histórico de respostas.",
                        size=theme.TAMANHO_LEGENDA,
                        color=theme.COR_TEXTO_SECUNDARIO,
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