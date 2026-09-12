import flet as ft  # Flet: framework que permite criar interfaces gráficas (UI) com Python


def main(page: ft.Page) -> None:
    # O Flet chama esta função automaticamente ao iniciar o app,
    # fornecendo o objeto 'page', que representa a janela/interface exibida.
    page.title = "Plataforma de Ensino de Lógica de Programação"  # Título da janela
    page.add(ft.Text("Plataforma iniciada."))  # Adiciona um widget de texto à página


if __name__ == "__main__":
    # Este bloco só executa quando rodamos `python main.py` diretamente,
    # e não quando o módulo é importado por outro arquivo.
    # ft.run inicializa o loop do Flet e chama a função main como callback.
    ft.run(main)