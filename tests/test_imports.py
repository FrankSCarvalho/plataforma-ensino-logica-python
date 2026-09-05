"""Garante que os módulos principais da aplicação importam sem erro."""

import importlib

# Módulos das camadas ativas da aplicação que devem importar corretamente.
MODULOS_PRINCIPAIS = [
    "app",
    "app.core",
    "app.core.config",
    "app.database",
    "app.database.connection",
    "app.database.initialize",
    "app.ui",
    "app.ui.main_view",
    "app.models",
    "app.repositories",
    "app.services",
]


def test_modulos_principais_importam_sem_erro():
    for nome in MODULOS_PRINCIPAIS:
        importlib.import_module(nome)


def test_entrada_principal_importa_sem_erro():
    # ``main.py`` fica na raiz do projeto; o caminho "." já está no sys.path
    # por causa da opção ``pythonpath`` do pyproject.toml.
    importlib.import_module("main")