"""Identidade visual centralizada da interface (Tarefa 09).

Concentra cores, espaçamentos e tamanhos de texto usados pelas telas,
evitando valores repetidos e "chapados" diretamente nas views. Ajustar
este módulo muda a aparência do aplicativo inteiro de forma consistente.
"""

import flet as ft

# ---- Paleta ---------------------------------------------------------------
COR_PRIMARIA = ft.Colors.BLUE_900           # títulos e destaques principais
COR_DESTAQUE_FUNDO = ft.Colors.BLUE_50      # fundo de itens clicáveis
COR_SUCESSO = ft.Colors.GREEN_700            # respostas corretas
COR_ERRO = ft.Colors.RED_700                 # respostas incorretas / erros
COR_PARCIAL = ft.Colors.AMBER_800            # parcialmente correta
COR_AVISO = ft.Colors.ORANGE_800             # avisos
COR_AVISO_FUNDO = ft.Colors.ORANGE_50        # fundo de avisos
COR_TEXTO_SECUNDARIO = ft.Colors.GREY_700    # legendas e informações

# ---- Espaçamentos (px) ------------------------------------------------------
PADDING_PAGINA = 24       # margem-padrão da página
ESPACO_PADRAO = 10        # espaçamento-base entre elementos
ESPACO_SECAO = 12         # espaçamento entre seções
ESPACO_INTERNO = 14       # padding interno de cartões/blocos

# ---- Texto -------------------------------------------------------------------
TAMANHO_TITULO_PAGINA = 28
TAMANHO_TITULO = 22
TAMANHO_SUBTITULO = 18
TAMANHO_TEXTO = 14
TAMANHO_LEGENDA = 13

# Família de letra monoespaçada usada para mostrar código (código
# fonte/exercícios de completar código). Centraliza a escolha para
# manter a aparência do código consistente em toda a plataforma.
FUENTE_CODIGO = "Consolas"