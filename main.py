import flet as ft


def main(page: ft.Page) -> None:
    page.title = "Plataforma de Ensino de Lógica de Programação"
    page.add(ft.Text("Plataforma iniciada."))


if __name__ == "__main__":
    ft.run(main)